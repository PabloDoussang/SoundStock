"""Pruebas funcionales: SimpleTestCase impide acceder a cualquier base de datos."""
import tempfile
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from . import store


PASSWORD = 'Fixture-Segura-739!'


class WarehouseTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password_hash = make_password(PASSWORD)

    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='soundstock-functional-')
        self.addCleanup(folder.cleanup)
        self.data_path = Path(folder.name) / 'bodega.json'
        override = override_settings(U1_DATA_FILE=self.data_path)
        override.enable()
        self.addCleanup(override.disable)
        with store.edit() as data:
            data['users'] = [
                dict(id=number, username=name, first_name=name, last_name='', email='',
                     role=role, is_active=True, password=self.password_hash, session_version=f'v{number}')
                for number, name, role in [(1, 'Admin prueba', 'Administrador'),
                                           (2, 'Operador prueba', 'Operador'),
                                           (3, 'Consulta prueba', 'Consulta')]
            ]
            data['products'] = [dict(id=1, code='MP-TEST', name='Guitarra de prueba',
                                    category='Cuerdas', location='A-01', minimum=3, stock=0, active=True)]
        self.login()

    def login(self, username='Admin prueba', password=PASSWORD, client=None):
        client = client or self.client
        if client.get(reverse('dashboard')).status_code == 200:
            client.post(reverse('logout'))
        response = client.post(reverse('login'), {'username': username, 'password': password})
        self.assertEqual(response.status_code, 302)
        return client

    def movement(self, kind='entrada', quantity=10, **changes):
        values = dict(product=1, kind=kind, quantity=quantity, reason='Prueba controlada',
                      destination='Sucursal del rock' if kind == 'salida' else '', token=str(uuid.uuid4()))
        values.update(changes)
        return self.client.post(reverse('movement_new'), values)

    def account_data(self, **changes):
        data = dict(username='Pablo Doussang', first_name='Pablo', last_name='Doussang',
                    email='', is_active='on', role='Administrador', password=PASSWORD)
        data.update(changes)
        return data

    def test_all_sections_forms_and_missing_objects(self):
        for name in ['dashboard', 'products', 'movement_new', 'movements', 'reports',
                     'locations', 'users', 'product_new', 'user_new']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        for name in ['product_edit', 'user_edit', 'product_archive']:
            self.assertEqual(self.client.get(reverse(name, args=[1])).status_code, 200)
            self.assertEqual(self.client.get(reverse(name, args=[999])).status_code, 404)

    def test_login_required(self):
        anonymous = Client()
        for name in ['dashboard', 'products', 'movement_new', 'movements', 'reports', 'locations', 'users']:
            with self.subTest(name=name):
                self.assertEqual(anonymous.get(reverse(name)).status_code, 302)

    def test_reader_can_read_but_cannot_mutate(self):
        self.login('Consulta prueba')
        before = store.read()
        for name, args in [('product_new', []), ('movement_new', []), ('product_edit', [1]),
                           ('product_archive', [1]), ('users', []), ('user_new', []), ('user_edit', [1])]:
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(name, args=args), {}).status_code, 403)
        self.assertEqual(store.read(), before)
        for name in ['dashboard', 'products', 'movements', 'reports', 'locations']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_operator_can_move_stock_but_cannot_manage_accounts_or_archive(self):
        self.login('Operador prueba')
        self.assertEqual(self.client.get(reverse('product_new')).status_code, 200)
        self.assertEqual(self.movement(quantity=4).status_code, 302)
        for name, args in [('users', []), ('user_new', []), ('user_edit', [1]), ('product_archive', [1])]:
            self.assertEqual(self.client.post(reverse(name, args=args), {}).status_code, 403)
        self.assertEqual(store.read()['products'][0]['stock'], 4)

    def test_stock_lifecycle_audit_and_statistics(self):
        for kind, quantity in [('entrada', 10), ('salida', 4), ('ajuste', 2)]:
            self.assertEqual(self.movement(kind, quantity).status_code, 302)
        saved = store.read()
        self.assertEqual(saved['products'][0]['stock'], 2)
        self.assertEqual([(m['before'], m['after'], m['delta']) for m in saved['movements']],
                         [(0, 10, 10), (10, 6, -4), (6, 2, -4)])
        self.assertTrue(all(m['user'] == 1 and m['product'] == 1 for m in saved['movements']))
        report = self.client.get(reverse('reports'))
        self.assertEqual((report.context['entries'], report.context['exits'], report.context['adjustments']), (10, 4, -4))
        self.assertEqual(sum(c['total'] for c in report.context['categories']), 2)

    def test_duplicate_submission_does_not_duplicate_stock(self):
        token = str(uuid.uuid4())
        self.assertEqual(self.movement(token=token).status_code, 302)
        self.assertEqual(self.movement(token=token).status_code, 302)
        self.assertEqual(store.read()['products'][0]['stock'], 10)
        self.assertEqual(len(store.read()['movements']), 1)
        self.login('Operador prueba')
        self.assertContains(self.movement(token=token), 'Identificador de operación inválido')
        self.assertEqual(len(store.read()['movements']), 1)

    def test_insufficient_stock_and_limits_leave_saved_data_unchanged(self):
        self.movement(quantity=10)
        before = self.data_path.read_bytes()
        self.assertContains(self.movement('salida', 11), 'Stock insuficiente')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertContains(self.movement(quantity=1000000), 'máximo permitido')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertContains(self.movement('ajuste', 10), 'no modifica')
        self.assertEqual(self.data_path.read_bytes(), before)

    def test_invalid_movement_fields_do_not_change_data(self):
        before = store.read()
        for changes in [dict(quantity=-1), dict(quantity=0), dict(quantity=1000001),
                        dict(kind='otro'), dict(reason=''), dict(token='inválido'),
                        dict(product=999), dict(kind='salida', destination='')]:
            with self.subTest(changes=changes):
                self.assertEqual(self.movement(**changes).status_code, 200)
                self.assertEqual(store.read(), before)

    def test_product_create_edit_and_unique_code(self):
        data = dict(code='MP-NEW', name='Teclado nuevo', category='Teclados', location='B-03', minimum=4)
        self.assertEqual(self.client.post(reverse('product_new'), data).status_code, 302)
        self.assertEqual(store.read()['products'][1]['stock'], 0)
        self.assertContains(self.client.post(reverse('product_new'), data), 'ya existe')
        data.update(name='Teclado editado', location='C-04')
        self.assertEqual(self.client.post(reverse('product_edit', args=[2]), data).status_code, 302)
        self.assertContains(self.client.get(reverse('products') + '?q=editado'), 'Teclado editado')
        self.assertEqual(store.read()['products'][1]['location'], 'C-04')
        invalid = {**data, 'code': 'inválido', 'minimum': -1}
        self.assertEqual(self.client.post(reverse('product_new'), invalid).status_code, 200)
        self.assertEqual(len(store.read()['products']), 2)

    def test_archive_requires_zero_and_keeps_history(self):
        self.movement()
        archive = reverse('product_archive', args=[1])
        self.client.post(archive)
        self.assertTrue(store.read()['products'][0]['active'])
        self.movement('ajuste', 0)
        self.client.post(archive)
        self.assertFalse(store.read()['products'][0]['active'])
        self.assertEqual(len(store.read()['movements']), 2)
        self.assertContains(self.client.get(reverse('products') + '?archived=1'), 'MP-TEST')
        self.assertEqual(self.client.get(reverse('product_edit', args=[1])).status_code, 404)
        self.assertEqual(self.movement().status_code, 200)
        self.assertEqual(len(store.read()['movements']), 2)
        self.client.post(archive)
        self.assertTrue(store.read()['products'][0]['active'])

    def test_spaced_username_and_password_edits_are_saved(self):
        data = self.account_data()
        self.assertEqual(self.client.post(reverse('user_new'), data).status_code, 302)
        saved = store.read()['users'][3]
        self.assertNotEqual(saved['password'], PASSWORD)
        self.assertTrue(check_password(PASSWORD, saved['password']))
        data.update(first_name='Pablo actualizado', password='')
        self.assertEqual(self.client.post(reverse('user_edit', args=[4]), data).status_code, 302)
        self.assertEqual(store.read()['users'][3]['password'], saved['password'])
        self.assertEqual(store.read()['users'][3]['first_name'], 'Pablo actualizado')
        self.login('Pablo Doussang')
        self.assertEqual(self.client.get(reverse('users')).status_code, 200)

    def test_duplicate_users_and_self_protection(self):
        before = store.read()
        duplicate = self.account_data(username='Admin prueba')
        self.assertContains(self.client.post(reverse('user_new'), duplicate), 'Ya existe')
        own = {**duplicate, 'role': 'Consulta', 'password': ''}
        self.assertContains(self.client.post(reverse('user_edit', args=[1]), own), 'propia cuenta')
        own.update(role='Administrador', is_active='')
        self.assertContains(self.client.post(reverse('user_edit', args=[1]), own), 'propia cuenta')
        self.assertEqual(store.read(), before)

    def test_password_change_and_deactivation_revoke_existing_sessions(self):
        reader = self.login('Consulta prueba', client=Client())
        data = self.account_data(username='Consulta prueba', role='Consulta', password='Fixture-Cambiada-832!')
        self.assertEqual(self.client.post(reverse('user_edit', args=[3]), data).status_code, 302)
        self.assertEqual(reader.get(reverse('products')).status_code, 302)
        self.assertEqual(reader.post(reverse('login'), {'username': 'Consulta prueba', 'password': PASSWORD}).status_code, 200)
        self.login('Consulta prueba', data['password'], reader)
        self.assertEqual(reader.get(reverse('products')).status_code, 200)
        data.update(password='', is_active='')
        self.assertEqual(self.client.post(reverse('user_edit', args=[3]), data).status_code, 302)
        self.assertEqual(reader.get(reverse('products')).status_code, 302)
        self.assertFalse(store.read()['users'][2]['is_active'])

    def test_logout_and_external_redirect_protection(self):
        cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertEqual(self.client.post(reverse('logout')).status_code, 302)
        self.assertEqual(self.client.get(reverse('products')).status_code, 302)
        replay = Client()
        replay.cookies[settings.SESSION_COOKIE_NAME] = cookie
        self.assertEqual(replay.get(reverse('products')).status_code, 302)
        response = self.client.post(reverse('login'), dict(username='Admin prueba', password=PASSWORD, next='https://example.com'))
        self.assertEqual(response.url, reverse('dashboard'))

    def test_csrf_is_required_for_mutation(self):
        secure = Client(enforce_csrf_checks=True)
        secure.cookies = self.client.cookies
        before = store.read()
        for name in ['movement_new', 'product_new', 'user_new', 'logout']:
            self.assertEqual(secure.post(reverse(name), {}).status_code, 403)
        self.assertEqual(store.read(), before)

    def test_dates_filters_and_exports(self):
        self.movement()
        self.assertContains(self.client.get(reverse('reports') + '?start=2026-12-31&end=2026-01-01'), 'no puede ser posterior')
        self.assertEqual(self.client.get(reverse('export', args=['movimientos']) + '?start=bad').status_code, 400)
        self.assertContains(self.client.get(reverse('export', args=['inventario'])), 'MP-TEST')
        self.assertContains(self.client.get(reverse('export', args=['movimientos'])), 'Prueba controlada')
        self.assertEqual(self.client.get(reverse('export', args=['desconocido'])).status_code, 404)
        self.assertEqual(self.client.get(reverse('movements') + '?kind=salida').context['count'], 0)

    def test_stock_alert_search_and_pagination(self):
        self.movement(quantity=3)
        self.assertEqual(self.client.get(reverse('dashboard')).context['low_count'], 1)
        self.assertContains(self.client.get(reverse('products') + '?status=low'), 'MP-TEST')
        self.assertNotContains(self.client.get(reverse('products') + '?q=No-existe'), 'MP-TEST')
        with store.edit() as data:
            for i in range(2, 15):
                data['products'].append(dict(id=i, code=f'MP-EXTRA-{i}', name=f'Guitarra {i}',
                    category='Cuerdas', location='A', minimum=1, stock=0, active=True))
        self.assertContains(self.client.get(reverse('products') + '?q=Guitarra'), 'q=Guitarra&amp;page=2')

    def test_empty_inventory_and_initial_setup_message(self):
        with store.edit() as data:
            data['products'] = []
        self.assertContains(self.client.get(reverse('products')), 'No hay productos')
        self.assertEqual(self.client.get(reverse('reports')).status_code, 200)
        with store.edit() as data:
            data['users'] = []
        self.assertContains(self.client.get(reverse('login')), 'iniciar.bat')

    def test_failed_write_keeps_previous_file(self):
        before = self.data_path.read_bytes()
        with self.assertRaises(RuntimeError):
            with store.edit() as data:
                data['products'][0]['stock'] = 999
                raise RuntimeError('Operación interrumpida antes de confirmar')
        self.assertEqual(self.data_path.read_bytes(), before)
