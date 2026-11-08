from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    propietario = models.ForeignKey(User, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=120)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        null=True,
        related_name='servicios'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['propietario', 'precio'],
                name='servicio_prop_precio_idx'
            ),
        ]

    def __str__(self):
        return self.titulo


class Factura(models.Model):
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='facturas'
    )
    cliente = models.CharField(max_length=120)
    fecha = models.DateField(default=timezone.localdate)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha', '-id']
        indexes = [
            models.Index(
                fields=['usuario', 'fecha'],
                name='factura_usuario_fecha_idx'
            ),
        ]

    @property
    def folio(self):
        if self.pk is None:
            return 'F-nueva'
        return f'F-{self.pk:05d}'

    def __str__(self):
        return f'{self.folio} · {self.cliente}'


class DetalleFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='detalles'
    )
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f'{self.cantidad} × {self.servicio}'