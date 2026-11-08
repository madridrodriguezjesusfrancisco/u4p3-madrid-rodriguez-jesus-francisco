from django.contrib import admin
from .models import Servicio, Categoria, Factura, DetalleFactura


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'precio', 'propietario']
    list_filter = ['categoria']


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion']


class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 1


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ['folio', 'cliente', 'fecha', 'usuario']
    inlines = [DetalleFacturaInline]