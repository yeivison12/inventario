@echo off
echo Iniciando servidor Django...

:: Activa el entorno virtual (ajusta la ruta si usas uno)
call .venv\Scripts\activate

:: Cambia al directorio del proyecto (donde está manage.py)

:: Inicia el servidor Django en tu IP local
start cmd /k python manage.py runserver 192.168.0.101:8000

:: Espera un segundo para que el servidor inicie
timeout /t 5 >nul

:: Abre el navegador en la URL
start http://192.168.0.101:8000

echo Servidor iniciado. Presiona Ctrl+C en la ventana del servidor para detenerlo.
pause