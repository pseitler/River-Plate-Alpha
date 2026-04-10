@echo off
color 0B
echo ===================================================
echo    RIVER PLATE ALPHA - SINCRONIZADOR A LA NUBE
echo ===================================================
echo.

cd /d "%~dp0"

echo [1/3] Calculando modelos y generando reportes...
python main.py
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Fallo al ejecutar el motor de analisis.
    pause
    exit /b 1
)

echo.
echo [2/3] Empaquetando cambios en Git...
git add .
git commit -m "Auto-update: %DATE% %TIME% - Actualizacion manual"
if %errorlevel% neq 0 (
    echo INFO: No habia cambios nuevos para subir.
)

echo.
echo [3/3] Enviando a GitHub y activando Vercel...
git push origin main
if %errorlevel% neq 0 (
    color 0E
    echo ADVERTENCIA: Hubo un problema al subir. Verifica que el repositorio remoto este configurado.
    pause
    exit /b 1
)

echo.
color 0A
echo =============================================================
echo EXITO: Cambios subidos. Vercel actualizara el reporte
echo en aproximadamente 30 segundos.
echo =============================================================
pause
