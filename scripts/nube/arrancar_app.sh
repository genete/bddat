#!/usr/bin/env bash
# Arranca BDDAT en una sesión de Claude Code en la nube (#949, parte B), para
# verificar la interfaz con datos sintéticos.
#
#     bash scripts/nube/arrancar_app.sh           # prepara lo que falte y arranca
#     bash scripts/nube/arrancar_app.sh --parar   # para la app
#
# Idempotente. Por orden:
#   1. entorno de tests y PostgreSQL (preparar_entorno.sh, ~2 s si ya está);
#   2. BD de desarrollo sembrada (preparar_bd_desarrollo.py);
#   3. build de react-src si faltan bundles: sin él, TODAS las páginas dan 404
#      (command-palette se carga desde base_app.html);
#   4. `python run.py` en segundo plano, en 127.0.0.1:5000, log en
#      ~/.cache/bddat-app.log. Si ya responde, no arranca otra.
#
# No va en el hook SessionStart a propósito: suma ~20 s la primera vez y la
# mayoría de sesiones no abren el navegador.
#
# Verificar en el navegador: node scripts/nube/captura.mjs (ver su cabecera).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    echo "arrancar_app: solo en la nube (CLAUDE_CODE_REMOTE=true). En el PC, run.py o flask_console.py."
    exit 1
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${BDDAT_VENV:-$HOME/.venvs/bddat}"
PUERTO="${FLASK_PORT:-5000}"
URL="http://127.0.0.1:$PUERTO"
LOG_APP="$HOME/.cache/bddat-app.log"
PID_APP="$HOME/.cache/bddat-app.pid"
mkdir -p "$HOME/.cache"

responde() { curl -s -o /dev/null --max-time 2 -w '%{http_code}' "$URL/auth/login" | grep -q '^200$'; }

if [ "${1:-}" = "--parar" ]; then
    if [ -f "$PID_APP" ] && kill -0 "$(cat "$PID_APP")" 2>/dev/null; then
        # run.py arranca con el reloader de Werkzeug: se para el grupo entero.
        kill -- "-$(cat "$PID_APP")" 2>/dev/null || kill "$(cat "$PID_APP")"
        rm -f "$PID_APP"
        echo "arrancar_app: app parada"
    else
        echo "arrancar_app: no había app arrancada por este script"
    fi
    exit 0
fi

# 1. Entorno y PostgreSQL
bash "$REPO/scripts/nube/preparar_entorno.sh" | head -1

# 2. BD de desarrollo
(cd "$REPO" && "$VENV/bin/python" scripts/nube/preparar_bd_desarrollo.py) > "$HOME/.cache/bddat-bd-desarrollo.log" 2>&1 \
    || { echo "arrancar_app: FALLO preparando la BD de desarrollo"; tail -20 "$HOME/.cache/bddat-bd-desarrollo.log"; exit 1; }
tail -1 "$HOME/.cache/bddat-bd-desarrollo.log"

# 3. Build de React si falta algún fichero del manifest
FALTAN="$("$VENV/bin/python" - "$REPO/app/static/js/react" <<'PY'
import json, os, sys
d = sys.argv[1]
try:
    m = json.load(open(os.path.join(d, 'manifest.json')))
except FileNotFoundError:
    print('manifest'); sys.exit()
print(sum(1 for e in m.values() if not os.path.isfile(os.path.join(d, e['file']))))
PY
)"
if [ "$FALTAN" != "0" ]; then
    bash "$REPO/scripts/build_react.sh" > "$HOME/.cache/bddat-react.log" 2>&1 \
        || { echo "arrancar_app: FALLO en el build de React"; tail -20 "$HOME/.cache/bddat-react.log"; exit 1; }
    echo "build de React hecho (faltaban: $FALTAN)"
    # El build no debe cambiar ficheros versionados: el manifest sale idéntico al del PC.
    if ! git -C "$REPO" diff --quiet -- app/static/js/react/manifest.json; then
        echo "AVISO: el build ha cambiado app/static/js/react/manifest.json; no lo subas sin revisarlo"
    fi
fi

# 4. La app
if responde; then
    echo "arrancar_app: la app ya responde en $URL"
else
    cd "$REPO"
    setsid "$VENV/bin/python" run.py > "$LOG_APP" 2>&1 < /dev/null &
    echo $! > "$PID_APP"
    for _ in $(seq 1 60); do responde && break; sleep 0.5; done
    responde || { echo "arrancar_app: la app no responde; log en $LOG_APP"; tail -20 "$LOG_APP"; exit 1; }
    echo "arrancar_app: app arrancada en $URL (log en $LOG_APP)"
fi

# Aviso de los CDN: sin ellos las páginas se ven rotas (sin CSS de la Junta ni
# Bootstrap: «bootstrap is not defined», modales desplegados).
for host in cdn.juntadeandalucia.es cdn.jsdelivr.net; do
    if [ "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' "https://$host/")" = "000" ]; then
        echo "AVISO: $host bloqueado por la red del entorno: la interfaz saldrá sin estilos."
        echo "       Permitirlo en claude.ai → entorno → Network access."
    fi
done
