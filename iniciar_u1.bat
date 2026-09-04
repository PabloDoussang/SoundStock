@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" manage.py preparar_u1 --settings=config.settings_u1
if errorlevel 1 goto failed
echo Abre http://127.0.0.1:8001 . Modo U1 sin base de datos.
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8001 --settings=config.settings_u1 --noreload
goto end
:failed
echo No se pudo iniciar. Revisa el mensaje anterior.
pause
:end
