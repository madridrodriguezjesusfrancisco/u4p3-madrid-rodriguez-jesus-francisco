from django.db import models
from django.contrib.auth.models import User


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

    # En este paso conservamos la categoría de texto y añadimos una FK temporal.
    categoria = models.CharField(max_length=60)
    categoria_ref = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        null=True,
        related_name='servicios'
    )

    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo