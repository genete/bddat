#!/usr/bin/env bash
# Compila los bundles React (multi-isla) para Flask. (#499, ADR-015)
# Salida: app/static/js/react/bundle.<isla>.<hash>.js + manifest.json
#
# Cada isla declarada en react-src/vite.config.js (objeto ISLANDS) produce su
# bundle. El manifest.json mapea nombre→fichero con hash; lo lee el helper Jinja
# react_bundle(). En Windows usar preferentemente el botón "Build React" de
# scripts/flask_console.py (no depende de bash).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REACT_DIR="$REPO_DIR/react-src"

echo "=== Build React — BDDAT ==="
echo "Directorio: $REACT_DIR"
echo ""

cd "$REACT_DIR"

# Usar npm.cmd en Windows (PowerShell bloquea npm.ps1), npm en otros sistemas
if command -v npm.cmd &>/dev/null; then
    NPM="npm.cmd"
else
    NPM="npm"
fi

echo "Usando: $NPM"
echo ""

echo "--- npm install ---"
"$NPM" install

echo ""
echo "--- npm run build ---"
"$NPM" run build

echo ""
echo "=== Listo. Bundles + manifest.json en app/static/js/react/ ==="
