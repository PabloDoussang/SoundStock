from uuid import NAMESPACE_URL, uuid5

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from catalogo.models import Producto
from inventario.models import Movimiento
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea entradas ficticias vinculadas a productos y un responsable; conserva el stock al repetir.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=100)
        parser.add_argument('--lote', type=int, default=2000)
        parser.add_argument('--semilla', type=int, default=42)
        parser.add_argument('--prefijo', default='DEMO')

    def handle(self, *args, **options):
        cantidad, lote = options['cantidad'], options['lote']
        if not 1 <= cantidad <= 1000000 or not 1 <= lote <= 10000:
            raise CommandError('Cantidad: 1 a 1.000.000; lote: 1 a 10.000.')
        productos = Producto.objects.filter(codigo__startswith=f'{options["prefijo"].upper()}-P-', activo=True).order_by('codigo')
        if productos.count() < cantidad:
            raise CommandError('Ejecuta primero seed_productos con esta cantidad y el mismo prefijo.')
        responsable, _ = Usuario.objects.get_or_create(username='demo_responsable', defaults={
            'first_name': 'Responsable ficticio', 'rol': 'Consulta', 'password': '!', 'is_active': False})
        fake = Faker('es_CL')
        fake.seed_instance(options['semilla'])
        creados = conservados = 0
        for comienzo in range(0, cantidad, lote):
            with transaction.atomic():
                grupo = list(productos.select_for_update()[comienzo:min(comienzo + lote, cantidad)])
                tokens = [uuid5(NAMESPACE_URL, f'soundstock:{p.codigo}') for p in grupo]
                existentes = set(Movimiento.objects.filter(token__in=tokens).values_list('token', flat=True))
                nuevos, modificados = [], []
                for producto, token in zip(grupo, tokens):
                    cantidad_stock = fake.random_int(min=1, max=100)
                    motivo = ('DEMO · ' + fake.sentence(nb_words=5))[:240]
                    if token in existentes:
                        conservados += 1
                        continue
                    if producto.stock + cantidad_stock > 1000000:
                        raise CommandError(f'Stock máximo excedido: {producto.codigo}.')
                    nuevos.append(Movimiento(producto=producto, usuario=responsable, tipo='entrada',
                        anterior=producto.stock, posterior=producto.stock + cantidad_stock,
                        variacion=cantidad_stock, motivo=motivo, token=token))
                    producto.stock += cantidad_stock
                    modificados.append(producto)
                Movimiento.objects.bulk_create(nuevos, batch_size=lote)
                Producto.objects.bulk_update(modificados, ['stock'], batch_size=lote)
                creados += len(nuevos)
        self.stdout.write(self.style.SUCCESS(f'Seeder terminado: {creados} movimientos creados, '
            f'{conservados} existentes conservados.'))
