"""merge_heads_seed_catalogo_base

Revision ID: merge_heads_seed_catalogo_base
Revises: e292f71a07a5, seed_catalogo_base
Create Date: 2026-05-17

Fusiona la rama paralela seed_catalogo_base con la cadena principal
para que haya un único head antes de las migraciones de #377.
"""
from alembic import op
import sqlalchemy as sa

revision = 'merge_heads_seed_catalogo_base'
down_revision = ('e292f71a07a5', 'seed_catalogo_base')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
