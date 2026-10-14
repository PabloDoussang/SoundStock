from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from inventario.access import roles_permitidos
from .forms import ProductoForm
from .models import Categoria, Producto


@login_required
def lista(request):
    productos = Producto.objects.select_related('categoria').filter(activo=request.GET.get('archivados') != '1')
    busqueda = request.GET.get('q', '').strip()
    if busqueda:
        productos = productos.filter(Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda) |
                                     Q(ubicacion__icontains=busqueda))
    if request.GET.get('categoria'):
        productos = productos.filter(categoria_id=request.GET['categoria'])
    if request.GET.get('estado') == 'bajo':
        productos = productos.filter(stock__gt=0, stock__lte=F('stock_minimo'))
    elif request.GET.get('estado') == 'agotado':
        productos = productos.filter(stock=0)
    elif request.GET.get('estado') == 'disponible':
        productos = productos.filter(stock__gt=F('stock_minimo'))
    for parametro, lookup in (('stock_min', 'stock__gte'), ('stock_max', 'stock__lte')):
        valor = request.GET.get(parametro, '').strip()
        if valor.isascii() and valor.isdecimal() and len(valor) <= 7 and int(valor) <= 1000000:
            productos = productos.filter(**{lookup: int(valor)})
    ordenes = {
        'recientes': ('-pk',),
        'nombre_az': ('nombre', 'pk'),
        'nombre_za': ('-nombre', '-pk'),
        'stock_asc': ('stock', 'nombre', 'pk'),
        'stock_desc': ('-stock', 'nombre', 'pk'),
    }
    productos = productos.order_by(*ordenes.get(request.GET.get('orden'), ordenes['recientes']))
    por_pagina = int(request.GET.get('por_pagina', '20')) if request.GET.get('por_pagina') in ('20', '50', '100') else 20
    parametros = request.GET.copy()
    parametros.pop('pagina', None)
    return render(request, 'catalogo/lista.html', {
        'pagina': Paginator(productos, por_pagina).get_page(request.GET.get('pagina')),
        'categorias': Categoria.objects.all(), 'total': productos.count(),
        'filtros_query': parametros.urlencode(),
    })


@roles_permitidos('Administrador', 'Operador')
def crear(request):
    form = ProductoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto creado. Registra sus existencias desde Movimientos.')
        return redirect('productos')
    return render(request, 'catalogo/formulario.html', {'form': form, 'titulo': 'Nuevo producto'})


@roles_permitidos('Administrador', 'Operador')
def editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Producto actualizado.')
        return redirect('productos')
    return render(request, 'catalogo/formulario.html', {'form': form, 'titulo': 'Editar producto'})


@require_POST
@roles_permitidos('Administrador')
def archivar(request, pk):
    with transaction.atomic():
        producto = get_object_or_404(Producto.objects.select_for_update(), pk=pk)
        if producto.activo and producto.stock:
            messages.error(request, 'Antes de archivar, el stock debe quedar en cero.')
        else:
            producto.activo = not producto.activo
            producto.save(update_fields=['activo'])
            messages.success(request, 'Estado del producto actualizado.')
    return redirect('productos')


@roles_permitidos('Administrador')
def eliminar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                producto = Producto.objects.select_for_update().get(pk=pk)
                if producto.stock or producto.movimientos.exists():
                    raise ProtectedError('Producto con existencias o historial', [producto])
                producto.delete()
            messages.success(request, 'Producto eliminado.')
        except ProtectedError:
            messages.error(request, 'No puedes eliminar productos con stock o movimientos. Usa Archivar.')
        return redirect('productos')
    return render(request, 'catalogo/eliminar.html', {'producto': producto})
