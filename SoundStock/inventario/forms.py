from uuid import uuid4

from django import forms

from catalogo.models import Producto
from .models import Movimiento


class MovimientoForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), empty_label='Seleccionar producto')
    tipo = forms.ChoiceField(choices=Movimiento.TIPOS)
    cantidad = forms.IntegerField(min_value=0, max_value=1000000,
        help_text='Entrada/salida: unidades a mover. Ajuste: saldo físico final.')
    motivo = forms.CharField(max_length=240, widget=forms.Textarea(attrs={'rows': 3}))
    destino = forms.CharField(max_length=120, required=False)
    token = forms.UUIDField(initial=uuid4, widget=forms.HiddenInput)

    def clean(self):
        values = super().clean()
        if values.get('tipo') != 'ajuste' and values.get('cantidad') == 0:
            self.add_error('cantidad', 'La cantidad debe ser mayor que cero.')
        if values.get('tipo') == 'salida' and not values.get('destino', '').strip():
            self.add_error('destino', 'Escribe el destino de la salida.')
        return values
