from functools import wraps
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url

def login_required(view):
    """Exige la sesión JSON sin importar formularios ni modelos de auth."""
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            target = urlsplit(resolve_url(settings.LOGIN_URL))
            query = parse_qsl(target.query, keep_blank_values=True)
            query.append(('next', request.get_full_path()))
            return HttpResponseRedirect(urlunsplit(target._replace(query=urlencode(query))))
        return view(request, *args, **kwargs)
    return wrapped
def role(user):
    if user.is_superuser: return 'Administrador'
    if user.groups.filter(name='Operador').exists(): return 'Operador'
    return 'Consulta'
def operator_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if role(request.user) == 'Consulta': raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped
def administrator_required(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser: raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped
