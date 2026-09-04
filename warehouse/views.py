"""Vistas U1: listas/diccionarios JSON, formularios y plantillas Django sin ORM."""
import csv
import uuid
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.middleware.csrf import rotate_token
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from warehouse.access import login_required, operator_required, administrator_required, role
from . import store
from .forms import ProductForm, MovementForm, UserForm, LoginForm, ReportFilter, CATEGORIES, KINDS

def page(request,template,**context):
    return render(request,'warehouse/'+template+'.html',context)

def fetch(rows,pk):
    item=next((row for row in rows if row['id']==pk),None)
    if item is None: raise Http404
    return item

def filtered_products(request,products):
    q=request.GET.get('q','').strip().casefold()
    category=request.GET.get('category','')
    state=request.GET.get('status','')
    return [p for p in products if p.active==(request.GET.get('archived')!='1')
        and (not q or q in f'{p.name} {p.code} {p.location}'.casefold())
        and (not category or p.category==category)
        and (state!='low' or p.stock<=p.minimum) and (state!='zero' or p.stock==0)]

def movement_query(request,rows):
    form=ReportFilter(request.GET)
    if not form.is_valid(): return [],form
    start,end=form.cleaned_data.get('start'),form.cleaned_data.get('end')
    q=request.GET.get('q','').strip().casefold()
    kind=request.GET.get('kind','')
    result=[]
    for m in rows:
        day=timezone.localtime(m.created_at).date()
        if start and day<start or end and day>end: continue
        if kind in dict(KINDS) and m.kind!=kind: continue
        if q and q not in f'{m.product.name} {m.product.code} {m.reason} {m.destination}'.casefold(): continue
        result.append(m)
    return result,form

def chart_data(rows):
    days={}
    for m in rows:
        day=timezone.localtime(m.created_at).date().isoformat()
        days.setdefault(day,dict(date=day,entrada=0,salida=0,ajuste=0))
        days[day][m.kind]+=abs(m.delta) if m.kind=='salida' else m.delta
    return [days[key] for key in sorted(days)]

def login(request):
    if request.user.is_authenticated: return redirect('dashboard')
    form=LoginForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        u=next((u for u in store.read()['users'] if u['username']==form.cleaned_data['username'] and u['is_active']),None)
        if u and check_password(form.cleaned_data['password'],u['password']):
            request.session.cycle_key()
            rotate_token(request)
            request.session['u1_user']=u['id']
            request.session['u1_version']=u['session_version']
            target=request.POST.get('next','/')
            if not url_has_allowed_host_and_scheme(target,{request.get_host()},require_https=request.is_secure()): target='/'
            return redirect(target or '/')
        form.add_error(None,'Usuario o contraseña incorrectos, o cuenta inactiva.')
    if not store.read()['users']:
        messages.warning(request,'Prepara la cuenta inicial ejecutando iniciar.bat.')
    return render(request,'registration/login.html',{'form':form,'next':request.GET.get('next','/')})

@require_POST
def logout(request):
    if request.user.is_authenticated:
        with store.edit() as data:
            fetch(data['users'],request.user.pk)['session_version']=str(uuid.uuid4())
    request.session.flush()
    return redirect('login')

@login_required
def dashboard(request):
    _,products,rows=store.objects(store.read())
    products=[p for p in products if p.active]
    today=timezone.localdate()
    low=sorted([p for p in products if p.stock<=p.minimum],key=lambda p:(p.stock,p.name))
    recent=[m for m in rows if today-timedelta(days=13)<=timezone.localtime(m.created_at).date()<=today]
    return page(request,'dashboard',title='Resumen de bodega',section='dashboard',product_count=len(products),
        unit_count=sum(p.stock for p in products),low_count=len(low),low_products=low[:5],recent=rows[:5],today=today,
        today_count=sum(timezone.localtime(m.created_at).date()==today for m in rows),chart=chart_data(recent))

@login_required
def products(request):
    _,products,_=store.objects(store.read())
    items=filtered_products(request,products)
    return page(request,'products',title='Inventario',section='products',items=Paginator(items,12).get_page(request.GET.get('page')),count=len(items),categories=CATEGORIES)

