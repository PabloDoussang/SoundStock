from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction

from catalogo.models import Producto
from .models import Movimiento


def calcular_saldo(anterior, tipo, cantidad, destino=''):
    if tipo not in dict(Movimiento.TIPOS):
        raise ValidationError('Tipo de movimiento inválido.')
    if cantidad < 0 or (tipo != 'ajuste' and cantidad == 0):
        raise ValidationError('La cantidad debe ser mayor que cero.')
    if tipo == 'salida' and not destino.strip():
        raise ValidationError('La salida requiere un destino.')
    posterior = cantidad if tipo == 'ajuste' else anterior + (cantidad if tipo == 'entrada' else -cantidad)
    if posterior < 0:
        raise ValidationError(f'Stock insuficiente: quedan {anterior} unidades.')
    if posterior > 1000000:
        raise ValidationError('El stock supera el máximo de 1.000.000 de unidades.')
    if posterior == anterior:
        raise ValidationError('El ajuste no cambia el stock.')
    return posterior


@transaction.atomic
def registrar_movimiento(*, producto_id, usuario, tipo, cantidad, motivo, destino='', token=None, instancia=None):
    producto = Producto.objects.select_for_update().get(pk=producto_id)
    if not producto.activo:
        raise ValidationError('El producto está archivado.')
    token = token or uuid4()
    if instancia is None:
        existente = Movimiento.objects.filter(token=token).first()
        if existente:
            if existente.usuario_id != usuario.pk:
                raise ValidationError('Identificador de operación inválido.')
            return existente, False
        anterior = producto.stock
        saldo_guardado = producto.stock
    else:
        guardado = Movimiento.objects.get(pk=instancia.pk)
        ultimo = producto.movimientos.order_by('-pk').first()
        if guardado.producto_id != producto.pk or not ultimo or ultimo.pk != guardado.pk:
            raise ValidationError('Solo se puede editar el último movimiento sin cambiar de producto.')
        anterior = guardado.anterior
        saldo_guardado = guardado.posterior
    if not motivo.strip():
        raise ValidationError('El motivo es obligatorio.')
    posterior = calcular_saldo(anterior, tipo, cantidad, destino)
    movimiento = instancia or Movimiento(token=token)
    movimiento.producto = producto
    movimiento.usuario = usuario
    movimiento.tipo = tipo
    movimiento.anterior = anterior
    movimiento.posterior = posterior
    movimiento.variacion = posterior - anterior
    movimiento.motivo = motivo
    movimiento.destino = destino if tipo == 'salida' else ''
    movimiento.full_clean()
    # El filtro por saldo evita perder cambios también con SQLite, donde SELECT FOR UPDATE no bloquea filas.
    if Producto.objects.filter(pk=producto.pk, stock=saldo_guardado).update(stock=posterior) != 1:
        raise ValidationError('El stock cambió. Recarga el formulario.')
    movimiento.save()
    return movimiento, True


@transaction.atomic
def eliminar_ultimo(movimiento):
    guardado = Movimiento.objects.get(pk=movimiento.pk)
    producto = Producto.objects.select_for_update().get(pk=guardado.producto_id)
    ultimo = producto.movimientos.order_by('-pk').first()
    if not ultimo or ultimo.pk != guardado.pk:
        raise ValidationError('Solo se puede eliminar el último movimiento.')
    if Producto.objects.filter(pk=producto.pk, stock=guardado.posterior).update(stock=guardado.anterior) != 1:
        raise ValidationError('El stock no coincide con el historial.')
    guardado.delete()
