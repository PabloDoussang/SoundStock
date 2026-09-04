"""Repositorio JSON del prototipo U1. Un proceso local; no utiliza ORM ni SQL."""
import json
import os
import tempfile
from pathlib import Path
from threading import RLock
from contextlib import contextmanager
from types import SimpleNamespace
from datetime import datetime
from django.conf import settings

lock = RLock()

def read():
    with lock:
        path = Path(settings.U1_DATA_FILE)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'products':[],'movements':[],'users':[]}

@contextmanager
def edit():
    with lock:
        data = read()
        yield data
        path = Path(settings.U1_DATA_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Cierra y sincroniza el archivo antes de reemplazar el anterior.
        # Una excepción dentro del bloque edit() nunca modifica el JSON guardado.
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=path.parent, prefix=path.name+'.', suffix='.tmp', delete=False) as output:
                temporary = Path(output.name)
                json.dump(data, output, ensure_ascii=False, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary,path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

def next_id(rows):
    return max((row['id'] for row in rows),default=0)+1

class MockGroups:
    def __init__(self,role): self.role=role
    def filter(self, name): return SimpleNamespace(exists=lambda:self.role==name)

class MockUser(SimpleNamespace):
    @property
    def pk(self): return self.id
    @property
    def is_authenticated(self): return True
    @property
    def is_superuser(self): return self.role == 'Administrador'
    @property
    def groups(self): return MockGroups(self.role)
    def get_full_name(self): return (self.first_name+' '+self.last_name).strip()

def objects(data):
    users={row['id']:MockUser(**row) for row in data['users']}
    products={}
    for row in data['products']:
        p=SimpleNamespace(**row,pk=row['id'])
        p.status='Agotado' if p.stock==0 else 'Stock bajo' if p.stock<=p.minimum else 'Disponible'
        products[p.id]=p
    movements=[]
    for row in data['movements']:
        fields={k:v for k,v in row.items() if k not in {'created_at','product','user'}}
        m=SimpleNamespace(**fields,pk=row['id'],created_at=datetime.fromisoformat(row['created_at']),product=products[row['product']],user=users[row['user']])
        m.get_kind_display=lambda kind=m.kind: {'entrada':'Entrada','salida':'Salida','ajuste':'Ajuste'}[kind]
        movements.append(m)
    return users, sorted(products.values(),key=lambda p:p.name.casefold()), sorted(movements,key=lambda m:(m.created_at,m.pk),reverse=True)
