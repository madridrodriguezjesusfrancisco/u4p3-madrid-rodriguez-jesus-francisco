from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.db import transaction

from core.models import Categoria, Servicio, Factura, DetalleFactura


CATEGORIAS = [
    ('Diseño', 'Logos, tarjetas e identidad visual'),
    ('Tutorías', 'Clases y asesorías académicas'),
    ('Desarrollo web', 'Sitios y aplicaciones'),
    ('Marketing', 'Campañas en redes sociales'),
]


SERVICIOS = [
    ('Clase de álgebra', '150.00', 'Tutorías'),
    ('Clase de física', '150.00', 'Tutorías'),
    ('Tarjetas de presentación', '300.00', 'Diseño'),
    ('Logo profesional', '800.00', 'Diseño'),
    ('Landing page', '1200.00', 'Desarrollo web'),
    ('Asesoría de tesis', '2500.00', 'Tutorías'),
    ('Sitio web completo', '2500.00', 'Desarrollo web'),
]


FACTURAS = [
    (
        'Papelería Luna',
        20,
        [('Logo profesional', 1), ('Tarjetas de presentación', 2)]
    ),
    (
        'Colegio Ámbar',
        15,
        [('Clase de álgebra', 4), ('Clase de física', 4)]
    ),
    (
        'Papelería Luna',
        10,
        [('Tarjetas de presentación', 3)]
    ),
    (
        'Taller Ruiz',
        7,
        [('Sitio web completo', 1)]
    ),
    (
        'Colegio Ámbar',
        3,
        [('Asesoría de tesis', 1), ('Clase de álgebra', 2)]
    ),
    (
        'Ana Torres',
        1,
        [('Clase de física', 2)]
    ),
]


class Command(BaseCommand):
    help = 'Carga categorías, servicios y facturas de prueba para un usuario'

    def add_arguments(self, parser):
        parser.add_argument('usuario')

    def handle(self, *args, **opciones):
        try:
            usuario = User.objects.get(username=opciones['usuario'])
        except User.DoesNotExist:
            raise CommandError(
                'Ese usuario no existe. Escribe uno que ya tenga cuenta.'
            )

        with transaction.atomic():
            for nombre, descripcion in CATEGORIAS:
                Categoria.objects.get_or_create(
                    nombre=nombre,
                    defaults={'descripcion': descripcion}
                )

            servicios = {}

            for titulo, precio, categoria in SERVICIOS:
                servicio, creado = Servicio.objects.get_or_create(
                    propietario=usuario,
                    titulo=titulo,
                    defaults={
                        'descripcion': 'Servicio de prueba',
                        'precio': precio,
                        'categoria': Categoria.objects.get(nombre=categoria),
                    },
                )
                servicios[titulo] = servicio

            if Factura.objects.filter(
                usuario=usuario,
                cliente='Papelería Luna'
            ).exists():
                self.stdout.write(
                    self.style.WARNING(
                        'Las facturas de prueba ya existían; no se duplicaron.'
                    )
                )
                return

            for cliente, dias, renglones in FACTURAS:
                factura = Factura.objects.create(
                    usuario=usuario,
                    cliente=cliente,
                    fecha=date.today() - timedelta(days=dias)
                )

                for titulo, cantidad in renglones:
                    servicio = servicios[titulo]
                    DetalleFactura.objects.create(
                        factura=factura,
                        servicio=servicio,
                        cantidad=cantidad,
                        precio_unitario=servicio.precio
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'Datos de prueba cargados para {usuario.username}.'
            )
        )