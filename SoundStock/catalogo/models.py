from django.core.validators import MaxValueValidator, RegexValidator
from django.db import models
from django.db.models import Q


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    codigo = models.CharField('SKU', max_length=30, unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]{3,30}$', 'Usa de 3 a 30 letras mayúsculas, números o guiones.')])
    nombre = models.CharField(max_length=120, db_index=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    ubicacion = models.CharField(max_length=60, db_index=True)
    stock = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1000000)])
    stock_minimo = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(1000000)])
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['nombre', 'pk']
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        constraints = [
            models.CheckConstraint(condition=Q(stock__lte=1000000), name='producto_stock_hasta_millon'),
            models.CheckConstraint(condition=Q(stock_minimo__lte=1000000), name='producto_minimo_hasta_millon'),
        ]
        indexes = [models.Index(fields=['activo', 'categoria'], name='producto_activo_categoria')]

    @property
    def estado_stock(self):
        if self.stock == 0:
            return 'Agotado'
        return 'Bajo' if self.stock <= self.stock_minimo else 'Disponible'

    def __str__(self):
        return f'{self.codigo} · {self.nombre}'
