"""665_entidad_abrev

Revision ID: 2af41834e5f9
Revises: ddb024625f6c
Create Date: 2026-07-16 19:14:38.772778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2af41834e5f9'
down_revision = 'ddb024625f6c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'entidades',
        sa.Column(
            'abrev',
            sa.String(20),
            nullable=True,
            comment='Abreviatura corta (organismos: usada en convención de carpetas ESFTT, ADR-032 #665)',
        ),
        schema='public',
    )


def downgrade():
    op.drop_column('entidades', 'abrev', schema='public')
