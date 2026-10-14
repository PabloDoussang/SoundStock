# SoundStock desde cero · guía para la terminal de VS Code

Este proyecto toma el caso de bodega del primer ZIP (`SoundStock-main.zip`) y sigue la secuencia de aprendizaje del segundo (`django-examples-main.zip`): crear proyecto y apps, configurar SQLite, definir modelos, generar y aplicar migraciones, crear un diagrama, cargar datos con Faker y usar Django Admin. El código y las migraciones ya están incluidos en `SoundStock/`.

**Abre esta carpeta (`SoundStock_desde_cero`) en Visual Studio Code.** En la terminal, usa el perfil **Símbolo del sistema / Command Prompt**. Los pasos 1–7 documentan cómo se creó la estructura en una carpeta vacía. Si trabajas con esta entrega ya creada, ve directamente a [Abrir la entrega existente](#abrir-la-entrega-existente): volver a ejecutar `startproject` o `startapp` sobre las carpetas existentes dará un error de nombre duplicado.

Para consultar rápidamente los comandos de Faker y la ubicación de cada archivo, abre [GUIA_FAKER_Y_ARCHIVOS.txt](GUIA_FAKER_Y_ARCHIVOS.txt).

## Construcción desde cero: comandos en el orden solicitado

### 1. Cambiar la terminal a CMD

```cmd
cmd
```

### 2. Crear el entorno virtual

Desde una carpeta nueva y vacía:

```cmd
python -m venv venv
```

### 3. Activar el entorno

Puedes arrastrar `venv\Scripts\activate.bat` a la terminal CMD y presionar **Enter**. Equivale a:

```cmd
venv\Scripts\activate.bat
```

El indicador de la terminal debe comenzar con `(venv)`.

### 4. Instalar Django

```cmd
pip install django
```

La entrega se creó con Django 6.1.2. `SoundStock/requirements.txt` fija esa versión y la de Faker para repetir el entorno.

### 5. Crear el proyecto Django

```cmd
django-admin startproject SoundStock
```

Esto crea la carpeta `SoundStock`, su archivo `manage.py` y la configuración `SoundStock/settings.py`.

### 6. Entrar en el proyecto

```cmd
cd SoundStock
```

Todos los comandos `python manage.py ...` se ejecutan **desde esta carpeta**, donde está `manage.py`.

### 7. Crear las aplicaciones con el comando de clase

```cmd
django-admin startapp usuarios
django-admin startapp catalogo
django-admin startapp inventario
```

| App | Responsabilidad | Modelos |
|---|---|---|
| `usuarios` | Cuentas y roles | `Usuario` |
| `catalogo` | Productos y categorías | `Categoria`, `Producto` |
| `inventario` | Entradas, salidas y ajustes de stock | `Movimiento` |

Esta división sigue la idea de las apps separadas en `django-examples-main.zip`. Los archivos de cada app (`models.py`, `admin.py`, `views.py`, `urls.py` y comandos) ya están desarrollados en esta entrega; `startapp` solo crea el esqueleto.

## Continuación: requisito por requisito

### 8. Configuración y conexión de la base de datos

En [SoundStock/settings.py](SoundStock/SoundStock/settings.py) están activadas las tres apps y `AUTH_USER_MODEL = 'usuarios.Usuario'`. `DATABASES['default']` usa **SQLite**, guardada en `SoundStock/db.sqlite3`. Antes de crear la primera migración se configura el usuario personalizado. La conexión se comprueba con:

```cmd
python manage.py check
python manage.py verificar_bd
```

`verificar_bd` informa motor, versión, archivo, migraciones pendientes, conteos, integridad de SQLite y claves foráneas.

### 9. Modelos, campos y relaciones

Lee [usuarios/models.py](SoundStock/usuarios/models.py), [catalogo/models.py](SoundStock/catalogo/models.py) e [inventario/models.py](SoundStock/inventario/models.py). `Producto.categoria` relaciona muchos productos con una categoría, como `Empleado.cargo` en el ejemplo. `Movimiento.producto` y `Movimiento.usuario` relacionan cada operación con su producto y responsable. Se declararon claves primarias, SKU único, tipos de campo, límites y restricciones para el saldo. `on_delete=PROTECT` conserva la integridad del historial.

### 10. Crear la primera migración

Después de escribir los modelos:

```cmd
python manage.py makemigrations usuarios catalogo inventario
```

Los archivos `0001_initial.py` están guardados en `migrations/` de cada app. Django dividió la migración inicial de `inventario` en `0001_initial.py` y `0002_initial.py` para resolver la relación con el usuario personalizado.

### 11. Aplicar migraciones y mostrar su historial

```cmd
python manage.py migrate
python manage.py showmigrations usuarios catalogo inventario
```

Las marcas `[X]` indican migraciones aplicadas. Para demostrar una **modificación posterior del modelo**, se añadió `Producto.descripcion` y se ejecutó:

```cmd
python manage.py makemigrations catalogo --name descripcion_producto
python manage.py migrate
python manage.py showmigrations catalogo
```

El historial incluye `catalogo/migrations/0002_descripcion_producto.py`. En la entrega actual esos archivos ya existen: `makemigrations` mostrará *No changes detected* hasta que cambies un modelo. Conservar `migrations/` permite reproducir el esquema en otra computadora.

### 12. Generar el diagrama de base de datos

Instala la biblioteca que crea la imagen para subir a la plataforma:

```cmd
pip install Pillow
```

```cmd
python manage.py diagrama_bd
```

Abre [DIAGRAMA_BD.md](SoundStock/DIAGRAMA_BD.md) con la vista previa de Markdown de VS Code. El diagrama Mermaid y su diccionario de datos se generan desde los modelos reales; muestran entidades, atributos, claves primarias, claves foráneas, valores únicos y relaciones. El mismo comando crea [IMAGEN_MODELO_BD.png](SoundStock/IMAGEN_MODELO_BD.png) con las cuatro tablas de negocio para subir como imagen a la plataforma. Vuelve a ejecutar el comando después de cambiar modelos.

### 13. Django Admin y sus CRUD

Los registros y la personalización están en los archivos `admin.py` de cada app. Contienen columnas (`list_display`), filtros (`list_filter`), búsquedas (`search_fields`), orden, paginación y campos de solo lectura, como en `README_ADMIN.md` del ZIP de ejemplos.

Para crear otra cuenta administradora desde la terminal:

```cmd
python manage.py createsuperuser
```

Después de iniciar el servidor, entra en `http://127.0.0.1:8000/admin/`. Puedes crear, consultar, modificar y eliminar usuarios, categorías, productos y movimientos. Para conservar la consistencia, un producto con stock o historial no se elimina; un movimiento solo se corrige o elimina si es el último de ese producto. El Admin recalcula el stock en la misma transacción.

### 14. Instalar Faker y cargar los 12 productos originales

```cmd
pip install Faker
python manage.py cargar_catalogo
```

`cargar_catalogo` lee `catalogo/data/productos_iniciales.json`, copiado del primer ZIP. Crea los 12 productos y las entradas iniciales de stock; repetirlo conserva los registros existentes. Necesita una cuenta administradora creada en el paso anterior.

### 15. Cargar datos ficticios como `seed_empleado`

Los comandos están en `management/commands/` de cada app. Usan `Faker('es_CL')`, una semilla reproducible y claves estables; buscan o crean las categorías compartidas. La carga de productos usa lotes, por lo que escala a un millón de filas. Si se repite, actualiza descripciones y otros datos de prueba sin duplicar SKU ni borrar stock o movimientos existentes.

```cmd
python manage.py seed_productos --cantidad 100
python manage.py seed_usuarios --cantidad 20
python manage.py seed_movimientos --cantidad 100
```

`seed_usuarios` crea cuentas ficticias desactivadas y sin contraseña utilizable. `seed_movimientos` crea una entrada por producto de prueba, vinculada a un responsable ficticio, y mantiene sincronizado el stock. Vuelve a ejecutar los tres comandos para mostrar que no generan duplicados:

```cmd
python manage.py seed_productos --cantidad 100
python manage.py seed_usuarios --cantidad 20
python manage.py seed_movimientos --cantidad 100
python manage.py verificar_bd
```

Puedes cambiar `--cantidad`, `--lote`, `--semilla` o `--prefijo` en `seed_productos`. Por ejemplo:

```cmd
python manage.py seed_productos --cantidad 1000 --lote 2000
```

### 16. Demostrar las cuatro cargas solicitadas

```cmd
python manage.py evaluar_cargas
```

Este comando aplica las migraciones en una **base SQLite temporal independiente**, ejecuta secuencialmente cargas de **100, 1.000, 100.000 y 1.000.000 productos**, verifica el número realmente almacenado, la integridad, las relaciones y las migraciones. También repite la primera carga para comprobar que no duplica registros. Guarda tiempos y resultados en [RESULTADOS_CARGAS.json](SoundStock/RESULTADOS_CARGAS.json). Puede tardar varios minutos; no llena la base de la aplicación que usas a diario.

Para hacer solo las primeras dos cargas en una demostración corta:

```cmd
python manage.py evaluar_cargas --cantidades 100 1000
```

### 17. Probar el proyecto y comprobar la base

```cmd
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py verificar_bd
```

Las pruebas incluyen conexión SQLite, historial de migraciones, permisos, CRUD, búsquedas, stock, restricciones, Admin, catálogo original y repetición de seeders. `VERIFICACION_BD.json` contiene el resultado de la base local preparada.

### 18. Ejecutar la aplicación

```cmd
python manage.py runserver 127.0.0.1:8000
```

Abre `http://127.0.0.1:8000/` para el resumen, productos, movimientos, reportes y ubicaciones. Abre `http://127.0.0.1:8000/admin/` para Django Admin. En un proyecto local de práctica, deja abierta la terminal mientras usas el servidor y deténlo con `Ctrl+C`.

### 19. Preparar la entrega de la Evaluación 2

La pauta pide subir a la plataforma [IMAGEN_MODELO_BD.png](SoundStock/IMAGEN_MODELO_BD.png) y el enlace de un repositorio **público** de GitHub con el último commit. La imagen se regenera con el comando del paso 12. Esta versión del proyecto está en la rama independiente `evaluacion-2-desde-cero` del repositorio público:

https://github.com/PabloDoussang/SoundStock/tree/evaluacion-2-desde-cero

Envía ese enlace, no solo la página principal del repositorio: `main` conserva la versión anterior. En GitHub, abre la rama y usa la sección **Commits** para mostrar el último cambio. El archivo `.gitignore` excluye el entorno virtual, la base local y los secretos.

## Abrir la entrega existente

La carpeta local preparada **ya trae** las apps, el código, las migraciones y una base local con datos de muestra. El ZIP de entrega omite la base local y los secretos; si partes del ZIP, crea tu administrador y carga los datos con los pasos 14–16. En una terminal nueva de VS Code, desde esta carpeta exterior ya preparada, ejecuta:

```cmd
cmd
venv\Scripts\activate.bat
cd SoundStock
pip install -r requirements.txt
python manage.py migrate
python manage.py verificar_bd
python manage.py test
python manage.py runserver 127.0.0.1:8000
```

La cuenta local inicial está en `ACCESO_LOCAL.txt`, fuera del proyecto. Si el servidor ya está abierto en el puerto 8000, entra directamente por el navegador; no abras una segunda instancia en el mismo puerto. Si copias el código sin `db.sqlite3`, ejecuta `python manage.py migrate` y `python manage.py createsuperuser` antes de cargar datos.

Para detener el servidor que dejé abierto en segundo plano y luego iniciarlo desde tu propia terminal de VS Code, ejecuta esto desde la carpeta exterior:

```cmd
powershell -ExecutionPolicy Bypass -File detener_servidor.ps1
```

## Archivos que conviene mostrar al docente

- `SoundStock/SoundStock/settings.py`: apps, conexión SQLite y usuario personalizado.
- `SoundStock/usuarios/models.py`, `SoundStock/catalogo/models.py`, `SoundStock/inventario/models.py`: modelos y relaciones.
- Las carpetas `migrations/`: historial generado y aplicado por Django.
- `SoundStock/DIAGRAMA_BD.md`: diagrama generado desde los modelos.
- `SoundStock/IMAGEN_MODELO_BD.png`: imagen del modelo solicitada por la pauta.
- Los tres `admin.py`: CRUD, filtros, búsquedas y personalización.
- `catalogo/management/commands/seed_productos.py`: patrón de `seed_empleado` con Faker, categorías compartidas, SKU estable y lotes.
- `SoundStock/RESULTADOS_CARGAS.json`: evidencia de las cuatro pruebas de volumen.

La documentación de los ZIP adjuntos se usó como referencia técnica. Esta guía describe el proyecto nuevo y los criterios enviados para esta evaluación.
