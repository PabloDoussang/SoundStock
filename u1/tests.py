"""Estas pruebas fallan si una vista U1 intenta consultar una base de datos."""
import tempfile
import uuid
from pathlib import Path
from django.test import SimpleTestCase, override_settings, Client
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from . import store

class U1Tests(SimpleTestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.override=override_settings(U1_DATA_FILE=Path(self.folder.name)/'demo.json')
        self.override.enable();self.addCleanup(self.override.disable)
        with store.edit() as data:
            data['users']=[dict(id=1,username='Pablo Doussang',first_name='Pablo',last_name='Doussang',email='',role='Administrador',is_active=True,password=make_password('Prueba-Segura-739!'),session_version='v1')]
            data['products']=[dict(id=1,code='MP-TEST',name='Guitarra demo',category='Cuerdas',location='A-01',stock=0,minimum=3,active=True)]
        self.assertEqual(self.client.post('/ingresar/',dict(username='Pablo Doussang',password='Prueba-Segura-739!')).status_code,302)

    def test_all_sections_and_forms_without_database(self):
        for path in ['/','/inventario/','/stock/','/movimientos/','/reportes/','/ubicaciones/','/usuarios/','/inventario/nuevo/','/inventario/1/editar/','/usuarios/nuevo/','/usuarios/1/editar/']:
            with self.subTest(path=path): self.assertEqual(self.client.get(path).status_code,200)

    def test_stock_lifecycle_and_rollback(self):
        data=dict(product=1,kind='entrada',quantity=10,reason='QA',token=str(uuid.uuid4()))
        self.assertEqual(self.client.post('/stock/',data).status_code,302)
        self.client.post('/stock/',data)
        self.assertEqual(len(store.read()['movements']),1)
        invalid={**data,'kind':'salida','quantity':11,'destination':'Sucursal del rock','token':str(uuid.uuid4())}
        self.assertContains(self.client.post('/stock/',invalid),'Stock insuficiente')
        self.assertEqual(store.read()['products'][0]['stock'],10)
        self.client.post('/stock/',{**invalid,'quantity':4,'token':str(uuid.uuid4())})
        self.client.post('/stock/',{**data,'kind':'ajuste','quantity':2,'token':str(uuid.uuid4())})
        result=store.read()
        self.assertEqual(result['products'][0]['stock'],2)
        self.assertEqual([m['delta'] for m in result['movements']],[10,-4,-4])
        self.assertEqual(self.client.get('/').context['low_count'],1)
        self.assertContains(self.client.get('/exportar/movimientos/'),'QA')
        report=self.client.get('/reportes/')
        self.assertEqual(report.context['entries'],10);self.assertEqual(report.context['exits'],4)
        self.assertEqual(report.context['adjustments'],-4)

    def test_product_crud_and_unique_code(self):
        data=dict(code='MP-NEW',name='Nuevo teclado',category='Teclados',location='B',minimum=3)
        self.assertEqual(self.client.post('/inventario/nuevo/',data).status_code,302)
        self.assertContains(self.client.post('/inventario/nuevo/',data),'ya existe')
        self.assertEqual(self.client.post('/inventario/2/editar/',{**data,'name':'Teclado editado'}).status_code,302)
        self.assertContains(self.client.get('/inventario/?q=editado'),'Teclado editado')
        self.client.post('/inventario/2/archivar/')
        self.assertFalse(store.read()['products'][1]['active'])
        self.client.post('/inventario/2/archivar/')
        self.assertTrue(store.read()['products'][1]['active'])

    def test_users_spaces_and_permissions(self):
        data=dict(username='Lector Demo',first_name='Lector',last_name='Demo',email='',role='Consulta',is_active='on',password='Prueba-Segura-739!')
        self.assertEqual(self.client.post('/usuarios/nuevo/',data).status_code,302)
        self.assertEqual(self.client.post('/usuarios/2/editar/',{**data,'password':''}).status_code,302)
        self.assertContains(self.client.post('/usuarios/1/editar/',{**data,'username':'Pablo Doussang','role':'Consulta','password':''}),'propia cuenta')
        self.client.post('/salir/')
        self.assertEqual(self.client.post('/ingresar/',dict(username='Lector Demo',password='Prueba-Segura-739!')).status_code,302)
        for path in ['/usuarios/','/stock/','/inventario/nuevo/','/inventario/1/archivar/']:
            self.assertEqual(self.client.post(path,{}).status_code,403)
        self.assertEqual(self.client.get('/inventario/').status_code,200)

    def test_csrf_dates_and_safe_redirect(self):
        secure=Client(enforce_csrf_checks=True)
        self.assertEqual(secure.post('/stock/',{}).status_code,403)
        self.assertContains(self.client.get('/reportes/?start=2026-12-31&end=2026-01-01'),'no puede ser posterior')
        self.assertEqual(self.client.get('/exportar/movimientos/?start=bad').status_code,400)
        self.client.post('/salir/')
        response=self.client.post('/ingresar/',dict(username='Pablo Doussang',password='Prueba-Segura-739!',next='https://example.com'))
        self.assertEqual(response.url,'/')

    def test_empty_setup_and_empty_inventory(self):
        with store.edit() as data:data['users']=[];data['products']=[]
        self.assertContains(self.client.get('/ingresar/'),'iniciar_u1.bat')
