# Matriz de cumplimiento E1 · versión SQLite

Fuente: E1 Escala_Apreciacion_U1 Backend.xlsx, hoja Escala de apreciacion, filas 12–21. Las marcas del Excel son parte de la pauta, no una calificación otorgada a este trabajo.

**Alcance actual:** se conserva únicamente la versión con base de datos por petición expresa del usuario. El PDF de U1 solicita un prototipo sin BD; esta versión se aparta de esa condición. No se declara cumplimiento total del encargo académico original.

| Nº | Evidencia de implementación | Resultado técnico |
|---|---|---|
| 1 | warehouse/models.py y MODELO_DATOS.md: atributos, tipos y relaciones | Implementado |
| 2 | warehouse/forms.py, views.py y services.py: validación, permisos y reglas | Implementado y probado |
| 3 | Condiciones, bucles y bifurcaciones; DIAGRAMAS.md | Implementado |
| 4 | index.html en la raíz y plantillas: variables, if, for, filtros y json_script | Implementado |
| 5 | requirements.txt con Django; Bootstrap local | Implementado |
| 6 | Formularios, messages y sesiones Django; repositorio GitHub creado | Publicación del código pendiente de verificar |
| 7 | Proyecto config y app warehouse registrada | Implementado |
| 8 | config/urls.py y warehouse/urls.py: path, name y navegación | Implementado |
| 9 | warehouse/views.py procesa peticiones y genera contextos con datos del ORM | Implementado con SQLite; se aparta del prototipo sin BD |
| 10 | Revisión crítica, correcciones y pruebas documentadas | Evidencia técnica disponible |

## Verificación

20 pruebas aprobadas, incluida persistencia con tres procesos independientes. Se mantienen los controles de stock, archivo lógico, historial y nombres de usuario con espacios.

El funcionamiento de SQLite, las instrucciones de inicio y la persistencia se documentan en README.md y REVISION_RUBRICA.md. La aprobación del alcance y la evaluación de la exposición corresponden al docente.
