from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_copiar_categorias'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='servicio',
            name='categoria',
        ),
        migrations.RenameField(
            model_name='servicio',
            old_name='categoria_ref',
            new_name='categoria',
        ),
    ]