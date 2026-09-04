import uuid
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from .models import Product, Movement
from .services import record_movement
class WarehouseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin=User.objects.create_superuser('admin',password='Example-test-739!')
        cls.operator=User.objects.create_user('operator',password='Example-test-739!')
        cls.operator.groups.add(Group.objects.create(name='Operador'))
        cls.reader=User.objects.create_user('reader',password='Example-test-739!')
        cls.product=Product.objects.create(code='MP-TEST',name='Guitarra de prueba',category='Cuerdas',location='A-01',minimum=3)
    def move(self,kind='entrada',quantity=10,**kwargs):
        data=dict(product_id=self.product.pk,kind=kind,quantity=quantity,reason='Prueba controlada',destination='Sucursal del rock' if kind=='salida' else '',user=self.admin,token=uuid.uuid4())
        data.update(kwargs)
        return record_movement(**data)
    def test_stock_and_audit(self):
        self.move()
        self.move('salida',4)
        self.move('ajuste',2)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,2)
        self.assertEqual(list(Movement.objects.order_by('id').values_list('before','after','delta')),[(0,10,10),(10,6,-4),(6,2,-4)])
    def test_insufficient_stock_rolls_back(self):
        self.move()
        with self.assertRaises(ValidationError): self.move('salida',11)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,10)
        self.assertEqual(Movement.objects.count(),1)
    def test_duplicate_submission_is_idempotent(self):
        token=uuid.uuid4()
        a,created=self.move(token=token)
        b,created=self.move(token=token)
        self.assertFalse(created)
        self.assertEqual(a.pk,b.pk)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,10)
    def test_invalid_operations(self):
        for kind,quantity in [('entrada',-1),('entrada',0),('ajuste',-2),('salida',0),('otro',1),('entrada',1000001)]:
            with self.subTest(kind=kind,quantity=quantity):
                with self.assertRaises(ValidationError): self.move(kind,quantity)
        with self.assertRaises(ValidationError): self.move(reason='')
        with self.assertRaises(ValidationError): self.move('salida',1,destination='')
        self.assertEqual(Movement.objects.count(),0)
    def test_login_required(self):
        for name in ['dashboard','products','movement_new','movements','reports','locations','users']:
            self.assertEqual(self.client.get(reverse(name)).status_code,302)
    def test_reader_denied_mutations(self):
        self.client.force_login(self.reader)
        for name,kwargs in [('product_new',{}),('movement_new',{}),('product_edit',{'pk':self.product.pk}),('product_archive',{'pk':self.product.pk}),('users',{}),('user_new',{})]:
            self.assertEqual(self.client.post(reverse(name,kwargs=kwargs),{}).status_code,403)
        for name in ['dashboard','products','movements','reports','locations']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)
    def test_all_admin_pages_render(self):
        self.client.force_login(self.admin)
        for name in ['dashboard','products','movement_new','movements','reports','locations','users','product_new','user_new']:
            with self.subTest(name=name): self.assertEqual(self.client.get(reverse(name)).status_code,200)
        self.assertEqual(self.client.get(reverse('product_edit',args=[self.product.pk])).status_code,200)
        self.assertEqual(self.client.get(reverse('user_edit',args=[self.admin.pk])).status_code,200)
    def test_create_edit_duplicate_product(self):
        self.client.force_login(self.operator)
        data={'code':'MP-NEW','name':'Teclado nuevo','category':'Teclados','location':'B-03','minimum':4}
        self.assertEqual(self.client.post(reverse('product_new'),data).status_code,302)
        product=Product.objects.get(code='MP-NEW')
        self.assertEqual(product.stock,0)
        duplicate=self.client.post(reverse('product_new'),data)
        self.assertEqual(duplicate.status_code,200)
        self.assertContains(duplicate,'ya existe')
        data['name']='Teclado editado'
        self.assertEqual(self.client.post(reverse('product_edit',args=[product.pk]),data).status_code,302)
        product.refresh_from_db()
        self.assertEqual(product.name,'Teclado editado')
    def test_archive_requires_zero_and_preserves_history(self):
        self.client.force_login(self.admin)
        self.move()
        self.client.post(reverse('product_archive',args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)
        self.move('ajuste',0)
        self.client.post(reverse('product_archive',args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertFalse(self.product.active)
        self.assertEqual(Movement.objects.count(),2)
        self.assertContains(self.client.get(reverse('products')+'?archived=1'),'MP-TEST')
        self.client.post(reverse('product_archive',args=[self.product.pk]))
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)
    def test_operator_cannot_archive_or_manage_users(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(reverse('users')).status_code,403)
        self.assertEqual(self.client.post(reverse('product_archive',args=[self.product.pk])).status_code,403)
    def test_movement_post_and_duplicate(self):
        self.client.force_login(self.operator)
        data={'product':self.product.pk,'kind':'entrada','quantity':'7','reason':'Guía 123','token':str(uuid.uuid4())}
        self.assertEqual(self.client.post(reverse('movement_new'),data).status_code,302)
        self.assertEqual(self.client.post(reverse('movement_new'),data).status_code,302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock,7)
    def test_csrf_required(self):
        client=Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse('movement_new'),{}).status_code,403)
    def test_dates_filters_exports_and_statistics(self):
        self.move()
        self.move('salida',3)
        self.client.force_login(self.admin)
        report=self.client.get(reverse('reports'))
        self.assertEqual(report.context['entries'],10)
        self.assertEqual(report.context['exits'],3)
        self.assertEqual(sum(x['total'] for x in report.context['categories']),7)
        invalid=self.client.get(reverse('reports')+'?start=2026-12-31&end=2026-01-01')
        self.assertContains(invalid,'no puede ser posterior')
        self.assertEqual(self.client.get(reverse('export',args=['movimientos'])+'?start=bad').status_code,400)
        self.assertContains(self.client.get(reverse('export',args=['inventario'])),'MP-TEST')
        self.assertContains(self.client.get(reverse('export',args=['movimientos'])),'Prueba controlada')
    def test_stock_alert_boundary_and_search(self):
        self.move(quantity=3)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('dashboard')).context['low_count'],1)
        self.assertContains(self.client.get(reverse('products')+'?status=low'),'MP-TEST')
        self.assertNotContains(self.client.get(reverse('products')+'?q=No-existe'),'MP-TEST')
    def test_user_creation_deactivation_and_self_protection(self):
        self.client.force_login(self.admin)
        data={'username':'nuevo','first_name':'Nuevo','last_name':'Usuario','email':'','is_active':'on','role':'Operador','password':'M3lodias-Acceso-783!'}
        self.assertEqual(self.client.post(reverse('user_new'),data).status_code,302)
        account=User.objects.get(username='nuevo')
        self.assertTrue(account.check_password(data['password']))
        self.assertTrue(account.groups.filter(name='Operador').exists())
        data.update(password='',is_active='')
        self.assertEqual(self.client.post(reverse('user_edit',args=[account.pk]),data).status_code,302)
        account.refresh_from_db()
        self.assertFalse(account.is_active)
        data.update(username='admin',role='Consulta')
        self.assertContains(self.client.post(reverse('user_edit',args=[self.admin.pk]),data),'propia cuenta')
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser)
        self.assertTrue(self.admin.is_active)
    def test_pagination_preserves_filters(self):
        self.client.force_login(self.admin)
        for i in range(13):
            Product.objects.create(code=f'MP-EXTRA-{i}',name=f'Guitarra {i}',category='Cuerdas',location='A')
        response=self.client.get(reverse('products')+'?q=Guitarra')
        self.assertContains(response,'q=Guitarra&amp;page=2')
        self.assertNotContains(response,'??')
    def test_empty_states(self):
        self.client.force_login(self.admin)
        Product.objects.all().delete()
        self.assertContains(self.client.get(reverse('products')),'No hay productos')
        self.assertEqual(self.client.get(reverse('reports')).status_code,200)

    def test_spaced_username_can_be_created_edited_and_used_to_login(self):
        self.client.force_login(self.admin)
        data = {'username':'Pablo Doussang','first_name':'Pablo','last_name':'Doussang',
                'email':'','is_active':'on','role':'Administrador','password':'Prueba-Segura-739!'}
        self.assertEqual(self.client.post(reverse('user_new'), data).status_code, 302)
        account = User.objects.get(username='Pablo Doussang')
        data.update(password='', first_name='Pablo actualizado')
        self.assertEqual(self.client.post(reverse('user_edit',args=[account.pk]),data).status_code,302)
        account.refresh_from_db()
        self.assertEqual(account.first_name, 'Pablo actualizado')
        self.client.logout()
        self.assertTrue(self.client.login(username='Pablo Doussang',password='Prueba-Segura-739!'))
        self.assertEqual(self.client.get(reverse('users')).status_code,200)

    def test_spaced_username_admin_form_and_uniqueness(self):
        from .admin import WarehouseUserChangeForm
        from .forms import UserForm
        account=User.objects.create_user('Pablo Doussang',password='Prueba-Segura-739!')
        data={'username':'Pablo Doussang','first_name':'Pablo','last_name':'Doussang','email':'',
              'is_active':'on','role':'Consulta','password':''}
        self.assertTrue(UserForm(data=data,instance=account).is_valid())
        duplicate=UserForm(data={**data,'password':'Prueba-Segura-739!'})
        self.assertFalse(duplicate.is_valid())
        self.assertIn('username',duplicate.errors)
        admin_form=WarehouseUserChangeForm(data={**data,'date_joined':account.date_joined},instance=account)
        self.assertTrue(admin_form.is_valid(),admin_form.errors)
