"""725_fases_tramites — tabla de vocabulario fase→trámite (ADR-037)

Revision ID: 725_fases_tramites
Revises: f8e1f7c4c059
Create Date: 2026-08-03

Issue #725, ADR-037 — Recrea (con semántica distinta a la whitelist eliminada
en #387/ADR-007) el vocabulario de qué tipos de trámite pertenecen a qué tipos
de fase. No gatea permiso: es taxonomía ESFTT, consultada por el listado
(despensa) y por la categoría de bloqueo estructural escapable — nunca por
reglas_motor.

Sin columna de orden: no hay caso de uso confirmado (los trámites de una fase
son mayoritariamente paralelos); se añade si aparece uno real.
"""
from alembic import op
import sqlalchemy as sa


revision = '725_fases_tramites'
down_revision = 'f8e1f7c4c059'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'fases_tramites',
        sa.Column('tipo_fase_id', sa.Integer(), nullable=False),
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=False),
        sa.Column('cardinalidad_maxima', sa.SmallInteger(), nullable=True,
                   comment='NULL = ilimitada'),
        sa.ForeignKeyConstraint(
            ['tipo_fase_id'], ['public.tipos_fases.id'],
            name='fk_fases_tramites_tipo_fase'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_tramite_id'], ['public.tipos_tramites.id'],
            name='fk_fases_tramites_tipo_tramite'
        ),
        sa.PrimaryKeyConstraint('tipo_fase_id', 'tipo_tramite_id', name='pk_fases_tramites'),
        schema='public'
    )


def downgrade():
    op.drop_table('fases_tramites', schema='public')
