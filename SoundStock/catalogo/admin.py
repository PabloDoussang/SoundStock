from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db.models import Count

from .models import Categoria, Producto


class CantidadStockFilter(admin.SimpleListFilter):
    title = 'cantidad en stock'
    parameter_name = 'cantidad_stock'

    def lookups(self, request, model_admin):
        return (('0', 'Sin stock'), ('1-10', '1 a 10 unidades'),
                ('11-50', '11 a 50 unidades'), ('51+', 'Más de 50 unidades'))

    def queryset(self, request, queryset):
        valor = self.value()
        if valor == '0':
            return queryset.filter(stock=0)
        if valor == '1-10':
            return queryset.filter(stock__range=(1, 10))
        if valor == '11-50':
            return queryset.filter(stock__range=(11, 50))
        if valor == '51+':
            return queryset.filter(stock__gt=50)
        return queryset


class OrdenProductoFilter(admin.SimpleListFilter):
    title = 'ordenar productos'
    parameter_name = 'orden_productos'

    def lookups(self, request, model_admin):
        return (('az', 'Nombre: A a Z'), ('za', 'Nombre: Z a A'),
                ('stock_asc', 'Stock: menor a mayor'),
                ('stock_desc', 'Stock: mayor a menor'))

    def queryset(self, request, queryset):
        return queryset


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
    list_filter = (CantidadStockFilter, OrdenProductoFilter, 'categoria', 'activo', 'ubicacion')
    search_fields = ('codigo', 'nombre', 'categoria__nombre', 'ubicacion')
    list_select_related = ('categoria',)
    autocomplete_fields = ('categoria',)
    readonly_fields = ('stock', 'estado_stock')
    list_per_page = 25
    show_full_result_count = False
    actions = None

    def get_ordering(self, request):
        return {
            'az': ('nombre', 'pk'),
            'za': ('-nombre', '-pk'),
            'stock_asc': ('stock', 'nombre', 'pk'),
            'stock_desc': ('-stock', 'nombre', 'pk'),
        }.get(request.GET.get('orden_productos'), ('-pk',))

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (
            obj is None or (obj.stock == 0 and not obj.movimientos.exists()))
