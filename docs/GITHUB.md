# Subir SoundStock a GitHub

Repositorio creado: **[PabloDoussang/SoundStock](https://github.com/PabloDoussang/SoundStock)**. Para subir o actualizar el código debes autenticar Git con tu cuenta. La contraseña de Music Pro no es tu contraseña de GitHub.

## 1. Preparar la carpeta

Extrae el ZIP y entra en `SoundStock`, donde están manage.py, README.md y .gitignore. Sube el **código extraído**, no solamente el ZIP.

Instala Git y crea una cuenta de GitHub si aún no tienes. Abre PowerShell dentro de esa carpeta.

## 2. Revisar el repositorio de destino

SoundStock ya fue creado. Abre el enlace anterior para comprobar su contenido; no crees un duplicado. Si ya contiene commits, usa un clon del repositorio para incorporar esta actualización y conservar su historial.

## 3. Registrar el proyecto local

Ejecuta cada línea:

```powershell
git init -b main
git config user.name "TU NOMBRE"
git config user.email "TU CORREO O CORREO NOREPLY DE GITHUB"
git add .
git status
git commit -m "Implementa sistema de bodega Music Pro"
```

Los valores entre comillas se reemplazan por tus datos. La configuración se aplica solo a este repositorio.

Antes del commit, revisa que no aparezcan `runtime/`, bases de respaldo, `.local-secret`, `.env`, contraseñas ni `.venv`. El .gitignore incluido ya los excluye. No copies ACCESO_LOCAL.txt a esta carpeta.

## 4. Conectar y subir

Utiliza la URL HTTPS del repositorio solicitado:

```powershell
git remote add origin https://github.com/PabloDoussang/SoundStock.git
git remote -v
git push -u origin main
```

Completa el inicio de sesión que solicite Git. No escribas contraseñas ni tokens dentro de la URL. Si ya existe un remoto origin, compruébalo con `git remote -v` antes de cambiarlo.

Actualiza la página de GitHub y confirma que aparecen index.html en la raíz, README.md, iniciar.bat, manage.py, warehouse, templates, static y docs. El diagrama Mermaid de docs/DIAGRAMAS.md se renderiza en GitHub.

## 5. Enviar modificaciones posteriores

```powershell
git add .
git commit -m "Describe aquí el cambio realizado"
git push
```

## 6. Probar la entrega desde otro equipo

```powershell
git clone https://github.com/PabloDoussang/SoundStock.git
cd SoundStock
.\iniciar.bat
```

Crea un usuario nuevo y carga los datos demo si quieres. Las cuentas y runtime/bodega.json no viajan en el repositorio.

## Qué entregar al docente

El enlace al repositorio, el diagrama de flujo, la matriz de rúbrica y una demostración con ingreso, búsqueda de producto, entrada, salida, ajuste, alerta y reporte. Explica las diferencias entre cantidad movida y conteo final, y por qué las salidas deben validarse en el servidor.

**GitHub almacena el código; no pone en marcha el servidor Django.** Para una URL pública se necesita un alojamiento Python independiente. La creación del repositorio fue verificada; la publicación de sus archivos debe comprobarse después de subirlos. Esta entrega contiene una única versión U1 con JSON, sin base de datos.

Referencia: [Guía oficial de GitHub para agregar código local](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).
