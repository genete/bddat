#!/usr/bin/env bash
# Clon reducido de legalize-es para una sesión de Claude Code en la nube (#949).
#
# A demanda, NO en el hook SessionStart: la mayoría de sesiones no lo necesitan.
#
#     bash scripts/nube/preparar_legalize.sh
#
# Deja en ${LEGALIZE_DIR:-$HOME/legalize-es} (fuera del repo BDDAT) un clon
# superficial y sparse de https://github.com/legalize-dev/legalize-es con:
#   - todo es-an/ (Andalucía: BOE-A-* históricas y BOJA-b-*), y
#   - de es/ solo los ficheros de las normas de docs/referencia/normas_catalog.csv
#     (id_tecnico BOE-A-*), que es lo que consulta el skill /legalize.
# Los patrones los calcula scripts/nube/legalize_patrones.py.
#
# NO sirve para legalize_xref.py ni legalize_compile.py: buscan en todo el
# corpus y necesitan el clon COMPLETO (solo PC, D:\legalize-es).
#
# Idempotente: si el clon ya existe, lo actualiza (fetch --depth 1) y recalcula
# los patrones. Solo en la nube; BDDAT_NUBE_FORZAR=1 para forzarlo fuera.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ] && [ "${BDDAT_NUBE_FORZAR:-}" != "1" ]; then
    echo "preparar_legalize: fuera de la nube, no hago nada (BDDAT_NUBE_FORZAR=1 para forzarlo)"
    exit 0
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DESTINO="${LEGALIZE_DIR:-$HOME/legalize-es}"
URL="https://github.com/legalize-dev/legalize-es.git"
PYTHON="${BDDAT_VENV:-$HOME/.venvs/bddat}/bin/python"
[ -x "$PYTHON" ] || PYTHON=python3
inicio=$SECONDS

if [ ! -e "$DESTINO" ]; then
    echo "preparar_legalize: clonando $URL en $DESTINO"
    git clone --depth 1 --filter=blob:none --sparse "$URL" "$DESTINO"
elif [ "$(git -C "$DESTINO" config --get core.sparseCheckout || true)" != "true" ]; then
    echo "preparar_legalize: $DESTINO existe y no es un clon sparse (¿completo?): no lo toco" >&2
    exit 1
else
    echo "preparar_legalize: actualizando $DESTINO"
    git -C "$DESTINO" fetch --depth 1 --filter=blob:none origin HEAD
    git -C "$DESTINO" reset --hard FETCH_HEAD
fi

"$PYTHON" "$REPO/scripts/nube/legalize_patrones.py" "$DESTINO" \
    | git -C "$DESTINO" sparse-checkout set --no-cone --stdin

n_normas="$(find "$DESTINO/es" "$DESTINO/es-an" -name '*.md' 2>/dev/null | wc -l)"
n_es="$(find "$DESTINO/es" -name '*.md' 2>/dev/null | wc -l)"
tam="$(du -sh "$DESTINO" | cut -f1)"
tam_git="$(du -sh "$DESTINO/.git" | cut -f1)"
commit="$(git -C "$DESTINO" log -1 --format='%h del %cs')"

echo "preparar_legalize: listo en $DESTINO"
echo "  normas en disco: $n_normas (es/: $n_es, es-an/: $((n_normas - n_es)))"
echo "  tamaño: $tam en total, $tam_git de ellos en .git"
echo "  commit: $commit"
echo "  tiempo: $((SECONDS - inicio)) s"
