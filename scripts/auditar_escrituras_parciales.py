# -*- coding: utf-8 -*-
"""Audita el patrón "campo ausente = vaciar campo" en las rutas de escritura (#832).

QUÉ BUSCA
---------
Una petición HTTP tiene tres estados posibles para cada campo:

    ausente           el cliente no habla de ese campo
    presente y vacío  el usuario lo ha vaciado a propósito
    presente          con valor

`request.form.get('x') or None` colapsa los dos primeros en `None`, así que
cualquier cuerpo parcial borra en silencio lo que no menciona. Ese defecto vació
`tipo_expediente_id`, `ia_id`, tres flags técnicos y la tensión de tres
expedientes, y las observaciones de tres solicitudes (#832).

Este script recorre TODAS las funciones de `app/` —handlers de ruta y también los
helpers tipo `_rellenar_*`, que es donde este repo suele poner la escritura y que
un grep por rutas se salta— y clasifica cada asignación
`objeto.campo = <algo leído del cuerpo de la petición>` según qué pasa si el
cliente no envía ese campo:

    BORRA     queda NULL / ''            vaciado silencioso
    FALSEA    queda False                checkbox: legítimo en formulario completo,
                                         destructivo en cuerpo parcial
    CONSERVA  mantiene el valor previo   a costa de impedir el vaciado deliberado
    RUIDOSO   request.form['x'] sin get  KeyError: falla, no corrompe
    ?         revisar a mano

Marca además la naturaleza de la función: CREA (instancia un modelo) o EDITA
(recupera uno existente). El vaciado silencioso solo es un bug en las de EDITA.

CÓMO LEER EL RESULTADO
----------------------
Que una función aparezca en el bloque A no significa que haya causado daño: si su
único cliente es un formulario completo, el patrón está pero no lo dispara nadie.
Para saber si ha sangrado, mirar `xmin` de las filas sospechosas en PostgreSQL
(transacción de la última escritura) y comprobar si fueron reescritas después de
crearse. Ver el diagnóstico de #832.

ARREGLO
-------
`app/utils/formularios.py` — marcador AUSENTE y aplicadores que solo escriben si
el campo viaja; centinela `_form_completo` para las casillas.

Uso:
    venv/Scripts/python.exe scripts/auditar_escrituras_parciales.py
    venv/Scripts/python.exe scripts/auditar_escrituras_parciales.py --salida informe.txt
"""
import argparse
import ast
import io
import os
import sys

RAIZ_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ_APP = os.path.join(RAIZ_REPO, 'app')

LECTURA_PETICION = ('request.form', 'request.json', 'request.values',
                    'data.get(', 'datos.get(', 'payload.get(', 'body.get(',
                    'data[', 'datos[')


def _fuente(nodo, lineas):
    """Texto original de un nodo, colapsado a una línea."""
    ini = nodo.lineno - 1
    fin = getattr(nodo, 'end_lineno', nodo.lineno)
    return ' '.join(l.strip() for l in lineas[ini:fin]).strip()


def _clasifica(txt):
    """Qué le pasa al campo si el cliente no lo envía."""
    der = txt.split('=', 1)[-1]
    if ('request.form[' in der or 'data[' in der or 'datos[' in der) and '.get(' not in der:
        return 'RUIDOSO'
    if ' in request.form' in der or ' in data' in der or ' in datos' in der:
        return 'FALSEA'
    if "== 'on'" in der or '== "on"' in der or "== 'true'" in der:
        return 'FALSEA'
    if ' or None' in der or 'else None' in der:
        return 'BORRA'
    if ' or ' in der:
        # `... or objeto.campo` conserva el valor previo; `... or 0` / `or ''` no.
        cola = der.split(' or ')[-1].strip()
        if '.' in cola and 'request' not in cola and 'data' not in cola:
            return 'CONSERVA'
        return 'BORRA'
    if '.get(' in der:
        return 'BORRA'
    return '?'


def _naturaleza(cuerpo):
    edita = ('.get_or_404(' in cuerpo) or ('.query.get(' in cuerpo) or ('.query.filter' in cuerpo)
    crea = 'db.session.add(' in cuerpo
    if crea and not edita:
        return 'CREA'
    if crea and edita:
        return 'MIXTA'
    return 'EDITA'


