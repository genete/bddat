"""899_cobertura_tecnica_version

Revision ID: 899_cobertura_tecnica_version
Revises: 899_documentos_requisito_ver
Create Date: 2026-09-10

`coberturas_item_tecnico.reformado_id` (ADR-044 §E bis, R4 #899) y la
sustitución del UniqueConstraint simple por dos índices únicos parciales.

A diferencia de `documentos_requisito`, aquí no hay flag de afección: todo
ítem técnico es solicitud+versión por definición (ADR §E bis — "la
verificación se predica del contenido del proyecto"), así que el mismo par
de índices se aplica sin distinción. `ON DELETE RESTRICT`, mismo criterio
que `fases.reformado_id`.
"""
from alembic import op
import sqlalchemy as sa

revision = '899_cobertura_tecnica_version'
down_revision = '899_documentos_requisito_ver'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'coberturas_item_tecnico',
        sa.Column(
            'reformado_id', sa.Integer(), nullable=True,
            comment='FK a REFORMADOS_PROYECTO (ADR-044 §E bis, R4 #899). NULL = versión '
                    'inicial. ON DELETE RESTRICT: mismo criterio que fases.reformado_id, '
                    'el corte no puede borrarse mientras una cobertura cuelgue de él.',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_coberturas_item_tecnico_reformado', 'coberturas_item_tecnico', 'reformados_proyecto',
        ['reformado_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )
    op.create_index(
        'idx_coberturas_item_tecnico_reformado', 'coberturas_item_tecnico', ['reformado_id'],
        schema='public',
    )

    op.drop_constraint(
        'uq_coberturas_item_tecnico_item_sol', 'coberturas_item_tecnico',
        schema='public', type_='unique',
    )
    op.create_index(
        'uq_coberturas_item_tecnico_no_afectado', 'coberturas_item_tecnico',
        ['item_tecnico_id', 'solicitud_id'],
        unique=True, schema='public',
        postgresql_where=sa.text('reformado_id IS NULL'),
    )
    op.create_index(
        'uq_coberturas_item_tecnico_por_version', 'coberturas_item_tecnico',
        ['item_tecnico_id', 'solicitud_id', 'reformado_id'],
        unique=True, schema='public',
    )


def downgrade():
    op.drop_index('uq_coberturas_item_tecnico_por_version', table_name='coberturas_item_tecnico',
                   schema='public')
    op.drop_index('uq_coberturas_item_tecnico_no_afectado', table_name='coberturas_item_tecnico',
                   schema='public')
    op.create_unique_constraint(
        'uq_coberturas_item_tecnico_item_sol', 'coberturas_item_tecnico',
        ['item_tecnico_id', 'solicitud_id'], schema='public',
    )

    op.drop_index('idx_coberturas_item_tecnico_reformado', table_name='coberturas_item_tecnico',
                   schema='public')
    op.drop_constraint('fk_coberturas_item_tecnico_reformado', 'coberturas_item_tecnico',
                        type_='foreignkey', schema='public')
    op.drop_column('coberturas_item_tecnico', 'reformado_id', schema='public')
