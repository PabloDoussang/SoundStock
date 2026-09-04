from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from warehouse.models import Product
class Command(BaseCommand):
    help='Asistente inicial de cuenta y datos opcionales.'
    def handle(self,*args,**options):
        if not User.objects.filter(is_superuser=True,is_active=True).exists():
            self.stdout.write('Crea tu cuenta administradora. La contraseña no se mostrará al escribir.')
            call_command('createsuperuser',interactive=True)
        if not Product.objects.exists():
            answer=input('¿Cargar 12 productos y 24 movimientos ficticios para explorar la aplicación? [s/N]: ')
            if answer.strip().lower()=='s':
                admin=User.objects.filter(is_superuser=True,is_active=True).first()
                call_command('seed_demo',username=admin.username)
