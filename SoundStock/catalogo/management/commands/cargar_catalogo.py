import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogo.models import Categoria, Producto
from inventario.services import registrar_movimiento
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Carga los 12 productos del SoundStock original y sus entradas de stock inicial.'

    def handle(self, *args, **options):
        usuario = Usuario.objects.filter(rol='Administrador', is_active=True).first()
        if not usuario:
            raise CommandError('Primero crea un superusuario: python manage.py createsuperuser.')
        path = settings.BASE_DIR / 'catalogo/data/productos_iniciales.json'
        datos = json.loads(path.read_text(encoding='utf-8'))
        creados = conservados = 0
        with transaction.atomic():
            for row in datos:
                categoria, _ = Categoria.objects.get_or_create(nombre=row['category'])
                producto, nuevo = Producto.objects.get_or_create(codigo=row['code'], defaults={
                    'nombre': row['name'], 'categoria': categoria, 'ubicacion': row['location'],
                    'stock_minimo': row['minimum'], 'stock': 0, 'activo': True,
                })
                if nuevo:
                    creados += 1
                    if row['stock']:
                        registrar_movimiento(producto_id=producto.pk, usuario=usuario, tipo='entrada',
                            cantidad=row['stock'], motivo='Inventario inicial del SoundStock original')
                else:
                    conservados += 1
        self.stdout.write(self.style.SUCCESS(f'Catálogo inicial: {creados} productos creados, '
            f'{conservados} existentes conservados.'))
