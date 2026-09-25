#!/usr/bin/env bash
# Ejecuta la prueba completa: arranca servidor.py sobre un directorio de datos
# limpio, lanza los escenarios de cliente_lo.py y para el servidor.
#
# Uso: scripts/poc_webdav/ejecutar.sh <dir_datos> [python_con_uno]
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
DATOS="${1:?falta dir_datos}"
PY="${2:-/usr/bin/python3}"
PUERTO=5077

rm -rf "$DATOS" && mkdir -p "$DATOS"
export NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost

"$PY" "$DIR/servidor.py" "$DATOS" "$DIR/../../app/data/plantillas_base/carta_base.odt" "$PUERTO" \
    > "$DATOS/servidor.log" 2>&1 &
SERVIDOR=$!
trap 'kill $SERVIDOR 2>/dev/null' EXIT

for _ in $(seq 1 20); do
    [ -f "$DATOS/urls.json" ] && break
    sleep 0.5
done

timeout 300 "$PY" "$DIR/cliente_lo.py" "$DATOS"
RC=$?
echo "cliente: exit=$RC"
exit $RC
