# Revisión de la entrega corregida

## Fallos corregidos

1. **Nombre de usuario con espacio:** se añadió una regla compartida que permite espacios, normaliza Unicode y comprueba unicidad. La restricción SQL de unicidad permanece activa. La misma regla se usa en el formulario de usuarios y Django Admin.
2. **U1 sin base de datos:** se incorporó config.settings_u1, con DATABASES vacío, vistas JSON y sesiones firmadas. No ejecuta migrate ni consulta el ORM. Las operaciones se simulan con datos JSON; SQLite se conserva como opción separada.
3. **Validación visual pendiente:** se revisaron login, resumen, inventario, formulario de stock, movimientos, reportes, ubicaciones y usuarios en el navegador de escritorio.
4. **Ajustes de presentación:** se ajustaron el ancho mínimo de las gráficas, la distribución de las acciones de inventario y el singular/plural del contador.
5. **Documentación desactualizada:** el README, la matriz y los flujos distinguen el modo evaluable U1 de la ampliación SQLite.

## Evidencias automatizadas

- 19 pruebas de warehouse aprobadas.
- 6 pruebas de u1 aprobadas usando SimpleTestCase: el acceso a conexiones de base de datos está prohibido durante estas pruebas.
- Django check sin errores en ambos modos.
- JavaScript comprobado con node --check.

## Evidencias en navegador

- Se ingresó con Pablo Doussang.
- Se pasó del resumen al inventario usando la misma pestaña.
- Se filtró el SKU MP-DJC-010 y se mostró únicamente el producto agotado.
- Se intentó retirar una unidad de ese producto con stock cero: el formulario mostró «Stock insuficiente: hay 0 unidades disponibles» y conservó los valores.
- Se revisaron las gráficas y las cifras: 405 entradas, 90 salidas y 315 unidades disponibles en los datos ficticios locales.
- Se abrieron historial, ubicaciones y usuarios.
- Se guardó el formulario de Pablo Doussang con su nombre de usuario con espacio y se recibió «Usuario guardado».
- No se observaron errores de consola en la navegación revisada.
- Las tablas amplias conservan desplazamiento horizontal para acceder a todas sus columnas.

Se intentó configurar una vista móvil de 390 × 844, pero el navegador mantuvo su tamaño efectivo de escritorio. Por ello **no se declara verificación móvil real**. El CSS incluye reglas adaptativas, pero la comprobación visual realizada fue de escritorio.

Las pruebas automáticas cubren las mutaciones completas de stock, productos y usuarios en datos de prueba. La revisión visual no afirma haber probado todas las combinaciones posibles.

## Requisito GitHub

Destino solicitado: PabloDoussang/SoundStock. La publicación necesita una sesión GitHub autenticada. No se marca como completada antes de verificar que los archivos estén en el repositorio remoto.
