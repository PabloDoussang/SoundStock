from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count

from .models import Categoria, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_productos')
    search_fields = ('nombre',)
    ordering = ('nombre',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(total_productos=Count('productos'))

    @admin.display(description='Productos', ordering='total_productos')
    def cantidad_productos(self, obj):
        return obj.total_productos


class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'

    def clean_codigo(self):
        return self.cleaned_data['codigo'].strip().upper()

    def clean(self):
        values = super().clean()
        if self.instance.pk and self.instance.stock and not values.get('activo'):
            raise ValidationError('Registra una salida o ajuste antes de archivar un producto con stock.')
        return values


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    form = ProductoAdminForm
    list_display = ('codigo', 'nombre', 'categoria', 'ubicacion', 'stock', 'stock_minimo', 'estado_stock', 'activo')
    list_filter = ('categoria', 'activo', 'ubicacion')
    search_fields = ('codigo', 'nombre', 'categoria__nombre', 'ubicacion')
    list_select_related = ('categoria',)
    autocomplete_fields = ('categoria',)
    readonly_fields = ('stock', 'estado_stock')
    list_per_page = 25
    show_full_result_count = False
    actions = None

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or (obj.stock == 0 and not obj.movimientos.exists()))
