# SoundStock · Bodega Music Pro

Prototipo funcional de bodega para **Unidad 1: Tecnologías del lado del servidor**. Usa Django, HTML dinámico, Bootstrap local y datos JSON, **sin conexión a base de datos**. Incluye inventario, ubicaciones, entradas, salidas, ajustes, historial, gráficas, CSV y roles.

Hay una única versión y un único iniciador: **`iniciar.bat`**, puerto **8000**. La plantilla principal **`index.html` está en la carpeta raíz**.

## Cómo abrir la página

1. Instala Python 3.12 con el lanzador `py` y extrae el ZIP completo.
2. Abre la carpeta **SoundStock**, donde están `index.html`, `manage.py` e `iniciar.bat`.
3. Ejecuta **iniciar.bat**. La primera ejecución instala las dependencias y solicita crear una cuenta administradora. La contraseña no se muestra al escribir.
4. Elige si deseas cargar los productos ficticios para probar el inventario.
5. Abre [http://127.0.0.1:8000/ingresar/](http://127.0.0.1:8000/ingresar/) e ingresa con la cuenta creada.
6. Cambia de sección mediante el menú: la navegación permanece en la misma pestaña.
7. Mantén abierta la consola mientras usas la página. Para detenerla, presiona **Ctrl+C**; para volver, ejecuta nuevamente `iniciar.bat`.

En el equipo original se conservó la cuenta **Pablo Doussang** con su contraseña configurada, así como los productos y movimientos existentes. Esos datos privados no se distribuyen en el ZIP ni en GitHub. Una instalación nueva solicita crear su propia cuenta. Se permiten espacios en los nombres de usuario.

No abras `index.html` directamente: Django debe procesar esa plantilla. Accede por la dirección anterior.

## Los datos sí se conservan

Usuarios, hashes de contraseñas, permisos, productos y movimientos se guardan en **`runtime/bodega.json`**. Este archivo permite conservar cambios sin conectar a una base de datos, como exige U1.

| Acción | Qué ocurre |
|---|---|
| Guardar un formulario válido | El servidor escribe los cambios en el JSON |
| Refrescar o cambiar de sección | La página vuelve a consultar los datos guardados |
| Cerrar sesión o cerrar el navegador | La cuenta y el inventario permanecen |
| Detener el servidor o reiniciar el equipo | Los datos permanecen; ejecuta otra vez `iniciar.bat` |
| Volver a iniciar el proyecto | Se reutiliza el JSON existente, sin reinicializarlo |
| Abandonar un formulario sin guardar | El borrador no se conserva |

Cerrar sesión invalida todas las sesiones abiertas de esa misma cuenta; conserva la cuenta y el inventario. Las sesiones firmadas vencen a las 8 horas. Las contraseñas se almacenan mediante hash; se cambian desde **Usuarios y roles**.

El servidor guarda las operaciones con un archivo temporal y reemplazo atómico: historial y stock se guardan juntos. Un error de validación no escribe cambios. El proyecto está diseñado para **una instancia local del servidor**; no ejecutes varios servidores simultáneamente sobre el mismo JSON.

El JSON de `warehouse/data/productos_demo.json` es solo un catálogo ficticio para la carga inicial opcional. Los cambios posteriores se guardan en `runtime/bodega.json`.

## Actualizar sin perder datos

1. Detén el servidor con Ctrl+C.
2. Respalda la carpeta `runtime` y el archivo `.local-secret` en una carpeta privada.
3. Actualiza el código conservando ambos elementos.
4. Ejecuta nuevamente `iniciar.bat`.

Una carpeta nueva del proyecto es una instalación independiente. Para trasladar tus datos a otro equipo, copia también `runtime` y `.local-secret` de forma privada. El ZIP y GitHub contienen código y documentación, no cuentas ni datos operativos.

La antigua base SQLite se conservó como respaldo privado en el equipo original; esta versión no la abre ni la modifica. Los cambios se realizan desde los formularios del sistema.

## Si no abre o no puedes ingresar

- **No se puede conectar:** inicia `iniciar.bat`, espera el mensaje del servidor y mantén la consola abierta.
- **Usuario o contraseña incorrectos:** revisa espacios, mayúsculas y símbolos.
- **Acceso restringido:** Consulta permite lectura; Operador administra productos y stock; Administrador gestiona además usuarios y archivo de productos.
- **Puerto ocupado:** usa la instancia ya abierta o ciérrala antes de iniciar otra.
- **Falta Python:** instala Python 3.12 y vuelve a ejecutar el iniciador.

## Ejecución manual

Desde la carpeta del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py preparar
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

No se ejecuta `migrate`: `DATABASES = {}` y los datos se gestionan como listas y diccionarios JSON.

## Secciones

| Sección | Funciones |
|---|---|
| Resumen | Referencias activas, unidades, alertas y actividad de 14 días |
| Inventario | Alta, edición, búsqueda, filtros, archivo, reactivación y CSV |
| Operaciones de stock | Entrada, salida con destino y ajuste por conteo físico |
| Movimientos | Fecha, usuario, motivo, destino, variación y saldos |
| Reportes | Períodos, gráficas, categorías y exportaciones |
| Ubicaciones | Agrupación física y búsqueda de productos |
| Usuarios y roles | Cuentas, permisos, estado y contraseñas |

Los productos comienzan con stock cero. Entrada y salida requieren un entero positivo; el ajuste indica la cantidad final contada. El motivo es obligatorio y las salidas requieren destino. Se impiden saldos negativos y envíos duplicados. Archivar requiere stock cero y conserva el historial. Los movimientos se corrigen con una nueva operación justificada.

## Estructura

```text
index.html                    Plantilla principal, en la raíz
iniciar.bat                   Único iniciador, puerto 8000
config/settings.py            Configuración sin base de datos
warehouse/views.py            Peticiones, listas, diccionarios y contextos
warehouse/forms.py            Formularios y validaciones
warehouse/store.py            Lectura y escritura persistente de JSON
warehouse/middleware.py       Sesión y usuario sin consultas SQL
warehouse/tests.py            Pruebas funcionales sin BD
warehouse/test_persistence.py Prueba entre procesos independientes
templates/                    Interfaces de todas las secciones
static/                       CSS, Bootstrap y JavaScript locales
docs/                         Diagramas, esquema y rúbrica
runtime/bodega.json           Datos privados locales; no se distribuye
```

## Verificar

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test warehouse
```

**31 pruebas aprobadas.** Las pruebas usan archivos temporales, prohíben el acceso a base de datos y comprueban permisos, operaciones, validaciones, renderizado y persistencia entre procesos. No modifican tus datos locales. Consulta [la revisión](docs/REVISION_RUBRICA.md) para los resultados.

## Documentación

- [Matriz de los diez indicadores](docs/RUBRICA.md)
- [Auditoría final para nivel Excelente](docs/AUDITORIA_FINAL.md)
- [Revisión y evidencias](docs/REVISION_RUBRICA.md)
- [Diagramas de flujo](docs/DIAGRAMAS.md)
- [Esquema de datos](docs/MODELO_DATOS.md)
- [Instrucciones de GitHub](docs/GITHUB.md)
- [Fuentes, decisiones y apoyo de IA](docs/FUENTES_Y_DECISIONES.md)

![Flujo general](docs/flujo-general.png)

Repositorio: [PabloDoussang/SoundStock](https://github.com/PabloDoussang/SoundStock). Código publicado y verificado en la rama main, con index.html en la raíz. GitHub almacena código; para abrir esta aplicación ejecuta el servidor Django. No se incluyen tienda, pagos, GPS ni API REST/JWT.
