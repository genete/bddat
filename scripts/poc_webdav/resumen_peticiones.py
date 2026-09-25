"""Resume peticiones.jsonl de servidor.py: una línea por petición, sin el token.

Uso: python resumen_peticiones.py <dir_datos> [-v]   (-v: cuerpos XML)
"""
import json
import os
import sys

datos = sys.argv[1] if len(sys.argv) > 1 else './datos_poc'
detalle = '-v' in sys.argv
with open(os.path.join(datos, 'peticiones.jsonl')) as f:
    for n, linea in enumerate(f, 1):
        d = json.loads(linea)
        cab = {k: v for k, v in d['cabeceras'].items() if k != 'User-Agent'}
        partes = d['ruta'].split('/')
        ruta = '/dav/<token>/' + '/'.join(partes[3:]) if len(partes) > 3 else d['ruta']
        print(f"{n:3} {d['metodo']:<9} {d['estado']} {ruta:<50} {d['cuerpo_bytes']:>6} B {cab}")
        if detalle and d.get('cuerpo'):
            print(f"      → {d['cuerpo']}")
