"""Persistencia entre tres procesos, sin SQL ni datos del usuario real."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from django.conf import settings
from django.test import SimpleTestCase


BOOT = """
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_DEBUG'] = '1'
os.environ['DJANGO_SECRET_KEY'] = 'solo-pruebas-de-persistencia'
import config.settings as project
from pathlib import Path
project.U1_DATA_FILE = Path(os.environ['SOUNDSTOCK_TEST_JSON'])
assert project.DATABASES == {}, 'Esta entrega no debe configurar bases de datos'
import django
django.setup()
from django.core.management import call_command
from django.contrib.auth.hashers import make_password, check_password
from django.test import Client
from django.urls import reverse
from warehouse import store
from unittest.mock import patch
import uuid

def saved_user(name):
    return next(user for user in store.read()['users'] if user['username'] == name)

def saved_product(code):
    return next(product for product in store.read()['products'] if product['code'] == code)

def login(client, name, password):
    assert client.post(reverse('login'), dict(username=name, password=password)).status_code == 302
    assert client.get(reverse('products')).status_code == 200
"""


class DiskPersistenceTests(SimpleTestCase):
    def test_saved_changes_survive_refresh_logout_reopen_and_process_restarts(self):
        with tempfile.TemporaryDirectory(prefix='soundstock-persistence-') as directory:
            data_file = Path(directory) / 'bodega.json'
            environment = {**os.environ, 'SOUNDSTOCK_TEST_JSON': str(data_file)}
            phases = [
                """
# Primer proceso: guardar administradores, productos y movimientos desde formularios.
with store.edit() as data:
    data['users'].append(dict(id=1, username='Responsable prueba', first_name='Responsable',
        last_name='', email='', role='Administrador', is_active=True,
        password=make_password('Fixture-Inicial-829!'), session_version=str(uuid.uuid4())))
client = Client()
login(client, 'Responsable prueba', 'Fixture-Inicial-829!')
account = dict(username='Admin persistente', first_name='Antes', last_name='Prueba',
               email='', is_active='on', role='Administrador', password='Fixture-Nueva-937!')
assert client.post(reverse('user_new'), account).status_code == 302
admin_id = saved_user(account['username'])['id']
account.update(first_name='Guardado', password='Fixture-Editada-618!')
assert client.post(reverse('user_edit', args=[admin_id]), account).status_code == 302
product_data = dict(code='MP-PERSIST', name='Antes', category='Cuerdas', location='A-01', minimum=2)
assert client.post(reverse('product_new'), product_data).status_code == 302
product_id = saved_product('MP-PERSIST')['id']
product_data.update(name='Producto guardado', location='B-02')
assert client.post(reverse('product_edit', args=[product_id]), product_data).status_code == 302
for kind, quantity in [('entrada', 10), ('salida', 3)]:
    response = client.post(reverse('movement_new'), dict(product=product_id, kind=kind,
        quantity=quantity, reason='Persistencia', destination='Sucursal del rock', token=str(uuid.uuid4())))
    assert response.status_code == 302
archive_data = dict(code='MP-ARCHIVE', name='Producto archivado', category='Audio', location='C-02', minimum=0)
assert client.post(reverse('product_new'), archive_data).status_code == 302
archive_id = saved_product('MP-ARCHIVE')['id']
assert client.post(reverse('product_archive', args=[archive_id])).status_code == 302
for _ in range(2):
    assert 'Producto guardado' in client.get(reverse('products')).content.decode()
assert client.post(reverse('logout')).status_code == 302
assert client.get(reverse('products')).status_code == 302
fresh_browser = Client()
login(fresh_browser, 'Admin persistente', 'Fixture-Editada-618!')
assert fresh_browser.get(reverse('users')).status_code == 200
assert saved_product('MP-PERSIST')['stock'] == 7
assert not saved_product('MP-ARCHIVE')['active']
assert len(store.read()['movements']) == 2
""",
                """
# Segundo proceso: iniciar de nuevo no pide cuentas ni reinicia el archivo.
before = project.U1_DATA_FILE.read_bytes()
with patch('builtins.input', side_effect=AssertionError('El inicio no debe recrear los datos')):
    call_command('preparar')
assert project.U1_DATA_FILE.read_bytes() == before
admin = saved_user('Admin persistente')
assert admin['first_name'] == 'Guardado' and admin['role'] == 'Administrador' and admin['is_active']
assert check_password('Fixture-Editada-618!', admin['password'])
assert not check_password('Fixture-Nueva-937!', admin['password'])
product = saved_product('MP-PERSIST')
assert (product['name'], product['location'], product['stock']) == ('Producto guardado', 'B-02', 7)
assert not saved_product('MP-ARCHIVE')['active']
assert [(m['before'], m['after']) for m in store.read()['movements']] == [(0, 10), (10, 7)]
# Modificar de nuevo tras reiniciar y comprobarlo desde otro proceso independiente.
client = Client()
login(client, 'Admin persistente', 'Fixture-Editada-618!')
account = dict(username='Admin persistente', first_name='Editado después del reinicio',
    last_name='Prueba', email='', is_active='on', role='Administrador', password='Fixture-Final-528!')
assert client.post(reverse('user_edit', args=[admin['id']]), account).status_code == 302
assert client.get(reverse('users')).status_code == 200
product_data = dict(code='MP-PERSIST', name='Producto guardado', category='Cuerdas', location='C-03', minimum=2)
assert client.post(reverse('product_edit', args=[product['id']]), product_data).status_code == 302
""",
                """
# Tercer proceso: las modificaciones posteriores al reinicio también permanecen.
client = Client()
login(client, 'Admin persistente', 'Fixture-Final-528!')
admin = saved_user('Admin persistente')
assert not check_password('Fixture-Editada-618!', admin['password'])
assert admin['first_name'] == 'Editado después del reinicio'
assert 'C-03' in client.get(reverse('products')).content.decode()
assert saved_product('MP-PERSIST')['stock'] == 7
assert not saved_product('MP-ARCHIVE')['active']
assert len(store.read()['movements']) == 2
assert client.get(reverse('users')).status_code == 200
""",
            ]
            for number, phase in enumerate(phases, 1):
                with self.subTest(process=number):
                    result = subprocess.run(
                        [sys.executable, '-c', BOOT + phase], cwd=settings.BASE_DIR,
                        env=environment, capture_output=True, text=True, timeout=60,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertTrue(data_file.is_file())
            self.assertFalse(list(Path(directory).glob('*.sqlite3')))
