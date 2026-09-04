import re
import uuid
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import Product, Movement
from .usernames import SpacedUsernameMixin
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code','name','category','location','minimum']
        widgets = {'code':forms.TextInput(attrs={'placeholder':'MP-GTR-001'}),'name':forms.TextInput(attrs={'placeholder':'Ej. Guitarra eléctrica Stratocaster'}),'location':forms.TextInput(attrs={'placeholder':'Ej. A-01-02'}),'minimum':forms.NumberInput(attrs={'min':0,'max':1000000})}
    def clean_code(self):
        code = self.cleaned_data['code'].strip().upper()
        if not re.fullmatch(r'[A-Z0-9-]{3,30}', code): raise forms.ValidationError('Usa entre 3 y 30 letras, números o guiones.')
        if Product.objects.filter(code=code).exclude(pk=self.instance.pk).exists(): raise forms.ValidationError('Este código ya existe, incluso si está archivado.')
        return code
    def clean_minimum(self):
        value = self.cleaned_data['minimum']
        if value > 1000000: raise forms.ValidationError('El máximo es 1.000.000.')
        return value
class MovementForm(forms.Form):
    product = forms.ModelChoiceField(label='Producto', queryset=Product.objects.filter(active=True))
    kind = forms.ChoiceField(label='Tipo de movimiento', choices=Movement.TYPES)
    quantity = forms.IntegerField(label='Cantidad',min_value=0,max_value=1000000,help_text='Entrada/salida: unidades a mover. Ajuste: cantidad física final contada.')
    destination = forms.ChoiceField(label='Destino de salida',required=False,choices=[('','Seleccionar destino'),('Sucursal del rock','Sucursal del rock'),('Sucursal del DJ','Sucursal del DJ'),('Sucursal de reggaetón y cumbia','Sucursal de reggaetón y cumbia'),('Franquicia','Franquicia'),('Cliente final','Cliente final')])
    reason = forms.CharField(label='Motivo y referencia',max_length=240,widget=forms.Textarea(attrs={'rows':3,'placeholder':'Ej. Recepción de proveedor, guía 1052'}))
    token = forms.UUIDField(widget=forms.HiddenInput,initial=uuid.uuid4)
    def clean(self):
        data = super().clean()
        if data.get('kind') == 'salida' and not data.get('destination'): self.add_error('destination','La salida requiere un destino.')
        if data.get('kind') != 'ajuste' and data.get('quantity') == 0: self.add_error('quantity','Ingresa una cantidad mayor que cero.')
        if data.get('kind') != 'salida': data['destination'] = ''
        return data
class UserForm(SpacedUsernameMixin, forms.ModelForm):
    username = forms.CharField(label='Nombre de usuario', max_length=150,
        help_text='Se permiten espacios, por ejemplo: Pablo Doussang.')
    role = forms.ChoiceField(label='Rol', choices=[('Consulta','Consulta'),('Operador','Operador'),('Administrador','Administrador')])
    password = forms.CharField(label='Contraseña',required=False,widget=forms.PasswordInput,help_text='Al editar, deja vacío para conservar la contraseña.')
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','is_active']
    def clean(self):
        data = super().clean()
        password = data.get('password')
        if not self.instance.pk and not password: self.add_error('password','Define una contraseña para la nueva cuenta.')
        if password:
            self.instance.username = data.get('username','')
            validate_password(password,self.instance)
        return data
class ReportFilter(forms.Form):
    start = forms.DateField(label='Desde', required=False, widget=forms.DateInput(attrs={'type':'date'}))
    end = forms.DateField(label='Hasta', required=False, widget=forms.DateInput(attrs={'type':'date'}))
    def clean(self):
        data = super().clean()
        if data.get('start') and data.get('end') and data['start'] > data['end']:
            raise forms.ValidationError('La fecha inicial no puede ser posterior a la final.')
        return data
