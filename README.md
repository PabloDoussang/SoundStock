# SoundStock · Bodega Music Pro

Sistema de bodega en Django con plantillas HTML, Bootstrap local, inventario, ubicaciones, entradas, salidas, ajustes, historial, gráficas, CSV y roles.

**Para la evaluación U1, ejecuta `iniciar_u1.bat`: utiliza JSON y no conecta a una base de datos.** La opción `iniciar.bat` mantiene la versión SQLite solicitada originalmente.

| Modo | Iniciar | Dirección | Datos |
|---|---|---|---|
| U1 · evaluación | `iniciar_u1.bat` | http://127.0.0.1:8001/ | JSON de demostración, sin SQL |
| SQLite · ampliación | `iniciar.bat` | http://127.0.0.1:8000/ | Base SQLite real |

Los modos comparten las plantillas y el diseño, pero tienen datos y sesiones separados. Un cambio en U1 no modifica SQLite ni viceversa.

## Cómo acceder

1. Instala Python 3.12 con el lanzador `py` y extrae el ZIP completo.
2. Abre la carpeta **SoundStock**, donde se encuentra `manage.py`.
3. Ejecuta **iniciar_u1.bat** para la entrega U1. En la primera ejecución instalará dependencias y solicitará un usuario y una contraseña. La contraseña no se muestra mientras escribes.
4. Decide si quieres cargar los productos ficticios.
5. Abre [http://127.0.0.1:8001/ingresar/](http://127.0.0.1:8001/ingresar/) y utiliza la cuenta que acabas de crear.
6. Pulsa **Ingresar**. Navega desde el menú a las secciones de bodega; los enlaces se abren en la misma pestaña.
7. Mantén abierta la consola. Para detener el servidor, presiona **Ctrl+C**.

En el equipo original ya existe la cuenta **Pablo Doussang**, con la contraseña configurada por el usuario, tanto en la copia local SQLite como en la preparación local U1. Esa cuenta y su contraseña **no se distribuyen** en el ZIP ni en GitHub. Al instalar en otro equipo debes crear tu propia cuenta. Los nombres de usuario admiten espacios y pueden editarse conservándolos.

## Si no abre o no te deja entrar

- **No se puede conectar:** inicia el servidor y espera el mensaje de arranque. Cada dirección funciona en el equipo donde se ejecuta Django.
- **Usuario o contraseña incorrectos:** revisa mayúsculas, espacios y símbolos; asegúrate de estar usando la cuenta del modo elegido.
- **Acceso restringido:** Consulta tiene lectura; Operador puede modificar productos y stock; Administrador puede además archivar productos y gestionar usuarios.
- **Puerto ocupado:** no inicies dos servidores del mismo modo. Si ya existe una instancia, utiliza su dirección.
- **Falta Python:** instala Python 3.12 y vuelve a ejecutar el iniciador.

No abras `index.html` directamente: es la plantilla base y Django debe procesarla. Las demás páginas heredan de ella.

## Ejecutar manualmente

Desde la carpeta del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**U1 sin base de datos:**

```powershell
.\.venv\Scripts\python.exe manage.py preparar_u1 --settings=config.settings_u1
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001 --settings=config.settings_u1 --noreload
```

No ejecutes migrate para U1. El comando inicial crea `runtime/u1.json` con cuentas y datos de demostración. Las contraseñas se guardan con hash; la sesión usa cookies firmadas. El JSON conserva los cambios entre reinicios. El prototipo está diseñado para un único proceso local, no para despliegue productivo concurrente.

**Versión SQLite:**

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py preparar
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

SQLite crea `db.sqlite3`. Para recuperar la contraseña de una cuenta SQLite:

```powershell
.\.venv\Scripts\python.exe manage.py changepassword "Pablo Doussang"
```

## Secciones y reglas

| Sección | Funciones |
|---|---|
| Resumen | Referencias activas, unidades, alertas, actividad y gráfica de 14 días |
| Inventario | Alta, edición, búsqueda, filtros, archivo, reactivación y CSV |
| Operaciones de stock | Entrada, salida con destino y ajuste por conteo físico |
| Movimientos | Fecha, usuario, motivo, destino, variación y saldos |
| Reportes | Períodos, gráficos, distribución por categoría y exportación |
| Ubicaciones | Agrupación física y búsqueda de productos |
| Usuarios y roles | Cuentas, roles, estado y contraseñas; solo administrador |

- Los productos nuevos empiezan con stock cero: una entrada incorpora existencias.
- Entrada/salida requiere un entero positivo; no se permiten salidas que dejen saldo negativo.
- Ajuste significa **cantidad final contada**, no cantidad a sumar o restar.
- El motivo es obligatorio. Las salidas requieren destino.
- Un producto al mínimo o por debajo genera una alerta.
- Archivar requiere stock cero y conserva el historial.
- Los movimientos no se editan: corrige con otro ajuste justificado.
- Un mismo envío de movimiento no se procesa dos veces.
- Los filtros de fecha afectan movimientos; las alertas y la distribución muestran existencias actuales.

## Estructura

```text
config/settings_u1.py       Configuración U1, DATABASES={}
config/urls_u1.py           Rutas U1 semánticas
u1/views.py                Vistas con listas/diccionarios y render()
u1/forms.py                Formularios U1
u1/store.py                Lectura y escritura JSON protegida
u1/middleware.py           Usuario y sesión sin base de datos
u1/tests.py                Pruebas que prohíben acceso SQL
warehouse/                 Versión SQLite: modelos, vistas, servicios y tests
warehouse/usernames.py     Regla de usuario con espacios
index.html       Plantilla base compartida
templates/warehouse/       Páginas de las secciones
static/                    CSS, Bootstrap y JS locales
docs/                      Diagramas, modelo y rúbrica
```

## Verificación reproducible

```powershell
.\.venv\Scripts\python.exe manage.py test warehouse
.\.venv\Scripts\python.exe manage.py test u1 --settings=config.settings_u1
```

Resultado de esta revisión: **25 pruebas aprobadas** (19 SQLite y 6 U1). Cubren creación/edición, nombres con espacios, roles, CSRF, saldo negativo, duplicados, archivo/reactivación, fechas, estadísticas, exportaciones y renderizado.

Se verificaron en navegador de escritorio las secciones, filtros, el rechazo de una salida sin existencias, el guardado del usuario con espacio, gráficos y navegación en la misma pestaña. Consulta [la revisión](docs/REVISION_RUBRICA.md) para evidencias y límites.

## Entrega académica y GitHub

- [Correspondencia de los diez indicadores](docs/RUBRICA.md)
- [Revisión y correcciones](docs/REVISION_RUBRICA.md)
- [Diagramas de flujo](docs/DIAGRAMAS.md)
- [Modelo de datos](docs/MODELO_DATOS.md)
- [Subir a PabloDoussang/SoundStock](docs/GITHUB.md)
- [Fuentes y uso de IA](docs/FUENTES_Y_DECISIONES.md)

![Flujo general](docs/flujo-general.png)

La evaluación U1 se demuestra con el modo JSON. SQLite queda como ampliación. La publicación efectiva en GitHub requiere completar el inicio de sesión del titular; no se considera cumplida solo por incluir instrucciones.

El código no incluye ecommerce, pagos, transporte GPS ni API REST/JWT de la unidad 3. Subir a GitHub no ejecuta el servidor. Para publicar una aplicación operativa en internet se requiere un alojamiento Python y configuración de producción.

## Datos privados

El .gitignore excluye `runtime/`, `db.sqlite3`, `.local-secret`, entornos virtuales y archivos de entorno. No subas cuentas, contraseñas ni bases locales. El ZIP contiene únicamente fuentes, migraciones, documentación y datos ficticios de catálogo.
