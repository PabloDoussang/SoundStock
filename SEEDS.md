# Dónde están los seed de SoundStock

Abre estos enlaces en la vista previa de Markdown de VS Code:

- [Productos: seed_productos.py](SoundStock/catalogo/management/commands/seed_productos.py)
- [Usuarios: seed_usuarios.py](SoundStock/usuarios/management/commands/seed_usuarios.py)
- [Movimientos: seed_movimientos.py](SoundStock/inventario/management/commands/seed_movimientos.py)

Los archivos deben permanecer en `management/commands/` de cada app para que Django reconozca los comandos. Desde la carpeta exterior `SoundStock-main`, con el entorno virtual activado, ejecuta:

```cmd
cd SoundStock
python manage.py seed_productos --cantidad 100
python manage.py seed_usuarios --cantidad 20
python manage.py seed_movimientos --cantidad 100
python manage.py verificar_bd
```

El nombre correcto es `seed_productos`, en plural, y la opción es `--cantidad`, en minúsculas. Carga primero los productos y después los movimientos. Los datos quedan en `SoundStock/db.sqlite3`; repetir los comandos reconoce los registros existentes y no los duplica.
