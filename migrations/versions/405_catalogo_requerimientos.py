"""405_catalogo_requerimientos

Revision ID: 405_catalogo_requerimientos
Revises: 404_informacion_publica
Create Date: 2026-05-20

Issue #405 — tablas catalogo_requerimientos y requerimientos_tarea.
"""
from alembic import op
import sqlalchemy as sa

revision = '405_catalogo_requerimientos'
down_revision = '404_informacion_publica'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'catalogo_requerimientos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('texto', sa.Text(), nullable=False,
                  comment='Texto del defecto. Puede contener huecos {placeholder}'),
        sa.Column('categoria', sa.String(20), nullable=False,
                  comment='Categoría: documental | tecnica | administrativa | tasas'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true',
                  comment='False = archivado; no aparece en el selector'),
        sa.CheckConstraint(
            "categoria IN ('documental', 'tecnica', 'administrativa', 'tasas')",
            name='ck_catalogo_requerimientos_categoria'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_catalogo_requerimientos'),
        schema='public',
    )
    op.create_index('idx_catalogo_requerimientos_categoria',
                    'catalogo_requerimientos', ['categoria'], schema='public')
    op.execute("GRANT SELECT ON public.catalogo_requerimientos TO claude_desktop")

    op.create_table(
        'requerimientos_tarea',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tarea_id', sa.Integer(), nullable=False,
                  comment='FK tareas. Tarea ANALIZAR contenedora'),
        sa.Column('catalogo_requerimientos_id', sa.Integer(), nullable=True,
                  comment='FK catalogo_requerimientos. NULL si origen es texto libre'),
        sa.Column('texto_libre', sa.Text(), nullable=True,
                  comment='Texto manual. NULL si origen es catálogo'),
        sa.Column('orden', sa.Integer(), nullable=False,
                  comment='Posición 1-based en el listado del escrito'),
        sa.CheckConstraint(
            "(catalogo_requerimientos_id IS NOT NULL AND texto_libre IS NULL) OR "
            "(catalogo_requerimientos_id IS NULL AND texto_libre IS NOT NULL)",
            name='ck_requerimientos_tarea_exactamente_uno'
        ),
        sa.ForeignKeyConstraint(['tarea_id'], ['public.tareas.id'],
                                name='fk_requerimientos_tarea_tarea',
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['catalogo_requerimientos_id'],
                                ['public.catalogo_requerimientos.id'],
                                name='fk_requerimientos_tarea_catalogo'),
        sa.PrimaryKeyConstraint('id', name='pk_requerimientos_tarea'),
        schema='public',
    )
    op.create_index('idx_requerimientos_tarea_tarea',
                    'requerimientos_tarea', ['tarea_id'], schema='public')
    op.create_index('idx_requerimientos_tarea_catalogo',
                    'requerimientos_tarea', ['catalogo_requerimientos_id'], schema='public')
    op.execute("GRANT SELECT ON public.requerimientos_tarea TO claude_desktop")


def downgrade():
    op.drop_table('requerimientos_tarea', schema='public')
    op.drop_table('catalogo_requerimientos', schema='public')
