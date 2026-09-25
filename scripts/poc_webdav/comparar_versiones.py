"""Compara dos versiones del almacén entrada a entrada del ZIP del .odt.

Sirve para ver qué reescribe LibreOffice al guardar sin cambios.
Uso: python comparar_versiones.py <dir_datos> <n_a> <n_b>
"""
import hashlib
import json
import os
import sys
import zipfile

datos, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
with open(os.path.join(datos, 'versiones.json')) as f:
    vs = {v['n']: v for v in json.load(f)['1']['versiones']}


def entradas(n):
    sha = vs[n]['sha256']
    with zipfile.ZipFile(os.path.join(datos, 'blobs', sha[:2], sha)) as z:
        return {i.filename: hashlib.sha256(z.read(i)).hexdigest() for i in z.infolist()}


ea, eb = entradas(a), entradas(b)
for nombre in sorted(set(ea) | set(eb)):
    if ea.get(nombre) != eb.get(nombre):
        print(f'distinta: {nombre}')
print(f'iguales: {sum(1 for k in ea if ea.get(k) == eb.get(k))} de {len(set(ea) | set(eb))}')
