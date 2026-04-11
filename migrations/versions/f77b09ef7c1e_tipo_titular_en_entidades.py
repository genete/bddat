"""tipo_titular en entidades

Revision ID: f77b09ef7c1e
Revises: c3d4e5f6a7b8
Create Date: 2026-03-26 20:30:51.173427

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f77b09ef7c1e'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('entidades',
        sa.Column(
            'tipo_titular',
            sa.String(30),
            nullable=True,
            comment='Categoría del administrado cuando actúa como titular. '
                    'NULL para entidades sin rol_titular. '
                    'Valores: GRAN_DISTRIBUIDORA | DISTRIBUIDOR_MENOR | PROMOTOR | ORGANISMO_PUBLICO | OTRO'
        ),
        schema='public'
    )
    # Entidades titulares existentes quedan como OTRO hasta revisión manual
    op.execute(
        "UPDATE public.entidades SET tipo_titular = 'OTRO' WHERE rol_titular = TRUE"
    )


def downgrade():
    op.drop_column('entidades', 'tipo_titular', schema='public')
