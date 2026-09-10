"""899_flag_afectado_reformado

Revision ID: 899_flag_afectado_reformado
Revises: 895_regla_version_cubierta
Create Date: 2026-09-10

`requisitos_documentales.afectado_por_reformado` (ADR-044 §E bis, R4 #899).

Marcado a mano por el Supervisor, sin inferencia: no hay hoy ninguna propiedad
del requisito de la que "afecta a reformado" se derive. Por defecto False —
la mayoría de requisitos documentales no cambian con un reformado; el caso
que motiva el flag es la tasa (ver `tasa_impagada` en la migración siguiente
de este mismo issue).
"""
from alembic import op
import sqlalchemy as sa

revision = '899_flag_afectado_reformado'
down_revision = '895_regla_version_cubierta'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'requisitos_documentales',
        sa.Column(
            'afectado_por_reformado', sa.Boolean(), nullable=False,
            server_default=sa.text('false'),
            comment='ADR-044 §E bis (R4 #899). Marcado a mano por el Supervisor — no '
                    'se infiere de ninguna otra propiedad del requisito. False: la '
                    'cobertura es global por solicitud, la misma vinculación vale para '
                    'todas las versiones del proyecto. True: un reformado puede exigir '
                    'una vinculación propia para la versión vigente (documentos_requisito. '
                    'reformado_id), aunque la de la versión inicial siga contando si nada '
                    'cambió (caso de origen: la tasa y su complementaria).',
        ),
        schema='public',
    )


def downgrade():
    op.drop_column('requisitos_documentales', 'afectado_por_reformado', schema='public')
