# Revisión final · prototipo U1 con JSON

## Correcciones

- Una única versión sin conexión a base de datos: DATABASES vacío, listas y diccionarios JSON, sesiones firmadas y formularios Django.
- Un único iniciar.bat en puerto 8000, sin migrate. index.html continúa en la raíz.
- Se conservaron la cuenta, hashes, permisos, productos e historial existentes mediante una conversión local; la antigua base SQLite se respaldó y no se distribuye.
- Las operaciones confirmadas se guardan en runtime/bodega.json mediante archivo temporal, sincronización y reemplazo atómico. Reiniciar y volver a ingresar conserva los datos.
- Se mantuvieron controles de permisos, archivo lógico, saldo insuficiente, UUID para envíos duplicados y nombres de usuario con espacios.
- Documentación y diagramas reflejan el uso de JSON, conforme al alcance de U1.

## Pruebas

La suite de warehouse usa SimpleTestCase y archivos temporales; está prohibido consultar una base de datos. Incluye persistencia entre tres procesos de Python independientes, creación/edición de administradores, contraseña modificada, productos, stock, recargas, cierre de sesión, cliente nuevo y preparación sin restablecer datos.

Resultado final: **31 pruebas aprobadas desde una extracción nueva del ZIP**; Django check sin problemas. Incluyen 19 pruebas funcionales, una de persistencia entre tres procesos, 9 regresiones de auditoría y 2 de navegación y errores de formulario. Se corrigió una importación indirecta de autenticación que causaba error al redirigir usuarios sin sesión. Las pruebas no alteran el JSON privado del usuario.

## Revisión visual

Las revisiones de escritorio comprobaron ingreso, secciones, filtros, rechazo de salida sin existencias, historial, ubicaciones, usuarios, gráficas y navegación en la misma pestaña. La revisión final confirmó el ingreso con la cuenta conservada y la navegación a reportes en la misma pestaña: 12 productos, 315 unidades, 24 movimientos, 405 entradas y 90 salidas en los datos ficticios locales.

La auditoría actual verificó dimensiones efectivas de 1440 × 1000 y 390 × 844. Se revisaron resumen, inventario, formulario de stock y reportes; el móvil no desborda horizontalmente la página. Las tablas amplias y el menú tienen desplazamiento propio. No se observaron errores de consola.

## GitHub

Repositorio: https://github.com/PabloDoussang/SoundStock . Publicación completada y verificada el 3 de septiembre de 2026. Se verifican la rama main y los archivos del remoto: index.html en la raíz, iniciar.bat, manage.py, config, warehouse, templates, static y docs. No se suben runtime, la base de respaldo, cuentas, hashes ni claves locales.

## Auditoría para nivel Excelente

[Informe completo por los diez indicadores](AUDITORIA_FINAL.md), con fallos corregidos, evidencias, alcance y demostración sugerida. Incluye validación de contraseñas, sesiones, SKU, cambio de operación sin perder producto y errores de escritura recuperables.
