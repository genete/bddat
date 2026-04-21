#!/usr/bin/env bash
# Compila el bundle React para Flask.
# Salida: app/static/js/react/diagrama-esftt.iife.js + diagrama-esftt.css

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REACT_DIR="$REPO_DIR/react-diagramas"

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
echo "=== Listo. Ficheros generados en app/static/js/react/ ==="
