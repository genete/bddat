"""899_requerimientos_version

Revision ID: 899_requerimientos_version
Revises: 899_cobertura_tecnica_version
Create Date: 2026-09-10

`requerimientos_tarea.reformado_id` (ADR-044 §E bis, R4 #899).

Solo la columna, sin rellenarla. Es atributo de nacimiento, nunca clave —
sin índice único—, y el shuttle (`post_requerimientos`,
`app/routes/api_expedientes.py`) sigue guardando hoy por reemplazo total
(`DELETE` + `INSERT` masivo en cada guardado, #884 todavía sin empezar):
fijar aquí la versión de nacimiento se perdería en el siguiente guardado.
Se rellena cuando #884 cambie el endpoint a merge por `id`.
"""
from alembic import op
import sqlalchemy as sa

revision = '899_requerimientos_version'
down_revision = '899_cobertura_tecnica_version'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'requerimientos_tarea',
        sa.Column(
            'reformado_id', sa.Integer(), nullable=True,
            comment='FK a REFORMADOS_PROYECTO (ADR-044 §E bis, R4 #899). Atributo de '
                    'nacimiento, nunca clave. Todavía sin rellenar: depende de que #884 '
                    'cambie el shuttle a merge por id — ver docstring de la clase.',
        ),
        schema='public',
    )
    op.create_foreign_key(
        'fk_requerimientos_tarea_reformado', 'requerimientos_tarea', 'reformados_proyecto',
        ['reformado_id'], ['id'],
        source_schema='public', referent_schema='public',
        ondelete='RESTRICT',
    )
    op.create_index(
        'idx_requerimientos_tarea_reformado', 'requerimientos_tarea', ['reformado_id'],
        schema='public',
    )


def downgrade():
    op.drop_index('idx_requerimientos_tarea_reformado', table_name='requerimientos_tarea',
                   schema='public')
    op.drop_constraint('fk_requerimientos_tarea_reformado', 'requerimientos_tarea',
                        type_='foreignkey', schema='public')
    op.drop_column('requerimientos_tarea', 'reformado_id', schema='public')
