from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from PIL import Image, ImageDraw, ImageFont


def generar_imagen(modelos, destino):
    """Dibuja las entidades de negocio desde los mismos modelos del diagrama Mermaid."""
    ancho, alto = 2000, 1510
    imagen = Image.new('RGB', (ancho, alto), '#f4f7fb')
    dibujo = ImageDraw.Draw(imagen)
    fuente = 'C:/Windows/Fonts/segoeui.ttf'
    fuente_negrita = 'C:/Windows/Fonts/segoeuib.ttf'
    try:
        titulo = ImageFont.truetype(fuente_negrita, 64)
        cabecera = ImageFont.truetype(fuente_negrita, 35)
        campo = ImageFont.truetype(fuente, 25)
        campo_negrita = ImageFont.truetype(fuente_negrita, 25)
        nota = ImageFont.truetype(fuente, 24)
    except OSError:
        titulo = cabecera = campo = campo_negrita = nota = ImageFont.load_default()

    dibujo.text((90, 55), 'Modelo de base de datos · SoundStock', fill='#14283f', font=titulo)
    dibujo.text((92, 136), 'Entidades de negocio y relaciones generadas desde Django', fill='#526578', font=nota)

    posiciones = {
        'catalogo_categoria': (90, 230),
        'catalogo_producto': (1090, 230),
        'usuarios_usuario': (90, 800),
        'inventario_movimiento': (1090, 800),
    }
    anchura = 820
    alturas = {}
    for tabla, (x, y) in posiciones.items():
        modelo = modelos[tabla]
        campos = modelo._meta.local_fields
        h = 84 + 42 * len(campos) + 26
        alturas[tabla] = h
        dibujo.rounded_rectangle((x + 8, y + 9, x + anchura + 8, y + h + 9), radius=18, fill='#dce4ed')
        dibujo.rounded_rectangle((x, y, x + anchura, y + h), radius=18, fill='white', outline='#b9c8d7', width=2)
        dibujo.rounded_rectangle((x, y, x + anchura, y + 77), radius=18, fill='#234c75')
        dibujo.rectangle((x, y + 56, x + anchura, y + 77), fill='#234c75')
        dibujo.text((x + 25, y + 18), tabla, fill='white', font=cabecera)
        for indice, field in enumerate(campos):
            cy = y + 96 + indice * 42
            if indice % 2 == 1:
                dibujo.rectangle((x + 10, cy - 7, x + anchura - 10, cy + 34), fill='#f1f5fa')
            clave = 'PK' if field.primary_key else 'FK' if field.is_relation else 'UK' if field.unique else ''
            if clave:
                dibujo.rounded_rectangle((x + 22, cy - 2, x + 78, cy + 27), radius=7, fill='#dbeafd')
                dibujo.text((x + 31, cy - 3), clave, fill='#174574', font=campo_negrita)
            dibujo.text((x + 93, cy - 3), field.column, fill='#1b344e', font=campo_negrita)
            tipo = field.get_internal_type()
            dibujo.text((x + 795, cy - 3), tipo, fill='#496178', font=campo, anchor='ra')

    azul = '#16739b'
    def flecha(puntos, etiqueta, posicion):
        dibujo.line(puntos, fill=azul, width=6, joint='curve')
        x, y = puntos[-1]
        if puntos[-2][0] < x:
            dibujo.polygon(((x, y), (x - 20, y - 11), (x - 20, y + 11)), fill=azul)
        else:
            dibujo.polygon(((x, y), (x - 11, y - 20), (x + 11, y - 20)), fill=azul)
        dibujo.text(posicion, etiqueta, fill=azul, font=nota)

    flecha([(910, 315), (1090, 315)], '1 : N', (959, 272))
    producto_abajo = 230 + alturas['catalogo_producto']
    flecha([(1500, producto_abajo), (1500, 800)], '1 : N', (1523, producto_abajo + 16))
    flecha([(910, 890), (1090, 890)], '1 : N', (959, 847))
    dibujo.text((92, alto - 88), 'PK: clave primaria   ·   FK: clave foránea   ·   UK: valor único', fill='#526578', font=nota)
    imagen.save(destino, optimize=True)


class Command(BaseCommand):
    help = 'Genera un diagrama y diccionario de datos desde los modelos implementados.'

    def handle(self, *args, **options):
        lines = ['# Diagrama de base de datos · SoundStock', '',
            'Este archivo se genera desde el código con `python manage.py diagrama_bd`.',
            'Las tablas de negocio son `usuarios_usuario`, `catalogo_categoria`, `catalogo_producto` e `inventario_movimiento`.',
            'Django también crea tablas para permisos, grupos, sesiones y auditoría del Admin.', '',
            '```mermaid', 'erDiagram']
        models = sorted(apps.get_models(include_auto_created=True), key=lambda model: model._meta.db_table)
        for model in models:
            lines.append(f'    {model._meta.db_table} {{')
            for field in model._meta.local_fields:
                key = ' PK' if field.primary_key else ' FK' if field.is_relation else ' UK' if field.unique else ''
                lines.append(f'        {field.get_internal_type()} {field.column}{key}')
            lines.append('    }')
        for model in models:
            for field in model._meta.local_fields:
                if field.many_to_one or field.one_to_one:
                    parent = field.related_model._meta.db_table
                    child = model._meta.db_table
                    side = '|o' if field.one_to_one else 'o{'
                    lines.append(f'    {parent} ||--{side} {child} : {field.column}')
        lines += ['```', '', '## Atributos y claves', '']
        for model in models:
            lines += [f'### {model._meta.db_table}', '', '| Atributo | Tipo SQL | Clave | Relación |', '|---|---|---|---|']
            for field in model._meta.local_fields:
                key = 'PK' if field.primary_key else 'FK' if field.is_relation else 'UK' if field.unique else ''
                relation = f'{field.related_model._meta.db_table}.{field.target_field.column}' if field.is_relation else ''
                lines.append(f'| {field.column} | {field.db_type(connection)} | {key} | {relation} |')
            if model._meta.constraints:
                lines += ['', 'Restricciones: ' + ', '.join(f'`{constraint.name}`' for constraint in model._meta.constraints) + '.']
            lines.append('')
        lines += ['## Correspondencia y reglas', '',
            '- `catalogo.Categoria` tiene muchos `catalogo.Producto` mediante `Producto.categoria`.',
            '- `catalogo.Producto` y `usuarios.Usuario` tienen muchos `inventario.Movimiento`.',
            '- Las claves foráneas usan `PROTECT` para conservar el historial.',
            '- El SKU, el nombre de categoría, el usuario y el token de movimiento son únicos.',
            '- La base comprueba que `posterior = anterior + variacion` y que el tipo coincida con el signo.',
            '- El servicio registra el movimiento y actualiza el stock en la misma transacción.', '']
        carpeta = settings.BASE_DIR / 'archivos_de_apoyo'
        carpeta.mkdir(parents=True, exist_ok=True)
        target = carpeta / 'DIAGRAMA_BD.md'
        target.write_text('\n'.join(lines), encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Diagrama creado: {target}'))
        tablas_negocio = ['catalogo_categoria', 'catalogo_producto', 'usuarios_usuario', 'inventario_movimiento']
        modelos_negocio = {model._meta.db_table: model for model in models if model._meta.db_table in tablas_negocio}
        imagen = carpeta / 'IMAGEN_MODELO_BD.png'
        generar_imagen(modelos_negocio, imagen)
        self.stdout.write(self.style.SUCCESS(f'Imagen para entregar: {imagen}'))
