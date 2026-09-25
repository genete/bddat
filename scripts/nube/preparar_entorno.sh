#!/usr/bin/env bash
# Deja `pytest` listo en una sesión de Claude Code en la nube (#949, parte A).
#
# Lo llama el hook SessionStart (.claude/hooks/session-start.sh) al abrir la
# sesión, y se puede lanzar a mano en cualquier momento:
#
#     bash scripts/nube/preparar_entorno.sh
#
# Hace falta relanzarlo cuando el contenedor se recicla y PostgreSQL se para
# («connection refused» en los tests). Es idempotente: cada paso comprueba si ya
# está hecho, y con todo listo termina en unos segundos.
#
# Solo para la nube (contenedor Linux, root). En el PC no hace nada: el hook ya
# lo filtra por CLAUDE_CODE_REMOTE, y aquí se vuelve a comprobar por si alguien
# lo lanza a mano en Windows. Para forzarlo fuera de la nube: BDDAT_NUBE_FORZAR=1.
#
# Pasos (tabla de #949 A):
#   1. Python 3.14 en un venv fuera del repo, con requirements.txt y pytest-cov
#   2. PostgreSQL 16: el cluster Debian si existe; si no, uno propio con initdb
#   3. Roles bddat_admin (CREATEDB) y claude_desktop (NOLOGIN), base bddat
#   4. .env de la nube, solo si no existe
#   5. BD de tests con preparar_bd_test.py, sin --recrear
#   6. LibreOffice Writer (test_182 y test_732)
#
# El detalle de cada paso va a un log; por la salida solo sale el resumen, que
# el hook entrega como contexto de la sesión.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ] && [ "${BDDAT_NUBE_FORZAR:-}" != "1" ]; then
    echo "preparar_entorno: fuera de la nube, no hago nada (BDDAT_NUBE_FORZAR=1 para forzarlo)"
    exit 0
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${BDDAT_VENV:-$HOME/.venvs/bddat}"
PYTHON_VERSION="3.14.7"
PG_VERSION=16
PG_BIN="/usr/lib/postgresql/$PG_VERSION/bin"
PG_DATOS_PROPIO="/var/lib/postgresql/$PG_VERSION/nube"
PG_SOCKET=/var/run/postgresql
# Contraseña de un contenedor efímero y solo accesible en 127.0.0.1: no es un
# secreto. Si ya hay un .env con otra, el script no lo toca (paso 4).
PG_PASSWORD="bddat_nube"
LOG="${BDDAT_NUBE_LOG:-$HOME/.cache/bddat-nube.log}"

mkdir -p "$(dirname "$LOG")"
: > "$LOG"
RESUMEN=()

paso() { echo "== $*" >> "$LOG"; }
nota() { RESUMEN+=("$*"); }
fallo() {
    echo "preparar_entorno: FALLO en «$1». Detalle en $LOG" >&2
    tail -20 "$LOG" >&2
    exit 1
}

# ── 1. Python 3.14 ────────────────────────────────────────────────────────────
# El uv del contenedor (0.8.17) solo conoce 3.14.0rc2 y `uv self update` choca
# con el límite de la API de GitHub; el de PyPI trae la versión final.
paso "1. Python $PYTHON_VERSION"
UV="$(python3 -c 'import uv; print(uv.find_uv_bin())' 2>/dev/null || true)"
if [ -z "$UV" ]; then
    python3 -m pip install -q -U uv >> "$LOG" 2>&1 || fallo "instalar uv desde PyPI"
    UV="$(python3 -c 'import uv; print(uv.find_uv_bin())')"
fi
if [ ! -x "$VENV/bin/python" ] || ! "$VENV/bin/python" -c "import sys; sys.exit(sys.version.split()[0] != '$PYTHON_VERSION')" 2>/dev/null; then
    rm -rf "$VENV"
    "$UV" venv -q --python "$PYTHON_VERSION" "$VENV" >> "$LOG" 2>&1 || fallo "crear el venv $PYTHON_VERSION"
    nota "venv creado en $VENV"
fi
"$UV" pip install -q --python "$VENV/bin/python" -r "$REPO/requirements.txt" pytest-cov >> "$LOG" 2>&1 \
    || fallo "instalar requirements.txt"
nota "Python $("$VENV/bin/python" -c 'import platform; print(platform.python_version())') en $VENV"

# ── 2. PostgreSQL 16 ──────────────────────────────────────────────────────────
# Dos contenedores posibles: con el cluster Debian ya creado
# (/etc/postgresql/16/main) o sin ninguno, y entonces se crea uno propio.
paso "2. PostgreSQL $PG_VERSION"
pg_arrancar() {
    if [ -d "/etc/postgresql/$PG_VERSION/main" ]; then
        pg_ctlcluster "$PG_VERSION" main start >> "$LOG" 2>&1 || true
        echo "cluster Debian $PG_VERSION/main"
    else
        mkdir -p "$PG_SOCKET" && chown postgres:postgres "$PG_SOCKET"
        if [ ! -f "$PG_DATOS_PROPIO/PG_VERSION" ]; then
            mkdir -p "$PG_DATOS_PROPIO" && chown postgres:postgres "$PG_DATOS_PROPIO"
            su postgres -c "$PG_BIN/initdb -D '$PG_DATOS_PROPIO' --auth-local=peer --auth-host=scram-sha-256 -E UTF8 --locale=C.UTF-8" >> "$LOG" 2>&1 \
                || fallo "initdb"
        fi
        su postgres -c "$PG_BIN/pg_ctl -D '$PG_DATOS_PROPIO' -l '$PG_DATOS_PROPIO/servidor.log' -o \"-c listen_addresses=127.0.0.1 -c port=5432 -k $PG_SOCKET\" start" >> "$LOG" 2>&1 || true
        echo "cluster propio en $PG_DATOS_PROPIO"
    fi
}
ORIGEN_PG="ya en marcha"
if ! pg_isready -q -h 127.0.0.1 -p 5432; then
    ORIGEN_PG="$(pg_arrancar)"
    for _ in $(seq 1 30); do pg_isready -q -h 127.0.0.1 -p 5432 && break; sleep 0.5; done
    pg_isready -q -h 127.0.0.1 -p 5432 || fallo "arrancar PostgreSQL"
