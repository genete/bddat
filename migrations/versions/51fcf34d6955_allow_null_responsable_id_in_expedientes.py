"""allow_null_responsable_id_in_expedientes

Revision ID: 51fcf34d6955
Revises: 3daee4b13400
Create Date: 2026-01-28 19:58:55.258731

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51fcf34d6955'
down_revision = '3daee4b13400'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('expedientes', 'responsable_id',
                    existing_type=sa.INTEGER(),
                    nullable=True,
                    schema='public')


def downgrade():
    op.alter_column('expedientes', 'responsable_id',
                    existing_type=sa.INTEGER(),
                    nullable=False,
                    schema='public')