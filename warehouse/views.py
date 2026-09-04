import csv
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import update_session_auth_hash
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError, OperationalError
from django.db.models import Q, F, Sum, Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Product, Movement
from .forms import ProductForm, MovementForm, UserForm, ReportFilter
from .services import record_movement
from .access import operator_required, administrator_required, role

def page(request, template, **context):
    return render(request, 'warehouse/' + template + '.html', context)

def filtered_products(request):
    products = Product.objects.filter(active=request.GET.get('archived') != '1')
    q = request.GET.get('q','').strip()
    if q: products = products.filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(location__icontains=q))
    category = request.GET.get('category','')
    if category: products = products.filter(category=category)
    if request.GET.get('status') == 'low': products = products.filter(stock__lte=F('minimum'))
    if request.GET.get('status') == 'zero': products = products.filter(stock=0)
    return products

def movement_query(request):
    form = ReportFilter(request.GET)
    rows = Movement.objects.select_related('product','user')
    if form.is_valid():
        if form.cleaned_data.get('start'): rows = rows.filter(created_at__date__gte=form.cleaned_data['start'])
        if form.cleaned_data.get('end'): rows = rows.filter(created_at__date__lte=form.cleaned_data['end'])
    else: rows = rows.none()
    kind = request.GET.get('kind','')
    if kind in dict(Movement.TYPES): rows = rows.filter(kind=kind)
    q = request.GET.get('q','').strip()
    if q: rows = rows.filter(Q(product__name__icontains=q)|Q(product__code__icontains=q)|Q(reason__icontains=q)|Q(destination__icontains=q))
    return rows, form

def chart_data(rows):
    grouped = list(rows.order_by().annotate(day=TruncDate('created_at')).values('day','kind').annotate(total=Sum('delta')).order_by('day'))
    dates = sorted(set(str(r['day']) for r in grouped))
    chart = [{'date':date,'entrada':0,'salida':0,'ajuste':0} for date in dates]
    mapping = {item['date']:item for item in chart}
    for row in grouped: mapping[str(row['day'])][row['kind']] = abs(row['total']) if row['kind'] != 'ajuste' else row['total']
    return chart

@login_required
def dashboard(request):
    products = Product.objects.filter(active=True)
    today = timezone.localdate()
    rows = Movement.objects.filter(created_at__date__gte=today-timedelta(days=13))
    return page(request,'dashboard',title='Resumen de bodega',section='dashboard',
        product_count=products.count(),unit_count=products.aggregate(n=Sum('stock'))['n'] or 0,
        low_count=products.filter(stock__lte=F('minimum')).count(),
        today_count=Movement.objects.filter(created_at__date=today).count(),
        low_products=products.filter(stock__lte=F('minimum')).order_by('stock','name')[:5],
        recent=Movement.objects.select_related('product','user')[:5],chart=chart_data(rows),today=today)

@login_required
def products(request):
    items = filtered_products(request)
    return page(request,'products',title='Inventario',section='products',items=Paginator(items,12).get_page(request.GET.get('page')),count=items.count(),categories=Product.CATEGORY)

@operator_required
def product_edit(request, pk=None):
    product = get_object_or_404(Product,pk=pk,active=True) if pk else None
    form = ProductForm(request.POST or None,instance=product)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                if product:
                    locked = Product.objects.select_for_update().get(pk=pk,active=True)
                    for key in form.Meta.fields: setattr(locked,key,form.cleaned_data[key])
                    locked.save(update_fields=form.Meta.fields+['updated_at'])
                else: form.save()
            messages.success(request,'Producto guardado. Registra una entrada para incorporar existencias.' if not product else 'Datos del producto actualizados.')
            return redirect('products')
        except (IntegrityError,Product.DoesNotExist):
            form.add_error(None,'El producto cambió o el código ya está registrado. Recarga e intenta nuevamente.')
    return page(request,'form',title='Editar producto' if product else 'Nuevo producto',section='products',form=form,back='products',hint='El stock se modifica desde Operaciones de stock para conservar la trazabilidad.',submit='Guardar producto')

@administrator_required
def product_archive(request, pk):
    product = get_object_or_404(Product,pk=pk)
    if request.method == 'POST':
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=pk)
            if product.active and product.stock != 0:
                messages.error(request,'Para archivar el producto, registra primero la salida o el ajuste de sus existencias.')
            else:
                product.active = not product.active
                product.save(update_fields=['active','updated_at'])
                messages.success(request,'Producto reactivado.' if product.active else 'Producto archivado; se conserva todo su historial.')
        return redirect('products')
    return page(request,'confirm',title='Archivar producto' if product.active else 'Reactivar producto',section='products',product=product,back='products')

