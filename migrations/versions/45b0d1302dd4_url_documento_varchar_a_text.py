"""url_documento_varchar_a_text

Revision ID: 45b0d1302dd4
Revises: fd2bc02d2474
Create Date: 2026-03-07 20:28:27.334886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45b0d1302dd4'
down_revision = 'fd2bc02d2474'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('documentos', 'url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        schema='public')


def downgrade():
    op.alter_column('documentos', 'url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        schema='public')
