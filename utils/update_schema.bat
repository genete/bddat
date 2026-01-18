@echo off
echo Generando schema.sql...
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -d bddat --schema-only > ..\schema.sql 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Revisa el archivo schema.sql para ver el error
    pause
    exit /b 1
)

echo Subiendo a GitHub...
cd ..
git add schema.sql
git commit -m "Update schema snapshot %date%"
git push

echo Listo!
pause
