#!/usr/bin/env bash
# fix_miro_svg.sh — Corrige SVGs exportados de Miro para compatibilidad con Inkscape
#
# Problema: Miro exporta fill="transparent" que es CSS válido pero no SVG 1.1.
# Inkscape lo muestra como "undefined" y aplica relleno negro.
# Solución: reemplazar por fill="none" (valor correcto en SVG 1.1).
#
# Uso:
#   ./fix_miro_svg.sh              # corrige todos los .svg del directorio actual
#   ./fix_miro_svg.sh archivo.svg  # corrige un fichero concreto

set -e

FILES="${@:-*.svg}"

for f in $FILES; do
    [ -f "$f" ] || { echo "No encontrado: $f"; continue; }
    count=$(grep -o 'fill="transparent"' "$f" | wc -l)
    if [ "$count" -gt 0 ]; then
        sed -i 's/fill="transparent"/fill="none"/g' "$f"
        echo "✓ $f — $count reemplazos"
    else
        echo "  $f — sin cambios"
    fi
done
