"""Cobertura por test: qué líneas de app/ cubre en exclusiva cada fichero de tests (#946).

Uso (desde la raíz, con la BD de tests preparada):

    COVERAGE_CORE=ctrace pytest --cov=app --cov-context=test --cov-report=
    python scripts/cobertura_por_test.py            # lee .coverage
    python scripts/cobertura_por_test.py ruta/.coverage

`COVERAGE_CORE=ctrace` es obligatorio en Python >= 3.12: el núcleo por defecto
(`sysmon`) registra cada línea solo la primera vez que se ejecuta en todo el
proceso, así que los contextos por test salen incompletos sin ningún aviso
(medido en #946: 797 contextos en vez de ~1.970).

Qué dice y qué no:
  - "exclusivas" = líneas de app/*.py que solo ejecuta ese fichero de tests.
  - Un fichero con 0 exclusivas no es un fichero que sobre: la cobertura de
    líneas dice qué se ejecuta, no qué se comprueba. Es un candidato a revisar
    a mano (o con mutación), no a borrar.
"""
import collections
import sqlite3
import sys

from coverage.numbits import numbits_to_nums


def main(ruta='.coverage'):
    con = sqlite3.connect(ruta)
    py = {i for i, p in con.execute('select id, path from file') if p.endswith('.py')}
    contexto = dict(con.execute('select id, context from context'))

    por_fichero = collections.defaultdict(set)
    n_tests = set()
    for fid, cid, bits in con.execute('select file_id, context_id, numbits from line_bits'):
        nombre = contexto[cid]
        if fid not in py or not nombre:
            continue
        test = nombre.split('|')[0]
        n_tests.add(test)
        por_fichero[test.split('::')[0]] |= {(fid, n) for n in numbits_to_nums(bits)}

    if len(n_tests) < 100:
        print(f'AVISO: solo {len(n_tests)} tests con contexto. ¿Faltó COVERAGE_CORE=ctrace?')

    cuenta = collections.Counter()
    for lineas in por_fichero.values():
        cuenta.update(lineas)

    filas = sorted(
        ((f, len(l), sum(1 for x in l if cuenta[x] == 1)) for f, l in por_fichero.items()),
        key=lambda r: (r[2], -r[1]),
    )
    print(f'{len(n_tests)} tests, {len(por_fichero)} ficheros con cobertura\n')
    print(f'{"exclusivas":>10} {"cubiertas":>9}  fichero')
    for f, n, u in filas:
        print(f'{u:>10} {n:>9}  {f}')
    print(f'\nficheros sin líneas exclusivas: {sum(1 for _, _, u in filas if u == 0)}')


if __name__ == '__main__':
    main(*sys.argv[1:])
