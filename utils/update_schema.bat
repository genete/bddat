@echo off
echo Generando schema.sql...
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d bddat --schema-only > ..\schema.sql 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Revisa el archivo schema.sql para ver el error
    pause
    exit /b 1
)

echo Cambiando a rama develop...
cd ..
git checkout develop
git pull origin develop

echo Subiendo a GitHub (develop)...
git add schema.sql
git commit -m "[BD] Update schema snapshot %date%"
git push origin develop

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Fallo al subir a GitHub
    pause
    exit /b 1
)

echo Listo! Schema actualizado en rama develop
pause