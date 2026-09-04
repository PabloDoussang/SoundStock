# Revisión de SoundStock · única versión SQLite

## Cambios actuales

- Se retiraron la aplicación u1, sus configuraciones, rutas y el iniciador alternativo. Solo se ejecuta `iniciar.bat` en el puerto 8000.
- `index.html` permanece en la carpeta principal y Django lo encuentra desde su configuración de plantillas.
- Usuarios, permisos, sesiones, productos y movimientos se guardan en `db.sqlite3`. El inicio reutiliza la base y no restablece sus registros.
- Se conservaron los datos locales de SQLite. El ZIP excluye la base y las credenciales.
- Se actualizaron el README, la matriz, el modelo de datos y los flujos para esta única versión.
- Se mantienen las correcciones de nombres de usuario con espacios, paginación, gráficas y acciones de inventario.

## Evidencia automatizada

**20 pruebas aprobadas** mediante `python manage.py test warehouse`:

- 19 pruebas de creación/edición, permisos, CSRF, stock, duplicados, rollback, archivo, estadísticas, exportaciones y plantillas.
- Una prueba de integración en un archivo SQLite temporal con tres procesos de Python independientes:
  1. Crea y edita un administrador y un producto mediante los formularios, cambia la contraseña, registra una entrada y una salida, recarga, cierra sesión e ingresa desde un cliente nuevo.
  2. Reinicia en otro proceso, ejecuta migraciones y preparación normal, comprueba los datos existentes y confirma cambios directos en la misma base.
  3. Reinicia otra vez y comprueba la nueva contraseña, el administrador, la ubicación editada, el stock y su historial.

Django no detectó problemas en sus comprobaciones de sistema. Las pruebas se ejecutan sobre bases separadas; no alteran la base local del usuario.

## Revisión visual anterior que sigue aplicando

Se revisaron ingreso, resumen, inventario, filtros, rechazo de una salida sin existencias, historial, ubicaciones, usuarios, gráficas y navegación en la misma pestaña, en navegador de escritorio. Se guardó un nombre de usuario con espacio y se comprobó el mensaje de éxito. Las tablas amplias permiten desplazamiento horizontal.

No se declara verificación visual móvil: el intento de cambiar la resolución mantuvo el tamaño efectivo de escritorio. Esta revisión de persistencia no modifica el diseño de las secciones.

## Límites de la entrega académica y GitHub

La elección de conservar solo SQLite responde a la petición actual del usuario y se aparta de la condición original del PDF U1 de trabajar sin base de datos. La matriz refleja esa diferencia.

Repositorio creado: https://github.com/PabloDoussang/SoundStock . La carga del código no se considera completada hasta verificar el contenido remoto. El ZIP contiene la versión SQLite actualizada.
