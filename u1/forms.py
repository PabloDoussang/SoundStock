import uuid
from django import forms
from django.contrib.auth.password_validation import validate_password
from warehouse.usernames import normalize_username

CATEGORIES=[(name,name) for name in ['Cuerdas','Percusión','Teclados','Audio','DJ','Accesorios']]
KINDS=[('entrada','Entrada'),('salida','Salida'),('ajuste','Ajuste')]

class ProductForm(forms.Form):
    code=forms.RegexField(r'^[A-Z0-9-]{3,30}$',label='Código SKU',max_length=30)
    name=forms.CharField(label='Nombre',max_length=120)
    category=forms.ChoiceField(label='Categoría',choices=CATEGORIES)
    location=forms.CharField(label='Ubicación',max_length=60)
    minimum=forms.IntegerField(label='Stock mínimo',min_value=0,max_value=1000000)

class MovementForm(forms.Form):
    product=forms.TypedChoiceField(label='Producto',coerce=int)
    kind=forms.ChoiceField(label='Tipo de movimiento',choices=KINDS)
    quantity=forms.IntegerField(label='Cantidad',min_value=0,max_value=1000000,help_text='Entrada/salida: unidades a mover. Ajuste: cantidad física final contada.')
    destination=forms.ChoiceField(label='Destino de salida',required=False,choices=[('','Seleccionar destino')]+[(n,n) for n in ['Sucursal del rock','Sucursal del DJ','Sucursal de reggaetón y cumbia','Franquicia','Cliente final']])
    reason=forms.CharField(label='Motivo y referencia',max_length=240,widget=forms.Textarea(attrs={'rows':3}))
    token=forms.UUIDField(widget=forms.HiddenInput,initial=uuid.uuid4)
    def __init__(self,*args,products=(),**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['product'].choices=[(p.id,f'{p.code} · {p.name}') for p in products if p.active]
    def clean(self):
        d=super().clean()
        if d.get('kind')!='ajuste' and d.get('quantity')==0: self.add_error('quantity','La cantidad debe ser mayor que cero.')
        if d.get('kind')=='salida' and not d.get('destination'): self.add_error('destination','La salida requiere un destino.')
        if d.get('kind')!='salida': d['destination']=''
        return d

class UserForm(forms.Form):
    username=forms.CharField(label='Nombre de usuario',max_length=150)
    first_name=forms.CharField(label='Nombre',max_length=150,required=False)
    last_name=forms.CharField(label='Apellido',max_length=150,required=False)
    email=forms.EmailField(label='Correo electrónico',required=False)
    is_active=forms.BooleanField(label='Activo',required=False,initial=True)
    role=forms.ChoiceField(label='Rol',choices=[(n,n) for n in ['Consulta','Operador','Administrador']])
    password=forms.CharField(label='Contraseña',required=False,widget=forms.PasswordInput,help_text='Al editar, deja vacío para conservar la contraseña.')
    def clean_username(self): return normalize_username(self.cleaned_data['username'])
    def clean_password(self):
        value=self.cleaned_data['password']
        if value: validate_password(value)
        return value

class LoginForm(forms.Form):
    username=forms.CharField(label='Nombre de usuario',max_length=150)
    password=forms.CharField(label='Contraseña',widget=forms.PasswordInput)

class ReportFilter(forms.Form):
    start=forms.DateField(label='Desde',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    end=forms.DateField(label='Hasta',required=False,widget=forms.DateInput(attrs={'type':'date'}))
    def clean(self):
        d=super().clean()
        if d.get('start') and d.get('end') and d['start']>d['end']: raise forms.ValidationError('La fecha inicial no puede ser posterior a la final.')
        return d
