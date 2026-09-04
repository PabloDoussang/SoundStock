from django.conf import settings
from django.db import models
from django.db.models import Q
class Product(models.Model):
    CATEGORY = [('Cuerdas','Cuerdas'),('Percusión','Percusión'),('Teclados','Teclados'),('Audio','Audio'),('DJ','DJ'),('Accesorios','Accesorios')]
    code = models.CharField('Código SKU', max_length=30, unique=True)
    name = models.CharField('Nombre', max_length=120)
    category = models.CharField('Categoría', max_length=30, choices=CATEGORY)
    location = models.CharField('Ubicación', max_length=60)
    stock = models.PositiveIntegerField('Stock', default=0, editable=False)
    minimum = models.PositiveIntegerField('Stock mínimo', default=5)
    active = models.BooleanField('Activo', default=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['name']
        constraints = [models.CheckConstraint(condition=Q(stock__gte=0), name='stock_nonnegative')]
    def __str__(self): return f'{self.code} · {self.name}'
    @property
    def status(self):
        if not self.stock: return 'Agotado'
        return 'Stock bajo' if self.stock <= self.minimum else 'Disponible'
class Movement(models.Model):
    TYPES = [('entrada','Entrada'),('salida','Salida'),('ajuste','Ajuste')]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    kind = models.CharField('Operación', max_length=10, choices=TYPES)
    delta = models.IntegerField('Variación')
    before = models.PositiveIntegerField('Stock anterior')
    after = models.PositiveIntegerField('Stock resultante')
    reason = models.CharField('Motivo / referencia', max_length=240)
    destination = models.CharField('Destino', max_length=120, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(unique=True, editable=False)
    class Meta: ordering = ['-created_at','-id']
    def __str__(self): return f'MOV-{self.pk:05d} · {self.product.code}'
