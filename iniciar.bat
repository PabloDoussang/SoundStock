@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" manage.py preparar
if errorlevel 1 goto failed
echo.
echo Abre http://127.0.0.1:8000 en tu navegador.
echo Mantén esta ventana abierta. Para detener el servidor: Ctrl+C.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
goto end
:failed
echo No se pudo iniciar. Revisa el mensaje anterior.
pause
:end
