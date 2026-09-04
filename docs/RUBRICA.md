# Matriz de cumplimiento · Unidad 1

Fuente: E1 Escala_Apreciacion_U1 Backend.xlsx, hoja Escala de apreciacion, indicadores 1–10. Las marcas del Excel corresponden a la pauta y no se interpretan como una nota otorgada al proyecto.

La versión actual usa Django, plantillas y JSON sin conexión a una base de datos, de acuerdo con la página 5 y la fase de prototipo funcional de la página 14 del PDF de evaluación.

| Nº | Indicador | Evidencia verificable |
|---|---|---|
| 1 | Atributos y tipos derivados del caso y el flujo | docs/MODELO_DATOS.md, warehouse/store.py y catálogo JSON |
| 2 | Entradas, salidas y validaciones de formularios | warehouse/forms.py y validaciones en warehouse/views.py |
| 3 | Condiciones, bucles, bifurcaciones y navegación | warehouse/views.py y docs/DIAGRAMAS.md |
| 4 | Plantillas que muestran datos del servidor | index.html en la raíz; templates con variables, if, for y filtros |
| 5 | Paquetes y librerías externas | requirements.txt, Django, Bootstrap local en static/vendor |
| 6 | Formularios, mensajes y repositorio GitHub | Django forms/messages; código completo publicado en [PabloDoussang/SoundStock](https://github.com/PabloDoussang/SoundStock), rama main |
| 7 | Proyecto y aplicación registrados | config/settings.py y warehouse/apps.py |
| 8 | Rutas semánticas con path y name | config/urls.py, warehouse/urls.py y navegación compartida |
| 9 | Peticiones, diccionarios de contexto y render | warehouse/views.py: procesa listas/diccionarios y renderiza plantillas |
| 10 | Validación y correcciones con apoyo de IA | docs/REVISION_RUBRICA.md y pruebas funcionales/persistencia |

Las pruebas impiden consultas a bases de datos; el JSON conserva cuentas y operaciones entre reinicios. La calificación y la exposición del estudiante corresponden al docente. La evidencia técnica no sustituye la demostración del proyecto ni la explicación del código.
