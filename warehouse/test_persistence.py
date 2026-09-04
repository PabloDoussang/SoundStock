"""Comprueba persistencia real en disco entre procesos, sin usar la base local."""
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
project.DATABASES['default']['NAME'] = os.environ['SOUNDSTOCK_TEST_DATABASE']
import django
django.setup()
from django.core.management import call_command
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from warehouse.models import Product, Movement
from unittest.mock import patch
import uuid
"""


class DiskPersistenceTests(SimpleTestCase):
    def test_saved_changes_survive_refresh_logout_restart_and_database_edits(self):
        with tempfile.TemporaryDirectory(prefix='soundstock-test-') as directory:
            database = Path(directory) / 'test.sqlite3'
            environment = {**os.environ, 'SOUNDSTOCK_TEST_DATABASE': str(database)}
            phases = [
                """
call_command('migrate', verbosity=0)
User.objects.create_superuser('Responsable prueba', password='Fixture-Inicial-829!')
client = Client()
assert client.login(username='Responsable prueba', password='Fixture-Inicial-829!')
account = dict(username='Admin persistente', first_name='Antes', last_name='Prueba',
               email='', is_active='on', role='Administrador', password='Fixture-Nueva-937!')
assert client.post(reverse('user_new'), account).status_code == 302
admin = User.objects.get(username=account['username'])
account.update(first_name='Guardado', password='Fixture-Editada-618!')
assert client.post(reverse('user_edit', args=[admin.pk]), account).status_code == 302
product_data = dict(code='MP-PERSIST', name='Antes', category='Cuerdas', location='A-01', minimum=2)
assert client.post(reverse('product_new'), product_data).status_code == 302
product = Product.objects.get(code='MP-PERSIST')
product_data.update(name='Producto guardado', location='B-02')
assert client.post(reverse('product_edit', args=[product.pk]), product_data).status_code == 302
for kind, quantity in [('entrada', 10), ('salida', 3)]:
    response = client.post(reverse('movement_new'), dict(product=product.pk, kind=kind,
        quantity=quantity, reason='Persistencia', destination='Sucursal del rock', token=str(uuid.uuid4())))
    assert response.status_code == 302
for _ in range(2):
    assert 'Producto guardado' in client.get(reverse('products')).content.decode()
assert client.post(reverse('logout')).status_code == 302
assert client.get(reverse('products')).status_code == 302
fresh_browser = Client()
assert fresh_browser.login(username='Admin persistente', password='Fixture-Editada-618!')
assert fresh_browser.get(reverse('users')).status_code == 200
assert Product.objects.get(pk=product.pk).stock == 7
assert Movement.objects.count() == 2
""",
                """
# Segundo proceso: arranque normal, sin reinicializar datos existentes.
call_command('migrate', verbosity=0)
with patch('builtins.input', side_effect=AssertionError('El inicio no debe recrear los datos')):
    call_command('preparar')
admin = User.objects.get(username='Admin persistente')
assert admin.first_name == 'Guardado' and admin.is_superuser and admin.is_active
assert admin.check_password('Fixture-Editada-618!')
assert not admin.check_password('Fixture-Nueva-937!')
product = Product.objects.get(code='MP-PERSIST')
assert (product.name, product.location, product.stock) == ('Producto guardado', 'B-02', 7)
assert list(Movement.objects.order_by('id').values_list('before', 'after')) == [(0, 10), (10, 7)]
# Cambios confirmados directamente en la base, fuera de la sesión del navegador.
from django.db import connection, transaction
with transaction.atomic(), connection.cursor() as cursor:
    cursor.execute('UPDATE warehouse_product SET location = %s WHERE id = %s', ['C-03', product.pk])
admin.first_name = 'Editado en base'
admin.set_password('Fixture-Base-528!')
admin.save(update_fields=['first_name', 'password'])
""",
                """
# Tercer proceso: leer las modificaciones confirmadas de la base.
client = Client()
assert client.login(username='Admin persistente', password='Fixture-Base-528!')
assert not User.objects.get(username='Admin persistente').check_password('Fixture-Editada-618!')
assert User.objects.get(username='Admin persistente').first_name == 'Editado en base'
assert 'C-03' in client.get(reverse('products')).content.decode()
assert Product.objects.get(code='MP-PERSIST').stock == 7
assert Movement.objects.count() == 2
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
                    self.assertTrue(database.is_file())
