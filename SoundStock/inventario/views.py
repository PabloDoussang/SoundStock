import csv
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from catalogo.models import Producto
from .access import roles_permitidos
from .forms import MovimientoForm
from .models import Movimiento
from .services import registrar_movimiento


@login_required
def inicio(request):
    productos = Producto.objects.filter(activo=True)
    movimientos = Movimiento.objects.select_related('producto', 'usuario')
    hoy = timezone.localdate()
    return render(request, 'inventario/inicio.html', {
        'cantidad_productos': productos.count(),
        'unidades': productos.aggregate(total=Sum('stock'))['total'] or 0,
        'alertas': productos.filter(stock__lte=F('stock_minimo')).count(),
        'movimientos_hoy': movimientos.filter(fecha__date=hoy).count(),
        'recientes': movimientos[:10],
    })


def filtrar_movimientos(request):
    rows = Movimiento.objects.select_related('producto', 'usuario')
    if request.GET.get('tipo') in dict(Movimiento.TIPOS):
        rows = rows.filter(tipo=request.GET['tipo'])
    q = request.GET.get('q', '').strip()
    if q:
        rows = rows.filter(Q(producto__codigo__icontains=q) | Q(producto__nombre__icontains=q) |
                           Q(motivo__icontains=q) | Q(usuario__username__icontains=q))
    try:
        desde = date.fromisoformat(request.GET['desde']) if request.GET.get('desde') else None
        hasta = date.fromisoformat(request.GET['hasta']) if request.GET.get('hasta') else None
    except ValueError:
        return rows.none()
    if desde and hasta and desde > hasta:
        return rows.none()
    if desde:
        rows = rows.filter(fecha__date__gte=desde)
    if hasta:
        rows = rows.filter(fecha__date__lte=hasta)
    return rows


@login_required
def movimientos(request):
    rows = filtrar_movimientos(request)
    return render(request, 'inventario/movimientos.html', {
        'pagina': Paginator(rows, 20).get_page(request.GET.get('pagina')),
        'total': rows.count(), 'tipos': Movimiento.TIPOS,
    })


@roles_permitidos('Administrador', 'Operador')
def nuevo_movimiento(request):
    selected = request.POST.get('producto') or request.GET.get('producto')
    form = MovimientoForm(request.POST or None, initial={'producto': selected})
    # En una base con un millón de productos el select solo muestra 100.
    opciones = list(Producto.objects.select_related('categoria').filter(activo=True).order_by('codigo')[:100])
    if selected and str(selected).isdigit():
        especifico = Producto.objects.select_related('categoria').filter(pk=selected, activo=True).first()
        if especifico and all(p.pk != especifico.pk for p in opciones):
            opciones.append(especifico)
    form.fields['producto'].choices = [('', 'Seleccionar producto')] + [(p.pk, str(p)) for p in opciones]
    if request.method == 'POST' and form.is_valid():
        try:
            values = form.cleaned_data
            movimiento, creado = registrar_movimiento(producto_id=values['producto'].pk,
                usuario=request.user, tipo=values['tipo'], cantidad=values['cantidad'],
                motivo=values['motivo'], destino=values['destino'], token=values['token'])
            messages.success(request, f'MOV-{movimiento.pk:05d}: stock resultante {movimiento.posterior}.'
                if creado else 'La operación ya estaba registrada; no se duplicó el stock.')
            return redirect('movimientos')
        except ValidationError as error:
            form.add_error(None, error)
    return render(request, 'inventario/nuevo_movimiento.html', {'form': form})


@login_required
def reportes(request):
    productos = Producto.objects.filter(activo=True)
    rows = filtrar_movimientos(request)
    por_categoria = productos.order_by().values('categoria__nombre').annotate(
        productos=Count('pk'), unidades=Sum('stock')).order_by('-unidades')
    resumen = rows.aggregate(entradas=Sum('variacion', filter=Q(tipo='entrada')),
        salidas=Sum('variacion', filter=Q(tipo='salida')),
        ajustes=Sum('variacion', filter=Q(tipo='ajuste')))
    por_dia = rows.order_by().annotate(dia=TruncDate('fecha')).values('dia', 'tipo').annotate(
        unidades=Sum('variacion')).order_by('-dia')[:90]
    return render(request, 'inventario/reportes.html', {
        'categorias': por_categoria, 'entradas': resumen['entradas'] or 0,
        'salidas': -(resumen['salidas'] or 0), 'ajustes': resumen['ajustes'] or 0,
        'movimientos': rows.count(), 'por_dia': por_dia,
    })


@login_required
def ubicaciones(request):
    rows = Producto.objects.filter(activo=True)
    q = request.GET.get('q', '').strip()
    if q:
        rows = rows.filter(Q(ubicacion__icontains=q) | Q(nombre__icontains=q) | Q(codigo__icontains=q))
    lugares = rows.order_by().values('ubicacion').annotate(
        productos=Count('pk'), unidades=Sum('stock')).order_by('ubicacion')
    return render(request, 'inventario/ubicaciones.html', {
        'pagina': Paginator(lugares, 20).get_page(request.GET.get('pagina')),
    })


class Echo:
    def write(self, text):
        return text


@login_required
def exportar(request, tipo):
    if tipo == 'productos':
        rows = Producto.objects.select_related('categoria').filter(activo=True)
        header = ['SKU', 'Producto', 'Categoría', 'Ubicación', 'Stock', 'Mínimo']
        values = ([p.codigo, p.nombre, p.categoria.nombre, p.ubicacion, p.stock, p.stock_minimo]
                  for p in rows.iterator(chunk_size=2000))
    elif tipo == 'movimientos':
        rows = filtrar_movimientos(request)
        header = ['ID', 'Fecha', 'SKU', 'Tipo', 'Anterior', 'Variación', 'Posterior', 'Responsable', 'Motivo', 'Destino']
        values = ([m.pk, timezone.localtime(m.fecha).isoformat(), m.producto.codigo, m.get_tipo_display(),
                   m.anterior, m.variacion, m.posterior, m.usuario.username, m.motivo, m.destino]
                  for m in rows.iterator(chunk_size=2000))
    else:
        raise Http404

    def content():
        writer = csv.writer(Echo(), delimiter=';')
        yield '\ufeff'
        yield writer.writerow(header)
        for row in values:
            yield writer.writerow(["'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v
                                   for v in row])

    response = StreamingHttpResponse(content(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="soundstock-{tipo}.csv"'
    return response
