# Diagramas de flujo del sistema

Los diagramas siguientes son editables en Mermaid y se renderizan en GitHub. Los PNG/SVG en esta carpeta permiten verlos sin conexión. El primer diagrama resume la navegación; el segundo detalla la lógica de stock. La fuente Mermaid documenta también las ramas secundarias.

## 1. Ingreso y navegación

```mermaid
flowchart TD
  A([Inicio]) --> B["Ingresar usuario y contraseña /ingresar/"]
  B --> C{"¿Cuenta activa y credenciales válidas?"}
  C -- No --> D["Mostrar error sin abrir sesión"]
  D --> B
  C -- Sí --> E["Crear sesión y determinar rol"]
  E --> F["Resumen /"]
  F --> G{"Seleccionar sección"}
  G --> H["Inventario /inventario/"]
  G --> I["Stock /stock/ · Operador o Administrador"]
  G --> J["Historial /movimientos/"]
  G --> K["Reportes /reportes/"]
  G --> L["Ubicaciones /ubicaciones/"]
  G --> M["Usuarios /usuarios/ · Administrador"]
  H --> H1["Buscar / filtrar / exportar CSV"]
  H --> H2{"¿Crear o editar producto?"}
  H2 -- Sí --> H3{"¿Rol con permiso?"}
  H3 -- No --> X["403 · Acceso restringido"]
  H3 -- Sí --> H4["Formulario ProductForm"]
  H4 --> H5{"¿Datos válidos y SKU único?"}
  H5 -- No --> H4
  H5 -- Sí --> H6["Guardar metadatos; stock se opera por separado"]
  H6 --> H
  H --> H7{"¿Archivar o reactivar?"}
  H7 -- Sí --> H8{"¿Administrador?"}
  H8 -- No --> X
  H8 -- Sí --> H9["Confirmar acción"]
  H9 --> H10{"¿Activo con stock mayor a cero?"}
  H10 -- Sí --> H11["Rechazar; requiere salida o ajuste justificado"]
  H11 --> H
  H10 -- No --> H12["Cambiar estado activo y conservar historial"]
  H12 --> H
  I --> N["Ver flujo detallado de stock"]
  J --> J1["Filtrar tipo, texto y fechas; exportar CSV"]
  K --> K1["Validar fechas; agregar movimientos y mostrar gráficas"]
  L --> L1["Buscar ubicación y abrir producto en inventario"]
  M --> M1["Crear/editar cuenta y rol"]
  M1 --> M2{"¿Formulario válido y no bloquea la propia cuenta?"}
  M2 -- No --> M1
  M2 -- Sí --> M3["Guardar usuario; contraseña con hash"]
  M3 --> M
  G --> O["Cerrar sesión · POST /salir/"]
  O --> B
```

Los filtros GET no modifican los datos guardados. Fechas inválidas muestran errores y no devuelven resultados del período. Exportar movimientos con fechas inválidas responde HTTP 400. Cada sección conserva el menú para regresar al resumen o cambiar de sección.

## 2. Operación de stock

```mermaid
flowchart TD
  A([Abrir /stock/]) --> B{"¿Sesión activa?"}
  B -- No --> C["Redirigir al ingreso"]
  B -- Sí --> D{"¿Operador o Administrador?"}
  D -- No --> E["403 · Acceso restringido"]
  D -- Sí --> F["Seleccionar producto, tipo, cantidad, motivo y destino"]
  F --> G{"¿Confirmar o cancelar?"}
  G -- Cancelar --> H["Volver al inventario"]
  G -- Confirmar --> I["POST con CSRF y UUID"]
  I --> J{"¿Formulario válido?"}
  J -- No --> K["Mostrar errores y conservar valores"]
  K --> F
  J -- Sí --> L["Abrir escritura JSON protegida"]
  L --> M{"¿UUID ya registrado?"}
  M -- Sí --> N["Mismo usuario: devolver operación existente"]
  N --> Z["Mensaje y redirección al historial"]
  M -- No --> O["Leer producto activo y stock actual"]
  O --> P{"Tipo"}
  P -- Entrada --> Q["Final = actual + cantidad"]
  P -- Salida --> R["Final = actual - cantidad; destino obligatorio"]
  P -- Ajuste --> S["Final = conteo físico ingresado"]
  Q --> T{"¿Saldo válido y diferente?"}
  R --> T
  S --> T
  T -- No --> U["Descartar cambios; explicar error"]
  U --> F
  T -- Sí --> V["Guardar movimiento con antes, después, variación, usuario y fecha"]
  V --> W["Actualizar stock del producto"]
  W --> X["Guardar cambios juntos"]
  X --> Y["Recalcular alertas y reportes desde JSON"]
  Y --> Z
  Z --> AA([Nueva operación o navegar])
```

Si el producto deja de estar activo, se rechaza sin escribir. Un UUID ajeno se rechaza. El almacén JSON agrupa las escrituras mediante archivo temporal y reemplazo atómico. Si falla antes de confirmar, se conserva el estado anterior. El prototipo usa un único proceso local y no consulta una base de datos.

## 3. Orden para dibujarlo en Draw.io

1. Óvalo: Inicio.
2. Paralelogramo: captura de usuario/contraseña.
3. Rombo: credenciales válidas; rama No al formulario y Sí a sesión/rol.
4. Rectángulo: resumen, seguido de rombo de selección de sección.
5. Una rama por sección según el primer diagrama.
6. Para modificaciones: rombo de permiso → formulario → rombo de validación.
7. Para stock: bloqueo de escritura → UUID → tipo → cálculo → validación de saldo → guardar historial y stock → confirmar.
8. La persistencia se representa con un símbolo de archivo JSON. Conecta errores al formulario y operaciones exitosas al historial.
9. Conecta cierre de sesión al ingreso.
10. Conecta el archivo JSON a las operaciones de lectura y guardado para representar persistencia.

## Persistencia al volver a abrir

Guardar formulario válido → reemplazar runtime/bodega.json → mostrar éxito. Refrescar o cambiar de sección → leer el mismo archivo. Cerrar sesión → invalidar sesión y conservar datos. Reiniciar → abrir el mismo JSON → ingresar y leer los últimos cambios guardados.