fi
nota "PostgreSQL $PG_VERSION en 127.0.0.1:5432 ($ORIGEN_PG)"

# ── 3. Roles y base de desarrollo ─────────────────────────────────────────────
# CREATEDB: preparar_bd_test.py --recrear hace DROP/CREATE DATABASE.
# claude_desktop: 32 migraciones hacen GRANT … TO claude_desktop.
paso "3. Roles"
psql_pg() { su postgres -c "psql -h $PG_SOCKET -v ON_ERROR_STOP=1 -qtAc \"$1\""; }
existe() { [ "$(psql_pg "$1")" = "1" ]; }
existe "SELECT 1 FROM pg_roles WHERE rolname='bddat_admin'" \
    || psql_pg "CREATE ROLE bddat_admin LOGIN PASSWORD '$PG_PASSWORD' CREATEDB" >> "$LOG" 2>&1 \
    || fallo "crear el rol bddat_admin"
existe "SELECT 1 FROM pg_roles WHERE rolname='claude_desktop'" \
    || psql_pg "CREATE ROLE claude_desktop NOLOGIN" >> "$LOG" 2>&1 \
    || fallo "crear el rol claude_desktop"
existe "SELECT 1 FROM pg_database WHERE datname='bddat'" \
    || psql_pg "CREATE DATABASE bddat OWNER bddat_admin" >> "$LOG" 2>&1 \
    || fallo "crear la base bddat"

# ── 4. .env ───────────────────────────────────────────────────────────────────
# Las cuatro rutas dentro del repo, las mismas carpetas que el PC; están en
# .gitignore. Un .env que ya exista no se toca.
paso "4. .env"
if [ -f "$REPO/.env" ]; then
    nota ".env ya existía: no se toca"
else
    {
        echo "DATABASE_URL=postgresql://bddat_admin:$PG_PASSWORD@127.0.0.1:5432/bddat"
        echo "TEST_DATABASE_URL=postgresql://bddat_admin:$PG_PASSWORD@127.0.0.1:5432/bddat_test"
        echo "FILESYSTEM_BASE=$REPO/docs_prueba/expedientes"
        echo "PLANTILLAS_BASE=$REPO/docs_prueba/plantillas_escritos"
        echo "TEST_FILESYSTEM_BASE=$REPO/docs_prueba_test/expedientes"
        echo "TEST_PLANTILLAS_BASE=$REPO/docs_prueba_test/plantillas_escritos"
        echo "SOFFICE=/usr/bin/soffice"
        echo "SECRET_KEY=nube-$(python3 -c 'import secrets; print(secrets.token_hex(16))')"
        echo "DEBUG=True"
        echo "SQLALCHEMY_ECHO=false"
    } > "$REPO/.env"
    nota ".env de la nube generado"
fi
mkdir -p "$REPO/docs_prueba/expedientes" "$REPO/docs_prueba/plantillas_escritos" \
         "$REPO/docs_prueba_test/expedientes" "$REPO/docs_prueba_test/plantillas_escritos"

# ── 5. BD de tests ────────────────────────────────────────────────────────────
# Sin --recrear: la crea si falta, aplica las migraciones pendientes y la
# semilla no repite lo que ya está (~1 s). --recrear queda para lanzarlo a mano.
paso "5. BD de tests"
(cd "$REPO" && "$VENV/bin/python" scripts/preparar_bd_test.py) >> "$LOG" 2>&1 \
    || fallo "preparar_bd_test.py"
nota "BD de tests al día (bddat_test)"

# ── 6. LibreOffice Writer ─────────────────────────────────────────────────────
# El contenedor trae solo libreoffice-core: sin Writer, soffice no abre un .odt
# y aun así devuelve 0. Los índices de apt del contenedor pueden estar
# caducados (404): se actualizan solo si hay que instalar.
paso "6. LibreOffice Writer"
# No vale `dpkg -s`: un paquete desinstalado que conserva su configuración
# (estado «rc») también devuelve 0.
if dpkg-query -W -f='${Status}' libreoffice-writer 2>/dev/null | grep -q 'install ok installed'; then
    nota "LibreOffice Writer ya instalado"
else
    { apt-get update -q && DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends libreoffice-writer; } >> "$LOG" 2>&1 \
        || fallo "instalar libreoffice-writer"
    nota "LibreOffice Writer instalado"
fi

echo "preparar_entorno: listo — $(IFS=';'; echo "${RESUMEN[*]}" | sed 's/;/; /g')"
echo "Tests: pytest (el venv ya está en el PATH). Si PostgreSQL se para: bash scripts/nube/preparar_entorno.sh"
echo "Interfaz: bash scripts/nube/arrancar_app.sh y node scripts/nube/captura.mjs <ruta> (ver scripts/nube/README.md)"