def _rutas_de(fn):
    """Rutas declaradas en los decoradores, si las hay."""
    out = []
    for dec in fn.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) \
                and dec.func.attr == 'route':
            r = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else '?'
            met = ''
            for kw in dec.keywords:
                if kw.arg == 'methods' and isinstance(kw.value, (ast.List, ast.Tuple)):
                    met = ','.join(e.value for e in kw.value.elts if isinstance(e, ast.Constant))
            out.append(f"{r} [{met}]")
    return '; '.join(out)


def recopilar(raiz=RAIZ_APP):
    """[(fichero, función, rutas, naturaleza, [(línea, clase, destino), ...]), ...]"""
    filas = []
    for base, _dirs, ficheros in os.walk(raiz):
        for nombre in ficheros:
            if not nombre.endswith('.py'):
                continue
            ruta_fich = os.path.join(base, nombre)
            with io.open(ruta_fich, encoding='utf-8') as f:
                texto = f.read()
            lineas = texto.splitlines()
            try:
                arbol = ast.parse(texto)
            except SyntaxError:
                continue
            for fn in [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)]:
                cuerpo = '\n'.join(lineas[fn.lineno - 1:getattr(fn, 'end_lineno', fn.lineno)])
                asigns = []
                for nodo in ast.walk(fn):
                    if not isinstance(nodo, ast.Assign):
                        continue
                    if not any(isinstance(t, ast.Attribute) for t in nodo.targets):
                        continue
                    txt = _fuente(nodo, lineas)
                    if not any(p in txt for p in LECTURA_PETICION):
                        continue
                    asigns.append((nodo.lineno, _clasifica(txt),
                                   _fuente(nodo.targets[0], lineas)))
                if asigns:
                    filas.append((
                        os.path.relpath(ruta_fich, RAIZ_REPO).replace('\\', '/'),
                        fn.name, _rutas_de(fn), _naturaleza(cuerpo), asigns,
                    ))
    return filas


def informe(filas, escribir):
    peligrosas = [f for f in filas
                  if f[3] in ('EDITA', 'MIXTA')
                  and any(a[1] in ('BORRA', 'FALSEA') for a in f[4])]

    escribir(f"Funciones que escriben en modelos desde el cuerpo de la peticion: {len(filas)}")
    escribir(f"Asignaciones totales: {sum(len(f[4]) for f in filas)}")
    escribir(f"Funciones de EDICION con vaciado por omision: {len(peligrosas)}")
    escribir('')
    escribir('=' * 96)
    escribir('A) EDICION CON VACIADO SILENCIOSO POR OMISION  <- mismo defecto que #832')
    escribir('=' * 96)
    for fich, fn, rutas, nat, asigns in sorted(peligrosas):
        escribir(f"\n-- {fich} :: {fn}()   {rutas or '(helper, sin ruta propia)'}   [{nat}]")
        for lineno, clase, destino in asigns:
            marca = '  <<<' if clase in ('BORRA', 'FALSEA') else ''
            escribir(f"   {lineno:>5}  {clase:<9} {destino}{marca}")
    escribir('')
    escribir('=' * 96)
    escribir('B) RESTO (creacion / conserva / ruidoso)')
    escribir('=' * 96)
    for fich, fn, rutas, nat, asigns in sorted(f for f in filas if f not in peligrosas):
        escribir(f"\n-- {fich} :: {fn}()   {rutas or '(helper)'}   [{nat}]")
        for lineno, clase, destino in asigns:
            escribir(f"   {lineno:>5}  {clase:<9} {destino}")
    return len(peligrosas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--salida', help='fichero donde escribir el informe (por defecto, stdout)')
    args = ap.parse_args()

    filas = recopilar()
    if args.salida:
        with io.open(args.salida, 'w', encoding='utf-8') as f:
            n = informe(filas, lambda s: f.write(s + '\n'))
        print(f"Informe escrito en {args.salida}")
        print(f"Funciones de EDICION con vaciado por omision: {n}")
    else:
        # La consola de Windows es cp1252 y el informe lleva rutas y nombres con acentos.
        sys.stdout.reconfigure(encoding='utf-8')
        informe(filas, print)


if __name__ == '__main__':
    main()
