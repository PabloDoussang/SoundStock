# Matriz de cumplimiento E1 · revisión corregida

Fuente: E1 Escala_Apreciacion_U1 Backend.xlsx, hoja Escala de apreciacion, filas 12–21. Las marcas del Excel son parte de la pauta, no una nota otorgada a este trabajo.

| Nº | Evidencia del modo U1 | Resultado técnico |
|---|---|---|
| 1 | u1/store.py, JSON de catálogo y MODELO_DATOS.md: atributos, tipos y relaciones | Cumple |
| 2 | u1/forms.py y u1/views.py: tipos, cantidades, destinos, unicidad, roles y nombres con espacios | Cumple; probado |
| 3 | Vistas con if/for, bifurcaciones de permisos y saldo; DIAGRAMAS.md actualizado | Cumple |
| 4 | index.html y plantillas de todas las secciones; variables, if, for, filtros y json_script | Cumple |
| 5 | requirements.txt con Django; Bootstrap 5.3.8 guardado localmente | Cumple |
| 6 | Formularios, messages y sesiones Django; GitHub requiere publicación efectiva | Código cumple; publicación pendiente de autenticación |
| 7 | Proyecto config, apps warehouse/u1 y registro en INSTALLED_APPS | Cumple |
| 8 | config/urls_u1.py con path, rutas name y navegación compartida | Cumple |
| 9 | u1/views.py recibe peticiones, procesa listas/diccionarios, genera contextos y renderiza | Cumple |
| 10 | Revisión de interfaz en navegador, correcciones y pruebas documentadas | Cumple técnicamente |

## Correcciones realizadas

- Se añadió el modo U1 sin base de datos: DATABASES={}, sesiones firmadas, JSON y formularios independientes del ORM.
- Se conservó el modo SQLite para la petición original.
- Se corrigió la validación del usuario con espacios en la interfaz y Django Admin.
- Se añadieron pruebas de regresión para edición, duplicados e ingreso.
- Se revisaron las pantallas en navegador de escritorio y la navegación en la misma pestaña.
- Se actualizaron los diagramas y el README para distinguir ambos modos.

## Verificación y pendientes externos

25 pruebas aprobadas: 19 SQLite y 6 U1 sin acceso a base de datos. Evidencia detallada en REVISION_RUBRICA.md.

El indicador 6 no está completamente cerrado hasta que el repositorio esté efectivamente publicado. El destino solicitado es PabloDoussang/SoundStock; la página de GitHub solicitó iniciar sesión.

La aprobación del alcance, exposición y comprensión del código corresponden al estudiante/docente. Esta matriz documenta el cumplimiento técnico; no asigna una calificación.
