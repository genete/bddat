"""Línea de órdenes del exportador: la reconstrucción a mano (ver `exportador`)."""
from __future__ import annotations

import argparse
import os
import sys

import almacen as libreria_almacen

from exportador import ManifiestoInvalido, cargar, exportar


def main(argv=None) -> int:
    # La consola de Windows puede no saber escribir un nombre de fichero: mejor un «?»
    # en el informe que perder el informe entero.
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')

    parser = argparse.ArgumentParser(
        prog='python -m exportador',
        description='Reconstruye el árbol de carpetas legible de los expedientes a partir de '
                    'sus manifiestos, leyendo los ficheros del almacén. No necesita BDDAT.')
    parser.add_argument('--almacen', required=True,
                        help='raíz del almacén (la carpeta que contiene ALMACEN.txt)')
    parser.add_argument('--destino', required=True,
                        help='carpeta donde se reconstruye; cada expediente va en su AT-N, '
                             'que no debe existir')
    parser.add_argument('manifiestos', nargs='+', metavar='MANIFIESTO',
                        help='fichero AT-N.json o carpeta de manifiestos (se recorre entera)')
    args = parser.parse_args(argv)

    rutas = []
    for entrada in args.manifiestos:
        if os.path.isdir(entrada):
            rutas.extend(_manifiestos_bajo(entrada))
        elif os.path.isfile(entrada):
            rutas.append(entrada)
        else:
            parser.error(f'no existe: {entrada}')
    if not rutas:
        parser.error('no hay ningún manifiesto AT-*.json en lo indicado')

    almacen = libreria_almacen.AlmacenDisco(args.almacen)
    expedientes_con_incidencias = 0
    copiados = 0
    for ruta in rutas:
        try:
            informe = exportar(cargar(ruta), args.destino, almacen)
        except ManifiestoInvalido as exc:
            print(f'{ruta}\n  INCIDENCIA: {exc}')
            expedientes_con_incidencias += 1
            continue
        _imprimir(informe)
        copiados += len(informe.copiados)
        if not informe.completo:
            expedientes_con_incidencias += 1

    print(f'\n{len(rutas)} manifiestos, {copiados} ficheros copiados, '
          f'{expedientes_con_incidencias} con incidencias. Destino: {os.path.abspath(args.destino)}')
    return 1 if expedientes_con_incidencias else 0


def _manifiestos_bajo(carpeta: str) -> list[str]:
    encontrados = []
    for actual, _dirs, ficheros in os.walk(carpeta):
        encontrados.extend(os.path.join(actual, f) for f in ficheros
                           if f.startswith('AT-') and f.endswith('.json'))
    return sorted(encontrados)


def _imprimir(informe) -> None:
    print(f'{informe.expediente}: {len(informe.copiados)} copiados, '
          f'{len(informe.enlaces)} enlaces, {len(informe.incidencias)} incidencias')
    for linea in informe.enlaces:
        print(f'  enlace (doc {linea.id}): {linea.texto}')
    for linea in informe.incidencias:
        quien = f'doc {linea.id}' if linea.id is not None else 'expediente'
        print(f'  INCIDENCIA ({quien}): {linea.texto}')


if __name__ == '__main__':
    sys.exit(main())
