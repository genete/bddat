"""637_fix_etiqueta_tramite_publicar_existe

Revision ID: 073a0df4493f
Revises: 4ebb96cd6bef
Create Date: 2026-07-15 14:57:41.559793

Issue #637 (checklist heredado de #638) — la etiqueta sembrada por
b4417076e504 ("Trámite PUBLICAR existe en fase RESOLUCIÓN") es engañosa:
no existe ningún tipo_tramite con código PUBLICAR, el real es PUBLICACION
(`app/services/variables/calculado.py::tramite_publicar_existe` comprueba
`codigo == 'PUBLICACION'`). Corrección textual aplazada a propósito hasta
que existiera un CRUD (#637) — se aplica ahora vía migración, no solo en la
BD de desarrollo, para que cualquier entorno que reconstruya desde
migraciones reciba el texto correcto.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '073a0df4493f'
down_revision = '4ebb96cd6bef'
branch_labels = None
depends_on = None

_ANTES    = 'Trámite PUBLICAR existe en fase RESOLUCIÓN'
_DESPUES  = 'Trámite de tipo PUBLICACION existe en fase RESOLUCIÓN'


def upgrade():
    op.execute(sa.text("""
        UPDATE public.catalogo_variables SET etiqueta = :despues
        WHERE nombre = 'tramite_publicar_existe'
    """).bindparams(despues=_DESPUES))


def downgrade():
    op.execute(sa.text("""
        UPDATE public.catalogo_variables SET etiqueta = :antes
        WHERE nombre = 'tramite_publicar_existe'
    """).bindparams(antes=_ANTES))