@operator_required
def product_edit(request,pk=None):
    existing=fetch(store.read()['products'],pk) if pk else None
    if existing and not existing['active']: raise Http404
    form=ProductForm(request.POST or None,initial=existing)
    if request.method=='POST' and form.is_valid():
        try:
            with store.edit() as data:
                values=form.cleaned_data
                if any(p['code']==values['code'] and p['id']!=pk for p in data['products']):
                    raise ValidationError('Este código ya existe, incluso si está archivado.')
                if pk:
                    p=fetch(data['products'],pk)
                    if not p['active']: raise ValidationError('El producto ya no está activo.')
                    p.update(values)
                else: data['products'].append(dict(values,id=store.next_id(data['products']),stock=0,active=True))
            messages.success(request,'Producto guardado. Registra existencias desde Operaciones de stock.')
            return redirect('products')
        except ValidationError as error: form.add_error(None,error)
    return page(request,'form',title='Editar producto' if pk else 'Nuevo producto',section='products',form=form,back='products',hint='El stock se modifica desde Operaciones de stock para conservar el historial.',submit='Guardar producto')

@administrator_required
def product_archive(request,pk):
    _,products,_=store.objects(store.read())
    p=next((p for p in products if p.pk==pk),None)
    if p is None: raise Http404
    if request.method=='POST':
        with store.edit() as data:
            row=fetch(data['products'],pk)
            if row['active'] and row['stock']:
                messages.error(request,'Para archivar el producto, registra primero la salida o el ajuste de sus existencias.')
            else:
                row['active']=not row['active']
                messages.success(request,'Producto reactivado.' if row['active'] else 'Producto archivado; se conserva todo su historial.')
        return redirect('products')
    return page(request,'confirm',title='Archivar producto' if p.active else 'Reactivar producto',section='products',product=p,back='products')

@operator_required
def movement_new(request):
    _,products,_=store.objects(store.read())
    form=MovementForm(request.POST or None,products=products,initial={'product':request.GET.get('product'),'kind':request.GET.get('kind','entrada')})
    if request.method=='POST' and form.is_valid():
        try:
            values=form.cleaned_data
            with store.edit() as data:
                existing=next((m for m in data['movements'] if m['token']==str(values['token'])),None)
                if existing:
                    if existing['user']!=request.user.pk: raise ValidationError('Identificador de operación inválido.')
                    messages.info(request,'Esta operación ya estaba registrada. No se duplicó el stock.')
                else:
                    p=fetch(data['products'],values['product'])
                    if not p['active']: raise ValidationError('El producto ya no está activo.')
                    before=p['stock'];kind=values['kind'];quantity=values['quantity']
                    after=quantity if kind=='ajuste' else before+(quantity if kind=='entrada' else -quantity)
                    if after<0: raise ValidationError(f'Stock insuficiente: hay {before} unidades disponibles.')
                    if after>1000000: raise ValidationError('El stock supera el máximo permitido de 1.000.000.')
                    if after==before: raise ValidationError('El ajuste no modifica las existencias.')
                    mid=store.next_id(data['movements'])
                    data['movements'].append(dict(id=mid,product=p['id'],kind=kind,delta=after-before,before=before,after=after,
                        reason=values['reason'],destination=values['destination'],user=request.user.pk,created_at=timezone.now().isoformat(),token=str(values['token'])))
                    p['stock']=after
                    messages.success(request,f'MOV-{mid:05d} registrado. Stock resultante: {after} unidades.')
            return redirect('movements')
        except ValidationError as error: form.add_error(None,error)
    return page(request,'stock_form',title='Operaciones de stock',section='movement_new',form=form,
        stock_data=[dict(id=p.id,stock=p.stock,minimum=p.minimum,location=p.location) for p in products if p.active])

@login_required
def movements(request):
    _,_,rows=store.objects(store.read())
    rows,form=movement_query(request,rows)
    return page(request,'movements',title='Movimientos',section='movements',items=Paginator(rows,15).get_page(request.GET.get('page')),count=len(rows),filter_form=form,kinds=KINDS)

