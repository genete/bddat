"""Revision modelo Documento: drop origen, drop nombre_display, fecha_administrativa nullable

Revision ID: fd2bc02d2474
Revises: 09855a1393f6
Create Date: 2026-03-05 19:14:10.418328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd2bc02d2474'
down_revision = '09855a1393f6'
branch_labels = None
depends_on = None


def upgrade():
    # Eliminar campo origen (semántica ambigua, procedencia va en tablas cualificadoras)
    op.drop_column('documentos', 'origen', schema='public')

    # Eliminar campo nombre_display (deducible de la URL, una sola fuente de la verdad)
    op.drop_column('documentos', 'nombre_display', schema='public')

    # Hacer nullable fecha_administrativa (NULL = pendiente de revisión o sin valor jurídico propio)
    op.alter_column('documentos', 'fecha_administrativa',
                    existing_type=sa.Date(),
                    nullable=True,
                    schema='public')


def downgrade():
    op.alter_column('documentos', 'fecha_administrativa',
                    existing_type=sa.Date(),
                    nullable=False,
                    schema='public')

    op.add_column('documentos',
                  sa.Column('nombre_display', sa.String(200), nullable=True,
                            comment='Nombre legible para mostrar en interfaz'),
                  schema='public')

    op.add_column('documentos',
                  sa.Column('origen', sa.String(100), nullable=True,
                            comment='Procedencia del documento (EXTERNO, INTERNO, ORGANISMO_X, etc.)'),
                  schema='public')
