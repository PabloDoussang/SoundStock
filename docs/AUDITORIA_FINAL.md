# Auditoría final de la rúbrica

**Resultado técnico: se encontró evidencia verificable para los diez indicadores y se corrigieron los defectos detectados en esta auditoría.** La entrega está preparada para ser evaluada en el nivel Excelente.

La pauta original establece Excelente (10), Bueno (5) e Insatisfactorio (0) por indicador. Esta revisión no asigna automáticamente 100 puntos: la nota corresponde al docente, incluyendo la demostración y la explicación del estudiante.

Fuentes: E1 Escala_Apreciacion_U1 Backend.xlsx, hoja Escala de apreciacion, filas 12–21; PDF E1 del caso, páginas 5 y 13–15. Se verificó que la entrega usa JSON sin conexión a base de datos, conforme a U1.

## Revisión indicador por indicador

| Nº | Indicador original | Evidencia y comprobación | Resultado técnico |
|---|---|---|---|
| 1 | Modela a partir del caso seleccionado y su diagrama de flujo los atributos y tipos de datos necesarios que representarán la información dentro de la aplicación. | [Esquema](MODELO_DATOS.md), [almacén JSON](../warehouse/store.py), [flujo](DIAGRAMAS.md). Atributos reales, tipos, identificadores y relaciones verificados; campo password documentado como hash. | Cumple en la revisión |
| 2 | Determina las operaciones de entrada/salida y validaciones de datos requeridas para procesar la lógica de los formularios administrativos del caso. | [Formularios](../warehouse/forms.py), [vistas](../warehouse/views.py), [regresiones](../warehouse/test_audit.py). Validación de SKU normalizado, cantidades, destino, duplicados, contraseña y errores; rechazo sin modificar datos. | Cumple en la revisión |
| 3 | Codifica las vistas del servidor utilizando estructuras de control condicionales y bucles para replicar exactamente las bifurcaciones y la navegación definidas en el diagrama de flujo del caso administrativo. | [Vistas](../warehouse/views.py), [diagramas](DIAGRAMAS.md). Condicionales y bucles coinciden con procesos principales; documentadas rutas next, UUID propio/ajeno y cierre de sesión. | Cumple en la revisión |
| 4 | Construye las páginas web administrativas en plantillas HTML que corresponden a cada una de las interfaces proyectadas en el diagrama de flujo, vinculando variables y operadores para mostrar los datos enviados desde el servidor. | [index.html](../index.html), [plantillas](../templates/warehouse). Interfaces por sección, herencia, variables, if/for/filtros y gráficas alimentadas por JSON del servidor. | Cumple en la revisión |
| 5 | Configura paquetes y librerías externas en el entorno de desarrollo para enriquecer las interfaces HTML o extender las utilidades administrativas del proyecto. | [Dependencias](../requirements.txt), [Bootstrap local](../static/vendor/bootstrap.min.css). Django y dependencias declaradas; Bootstrap y CSS/JS propios cargados localmente. | Cumple en la revisión |
| 6 | Implementa módulos externos de Django (como el framework de mensajes, formularios o librerías de estilos) respetando la sintaxis y buenas prácticas del ecosistema y agregado al proyecto a un repositorio de github. | [Configuración](../config/settings.py), [GitHub](https://github.com/PabloDoussang/SoundStock). Formularios, mensajes y sesiones firmadas de Django; fuentes completas publicadas, sin datos privados. | Cumple en la revisión |
| 7 | (Inicialización y Estructura Base): Inicializa correctamente el proyecto y la aplicación en Django (startproject y startapp), registrando la app en settings.py para dejar operativo el entorno del caso seleccionado. | [Configuración](../config/settings.py), [app](../warehouse/apps.py), [iniciador](../iniciar.bat). Proyecto operativo, app registrada, un único iniciador y configuración sin BD. Preparación desde cero comprobada. | Cumple en la revisión |
| 8 | (Enrutamiento Modular y Amigable): Define rutas limpias y semánticas mediante urls.py (usando path() y nombres de ruta name), vinculando la navegación entre las diferentes páginas administrativas del flujo. | [Rutas del proyecto](../config/urls.py), [rutas de bodega](../warehouse/urls.py). Rutas semánticas con path/name; navegación en la misma pestaña y retorno tras ingreso. | Cumple en la revisión |
| 9 | (Lógica de Vistas y Paso de Datos): Codifica las funciones de vista en views.py para capturar la petición, estructurar la información en diccionarios de contexto y renderizarla hacia los archivos HTML correspondientes. | [Vistas](../warehouse/views.py). Peticiones GET/POST, listas/diccionarios, diccionarios de contexto y render de plantillas sin ORM. | Cumple en la revisión |
| 10 | (Integración y Asistencia con IA): Valida la visualización de los datos en las plantillas HTML apoyándose en sugerencias de herramientas de IA para resolver errores de sintaxis, depurar rutas o mejorar la estructura inicial de la aplicación. | [Pruebas](../warehouse/tests.py), [auditoría](../warehouse/test_audit.py), [navegación](../warehouse/test_navigation.py), [persistencia](../warehouse/test_persistence.py). Revisión crítica con IA, corrección de fallos reproducidos y verificación en navegador y ZIP independiente. | Cumple en la revisión |

## Correcciones realizadas para cerrar la revisión

- Contraseñas con espacios: el alta inicial, la edición y el ingreso conservan exactamente el valor escrito.
- Contraseñas semejantes al usuario: la validación ahora recibe nombre, apellidos y correo; funciona también en la preparación inicial.
- Desactivar/reactivar una cuenta invalida sus sesiones anteriores.
- Los SKU se normalizan a mayúsculas y la unicidad se comprueba después de normalizar.
- Cambiar Entrada/Salida/Ajuste conserva producto, cantidad y motivo; sin JavaScript, los enlaces mantienen el producto solicitado.
- La selección de producto empieza vacía cuando no se indicó uno; se evita operar accidentalmente el primero de la lista.
- Un identificador oculto inválido muestra un error visible y un enlace para abrir un formulario nuevo, sin guardar el movimiento.
- Un fallo de escritura no genera un éxito falso: conserva los datos y permite reintentar; incluye productos, usuarios, stock, archivo y cierre de sesión.
- Se corrigieron el esquema de campos y los diagramas: destino posterior al ingreso, UUID propio/ajeno, cierre de sesión conectado y cálculo de reportes al consultarlos.

## Evidencias de ejecución

- **31 pruebas aprobadas en 40,350 segundos**, ejecutadas desde una extracción nueva del ZIP, con Django check sin problemas.
- Las pruebas usan SimpleTestCase y JSON temporales; el acceso a base de datos está prohibido. Se comprobó persistencia entre tres procesos independientes.
- Preparación desde cero con usuario que contiene espacios, hash de contraseña y catálogo demo; repetir preparar conserva exactamente los datos existentes.
- La entrega funciona sin db.sqlite3 ni runtime del proyecto original. No se instalaron dependencias de nuevo por red: se reutilizó el entorno disponible.
- Revisión en navegador a **1440 × 1000** y **390 × 844**, con dimensiones efectivas verificadas. Se inspeccionaron resumen, inventario, operaciones y reportes; sin desbordamiento horizontal de la página móvil. Menú y tablas amplias tienen desplazamiento dentro de sus contenedores.
- Se comprobó en navegador que cambiar a Salida conserva el producto seleccionado, la cantidad y el motivo, y muestra el destino. No se envió ese formulario ni se alteraron los datos reales.
- Gráficas presentes y cero errores/advertencias de consola en la navegación revisada. Todos los enlaces internos revisados usan la misma pestaña.
- Los dos diagramas PNG regenerados se inspeccionaron visualmente para comprobar texto, ramas y flechas.
- GitHub y ZIP excluyen cuentas, hashes locales, archivos runtime, SQLite, claves, entornos y archivos de trabajo.

## Qué demostrar al docente

1. Iniciar con iniciar.bat, ingresar y recorrer las secciones en la misma pestaña.
2. Crear un producto de prueba, registrar una entrada y una salida; mostrar el rechazo de una salida que supere el saldo.
3. Enseñar el historial, una alerta, los filtros y una gráfica; explicar cómo se calculan before, after y delta.
4. Guardar un cambio, reiniciar y mostrar que sigue en runtime/bodega.json, sin conexión SQL.
5. Relacionar urls.py → vista → formulario/contexto → plantilla con el diagrama. Explicar los if/for, validaciones y el aporte de IA.
6. Mostrar el repositorio público y ejecutar python manage.py test warehouse.

La auditoría cubre el prototipo académico local de una sola instancia. No se presenta como certificación de seguridad o despliegue productivo; ese alcance no forma parte de U1.
