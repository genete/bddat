"""
auditar_catalogo_plazos.py — Detecta colisiones de camino en catalogo_plazos (#786)

Aplica sobre el catálogo ya existente en BD la misma regla que la validación de
alta/edición del CRUD (app/modules/catalogo_plazos/routes.py, _validar_colision_camino):

  - Duplicado ciego: dos o más filas activas con el mismo `camino` y ninguna
    tiene condiciones en condiciones_plazo → la de mayor orden/id queda siempre
    inerte, sin aviso en tiempo de ejecución. ERROR.
  - Solape condicionado: dos o más filas activas con el mismo `camino` donde al
    menos una tiene condiciones → puede ser el patrón legítimo condición+reserva
    (CONSULTA_SEPARATA, CONSULTAS) o un solape legal real no discriminable en
    general (operadores arbitrarios de condiciones_plazo). AVISO — requiere
    revisión manual.

Pensado para el administrador de sistema, fuera de la interfaz de Supervisor: el
CRUD ya bloquea/avisa en el momento del alta o edición (#786), así que si algo
aparece aquí es porque se coló por fuera (migración, SQL directo, dato anterior
a la validación) — la corrección se hace directamente en BD (desactivar, editar
o borrar la fila sobrante), no desde la aplicación.

Uso:
    cd /d/BDDAT
    source venv/Scripts/activate
    python scripts/auditar_catalogo_plazos.py

Código de salida: 1 si hay algún duplicado ciego, 0 en caso contrario (los
avisos de solape no afectan al código de salida — son revisión, no error).
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.catalogo_plazos import CatalogoPlazo

app = create_app()


def main():
    with app.app_context():
        entradas = (
            CatalogoPlazo.query
            .filter_by(activo=True)
            .order_by(CatalogoPlazo.camino, CatalogoPlazo.orden, CatalogoPlazo.id)
            .all()
        )

        por_camino = defaultdict(list)
        for entrada in entradas:
            por_camino[entrada.camino].append(entrada)

        errores = []
        avisos = []
        for camino, filas in por_camino.items():
            if len(filas) < 2:
                continue
            sin_condicion = [f for f in filas if not f.condiciones]
            if len(sin_condicion) >= 2:
                ids = ', '.join(f'#{f.id}' for f in sin_condicion)
                errores.append(
                    f'{camino}: {len(sin_condicion)} filas activas sin condiciones ({ids}) '
                    '- duplicado ciego, quedan inertes todas menos la de menor orden/id.'
                )
            elif any(f.condiciones for f in filas):
                ids = ', '.join(f'#{f.id}' for f in filas)
                avisos.append(
                    f'{camino}: {len(filas)} filas activas comparten camino con condiciones '
                    f'de por medio ({ids}) - revisar que sean mutuamente excluyentes.'
                )

        print(f'Comprobadas {len(entradas)} entradas activas en {len(por_camino)} caminos distintos.\n')

        if errores:
            print(f'ERRORES - duplicado ciego ({len(errores)}):')
            for e in errores:
                print(f'  x {e}')
        else:
            print('Sin duplicados ciegos.')

        print()
        if avisos:
            print(f'AVISOS - posible solape condicionado ({len(avisos)}):')
            for a in avisos:
                print(f'  ! {a}')
        else:
            print('Sin solapes detectados.')

        sys.exit(1 if errores else 0)


if __name__ == '__main__':
    main()
