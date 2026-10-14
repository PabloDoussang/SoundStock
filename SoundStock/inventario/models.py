import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from catalogo.models import Producto


class Movimiento(models.Model):
    TIPOS = [('entrada', 'Entrada'), ('salida', 'Salida'), ('ajuste', 'Ajuste')]
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='movimientos')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    anterior = models.PositiveIntegerField()
    posterior = models.PositiveIntegerField()
    variacion = models.IntegerField()
    motivo = models.CharField(max_length=240)
    destino = models.CharField(max_length=120, blank=True)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['-fecha', '-pk']
        verbose_name = 'movimiento'
        verbose_name_plural = 'movimientos'
        constraints = [
            models.CheckConstraint(condition=Q(posterior=F('anterior') + F('variacion')), name='movimiento_saldo_cuadra'),
            models.CheckConstraint(condition=Q(posterior__lte=1000000) & Q(anterior__lte=1000000), name='movimiento_saldo_maximo'),
            models.CheckConstraint(condition=Q(tipo__in=['entrada', 'salida', 'ajuste']), name='movimiento_tipo_valido'),
            models.CheckConstraint(condition=(Q(tipo='entrada', variacion__gt=0) | Q(tipo='salida', variacion__lt=0) |
                (Q(tipo='ajuste') & ~Q(variacion=0))), name='movimiento_signo_valido'),
            models.CheckConstraint(condition=~Q(tipo='salida') | ~Q(destino=''), name='movimiento_destino_salida'),
        ]

    def __str__(self):
        return f'MOV-{self.pk:05d} · {self.get_tipo_display()}' if self.pk else 'Nuevo movimiento'
