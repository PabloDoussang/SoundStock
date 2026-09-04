from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
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
