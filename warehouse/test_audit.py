"""Regresiones de la revisión U1; cada prueba usa archivos JSON temporales."""
import io
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from . import store
from .views import SAVE_ERROR


PASSWORD = 'Audit-Resistente-624!'


class AuditRegressionTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.password_hash = make_password(PASSWORD)

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='soundstock-audit-')
        self.addCleanup(directory.cleanup)
        self.data_path = Path(directory.name) / 'bodega.json'
        override = override_settings(U1_DATA_FILE=self.data_path)
        override.enable()
        self.addCleanup(override.disable)
        with store.edit() as data:
            data['users'] = [
                dict(id=number, username=username, first_name='', last_name='', email='',
                     role=role, is_active=True, password=self.password_hash, session_version=f'v{number}')
                for number, username, role in [(1, 'Administrador audit', 'Administrador'),
                                               (2, 'Consulta audit', 'Consulta')]
            ]
            data['products'] = [dict(id=1, code='MP-AUDIT', name='Guitarra audit',
                                    category='Cuerdas', location='A-01', minimum=2, stock=5, active=True)]
        self.assertEqual(self.client.post(reverse('login'),
                         dict(username='Administrador audit', password=PASSWORD)).status_code, 302)

    def account(self, **changes):
        return {**dict(username='Persona nueva', first_name='', last_name='', email='',
                       role='Consulta', is_active='on', password=PASSWORD), **changes}

    def test_password_spaces_survive_initial_setup_and_web_creation(self):
        password = '  Clave-Exacta-835!  '
        initial_path = self.data_path.with_name('inicial.json')
        with override_settings(U1_DATA_FILE=initial_path), \
                patch('builtins.input', side_effect=['Cuenta inicial', 'n']), \
                patch('warehouse.management.commands.preparar.getpass', side_effect=[password, password]):
            call_command('preparar', stdout=io.StringIO())
            browser = Client()
            self.assertEqual(browser.post(reverse('login'),
                             dict(username='Cuenta inicial', password=password)).status_code, 302)
            saved = store.read()['users'][0]
            self.assertTrue(check_password(password, saved['password']))
            self.assertFalse(check_password(password.strip(), saved['password']))

        response = self.client.post(reverse('user_new'), self.account(password=password))
        self.assertEqual(response.status_code, 302)
        saved = store.read()['users'][-1]
        self.assertTrue(check_password(password, saved['password']))
        self.assertFalse(check_password(password.strip(), saved['password']))
        browser = Client()
        self.assertEqual(browser.post(reverse('login'),
                         dict(username='Persona nueva', password=password.strip())).status_code, 200)
        self.assertEqual(browser.post(reverse('login'),
                         dict(username='Persona nueva', password=password)).status_code, 302)

    def test_similar_password_is_rejected_in_web_and_initial_setup(self):
        same = 'CoincidenciaSegura937'
        before = self.data_path.read_bytes()
        response = self.client.post(reverse('user_new'), self.account(username=same, password=same))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].errors.as_data()['password'][0].code,
                         'password_too_similar')
        self.assertEqual(self.data_path.read_bytes(), before)
        initial_path = self.data_path.with_name('rechazado.json')
        with override_settings(U1_DATA_FILE=initial_path), \
                patch('builtins.input', return_value=same), \
                patch('warehouse.management.commands.preparar.getpass', return_value=same):
            with self.assertRaises(CommandError):
                call_command('preparar', stdout=io.StringIO())
        self.assertFalse(initial_path.exists())

    def test_deactivation_then_reactivation_does_not_revive_old_session(self):
        reader = Client()
        self.assertEqual(reader.post(reverse('login'),
                         dict(username='Consulta audit', password=PASSWORD)).status_code, 302)
        data = self.account(username='Consulta audit', password='', is_active='')
        self.assertEqual(self.client.post(reverse('user_edit', args=[2]), data).status_code, 302)
        data['is_active'] = 'on'
        self.assertEqual(self.client.post(reverse('user_edit', args=[2]), data).status_code, 302)
        # No petición del lector entre desactivar y reactivar: la cookie sigue siendo la original.
        self.assertEqual(reader.get(reverse('products')).status_code, 302)
        self.assertEqual(reader.post(reverse('login'),
                         dict(username='Consulta audit', password=PASSWORD)).status_code, 302)
        self.assertEqual(reader.get(reverse('products')).status_code, 200)

    def test_sku_normalization_prevents_case_duplicates(self):
        data = dict(code='  mp-nuevo  ', name='Teclado audit', category='Teclados', location='B', minimum=1)
        self.assertEqual(self.client.post(reverse('product_new'), data).status_code, 302)
        self.assertEqual(store.read()['products'][-1]['code'], 'MP-NUEVO')
        before = self.data_path.read_bytes()
        self.assertContains(self.client.post(reverse('product_new'), {**data, 'code': 'MP-NUEVO'}), 'ya existe')
        self.assertContains(self.client.post(reverse('product_edit', args=[1]), data), 'ya existe')
        self.assertEqual(self.data_path.read_bytes(), before)

    def test_stock_requires_an_explicit_product(self):
        page = self.client.get(reverse('movement_new'))
        self.assertContains(page, '<option value="" selected>Seleccionar producto</option>', html=True)
        before = self.data_path.read_bytes()
        response = self.client.post(reverse('movement_new'),
            dict(product='', kind='entrada', quantity=2, reason='Audit', token=str(uuid.uuid4())))
        self.assertEqual(response.status_code, 200)
        self.assertIn('product', response.context['form'].errors)
        self.assertEqual(self.data_path.read_bytes(), before)

    def test_product_write_failure_preserves_form_and_allows_retry(self):
        data = dict(code='MP-NUEVO', name='Teclado audit', category='Teclados', location='B', minimum=1)
        before = self.data_path.read_bytes()
        with patch('warehouse.store.os.replace', side_effect=OSError('Fallo de escritura simulado')):
            response = self.client.post(reverse('product_new'), data)
        self.assertContains(response, SAVE_ERROR)
        self.assertContains(response, 'value="Teclado audit"')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertEqual(self.client.post(reverse('product_new'), data).status_code, 302)
        self.assertEqual(len(store.read()['products']), 2)

    def test_stock_write_failure_keeps_balance_history_and_token_for_retry(self):
        token = str(uuid.uuid4())
        data = dict(product=1, kind='entrada', quantity=2, reason='Audit', token=token)
        before = self.data_path.read_bytes()
        with patch('warehouse.store.os.replace', side_effect=OSError('Fallo de escritura simulado')):
            response = self.client.post(reverse('movement_new'), data)
        self.assertContains(response, SAVE_ERROR)
        self.assertContains(response, token)
        self.assertNotContains(response, 'registrado. Stock resultante')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertEqual(self.client.post(reverse('movement_new'), data).status_code, 302)
        saved = store.read()
        self.assertEqual(saved['products'][0]['stock'], 7)
        self.assertEqual([(m['before'], m['after'], m['token']) for m in saved['movements']], [(5, 7, token)])

    def test_failed_own_password_edit_keeps_session_and_old_password(self):
        data = self.account(username='Administrador audit', role='Administrador', password='Nueva-Clave-518!')
        before = self.data_path.read_bytes()
        with patch('warehouse.store.os.replace', side_effect=OSError('Fallo de escritura simulado')):
            response = self.client.post(reverse('user_edit', args=[1]), data)
        self.assertContains(response, SAVE_ERROR)
        self.assertNotContains(response, 'Usuario guardado.')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertEqual(self.client.get(reverse('users')).status_code, 200)
        self.assertEqual(self.client.post(reverse('user_edit', args=[1]), data).status_code, 302)
        self.assertTrue(check_password(data['password'], store.read()['users'][0]['password']))
        self.assertEqual(self.client.get(reverse('users')).status_code, 200)

    def test_failed_archive_and_logout_report_failure_without_changing_state(self):
        with store.edit() as data:
            data['products'][0]['stock'] = 0
        before = self.data_path.read_bytes()
        with patch('warehouse.store.os.replace', side_effect=OSError('Fallo de escritura simulado')):
            archive = self.client.post(reverse('product_archive', args=[1]), follow=True)
            logout = self.client.post(reverse('logout'), follow=True)
        self.assertContains(archive, SAVE_ERROR)
        self.assertNotContains(archive, 'Producto archivado;')
        self.assertContains(logout, 'No se pudo cerrar la sesión')
        self.assertEqual(self.data_path.read_bytes(), before)
        self.assertEqual(self.client.get(reverse('users')).status_code, 200)
        self.assertEqual(self.client.post(reverse('product_archive', args=[1])).status_code, 302)
        self.assertFalse(store.read()['products'][0]['active'])
        self.assertEqual(self.client.post(reverse('logout')).status_code, 302)
        self.assertEqual(self.client.get(reverse('products')).status_code, 302)
