"""171_fk_tramites_tareas_documentos

FK compuesta que faltaba entre tramites_tareas_documentos y tramites_tareas
(#171): hoy tramites_tareas_documentos.orden_tarea es un entero suelto que
"debe coincidir" con tramites_tareas.orden solo por convención documentada,
sin que la BD lo garantice. Verificado sin huérfanos (0 filas inconsistentes)
antes de añadir la restricción.

Revision ID: e5d05d4df0f2
Revises: 8c29a9fcfc7e
Create Date: 2026-07-11 09:02:27.794815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5d05d4df0f2'
down_revision = '8c29a9fcfc7e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        'fk_ttd_tramite_tarea',
        'tramites_tareas_documentos',
        'tramites_tareas',
        ['tipo_tramite_id', 'orden_tarea'],
        ['tipo_tramite_id', 'orden'],
        source_schema='public',
        referent_schema='public',
    )


def downgrade():
    op.drop_constraint(
        'fk_ttd_tramite_tarea',
        'tramites_tareas_documentos',
        schema='public',
        type_='foreignkey',
    )
