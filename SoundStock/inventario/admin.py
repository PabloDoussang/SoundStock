from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from .models import Movimiento
from .services import calcular_saldo, eliminar_ultimo, registrar_movimiento


class MovimientoAdminForm(forms.ModelForm):
    cantidad = forms.IntegerField(min_value=0, max_value=1000000,
        help_text='Entrada/salida: unidades. Ajuste: saldo final. La edición se limita al último movimiento.')

    class Meta:
        model = Movimiento
        fields = ('producto', 'usuario', 'tipo', 'cantidad', 'motivo', 'destino')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['cantidad'].initial = (self.instance.posterior if self.instance.tipo == 'ajuste'
                                               else abs(self.instance.variacion))

    def clean(self):
        data = super().clean()
        producto = data.get('producto')
        if producto and data.get('tipo') and data.get('cantidad') is not None:
            if not producto.activo:
                raise ValidationError('El producto está archivado.')
            anterior = producto.stock
            if self.instance.pk:
                ultimo = producto.movimientos.order_by('-pk').first()
                if producto.pk != self.instance.producto_id or not ultimo or ultimo.pk != self.instance.pk:
                    raise ValidationError('Solo se puede editar el último movimiento sin cambiar de producto.')
                anterior = self.instance.anterior
            calcular_saldo(anterior, data['tipo'], data['cantidad'], data.get('destino', ''))
        return data


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    form = MovimientoAdminForm
    fields = ('producto', 'usuario', 'tipo', 'cantidad', 'motivo', 'destino',
              'anterior', 'posterior', 'variacion', 'fecha', 'token')
    readonly_fields = ('anterior', 'posterior', 'variacion', 'fecha', 'token')
    list_display = ('id', 'producto', 'tipo', 'variacion', 'anterior', 'posterior', 'usuario', 'fecha')
    list_filter = ('tipo', 'fecha', 'producto__categoria')
    search_fields = ('producto__codigo', 'producto__nombre', 'usuario__username', 'motivo', 'destino')
    autocomplete_fields = ('producto', 'usuario')
    list_select_related = ('producto', 'usuario')
    date_hierarchy = 'fecha'
    list_per_page = 25
    show_full_result_count = False
    actions = None

    def save_model(self, request, obj, form, change):
        guardado, _ = registrar_movimiento(producto_id=form.cleaned_data['producto'].pk,
            usuario=form.cleaned_data['usuario'], tipo=form.cleaned_data['tipo'],
            cantidad=form.cleaned_data['cantidad'], motivo=form.cleaned_data['motivo'],
            destino=form.cleaned_data.get('destino', ''), instancia=obj if change else None)
        obj.__dict__.update(guardado.__dict__)

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or obj.producto.movimientos.order_by('-pk').first().pk == obj.pk)

    def delete_model(self, request, obj):
        eliminar_ultimo(obj)
