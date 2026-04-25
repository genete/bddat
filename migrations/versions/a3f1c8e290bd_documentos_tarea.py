"""Crear tabla documentos_tarea (issue #290 — INCORPORAR multi-doc v5.5)

Revision ID: a3f1c8e290bd
Revises: fd2bc02d2474
Create Date: 2026-04-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a3f1c8e290bd'
down_revision = '319_descripcion_regla_motor'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'documentos_tarea',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False,
                  comment='Identificador único autogenerado'),
        sa.Column('tarea_id', sa.Integer(), nullable=False,
                  comment='FK a TAREAS. Acto de incorporación'),
        sa.Column('documento_id', sa.Integer(), nullable=False,
                  comment='FK a DOCUMENTOS. Documento incorporado'),
        sa.ForeignKeyConstraint(['tarea_id'], ['public.tareas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['documento_id'], ['public.documentos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tarea_id', 'documento_id', name='uq_documentos_tarea'),
        schema='public'
    )
    op.create_index('idx_documentos_tarea_tarea', 'documentos_tarea', ['tarea_id'], schema='public')


def downgrade():
    op.drop_index('idx_documentos_tarea_tarea', table_name='documentos_tarea', schema='public')
    op.drop_table('documentos_tarea', schema='public')
