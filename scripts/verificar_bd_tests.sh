#!/usr/bin/env bash
# pg_dump antes/después de correr tests, para detectar mutaciones silenciosas
# de la suite sobre la BD real de desarrollo (huérfanos, filas editadas sin
# revertir el marcador que las identifica como datos de prueba...).
#
# NO es un test con veredicto propio: el diff se guarda para análisis manual
# (o asistido por IA) — hay ruido esperado sin criterio automático fiable de
# pass/fail (reordenamiento físico de filas sin cambio de contenido, avance
# de secuencias — ver docs_prueba/temp/ de la sesión que originó este script,
# issue #672). Solo se filtra el ruido 100% seguro: el token
# \restrict/\unrestrict aleatorio que pg_dump 18 genera en cada ejecución.
#
# Uso:
#   scripts/verificar_bd_tests.sh                                  # suite completa
#   scripts/verificar_bd_tests.sh tests/test_667_mover_documento_esftt.py
#   scripts/verificar_bd_tests.sh -k test_supervisor_puede_anadir_condicion
#   scripts/verificar_bd_tests.sh tests/smoke/test_smoke_reglas_motor.py -v
#
# Salida: docs_prueba/temp/bd_antes.sql, bd_despues.sql, bd_diff.txt
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_DIR"

export PGPASSWORD=bddatpass
HOST=localhost
PORT=5432
USUARIO=bddat_admin
BASE=bddat

mkdir -p docs_prueba/temp
ANTES=docs_prueba/temp/bd_antes.sql
DESPUES=docs_prueba/temp/bd_despues.sql
DIFF_OUT=docs_prueba/temp/bd_diff.txt

echo "== Volcando estado ANTES =="
pg_dump --data-only --inserts --rows-per-insert=1 \
  --host="$HOST" --port="$PORT" --username="$USUARIO" --dbname="$BASE" \
  > "$ANTES"

if [ "$#" -eq 0 ]; then
    echo "== Ejecutando: pytest tests/ (sin argumentos = suite completa) =="
    venv/Scripts/python.exe -m pytest tests/ -q
else
    echo "== Ejecutando: pytest $* =="
    venv/Scripts/python.exe -m pytest "$@" -q
fi

echo "== Volcando estado DESPUES =="
pg_dump --data-only --inserts --rows-per-insert=1 \
  --host="$HOST" --port="$PORT" --username="$USUARIO" --dbname="$BASE" \
  > "$DESPUES"

echo "== Comparando (filtrado: token aleatorio \\restrict/\\unrestrict de pg_dump 18) =="
grep -v -E '^\\(un)?restrict ' "$ANTES" > "$ANTES.filtrado"
grep -v -E '^\\(un)?restrict ' "$DESPUES" > "$DESPUES.filtrado"
diff "$ANTES.filtrado" "$DESPUES.filtrado" > "$DIFF_OUT" || true

echo "== Resumen =="
wc -l "$DIFF_OUT"
echo "Diff completo en: $DIFF_OUT (revisar a mano — no hay veredicto automático)"
