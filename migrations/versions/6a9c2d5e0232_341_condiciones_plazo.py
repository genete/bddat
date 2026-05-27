"""341_condiciones_plazo

Revision ID: 6a9c2d5e0232
Revises: c9379e09ae01
Create Date: 2026-04-30 08:28:10.821436

Issue #341 — Condiciones de aplicabilidad en catalogo_plazos:
  - Columna 'orden' en catalogo_plazos (server_default=100; las 7 entradas
    existentes quedan con orden=100, comportando como fallback general).
  - Índice idx_catalogo_plazos_tipo_orden para ordenación por prioridad.
  - Tabla condiciones_plazo: condiciones AND para selección de entrada.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a9c2d5e0232'
down_revision = 'c9379e09ae01'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Columna orden en catalogo_plazos
    op.add_column(
        'catalogo_plazos',
        sa.Column(
            'orden', sa.Integer, nullable=False,
            server_default='100',
            comment='Prioridad de selección: menor primero. No unique. '
                    'Fallback sin condiciones: 100.',
        ),
        schema='public',
    )

    # 2. Índice compuesto para la consulta de selección (sesión 4)
    op.create_index(
        'idx_catalogo_plazos_tipo_orden',
        'catalogo_plazos',
        ['tipo_elemento', 'tipo_elemento_id', 'orden'],
        schema='public',
    )

    # 3. Tabla condiciones_plazo
    op.create_table(
        'condiciones_plazo',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            'catalogo_plazo_id', sa.Integer, nullable=False,
            comment='FK a catalogo_plazos — entrada condicionada',
        ),
        sa.Column(
            'variable_id', sa.Integer, nullable=False,
            comment='FK a catalogo_variables — variable evaluada',
        ),
        sa.Column(
            'operador', sa.String(20), nullable=False,
            comment='Operador de comparación',
        ),
        sa.Column(
            'valor', sa.JSON, nullable=True,
            comment='Valor de referencia. Lista para IN/BETWEEN, None para IS_NULL/NOT_NULL',
        ),
        sa.Column(
            'orden', sa.Integer, nullable=False,
            server_default='1',
            comment='Orden de evaluación dentro de la entrada',
        ),
        sa.ForeignKeyConstraint(
            ['catalogo_plazo_id'], ['public.catalogo_plazos.id'],
            name='fk_condiciones_plazo_catalogo', ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['variable_id'], ['public.catalogo_variables.id'],
            name='fk_condiciones_plazo_variable', ondelete='RESTRICT',
        ),
        sa.CheckConstraint(
            "operador IN ('EQ','NEQ','IN','NOT_IN','IS_NULL','NOT_NULL',"
            "'GT','GTE','LT','LTE','BETWEEN','NOT_BETWEEN')",
            name='ck_condiciones_plazo_operador',
        ),
        sa.Index('idx_condiciones_plazo_catalogo', 'catalogo_plazo_id'),
        sa.Index('idx_condiciones_plazo_variable', 'variable_id'),
        schema='public',
    )


def downgrade():
    op.drop_table('condiciones_plazo', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_orden',
                  table_name='catalogo_plazos', schema='public')
    op.drop_column('catalogo_plazos', 'orden', schema='public')
