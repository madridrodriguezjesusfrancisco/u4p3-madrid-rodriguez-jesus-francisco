from django.db import migrations


def copiar_categorias(apps, schema_editor):
    # Usa los modelos históricos de esta migración.
    Servicio = apps.get_model('core', 'Servicio')
    Categoria = apps.get_model('core', 'Categoria')

    # Copia el texto de categoría de cada servicio a la tabla Categoria.
    for servicio in Servicio.objects.all():
        nombre = (servicio.categoria or '').strip() or 'Sin categoría'

        # Reutiliza la categoría si ya existe, ignorando mayúsculas.
        categoria = Categoria.objects.filter(nombre__iexact=nombre).first()

        # Si no existe, la crea.
        if categoria is None:
            categoria = Categoria.objects.create(nombre=nombre)

        # Guarda la relación temporal en el servicio.
        servicio.categoria_ref = categoria
        servicio.save(update_fields=['categoria_ref'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_categoria_servicio_categoria_ref'),
    ]

    operations = [
        migrations.RunPython(copiar_categorias, migrations.RunPython.noop),
    ]