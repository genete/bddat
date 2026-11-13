#!/usr/bin/env bash
# Lanza el expediente-tipo por la interfaz (#1106) en una sesión de Claude Code
# en la nube, de punta a punta con un solo comando.
#
#     bash scripts/nube/guion_interfaz.sh --nuevo
#     bash scripts/nube/guion_interfaz.sh --lista
#     bash scripts/nube/guion_interfaz.sh --visible --hasta vincular_presentacion
#
# Es solo el preparador de la nube: el guion es el mismo módulo que en el PC
# (`python -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas`) y
# recibe los argumentos tal cual. Por orden:
#   1. arrancar_app.sh (BD sembrada, bundles de React y app en 127.0.0.1:5000;
#      idempotente: si la app ya responde, no hace nada);
#   2. `playwright` para Python en el venv, si falta. No está en requirements.txt a
#      propósito, y el venv lo crea uv, sin `pip`: se instala con `uv pip`;
#   3. variables que el guion ya sabe leer, solo si no vienen puestas:
#        CHROMIUM_PATH         el Chromium de la imagen (/opt/pw-browsers/chromium); sin él,
#                              Playwright busca uno propio que aquí no está descargado
#        BDDAT_UI_USUARIO      TTRA  } usuario y contraseña de la semilla de la nube
#        BDDAT_UI_PASSWORD     test  } (scripts/nube/README.md)
#   4. el guion.
#
# Cada ejecución CREA DATOS en la BD de desarrollo de la nube y deja fijado el
# reloj de desarrollo (ver scripts/expedientes_dummy/interfaz/README.md).
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    echo "guion_interfaz: solo en la nube (CLAUDE_CODE_REMOTE=true). En el PC, ver scripts/expedientes_dummy/interfaz/README.md."
    exit 1
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV="${BDDAT_VENV:-$HOME/.venvs/bddat}"
CHROMIUM_IMAGEN=/opt/pw-browsers/chromium

# 1. La app (--lista no abre el navegador ni necesita la app)
if [[ " $* " != *" --lista "* ]]; then
    bash "$REPO/scripts/nube/arrancar_app.sh"
fi

# 2. Playwright para Python
if ! "$VENV/bin/python" -c "import playwright" 2>/dev/null; then
    UV="$(command -v uv || true)"
    [ -n "$UV" ] || { echo "guion_interfaz: no encuentro uv; ejecuta bash scripts/nube/preparar_entorno.sh"; exit 1; }
    echo "guion_interfaz: instalando playwright en $VENV (una vez)"
    "$UV" pip install -q --python "$VENV/bin/python" playwright \
        || { echo "guion_interfaz: FALLO instalando playwright"; exit 1; }
fi

# 3. Valores por defecto de la nube; lo que venga puesto se respeta
if [ -z "${CHROMIUM_PATH:-}" ] && [ -x "$CHROMIUM_IMAGEN" ]; then
    export CHROMIUM_PATH="$CHROMIUM_IMAGEN"
fi
export BDDAT_UI_USUARIO="${BDDAT_UI_USUARIO:-TTRA}"
export BDDAT_UI_PASSWORD="${BDDAT_UI_PASSWORD:-test}"

# 4. El guion, desde la raíz del repo (es un módulo: -m)
cd "$REPO"
exec "$VENV/bin/python" -m scripts.expedientes_dummy.interfaz.analisis_doc_dos_vueltas "$@"
