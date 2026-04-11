"""Proyecto — añadir es_modificacion

Revision ID: cae8e6d884af
Revises: 20e383031811
Create Date: 2026-02-28 08:58:19.383819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cae8e6d884af'
down_revision = '20e383031811'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'proyectos',
        sa.Column('es_modificacion', sa.Boolean(), nullable=False, server_default='false'),
        schema='public'
    )


def downgrade():
    op.drop_column('proyectos', 'es_modificacion', schema='public')
