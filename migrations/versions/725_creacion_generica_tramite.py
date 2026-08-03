"""725_creacion_generica_tramite — centraliza _CODIGOS_TRASLADO (#725)

Revision ID: 725_creacion_generica_tramite
Revises: 725_seed_fases_tramites
Create Date: 2026-08-03

Issue #725 — `_CODIGOS_TRASLADO` estaba triplicado (api_bc.py,
mutaciones_arbol.py, tipos_creables.py), tres copias del mismo frozenset
mantenidas a mano. Se centraliza en una columna de catálogo:
`tipos_tramites.creacion_generica` (default True). Los trámites de traslado
(CONSULTA_TRASLADO_ORGANISMO/TITULAR) se crean desde su propia acción de
organismo (api_bc.crear_traslado), no por la vía genérica — quedan en False.
"""
from alembic import op
import sqlalchemy as sa


revision = '725_creacion_generica_tramite'
down_revision = '725_seed_fases_tramites'
branch_labels = None
depends_on = None

_CODIGOS_NO_GENERICOS = ('CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR')


def upgrade():
    op.add_column(
        'tipos_tramites',
        sa.Column('creacion_generica', sa.Boolean(), nullable=False, server_default='true',
                   comment='False si este trámite se crea desde una acción dedicada, no por la despensa genérica'),
        schema='public',
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE public.tipos_tramites SET creacion_generica = false WHERE codigo = ANY(:codigos)"),
        {'codigos': list(_CODIGOS_NO_GENERICOS)},
    )


def downgrade():
    op.drop_column('tipos_tramites', 'creacion_generica', schema='public')
