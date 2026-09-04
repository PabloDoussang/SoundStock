"""Stock e historial se escriben juntos. SQLite IMMEDIATE serializa escrituras."""
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Product, Movement
@transaction.atomic
def record_movement(*, product_id, kind, quantity, reason, destination, user, token):
    previous = Movement.objects.filter(token=token).first()
    if previous:
        if previous.user_id != user.pk: raise ValidationError('Identificador de operación inválido.')
        return previous, False
    p = Product.objects.select_for_update().get(pk=product_id, active=True)
    if kind not in dict(Movement.TYPES): raise ValidationError('Operación desconocida.')
    if not isinstance(quantity, int) or quantity < 0 or quantity > 1000000:
        raise ValidationError('La cantidad debe ser un entero entre 0 y 1.000.000.')
    if kind != 'ajuste' and quantity == 0: raise ValidationError('La cantidad debe ser mayor que cero.')
    if not reason.strip(): raise ValidationError('Indica el motivo del movimiento.')
    if kind == 'salida' and not destination.strip(): raise ValidationError('Selecciona el destino de la salida.')
    after = quantity if kind == 'ajuste' else p.stock + (quantity if kind == 'entrada' else -quantity)
    if after < 0: raise ValidationError(f'Stock insuficiente: hay {p.stock} unidades disponibles.')
    if after > 1000000: raise ValidationError('El stock supera el máximo permitido de 1.000.000.')
    if after == p.stock: raise ValidationError('El ajuste no modifica las existencias.')
    movement = Movement.objects.create(product=p,kind=kind,delta=after-p.stock,before=p.stock,after=after,reason=reason.strip(),destination=destination.strip(),user=user,token=token)
    p.stock = after
    p.save(update_fields=['stock','updated_at'])
    return movement, True
