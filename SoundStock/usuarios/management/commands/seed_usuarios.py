from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from faker import Faker

from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Crea usuarios ficticios deshabilitados, sin duplicarlos al repetir el comando.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=20)
        parser.add_argument('--lote', type=int, default=2000)
        parser.add_argument('--semilla', type=int, default=42)

    def handle(self, *args, **options):
        cantidad, lote = options['cantidad'], options['lote']
        if not 1 <= cantidad <= 1000000 or not 1 <= lote <= 10000:
            raise CommandError('Cantidad: 1 a 1.000.000; lote: 1 a 10.000.')
        fake = Faker('es_CL')
        fake.seed_instance(options['semilla'])
        creados = actualizados = 0
        for comienzo in range(0, cantidad, lote):
            usuarios = [Usuario(username=f'demo_usuario_{i + 1:07d}', first_name=fake.first_name()[:150],
                last_name=fake.last_name()[:150], email=fake.safe_email(), rol='Consulta',
                password='!', is_active=False, is_staff=False, is_superuser=False)
                for i in range(comienzo, min(comienzo + lote, cantidad))]
            with transaction.atomic():
                existentes = Usuario.objects.filter(username__in=[u.username for u in usuarios]).count()
                Usuario.objects.bulk_create(usuarios, batch_size=lote, update_conflicts=True,
                    unique_fields=['username'], update_fields=['first_name', 'last_name', 'email'])
            creados += len(usuarios) - existentes
            actualizados += existentes
        self.stdout.write(self.style.SUCCESS(f'Seeder terminado: {creados} usuarios creados, {actualizados} actualizados.'))
