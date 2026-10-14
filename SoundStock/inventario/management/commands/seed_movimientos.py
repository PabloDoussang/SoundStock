from uuid import NAMESPACE_URL, uuid5

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from catalogo.models import Producto
from inventario.models import Movimiento
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea entradas o salidas ficticias; conserva el stock al repetir cada carga.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=100)
        parser.add_argument('--lote', type=int, default=2000)
        parser.add_argument('--semilla', type=int, default=42)
        parser.add_argument('--prefijo', default='DEMO')
        parser.add_argument('--tipo', choices=('entrada', 'salida'), default='entrada')

    def handle(self, *args, **options):
        cantidad, lote, tipo = options['cantidad'], options['lote'], options['tipo']
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
                tokens = [uuid5(NAMESPACE_URL, f'soundstock:{p.codigo}' if tipo == 'entrada'
                                else f'soundstock:salida:{p.codigo}') for p in grupo]
                existentes = set(Movimiento.objects.filter(token__in=tokens).values_list('token', flat=True))
                nuevos, modificados = [], []
                for producto, token in zip(grupo, tokens):
                    if token in existentes:
                        conservados += 1
                        continue
                    if tipo == 'entrada':
                        cantidad_stock = fake.random_int(min=1, max=100)
                        if producto.stock + cantidad_stock > 1000000:
                            raise CommandError(f'Stock máximo excedido: {producto.codigo}.')
                        destino = ''
                        motivo = ('DEMO · ' + fake.sentence(nb_words=5))[:240]
                        variacion = cantidad_stock
                    else:
                        if producto.stock == 0:
                            raise CommandError(f'{producto.codigo} no tiene stock. Ejecuta primero seed_movimientos --tipo entrada.')
                        cantidad_stock = fake.random_int(min=1, max=max(1, producto.stock // 2))
                        destino = fake.company()[:120]
                        motivo = ('DEMO · Venta a ' + destino)[:240]
                        variacion = -cantidad_stock
                    nuevos.append(Movimiento(producto=producto, usuario=responsable, tipo=tipo,
                        anterior=producto.stock, posterior=producto.stock + variacion,
                        variacion=variacion, motivo=motivo, destino=destino, token=token))
                    producto.stock += variacion
                    modificados.append(producto)
                Movimiento.objects.bulk_create(nuevos, batch_size=lote)
                Producto.objects.bulk_update(modificados, ['stock'], batch_size=lote)
                creados += len(nuevos)
        self.stdout.write(self.style.SUCCESS(f'Seeder de {tipo}: {creados} movimientos creados, '
            f'{conservados} existentes conservados.'))
