from django.urls import path
from . import views


urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/nuevo/', views.crear_servicio, name='crear_servicio'),
    path(
        'servicios/<int:pk>/editar/',
        views.editar_servicio,
        name='editar_servicio'
    ),
    path(
        'servicios/<int:pk>/eliminar/',
        views.eliminar_servicio,
        name='eliminar_servicio'
    ),
    path('categorias/', views.categorias, name='categorias'),
    path(
        'categorias/<int:pk>/editar/',
        views.editar_categoria,
        name='editar_categoria'
    ),
    path(
        'categorias/<int:pk>/eliminar/',
        views.eliminar_categoria,
        name='eliminar_categoria'
    ),
    path('facturas/', views.facturas, name='facturas'),
    path('facturas/nueva/', views.crear_factura, name='crear_factura'),
    path('facturas/<int:pk>/', views.detalle_factura, name='detalle_factura'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/<slug:clave>/', views.reporte, name='reporte'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.iniciar_sesion, name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),
]