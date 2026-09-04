import json
import uuid
from getpass import getpass
from datetime import timedelta
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from warehouse.usernames import normalize_username
from warehouse.forms import validate_account_password
from warehouse import store

class Command(BaseCommand):
    help='Crea la primera cuenta de SoundStock sin modificar los datos existentes.'
    def handle(self,*args,**options):
        if store.read()['users']:
            self.stdout.write('Prototipo U1 preparado; se conservan sus datos JSON.')
            return
        try: username=normalize_username(input('Nombre de usuario (admite espacios): '))
        except ValidationError as error: raise CommandError(' '.join(error.messages))
        password=getpass('Contraseña: ')
        if password!=getpass('Repite la contraseña: '): raise CommandError('Las contraseñas no coinciden.')
        try: validate_account_password(password,dict(username=username,first_name=username))
        except ValidationError as error: raise CommandError(' '.join(error.messages))
        demo=input('¿Cargar productos ficticios? [s/N]: ').strip().lower()=='s'
        with store.edit() as data:
            # Otro inicio pudo terminar mientras se respondía al asistente.
            if data['users']:
                self.stdout.write('La cuenta inicial ya existe; se conservan todos los datos.')
                return
            uid=store.next_id(data['users'])
            data['users'].append(dict(id=uid,username=username,first_name=username,last_name='',email='',is_active=True,role='Administrador',password=make_password(password),session_version=str(uuid.uuid4())))
            if demo and not data['products']:
                sample=json.loads((settings.BASE_DIR/'warehouse/data/productos_demo.json').read_text(encoding='utf-8'))
                for i,p in enumerate(sample,1):
                    p.update(id=i,active=True);data['products'].append(p)
                    if p['stock']:
                        data['movements'].append(dict(id=store.next_id(data['movements']),product=i,user=uid,kind='entrada',before=0,after=p['stock'],delta=p['stock'],reason='DEMO · Inventario inicial',destination='',token=str(uuid.uuid4()),created_at=(timezone.now()-timedelta(days=i%7)).isoformat()))
        self.stdout.write(self.style.SUCCESS('U1 preparado: JSON y cookies firmadas, sin base de datos.'))
