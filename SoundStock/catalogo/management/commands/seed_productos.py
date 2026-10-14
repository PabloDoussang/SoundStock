import re
from time import perf_counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from catalogo.models import Categoria, Producto


CATEGORIAS = ('Cuerdas', 'Percusión', 'Teclados', 'Audio', 'DJ', 'Accesorios')
ARTICULOS = ('Guitarra', 'Bajo', 'Teclado', 'Batería', 'Micrófono', 'Cable', 'Monitor')


class Command(BaseCommand):
    help = 'Carga productos ficticios con Faker es_CL y categorías compartidas, siguiendo seed_empleado.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=100)
        parser.add_argument('--lote', type=int, default=5000)
        parser.add_argument('--semilla', type=int, default=42)
        parser.add_argument('--prefijo', default='DEMO')

    def handle(self, *args, **options):
        cantidad, lote, prefijo = options['cantidad'], options['lote'], options['prefijo'].upper()
        if not 1 <= cantidad <= 1000000 or not 1 <= lote <= 10000:
            raise CommandError('Cantidad: 1 a 1.000.000; lote: 1 a 10.000.')
        if not re.fullmatch(r'[A-Z][A-Z0-9]{0,9}', prefijo):
            raise CommandError('Prefijo: 1 a 10 letras/números, comenzando con letra.')
        fake = Faker('es_CL')
        fake.seed_instance(options['semilla'])
        categorias = [Categoria.objects.get_or_create(nombre=nombre)[0] for nombre in CATEGORIAS]
        creados = actualizados = 0
        inicio = perf_counter()
        for comienzo in range(0, cantidad, lote):
            productos = []
            for indice in range(comienzo, min(comienzo + lote, cantidad)):
                productos.append(Producto(
                    codigo=f'{prefijo}-P-{indice + 1:07d}',
                    nombre=f'{fake.random_element(elements=ARTICULOS)} {fake.word()} {indice + 1}'[:120],
                    categoria=fake.random_element(elements=categorias),
                    ubicacion=f'{fake.random_element(elements=("A", "B", "C", "D"))}-{fake.random_int(min=1, max=20):02d}',
                    stock=0, stock_minimo=fake.random_int(min=0, max=30), activo=True,
                    descripcion=fake.sentence(nb_words=6),
                ))
            codigos = [p.codigo for p in productos]
            with transaction.atomic():
                existentes = Producto.objects.filter(codigo__in=codigos).count()
                # La misma regla de update_or_create por clave estable usada en el ejemplo.
                # bulk_create procesa miles de registros por lote para llegar al millón.
                Producto.objects.bulk_create(productos, batch_size=lote, update_conflicts=True,
                    unique_fields=['codigo'], update_fields=['nombre', 'categoria', 'ubicacion', 'stock_minimo', 'descripcion'])
            creados += len(productos) - existentes
            actualizados += existentes
            if cantidad >= 100000 and (comienzo + len(productos)) % 100000 == 0:
                self.stdout.write(f'Procesados {comienzo + len(productos):,} de {cantidad:,}')
        total = Producto.objects.filter(codigo__startswith=f'{prefijo}-P-').count()
        self.stdout.write(self.style.SUCCESS(f'Seeder terminado: {creados} productos creados, '
            f'{actualizados} actualizados; {total} almacenados; {perf_counter() - inicio:.2f} s.'))
