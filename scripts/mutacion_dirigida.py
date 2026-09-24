"""Mutación dirigida: ¿detecta un fichero de tests errores que ningún otro detecta? (#946)

Requiere los contextos de cobertura por test (ver `scripts/cobertura_por_test.py`):

    COVERAGE_CORE=ctrace pytest --cov=app --cov-context=test --cov-report=

Uso:

    python scripts/mutacion_dirigida.py tests/test_899_x.py
    python scripts/mutacion_dirigida.py tests/test_899_x.py --max 30 --max-tests-linea 20
    python scripts/mutacion_dirigida.py tests/test_899_x.py --solape

Para cada fichero candidato:
  1. Introduce errores a propósito (mutantes) en las líneas de app/ que ejecuta:
     comparaciones invertidas, and↔or, quitar `not`, True↔False, entero +1,
     `return X` → `return None`.
  2. Ejecuta los tests del candidato. Si alguno falla, el mutante queda detectado.
  3. Ejecuta los demás tests que pasan por esa línea. Si ninguno falla, el
     candidato lo detecta EN EXCLUSIVA: aporta una protección que nadie más da.
  Con --solape, en el paso 3 ejecuta cada fichero por separado y dice cuáles
  detectan cada mutante (más lento).

--max-tests-linea N descarta las líneas que ejecutan más de N tests. Sin él,
el muestreo cae sobre todo en código por el que pasa media suite (alta,
crear_fase) y el solape sale inflado.

Escribe el mutante EN DISCO y lo deshace en un `finally`; no lanzar dos a la vez
ni tocar el árbol mientras corre. Al terminar comprobar `git status`.
Un mutante que cuelga la suite (timeout) cuenta como detectado.
"""
import argparse
import ast
import collections
import json
import pathlib
import random
import sqlite3
import subprocess
import sys

from coverage.numbits import numbits_to_nums

REPO = pathlib.Path(__file__).resolve().parent.parent
TIMEOUT = 240


class Mutador(ast.NodeTransformer):
    """Cuenta (objetivo=-1) o aplica (objetivo=k) la k-ésima mutación de una línea."""
    CMP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt,
           ast.Gt: ast.LtE, ast.LtE: ast.Gt, ast.Is: ast.IsNot, ast.IsNot: ast.Is,
           ast.In: ast.NotIn, ast.NotIn: ast.In}

    def __init__(self, linea, objetivo=-1):
        self.linea, self.objetivo, self.i, self.desc = linea, objetivo, 0, None

    def _toca(self, desc):
        hit = self.i == self.objetivo
        if hit:
            self.desc = desc
        self.i += 1
        return hit

    def visit_Compare(self, n):
        self.generic_visit(n)
        op = type(n.ops[0])
        if n.lineno == self.linea and op in self.CMP and self._toca(f'{op.__name__}→{self.CMP[op].__name__}'):
            n.ops[0] = self.CMP[op]()
        return n

    def visit_BoolOp(self, n):
        self.generic_visit(n)
        if n.lineno == self.linea and self._toca('and↔or'):
            n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
        return n

    def visit_UnaryOp(self, n):
        self.generic_visit(n)
        if n.lineno == self.linea and isinstance(n.op, ast.Not) and self._toca('quitar not'):
            return n.operand
        return n

    def visit_Constant(self, n):
        if n.lineno != self.linea:
            return n
        if isinstance(n.value, bool) and self._toca('True↔False'):
            return ast.copy_location(ast.Constant(not n.value), n)
        if type(n.value) is int and self._toca(f'{n.value}→{n.value + 1}'):
            return ast.copy_location(ast.Constant(n.value + 1), n)
        return n

    def visit_Return(self, n):
        self.generic_visit(n)
        if (n.lineno == self.linea and n.value is not None
                and not (isinstance(n.value, ast.Constant) and n.value.value is None)
                and self._toca('return None')):
            n.value = None
        return n


def _arbol(path):
    return ast.parse(pathlib.Path(path).read_text(encoding='utf-8'))


def n_mutantes(path, linea):
    m = Mutador(linea)
    m.visit(_arbol(path))
    return m.i


def fuente_mutada(path, linea, k):
    m = Mutador(linea, objetivo=k)
    arbol = ast.fix_missing_locations(m.visit(_arbol(path)))
    return ast.unparse(arbol), m.desc


