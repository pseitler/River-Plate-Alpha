@echo off
color 0B
echo ===================================================
echo    RIVER PLATE ALPHA - ANALISIS LOCAL (OFFLINE)
echo ===================================================
echo.

cd /d "%~dp0"

echo [+] Calculando modelos de riesgo y rentabilidad...
python main.py
if %errorlevel% neq 0 (
    color 0C
    echo ERROR: Fallo al ejecutar el motor de analisis.
    pause
    exit /b 1
)

echo.
color 0A
echo =============================================================
echo EXITO: Modelos calculados. 
echo Abriendo el reporte en tu navegador predeterminado...
echo =============================================================
start public\index.html
