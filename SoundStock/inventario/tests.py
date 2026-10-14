import io
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalogo.models import Categoria, Producto
from inventario.models import Movimiento
from inventario.services import eliminar_ultimo, registrar_movimiento
from usuarios.models import Usuario


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SoundStockTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_superuser('admin', password='Clave-Prueba-739!')
        self.operador = Usuario.objects.create_user('operador', password='Clave-Prueba-739!', rol='Operador')
        self.consulta = Usuario.objects.create_user('consulta', password='Clave-Prueba-739!')
        self.categoria = Categoria.objects.create(nombre='Cuerdas')
        self.producto = Producto.objects.create(codigo='MP-PRUEBA', nombre='Guitarra', categoria=self.categoria,
            ubicacion='A-01', stock_minimo=3)
        self.client.force_login(self.admin)

    def mover(self, tipo='entrada', cantidad=10, **extra):
        return registrar_movimiento(producto_id=self.producto.pk, usuario=self.admin,
            tipo=tipo, cantidad=cantidad, motivo='Prueba',
            destino='Sucursal' if tipo == 'salida' else '', **extra)

    def test_sqlite_models_and_migration_history(self):
        self.assertEqual(connection.vendor, 'sqlite')
        loader = MigrationExecutor(connection)
        self.assertFalse(loader.migration_plan(loader.loader.graph.leaf_nodes()))
        self.assertIn(('catalogo', '0001_initial'), loader.loader.applied_migrations)
        self.assertIn(('catalogo', '0002_descripcion_producto'), loader.loader.applied_migrations)
        self.assertIn(('usuarios', '0001_initial'), loader.loader.applied_migrations)
        self.assertIn(('inventario', '0002_initial'), loader.loader.applied_migrations)

    def test_stock_history_and_transactional_correction(self):
        primero, _ = self.mover()
        ultimo, _ = self.mover(tipo='salida', cantidad=3)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)
        self.assertEqual(list(Movimiento.objects.order_by('pk').values_list('anterior', 'posterior', 'variacion')),
            [(0, 10, 10), (10, 7, -3)])
        with self.assertRaises(ValidationError):
            eliminar_ultimo(primero)
        corregido, _ = registrar_movimiento(producto_id=self.producto.pk, usuario=self.admin,
            tipo='salida', cantidad=2, motivo='Corrección', destino='Sucursal', instancia=ultimo)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 8)
        eliminar_ultimo(corregido)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_invalid_values_and_duplicate_token(self):
        token = uuid4()
        self.mover(token=token)
        _, created = self.mover(token=token)
        self.assertFalse(created)
        self.assertEqual(Movimiento.objects.count(), 1)
        for tipo, cantidad in [('salida', 11), ('entrada', 1000000), ('entrada', 0), ('ajuste', 10)]:
            with self.assertRaises(ValidationError):
                self.mover(tipo=tipo, cantidad=cantidad)
        with self.assertRaises(ValidationError):
            registrar_movimiento(producto_id=self.producto.pk, usuario=self.admin,
                tipo='salida', cantidad=1, motivo='Prueba')
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 10)

    def test_database_constraints_and_protected_relations(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.filter(pk=self.producto.pk).update(stock=-1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.filter(pk=self.producto.pk).update(stock=1000001)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Producto.objects.create(codigo='MP-PRUEBA', nombre='Repetido', categoria=self.categoria, ubicacion='A')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Movimiento.objects.create(producto=self.producto, usuario=self.admin, tipo='entrada',
                anterior=0, posterior=10, variacion=9, motivo='Mal saldo')
        self.mover()
        from django.db.models.deletion import ProtectedError
        with self.assertRaises(ProtectedError):
            self.producto.delete()
        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_public_pages_and_access_roles(self):
        self.mover()
        for name in ['inicio', 'productos', 'movimientos', 'movimiento_crear', 'reportes',
                     'ubicaciones', 'producto_crear', 'admin:index', 'admin:catalogo_producto_changelist',
                     'admin:inventario_movimiento_changelist', 'admin:usuarios_usuario_changelist']:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.client.force_login(self.consulta)
        self.assertEqual(self.client.get(reverse('productos')).status_code, 200)
        self.assertEqual(self.client.get(reverse('movimiento_crear')).status_code, 403)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(reverse('producto_crear')).status_code, 200)
        self.assertEqual(self.client.get(reverse('producto_eliminar', args=[self.producto.pk])).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('inicio')).status_code, 302)

    def test_product_web_crud_search_and_filters(self):
        values = dict(codigo='mp-nuevo', nombre='Bajo', categoria=self.categoria.pk,
            ubicacion='B-02', stock_minimo=2, descripcion='Prueba')
        self.assertEqual(self.client.post(reverse('producto_crear'), values).status_code, 302)
        nuevo = Producto.objects.get(codigo='MP-NUEVO')
        values['nombre'] = 'Bajo actualizado'
        self.assertEqual(self.client.post(reverse('producto_editar', args=[nuevo.pk]), values).status_code, 302)
        self.assertContains(self.client.get(reverse('productos'), {'q': 'MP-NUEVO'}), 'Bajo actualizado')
        self.assertContains(self.client.get(reverse('productos'), {'categoria': self.categoria.pk}), 'Bajo actualizado')
        self.client.post(reverse('producto_archivar', args=[nuevo.pk]))
        self.assertFalse(Producto.objects.get(pk=nuevo.pk).activo)
        self.client.post(reverse('producto_eliminar', args=[nuevo.pk]))
        self.assertFalse(Producto.objects.filter(pk=nuevo.pk).exists())

    def test_movement_web_forms_filters_and_csv(self):
        values = dict(producto=self.producto.pk, tipo='entrada', cantidad=8,
            motivo='Ingreso', destino='', token=str(uuid4()))
        self.assertEqual(self.client.post(reverse('movimiento_crear'), values).status_code, 302)
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 8)
        self.assertContains(self.client.get(reverse('movimientos'), {'tipo': 'entrada'}), 'MP-PRUEBA')
        self.assertEqual(self.client.get(reverse('movimientos'), {'desde': 'fecha-mala'}).status_code, 200)
        response = self.client.get(reverse('exportar', args=['productos']))
        self.assertIn('MP-PRUEBA', b''.join(response.streaming_content).decode())
        response = self.client.get(reverse('exportar', args=['movimientos']))
        self.assertIn('Ingreso', b''.join(response.streaming_content).decode())

    def test_admin_crud_categories_products_users_and_movements(self):
        self.assertEqual(self.client.post(reverse('admin:catalogo_categoria_add'),
            {'nombre': 'Audio', '_save': 'Guardar'}).status_code, 302)
        categoria = Categoria.objects.get(nombre='Audio')
        self.client.post(reverse('admin:catalogo_categoria_change', args=[categoria.pk]),
            {'nombre': 'Audio nuevo', '_save': 'Guardar'})
        self.assertEqual(Categoria.objects.get(pk=categoria.pk).nombre, 'Audio nuevo')
        self.client.post(reverse('admin:catalogo_categoria_delete', args=[categoria.pk]), {'post': 'yes'})
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())
        producto_data = dict(codigo='MP-ADMIN', nombre='Batería', categoria=self.categoria.pk,
            ubicacion='D', stock_minimo=1, descripcion='Prueba', activo='on', _save='Guardar')
        self.assertEqual(self.client.post(reverse('admin:catalogo_producto_add'), producto_data).status_code, 302)
        producto = Producto.objects.get(codigo='MP-ADMIN')
        producto_data['nombre'] = 'Batería editada'
        self.assertEqual(self.client.post(reverse('admin:catalogo_producto_change', args=[producto.pk]), producto_data).status_code, 302)
        self.client.post(reverse('admin:catalogo_producto_delete', args=[producto.pk]), {'post': 'yes'})
        self.assertFalse(Producto.objects.filter(pk=producto.pk).exists())
        user_data = dict(username='Nuevo', email='nuevo@example.com', rol='Consulta',
            password1='Clave-Prueba-739!', password2='Clave-Prueba-739!', _save='Guardar')
        self.assertEqual(self.client.post(reverse('admin:usuarios_usuario_add'), user_data).status_code, 302)
        nuevo = Usuario.objects.get(username='Nuevo')
        self.assertTrue(nuevo.check_password('Clave-Prueba-739!'))
        cambio = dict(username='Nuevo', first_name='Nombre cambiado', last_name='', email='nuevo@example.com',
            rol='Operador', is_active='on', _save='Guardar')
        self.assertEqual(self.client.post(reverse('admin:usuarios_usuario_change', args=[nuevo.pk]), cambio).status_code, 302)
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.first_name, nuevo.rol), ('Nombre cambiado', 'Operador'))
        self.assertContains(self.client.get(reverse('admin:usuarios_usuario_changelist'), {'q': 'Nuevo'}), 'Nuevo')
        self.client.post(reverse('admin:usuarios_usuario_delete', args=[nuevo.pk]), {'post': 'yes'})
        self.assertFalse(Usuario.objects.filter(pk=nuevo.pk).exists())
        mov_data = dict(producto=self.producto.pk, usuario=self.admin.pk, tipo='entrada',
            cantidad=7, motivo='Admin', destino='', _save='Guardar')
        self.assertEqual(self.client.post(reverse('admin:inventario_movimiento_add'), mov_data).status_code, 302)
        movimiento = Movimiento.objects.get()
        mov_data['cantidad'] = 5
        self.assertEqual(self.client.post(reverse('admin:inventario_movimiento_change', args=[movimiento.pk]), mov_data).status_code, 302)
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 5)
        self.client.post(reverse('admin:inventario_movimiento_delete', args=[movimiento.pk]), {'post': 'yes'})
        self.assertEqual(Producto.objects.get(pk=self.producto.pk).stock, 0)

    def test_seeders_and_original_catalog_are_repeatable(self):
        output = io.StringIO()
        call_command('cargar_catalogo', stdout=output)
        self.assertEqual(Producto.objects.count(), 13)
        self.assertEqual(Movimiento.objects.count(), 11)
        call_command('cargar_catalogo', stdout=output)
        self.assertEqual(Producto.objects.count(), 13)
        call_command('seed_productos', cantidad=100, lote=19, stdout=output)
        call_command('seed_productos', cantidad=100, lote=31, stdout=output)
        self.assertEqual(Producto.objects.filter(codigo__startswith='DEMO-P-').count(), 100)
        call_command('seed_usuarios', cantidad=10, lote=3, stdout=output)
        call_command('seed_usuarios', cantidad=10, lote=7, stdout=output)
        self.assertEqual(Usuario.objects.filter(username__startswith='demo_usuario_').count(), 10)
        call_command('seed_movimientos', cantidad=100, lote=19, stdout=output)
        stock = Producto.objects.get(codigo='DEMO-P-0000001').stock
        call_command('seed_movimientos', cantidad=100, lote=31, stdout=output)
        self.assertEqual(Producto.objects.get(codigo='DEMO-P-0000001').stock, stock)
        self.assertEqual(Movimiento.objects.count(), 111)
