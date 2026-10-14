import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Comprueba las cargas de 100, 1.000, 100.000 y 1.000.000 en una SQLite temporal.'

    def add_arguments(self, parser):
        parser.add_argument('--cantidades', nargs='+', type=int, default=[100, 1000, 100000, 1000000])
        parser.add_argument('--salida', type=Path, default=settings.BASE_DIR / 'RESULTADOS_CARGAS.json')

    def handle(self, *args, **options):
        cantidades = options['cantidades']
        if cantidades != sorted(set(cantidades)) or any(n < 1 or n > 1000000 for n in cantidades):
            raise CommandError('Usa cantidades distintas, crecientes, entre 1 y 1.000.000.')
        resultados = []
        with tempfile.TemporaryDirectory(prefix='soundstock-cargas-') as carpeta:
            ambiente = {**os.environ, 'SOUNDSTOCK_DB': str(Path(carpeta) / 'cargas.sqlite3')}

            def ejecutar(*argumentos):
                proceso = subprocess.run([sys.executable, str(settings.BASE_DIR / 'manage.py'), *argumentos],
                    cwd=settings.BASE_DIR, env=ambiente, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if proceso.returncode:
                    raise CommandError(proceso.stdout + proceso.stderr)
                return proceso.stdout

            ejecutar('migrate', '--noinput')
            for cantidad in cantidades:
                self.stdout.write(f'Probando {cantidad:,} productos...', ending='\n')
                self.stdout.flush()
                inicio = perf_counter()
                salida_seeder = ejecutar('seed_productos', '--cantidad', str(cantidad), '--prefijo', 'CARGA')
                segundos = perf_counter() - inicio
                verificacion = json.loads(ejecutar('verificar_bd'))
                if verificacion['registros']['productos'] != cantidad:
                    raise CommandError(f'Conteo incorrecto en la carga {cantidad}.')
                resultado = {'cantidad': cantidad, 'segundos': round(segundos, 3),
                    'registros_guardados': verificacion['registros']['productos'],
                    'integridad': verificacion['integridad'], 'errores_claves_foraneas': verificacion['errores_claves_foraneas'],
                    'migraciones_pendientes': verificacion['migraciones_pendientes'],
                    'seeder': salida_seeder.strip()}
                if cantidad == cantidades[0]:
                    ejecutar('seed_productos', '--cantidad', str(cantidad), '--prefijo', 'CARGA')
                    resultado['repeticion_sin_duplicados'] = json.loads(ejecutar('verificar_bd'))['registros']['productos'] == cantidad
                resultados.append(resultado)
                options['salida'].parent.mkdir(parents=True, exist_ok=True)
                options['salida'].write_text(json.dumps({'motor': 'SQLite temporal independiente',
                    'python': sys.version.split()[0], 'sqlite': verificacion['version_sqlite'],
                    'cargas': resultados}, ensure_ascii=False, indent=2), encoding='utf-8')
                self.stdout.write(self.style.SUCCESS(f'{cantidad:,} almacenados y verificados en {segundos:.2f} s.'))
        self.stdout.write(self.style.SUCCESS(f'Informe: {options["salida"]}'))
