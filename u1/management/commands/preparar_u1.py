import json
import uuid
from getpass import getpass
from pathlib import Path
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from warehouse.usernames import normalize_username
from u1 import store

class Command(BaseCommand):
    help='Prepara el prototipo U1 sin base de datos. No ejecuta migrate.'
    def handle(self,*args,**options):
        if store.read()['users']:
            self.stdout.write('Prototipo U1 preparado; se conservan sus datos JSON.')
            return
        username=normalize_username(input('Nombre de usuario (admite espacios): '))
        password=getpass('Contraseña: ')
        if password!=getpass('Repite la contraseña: '): raise CommandError('Las contraseñas no coinciden.')
        try: validate_password(password)
        except ValidationError as error: raise CommandError(' '.join(error.messages))
        demo=input('¿Cargar productos ficticios? [s/N]: ').strip().lower()=='s'
        with store.edit() as data:
            data['users'].append(dict(id=1,username=username,first_name=username,last_name='',email='',is_active=True,role='Administrador',password=make_password(password),session_version=str(uuid.uuid4())))
            if demo:
                sample=json.loads((settings.BASE_DIR/'warehouse/data/productos_demo.json').read_text(encoding='utf-8'))
                for i,p in enumerate(sample,1):
                    p.update(id=i,active=True);data['products'].append(p)
                    if p['stock']:
                        data['movements'].append(dict(id=i,product=i,user=1,kind='entrada',before=0,after=p['stock'],delta=p['stock'],reason='DEMO · Inventario inicial',destination='',token=str(uuid.uuid4()),created_at=(timezone.now()-timedelta(days=i%7)).isoformat()))
        self.stdout.write(self.style.SUCCESS('U1 preparado: JSON y cookies firmadas, sin base de datos.'))
