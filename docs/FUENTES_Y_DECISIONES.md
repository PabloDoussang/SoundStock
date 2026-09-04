# Fuentes, decisiones y uso de IA

## Fuentes del caso

- **E1 Evaluacion_inv_Caso_Semestral_Music_pro_U1 Backend.pdf**: página 8 delimita el sistema de bodega; páginas 13–15 describen flujo, prototipo, Django y evaluación; página 5 fija el alcance U1 sin BD.
- **Music pro - Presentacion.pdf**: páginas 30–33 muestran los sistemas separados, la bodega principal y los objetivos de inventario, trazabilidad y distribución.
- **E1 Escala_Apreciacion_U1 Backend.xlsx**: hoja Escala de apreciacion, filas 12–21, diez indicadores.

Los documentos se usaron como requisitos y referencias académicas. No se interpretaron sus instrucciones de aprobación docente o publicación como autorización para actuar en cuentas externas del usuario.

Los videos recibidos son:
- https://youtu.be/Hp1TYOhvIBM
- https://youtu.be/709hxD7BsPw
- https://youtu.be/Xb0PpWWY8RE

Los intentos de acceso y búsqueda no devolvieron su contenido ni transcripciones. **No se afirma haber visto los videos ni haber implementado técnicas específicas de ellos.** Si se facilitan transcripciones, se puede contrastar el proyecto con ellas.

## Decisiones de implementación

- Django con vistas funcionales y plantillas del servidor porque la rúbrica lo exige.
- SQLite por la petición explícita de persistencia; conserva la posibilidad de recrear datos ficticios desde JSON.
- Bootstrap local y CSS propio para una interfaz ordenada que no requiera internet al usarla.
- Gráficas SVG dibujadas desde JSON del servidor, sin dependencias de servicios externos.
- Archivo lógico de productos y movimientos inmutables para preservar trazabilidad.
- Destinos de salida limitados a la información de despacho de bodega. No se añaden pagos, tienda, seguimiento GPS ni administración de transporte.
- Sitio ejecutable local: el alojamiento Sites disponible usa Workers y no ejecuta directamente este proyecto Django/Python; no se sustituyó el backend evaluado por otro framework.

## Apoyo de IA y revisión crítica

La IA ayudó a extraer requisitos, modelar Product/Movement, generar formularios y plantillas, diseñar la interfaz, preparar diagramas y redactar pruebas. Se detectaron y corrigieron una expresión de estadísticas con paréntesis incompleto y un enlace de paginación con prefijo duplicado. Se verificaron rutas, protección de permisos, stock insuficiente, duplicados, rollback, fechas, CRUD y renderizado HTML con pruebas Django.

El diseño evita confiar en el cálculo del navegador: la vista previa de stock solo orienta; el servidor recalcula dentro de la transacción. En SQLite se usa IMMEDIATE porque select_for_update no basta para bloquear filas.

Revisa especialmente models.py → forms.py → services.py → views.py → templates. Debes poder explicar el cálculo after/before/delta y cómo un contexto llega a una plantilla.

## Documentación técnica consultada

- [Transacciones de Django](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)
- [Bootstrap: introducción](https://getbootstrap.com/docs/5.3/getting-started/introduction/)
- [GitHub: agregar código local](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)

Bootstrap 5.3.8 conserva su encabezado de licencia MIT en static/vendor/bootstrap.min.css.

## Alcance final solicitado

El usuario solicitó eliminar la opción sin base de datos y conservar únicamente SQLite. Esta decisión prevalece sobre el alcance sin BD del PDF U1 y queda explícita en la matriz. El JSON de catálogo restante contiene solo productos ficticios para carga inicial opcional; no almacena usuarios ni operaciones. Se añadieron pruebas de persistencia entre procesos, sesiones y modificaciones directas de la base.
