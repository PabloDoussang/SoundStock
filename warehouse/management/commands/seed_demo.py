import json
import uuid
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from warehouse.models import Product, Movement
from warehouse.services import record_movement
class Command(BaseCommand):
    help = 'Carga datos ficticios una sola vez. Requiere una cuenta administradora existente.'
    def add_arguments(self, parser): parser.add_argument('--username',required=True)
    @transaction.atomic
    def handle(self,*args,**options):
        user=User.objects.filter(username=options['username'],is_superuser=True).first()
        if not user: raise CommandError('Primero crea un superusuario con createsuperuser.')
        if Product.objects.exists(): raise CommandError('La bodega ya contiene productos. No se modifica ni duplica el inventario.')
        for name in ['Consulta','Operador']: Group.objects.get_or_create(name=name)
        data=json.loads((Path(__file__).resolve().parents[2]/'data'/'productos_demo.json').read_text(encoding='utf-8'))
        for i,row in enumerate(data):
            amount=row.pop('stock')
            p=Product.objects.create(**row)
            added=amount+5+i%6
            m,_=record_movement(product_id=p.pk,kind='entrada',quantity=added,reason='DEMO · Recepción inicial, guía '+str(1000+i),destination='',user=user,token=uuid.uuid4())
            Movement.objects.filter(pk=m.pk).update(created_at=timezone.now()-timedelta(days=12-i%10,hours=i%4))
            m,_=record_movement(product_id=p.pk,kind='salida',quantity=added-amount,reason='DEMO · Despacho de prueba, guía '+str(2000+i),destination=['Sucursal del rock','Sucursal del DJ','Sucursal de reggaetón y cumbia'][i%3],user=user,token=uuid.uuid4())
            Movement.objects.filter(pk=m.pk).update(created_at=timezone.now()-timedelta(days=5-i%6,hours=i%3))
        self.stdout.write(self.style.SUCCESS('12 productos y 24 movimientos ficticios cargados.'))
