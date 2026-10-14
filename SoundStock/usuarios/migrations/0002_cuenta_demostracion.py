from django.db import migrations


USUARIO_DEMO = 'Pablo Doussang'
CLAVE_DEMO_HASH = 'pbkdf2_sha256$1500000$YcJrLJg8DszzqxmCnmJEzG$TMZMub5rjfzdtgfVyPnIj2BRmGpSNZGNrbAFLfZyuUQ='


def crear_cuenta_demostracion(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.using(schema_editor.connection.alias).get_or_create(
        username=USUARIO_DEMO,
        defaults={
            'password': CLAVE_DEMO_HASH,
            'rol': 'Administrador',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0001_initial')]
    operations = [migrations.RunPython(crear_cuenta_demostracion, migrations.RunPython.noop)]
