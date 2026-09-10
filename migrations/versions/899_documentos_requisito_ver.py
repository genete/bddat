"""899_documentos_requisito_ver

Revision ID: 899_documentos_requisito_ver
Revises: 899_flag_afectado_reformado
Create Date: 2026-09-10

`documentos_requisito.reformado_id` (ADR-044 §E bis, R4 #899) y la sustitución
del UniqueConstraint simple por dos índices únicos parciales.

`NULL` es la versión inicial, o el único valor que usa un requisito no
afectado por reformado. `ON DELETE RESTRICT`, mismo criterio que
`fases.reformado_id` (R3, #895): el corte no puede borrarse mientras una
vinculación cuelgue de él.

Postgres no deduplica NULL en un índice único multi-columna, así que
`uq_documentos_requisito_req_sol` no basta por sí solo una vez que
`reformado_id` puede repetirse a NULL entre versiones: hacen falta dos
índices parciales — uno específico para el caso NULL y otro para el resto —
en vez de uno solo, patrón ya usado en `documentos_tarea`
(`migrations/versions/420_modelo_nm_documento_tarea.py`).

Sin backfill: la columna nace NULL en las filas existentes, que es
exactamente su significado (versión inicial).
"""
from alembic import op
import sqlalchemy as sa

revision = '899_documentos_requisito_ver'
down_revision = '899_flag_afectado_reformado'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'documentos_requisito',
        sa.Column(
            'reformado_id', sa.Integer(), nullable=True,
            comment='FK a REFORMADOS_PROYECTO (ADR-044 §E bis, R4 #899). NULL = versión '
                    'inicial, o único valor posible si el requisito no está afectado por '
                    'reformado. ON DELETE RESTRICT: mismo criterio que fases.reformado_id, '
                    'el corte no puede borrarse mientras una vinculación cuelgue de él.',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_documentos_requisito_reformado', 'documentos_requisito', 'reformados_proyecto',
        ['reformado_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )
    op.create_index(
        'idx_documentos_requisito_reformado', 'documentos_requisito', ['reformado_id'],
        schema='public',
    )

    op.drop_constraint(
        'uq_documentos_requisito_req_sol', 'documentos_requisito',
        schema='public', type_='unique',
    )
    op.create_index(
        'uq_documentos_requisito_no_afectado', 'documentos_requisito',
        ['requisito_id', 'solicitud_id'],
        unique=True, schema='public',
        postgresql_where=sa.text('reformado_id IS NULL'),
    )
    op.create_index(
        'uq_documentos_requisito_por_version', 'documentos_requisito',
        ['requisito_id', 'solicitud_id', 'reformado_id'],
        unique=True, schema='public',
    )


def downgrade():
    op.drop_index('uq_documentos_requisito_por_version', table_name='documentos_requisito',
                   schema='public')
    op.drop_index('uq_documentos_requisito_no_afectado', table_name='documentos_requisito',
                   schema='public')
    op.create_unique_constraint(
        'uq_documentos_requisito_req_sol', 'documentos_requisito',
        ['requisito_id', 'solicitud_id'], schema='public',
    )

    op.drop_index('idx_documentos_requisito_reformado', table_name='documentos_requisito',
                   schema='public')
    op.drop_constraint('fk_documentos_requisito_reformado', 'documentos_requisito',
                        type_='foreignkey', schema='public')
    op.drop_column('documentos_requisito', 'reformado_id', schema='public')
