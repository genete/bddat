@echo off
echo Generando schema.sql...
pg_dump -U postgres -d bddat --schema-only > ..\schema.sql

echo Subiendo a GitHub...
cd ..
git add schema.sql
git commit -m "Update schema snapshot %date%"
git push

echo Listo!
pause
