"""1114_plazo_tablon_dup_habiles — el tablón de la DUP cuenta 30 días hábiles, no naturales

Revision ID: 1114_plazo_tablon_dup_habiles
Revises: 652_sentido_diagnostico
Create Date: 2026-11-15

Issue #1114. `416_seed_plazos_tablon` sembró el ESPERAR_PLAZO de TABLON_AYUNTAMIENTOS
como 30 `DIAS_NATURALES` con norma «Art. 125 RD 1955/2000», sin razonar la unidad. Las
dos cosas están mal.

Norma. TABLON_AYUNTAMIENTOS es la exposición en el tablón de los ayuntamientos de la
información pública de la DUP. Su base es el art. 144 del RD 1955/2000: la información
de la DUP se comunica a los ayuntamientos para su exposición al público «por igual
período de tiempo» que el de la información pública (treinta días). El art. 125 no
menciona a los ayuntamientos.

Unidad. El art. 144 no dice «naturales», y el art. 30.2 de la LPACAP fija que los plazos
por días son hábiles salvo que una **ley** o el Derecho de la UE disponga otro cómputo;
el RD 1955/2000 es un reglamento. Coherente con ANUNCIO_BOE, ANUNCIO_BOP y
ANUNCIO_PRENSA (la misma información pública), que ya están como 30 `DIAS_HABILES`:
el tablón era la única excepción.

Alcance. Una fila de `catalogo_plazos`, la de la DUP. El tablón ambiental (Ley 21/2013,
art. 9.4) no está modelado y no entra aquí.

Cómo se localiza la fila. Por su `camino`, nunca por `id` (los ids no son estables entre
instalaciones). Si no hay exactamente una fila se aborta: un UPDATE que afecta a cero
filas no da error y dejaría el catálogo equivocado sin avisar. No se toca la 416, que ya
está aplicada.
"""
from alembic import op
import sqlalchemy as sa


revision = '1114_plazo_tablon_dup_habiles'
down_revision = '652_sentido_diagnostico'
branch_labels = None
depends_on = None


_CAMINO = 'ANY/ANY/ANY/TABLON_AYUNTAMIENTOS/ESPERAR_PLAZO'


def _fijar(unidad, norma):
    resultado = op.get_bind().execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET plazo_unidad = :unidad,
            norma_origen = :norma
        WHERE camino = :camino
          AND tipo_elemento = 'TAREA'
    """), {'unidad': unidad, 'norma': norma, 'camino': _CAMINO})

    if resultado.rowcount != 1:
        raise RuntimeError(
            f"Se esperaba exactamente 1 fila de catalogo_plazos con camino "
            f"{_CAMINO!r} y hay {resultado.rowcount}; no se cambia nada."
        )


def upgrade():
    _fijar('DIAS_HABILES', 'Art. 144 RD 1955/2000')


def downgrade():
    _fijar('DIAS_NATURALES', 'Art. 125 RD 1955/2000')
