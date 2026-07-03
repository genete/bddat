"""activo en requisitos_documentales

Revision ID: b88f9bb4755b
Revises: 500_doc_borrador_firma
Create Date: 2026-07-03 14:57:52.124319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b88f9bb4755b'
down_revision = '500_doc_borrador_firma'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'requisitos_documentales',
        sa.Column('activo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        schema='public',
    )


def downgrade():
    op.drop_column('requisitos_documentales', 'activo', schema='public')
