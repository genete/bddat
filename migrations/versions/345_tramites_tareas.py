"""345_tramites_tareas — tabla catálogo de secuencias de tareas por trámite

Revision ID: 345_tramites_tareas
Revises: 350_seed_catalogo_plazos
Create Date: 2026-05-08

Issue #345 — PK compuesta (tipo_tramite_id, orden) para admitir que
ESPERAR_PLAZO aparezca dos veces en el mismo trámite (p.ej. ANUNCIO_BOE).
"""
from alembic import op
import sqlalchemy as sa


revision = '345_tramites_tareas'
down_revision = '350_seed_catalogo_plazos'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tramites_tareas',
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=False),
        sa.Column('orden', sa.SmallInteger(), nullable=False),
        sa.Column('tipo_tarea_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['tipo_tramite_id'], ['public.tipos_tramites.id'],
            name='fk_tram_tareas_tipo_tramite'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_tarea_id'], ['public.tipos_tareas.id'],
            name='fk_tram_tareas_tipo_tarea'
        ),
        sa.PrimaryKeyConstraint('tipo_tramite_id', 'orden', name='pk_tramites_tareas'),
        schema='public'
    )


def downgrade():
    op.drop_table('tramites_tareas', schema='public')
