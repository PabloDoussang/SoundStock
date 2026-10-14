from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Usuario


class CrearUsuarioForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ('username', 'email', 'rol')


class EditarUsuarioForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = '__all__'


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = EditarUsuarioForm
    add_form = CrearUsuarioForm
    list_display = ('username', 'first_name', 'last_name', 'email', 'rol', 'is_active')
    list_filter = ('rol', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Datos personales', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('rol', 'is_active')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('username', 'email', 'rol', 'password1', 'password2')}),)
    readonly_fields = ('last_login', 'date_joined')
    actions = None

    def get_form(self, request, obj=None, **kwargs):
        base = super().get_form(request, obj, **kwargs)

        class FormularioSeguro(base):
            def clean(self):
                data = super().clean()
                if obj and obj.pk == request.user.pk and (data.get('rol') != 'Administrador' or not data.get('is_active')):
                    raise ValidationError('No puedes desactivar tu propia cuenta administradora.')
                return data

        return FormularioSeguro

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.pk != request.user.pk)
