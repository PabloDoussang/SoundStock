"""Errores de formulario y navegación de operaciones, con datos temporales."""
from html.parser import HTMLParser
from pathlib import Path
import tempfile
from urllib.parse import parse_qs, urlsplit
from django.contrib.auth.hashers import make_password
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from . import store


class OperationLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'data-operation' in attrs:
            self.links[attrs['data-operation']] = attrs['href']


class StockNavigationTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='soundstock-navigation-')
        self.addCleanup(directory.cleanup)
        override = override_settings(U1_DATA_FILE=Path(directory.name) / 'bodega.json')
        override.enable()
        self.addCleanup(override.disable)
        with store.edit() as data:
            data['users'] = [dict(id=1, username='Cuenta prueba', first_name='', last_name='',
                email='', role='Administrador', is_active=True,
                password=make_password('Fixture-Operaciones-972!'), session_version='v1')]
            data['products'] = [dict(id=i, code=f'MP-{i:03}', name=f'Producto {i}',
                category='Cuerdas', location='A', stock=10, minimum=1, active=True) for i in (1, 2)]
        self.client.post(reverse('login'), {'username':'Cuenta prueba','password':'Fixture-Operaciones-972!'})

    def test_operation_links_preserve_selected_product_without_javascript(self):
        response = self.client.get(reverse('movement_new'), {'product':2})
        parser = OperationLinks()
        parser.feed(response.content.decode())
        self.assertEqual(set(parser.links), {'entrada','salida','ajuste'})
        for kind, link in parser.links.items():
            with self.subTest(kind=kind):
                params = parse_qs(urlsplit(link).query)
                self.assertEqual(params['product'], ['2'])
                following = self.client.get(reverse('movement_new') + link)
                self.assertEqual(str(following.context['form']['product'].value()), '2')
                self.assertEqual(following.context['form']['kind'].value(), kind)

    def test_invalid_hidden_token_has_visible_recovery_and_does_not_mutate_stock(self):
        original = store.read()
        response = self.client.post(reverse('movement_new'), dict(product=2,kind='entrada',
            quantity=3,reason='Prueba de formulario inválido',token='identificador-invalido'))
        self.assertContains(response, 'No se pudo validar este formulario')
        self.assertContains(response, 'Abrir un formulario nuevo')
        self.assertEqual(store.read(), original)
