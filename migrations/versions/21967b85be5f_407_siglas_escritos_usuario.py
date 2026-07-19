"""407_siglas_escritos_usuario

Revision ID: 21967b85be5f
Revises: 2af41834e5f9
Create Date: 2026-07-19 09:31:05.095737

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21967b85be5f'
down_revision = '2af41834e5f9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'usuarios',
        sa.Column(
            'siglas_escritos',
            sa.String(20),
            nullable=True,
            comment='Siglas históricas del usuario (p.ej. CLG), distintas de SIGLAS. '
                    'Token para el firmante en plantillas de escritos (#407)',
        ),
        schema='public',
    )


def downgrade():
    op.drop_column('usuarios', 'siglas_escritos', schema='public')