@login_required
def reports(request):
    _,products,rows=store.objects(store.read())
    rows,form=movement_query(request,rows)
    products=[p for p in products if p.active]
    cats={}
    for p in products:
        cats.setdefault(p.category,dict(category=p.category,total=0,products=0))
        cats[p.category]['total']+=p.stock;cats[p.category]['products']+=1
    return page(request,'reports',title='Reportes de inventario',section='reports',filter_form=form,chart=chart_data(rows),
        categories=sorted(cats.values(),key=lambda c:c['total'],reverse=True),count=len(rows),
        entries=sum(m.delta for m in rows if m.kind=='entrada'),exits=-sum(m.delta for m in rows if m.kind=='salida'),
        adjustments=sum(m.delta for m in rows if m.kind=='ajuste'),low=sum(p.stock<=p.minimum for p in products))

@login_required
def locations(request):
    _,products,_=store.objects(store.read())
    q=request.GET.get('q','').strip().casefold();groups={}
    for p in sorted(products,key=lambda p:(p.location,p.name)):
        if not p.active or (q and q not in f'{p.location} {p.name} {p.code}'.casefold()): continue
        groups.setdefault(p.location,dict(name=p.location,products=[],stock=0))
        groups[p.location]['products'].append(p);groups[p.location]['stock']+=p.stock
    return page(request,'locations',title='Ubicaciones',section='locations',locations=groups.values())

@login_required
def export(request,kind):
    _,products,rows=store.objects(store.read())
    response=HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition']=f'attachment; filename="music-pro-{kind}.csv"'
    response.write('\ufeff');writer=csv.writer(response,delimiter=';')
    if kind=='inventario':
        writer.writerow(['SKU','Producto','Categoría','Ubicación','Stock','Mínimo','Estado'])
        values=[[p.code,p.name,p.category,p.location,p.stock,p.minimum,p.status] for p in filtered_products(request,products)]
    elif kind=='movimientos':
        rows,form=movement_query(request,rows)
        if not form.is_valid(): return HttpResponse('Rango de fechas inválido.',status=400)
        writer.writerow(['Movimiento','Fecha','SKU','Producto','Tipo','Variación','Anterior','Resultante','Responsable','Destino','Motivo'])
        values=[[m.pk,timezone.localtime(m.created_at).isoformat(),m.product.code,m.product.name,m.get_kind_display(),m.delta,m.before,m.after,m.user.username,m.destination,m.reason] for m in rows]
    else: raise Http404
    for row in values:
        writer.writerow([("'"+str(v)) if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in row])
    return response

@administrator_required
def users(request):
    accounts,_,_=store.objects(store.read())
    return page(request,'users',title='Usuarios y roles',section='users',users=[{'account':u,'role':u.role} for u in sorted(accounts.values(),key=lambda u:u.username)])

@administrator_required
def user_edit(request,pk=None):
    existing=fetch(store.read()['users'],pk) if pk else None
    initial={k:v for k,v in existing.items() if k!='password'} if existing else None
    form=UserForm(request.POST or None,initial=initial)
    if request.method=='POST' and form.is_valid():
        try:
            values=form.cleaned_data.copy();password=values.pop('password')
            if not pk and not password: raise ValidationError('Define una contraseña para la nueva cuenta.')
            if pk==request.user.pk and (not values['is_active'] or values['role']!='Administrador'):
                raise ValidationError('No puedes desactivar ni quitar el rol administrador de tu propia cuenta.')
            with store.edit() as data:
                if any(u['username']==values['username'] and u['id']!=pk for u in data['users']): raise ValidationError('Ya existe una cuenta con este nombre de usuario.')
                row=fetch(data['users'],pk) if pk else dict(id=store.next_id(data['users']),session_version=str(uuid.uuid4()))
                row.update(values)
                if password:
                    row['password']=make_password(password);row['session_version']=str(uuid.uuid4())
                if not pk: data['users'].append(row)
                if pk==request.user.pk: request.session['u1_version']=row['session_version']
            messages.success(request,'Usuario guardado.')
            return redirect('users')
        except ValidationError as error: form.add_error(None,error)
    return page(request,'form',title='Editar usuario' if pk else 'Nuevo usuario',section='users',form=form,back='users',hint='Consulta: lectura. Operador: productos y stock. Administrador: acceso completo.',submit='Guardar usuario')