def algun_test_falla(tests):
    if not tests:
        return False
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'pytest', '-q', '-x', '-p', 'no:cacheprovider', *sorted(tests)],
            cwd=REPO, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return True
    ultima = (r.stdout.strip().splitlines() or [''])[-1]
    # El umbral de skips (#849) también da rc=1: mirar el resumen, no el código de salida.
    return 'failed' in ultima or 'error' in ultima


def cargar_contextos(ruta):
    """(ruta_app, línea) -> {test node id}, solo app/*.py."""
    con = sqlite3.connect(ruta)
    files = dict(con.execute('select id, path from file'))
    ctx = dict(con.execute('select id, context from context'))
    lineas = collections.defaultdict(set)
    for fid, cid, bits in con.execute('select file_id, context_id, numbits from line_bits'):
        p, c = files[fid], ctx[cid]
        if not c or not p.endswith('.py') or f'{REPO}/app/' not in p:
            continue
        t = c.split('|')[0]
        for n in numbits_to_nums(bits):
            lineas[(p, n)].add(t)
    return lineas


def con_mutante(path, linea, k, accion):
    original = pathlib.Path(path).read_bytes()
    try:
        src, _ = fuente_mutada(path, linea, k)
        pathlib.Path(path).write_text(src, encoding='utf-8')
        return accion()
    finally:
        pathlib.Path(path).write_bytes(original)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidato', help='fichero de tests, p. ej. tests/test_899_x.py')
    ap.add_argument('--max', type=int, default=30, help='mutantes como máximo (muestra aleatoria)')
    ap.add_argument('--max-tests-linea', type=int, default=None,
                    help='solo líneas ejecutadas por <= N tests en total')
    ap.add_argument('--solape', action='store_true', help='qué otros ficheros detectan cada mutante')
    ap.add_argument('--coverage', default=str(REPO / '.coverage'))
    ap.add_argument('--salida', default=None, help='JSON con el detalle por mutante')
    ap.add_argument('--semilla', type=int, default=946)
    a = ap.parse_args()

    lineas = cargar_contextos(a.coverage)
    cand = a.candidato
    propias = sorted(k for k, ts in lineas.items()
                     if any(t.startswith(cand + '::') for t in ts)
                     and (a.max_tests_linea is None or len(ts) <= a.max_tests_linea))
    if not propias:
        sys.exit(f'{cand}: ninguna línea de app/ con esos criterios (¿contextos con COVERAGE_CORE=ctrace?)')

    muestra = [(p, l, k) for p, l in propias for k in range(n_mutantes(p, l))]
    random.Random(a.semilla).shuffle(muestra)
    muestra = muestra[:a.max]

    resultados, solape = [], collections.Counter()
    for p, l, k in muestra:
        tests = lineas[(p, l)]
        suyos = {t for t in tests if t.startswith(cand + '::')}
        otros = tests - suyos
        por_fichero = collections.defaultdict(set)
        for t in otros:
            por_fichero[t.split('::')[0]].add(t)

        def evaluar():
            if not algun_test_falla(suyos):
                return False, None, []
            if a.solape:
                matan = sorted(f for f, ts in por_fichero.items() if algun_test_falla(ts))
                return True, bool(matan), matan
            return True, algun_test_falla(otros), []

        detecta, otros_detectan, matan = con_mutante(p, l, k, evaluar)
        solape.update(matan)
        fila = dict(fichero=str(pathlib.Path(p).relative_to(REPO)), linea=l,
                    mutacion=fuente_mutada(p, l, k)[1], tests_en_linea=len(tests),
                    detecta=detecta, otros_detectan=otros_detectan, ficheros_que_detectan=matan)
        resultados.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)

    detectados = sum(r['detecta'] for r in resultados)
    exclusivos = sum(1 for r in resultados if r['detecta'] and r['otros_detectan'] is False)
    print(f'\nRESUMEN {cand}: {len(resultados)} mutantes, detecta {detectados}, en exclusiva {exclusivos}')
    for f, c in solape.most_common(15):
        print(f'   {c:>3}/{detectados}  {f}')
    if a.salida:
        pathlib.Path(a.salida).write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
