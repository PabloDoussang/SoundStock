import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from catalogo.models import Categoria, Producto
from inventario.models import Movimiento
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Comprueba conexión SQLite, migraciones, integridad, relaciones y registros almacenados.'

    def add_arguments(self, parser):
        parser.add_argument('--salida', type=Path)

    def handle(self, *args, **options):
        connection.ensure_connection()
        executor = MigrationExecutor(connection)
        pendientes = executor.migration_plan(executor.loader.graph.leaf_nodes())
        with connection.cursor() as cursor:
            cursor.execute('SELECT sqlite_version()')
            version = cursor.fetchone()[0]
            cursor.execute('PRAGMA integrity_check')
            integridad = [row[0] for row in cursor.fetchall()]
            cursor.execute('PRAGMA foreign_key_check')
            errores_fk = cursor.fetchall()
        datos = {
            'motor': connection.vendor, 'version_sqlite': version,
            'archivo': str(connection.settings_dict['NAME']),
            'migraciones_pendientes': len(pendientes), 'integridad': integridad,
            'errores_claves_foraneas': errores_fk,
            'registros': {'usuarios': Usuario.objects.count(), 'categorias': Categoria.objects.count(),
                          'productos': Producto.objects.count(), 'movimientos': Movimiento.objects.count()},
        }
        resultado = json.dumps(datos, indent=2, ensure_ascii=False)
        if options['salida']:
            options['salida'].parent.mkdir(parents=True, exist_ok=True)
            options['salida'].write_text(resultado, encoding='utf-8')
        self.stdout.write(resultado)
        if pendientes or errores_fk or integridad != ['ok']:
            raise CommandError('La base requiere revisión.')