@operator_required
def movement_new(request):
    initial = {'kind':request.GET.get('kind','entrada')}
    if request.GET.get('product','').isdigit(): initial['product'] = request.GET['product']
    form = MovementForm(request.POST or None,initial=initial)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        try:
            movement, created = record_movement(product_id=data['product'].pk,kind=data['kind'],quantity=data['quantity'],reason=data['reason'],destination=data['destination'],user=request.user,token=data['token'])
            messages.success(request,f'MOV-{movement.pk:05d} registrado. Stock resultante: {movement.after} unidades.' if created else 'Esta operación ya estaba registrada. No se duplicó el stock.')
            return redirect('movements')
        except ValidationError as error: form.add_error(None,error)
        except Product.DoesNotExist: form.add_error('product','El producto ya no está activo.')
        except OperationalError: form.add_error(None,'La base de datos está ocupada. Intenta guardar nuevamente.')
    stock_data = list(Product.objects.filter(active=True).values('id','stock','minimum','location'))
    return page(request,'stock_form',title='Operaciones de stock',section='movement_new',form=form,stock_data=stock_data)

@login_required
def movements(request):
    rows, form = movement_query(request)
    return page(request,'movements',title='Movimientos',section='movements',items=Paginator(rows,15).get_page(request.GET.get('page')),filter_form=form,kinds=Movement.TYPES,count=rows.count())

@login_required
def reports(request):
    rows, form = movement_query(request)
    products = Product.objects.filter(active=True)
    categories = list(products.order_by().values('category').annotate(total=Sum('stock'),products=Count('id')).order_by('-total'))
    return page(request,'reports',title='Reportes de inventario',section='reports',filter_form=form,chart=chart_data(rows),categories=categories,
        entries=rows.filter(kind='entrada').aggregate(n=Sum('delta'))['n'] or 0,
        exits=abs(rows.filter(kind='salida').aggregate(n=Sum('delta'))['n'] or 0),
        adjustments=rows.filter(kind='ajuste').aggregate(n=Sum('delta'))['n'] or 0,
        low=products.filter(stock__lte=F('minimum')).count(),count=rows.count())

@login_required
def locations(request):
    products = Product.objects.filter(active=True)
    q = request.GET.get('q','').strip()
    if q: products = products.filter(Q(location__icontains=q)|Q(name__icontains=q)|Q(code__icontains=q))
    groups = {}
    for product in products.order_by('location','name'):
        groups.setdefault(product.location,{'name':product.location,'products':[],'stock':0})
        groups[product.location]['products'].append(product)
        groups[product.location]['stock'] += product.stock
    return page(request,'locations',title='Ubicaciones',section='locations',locations=groups.values())

def safe_csv(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(('=','+','-','@')) else value

@login_required
def export(request, kind):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="music-pro-{kind}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response,delimiter=';')
    if kind == 'inventario':
        writer.writerow(['SKU','Producto','Categoría','Ubicación','Stock','Mínimo','Estado'])
        for p in filtered_products(request): writer.writerow([safe_csv(x) for x in [p.code,p.name,p.category,p.location,p.stock,p.minimum,p.status]])
    elif kind == 'movimientos':
        rows, form = movement_query(request)
        if not form.is_valid(): return HttpResponse('Rango de fechas inválido.',status=400)
        writer.writerow(['Movimiento','Fecha','SKU','Producto','Tipo','Variación','Anterior','Resultante','Responsable','Destino','Motivo'])
        for m in rows: writer.writerow([safe_csv(x) for x in [m.pk,timezone.localtime(m.created_at).isoformat(),m.product.code,m.product.name,m.get_kind_display(),m.delta,m.before,m.after,m.user.username,m.destination,m.reason]])
    else: return HttpResponse(status=404)
    return response

@administrator_required
def users(request):
    return page(request,'users',title='Usuarios y roles',section='users',users=[{'account':u,'role':role(u)} for u in User.objects.prefetch_related('groups').order_by('username')])

@administrator_required
def user_edit(request, pk=None):
    account = get_object_or_404(User,pk=pk) if pk else None
    form = UserForm(request.POST or None,instance=account,initial={'role':role(account) if account else 'Consulta'})
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        if account and account.pk == request.user.pk and (not data['is_active'] or data['role'] != 'Administrador'):
            form.add_error(None,'No puedes desactivar ni quitar el rol administrador de tu propia cuenta.')
        else:
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_superuser = data['role'] == 'Administrador'
                user.is_staff = user.is_superuser
                if data['password']: user.set_password(data['password'])
                user.save()
                user.groups.clear()
                if not user.is_superuser: user.groups.add(Group.objects.get_or_create(name=data['role'])[0])
            if user.pk == request.user.pk: update_session_auth_hash(request,user)
            messages.success(request,'Usuario guardado.')
            return redirect('users')
    return page(request,'form',title='Editar usuario' if account else 'Nuevo usuario',section='users',form=form,back='users',hint='Consulta: lectura. Operador: productos y stock. Administrador: acceso completo.',submit='Guardar usuario')
