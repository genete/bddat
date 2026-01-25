@echo off
echo ========================================
echo Exportando datos de tablas maestras
echo Schema: estructura
echo ========================================
echo.

REM Verificar que PostgreSQL está accesible
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se encuentra pg_dump en la ruta especificada
    echo Verifica la instalacion de PostgreSQL
    pause
    exit /b 1
)

echo Generando datos_estructurales.sql...
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d bddat ^
    --data-only ^
    --inserts ^
    --column-inserts ^
    --schema=estructura ^
    --no-owner ^
    --no-privileges ^
    > ..\datos_estructurales.sql 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al exportar datos
    echo Revisa el archivo datos_estructurales.sql para ver el error
    pause
    exit /b 1
)

echo.
echo ========================================
echo Datos exportados correctamente
echo Archivo: datos_estructurales.sql
echo ========================================
echo.
echo Cambiando a rama develop...
cd ..
git checkout develop
git pull origin develop

echo Subiendo a GitHub (develop)...
git add datos_estructurales.sql
git commit -m "[BD] Update datos estructurales %date%"
git push origin develop

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir a GitHub
    pause
    exit /b 1
)

echo.
echo ========================================
echo COMPLETADO CON EXITO
echo Archivo subido a rama develop
echo ========================================
echo.
pause