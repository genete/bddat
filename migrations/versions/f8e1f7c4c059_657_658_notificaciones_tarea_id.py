"""657_658_notificaciones_tarea_id

Revision ID: f8e1f7c4c059
Revises: 5156c1858a25
Create Date: 2026-07-23 18:05:49.538414

Corrige el schema de `notificaciones` (ADR-034, #657/#658): la tabla pasa de
"documento vitaminado" 1:1 (ADR-008) a tabla de seguimiento anclada a
`tarea_id`. `documento_id` y `resultado` pasan a NULLABLE (la fila puede vivir
sin documento/resultado mientras se espera el definitivo); se añade
`identificador_envio` (cotejo, #658) y `fecha_puesta_disposicion`; se renombra
`fecha_notificacion` a `fecha_resultado`.

UNIQUE(tarea_id) no está en el CREATE TABLE del ADR-034 §7, pero se añade
aquí: el hook de `editar_tarea` siempre hace upsert por `tarea_id` (nunca crea
una segunda fila para la misma tarea) — blinda esa invariante 1:1 a nivel BD.

Tabla vacía en desarrollo (0 filas) — sin backfill necesario.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8e1f7c4c059'
down_revision = '5156c1858a25'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('notificaciones',
        sa.Column('tarea_id', sa.Integer(), nullable=False),
        schema='public')
    op.create_foreign_key(
        'fk_notificaciones_tarea', 'notificaciones', 'tareas',
        ['tarea_id'], ['id'], source_schema='public', referent_schema='public',
        ondelete='CASCADE')
    op.create_unique_constraint(
        'uq_notificaciones_tarea_id', 'notificaciones', ['tarea_id'], schema='public')

    op.add_column('notificaciones',
        sa.Column('identificador_envio', sa.String(30), nullable=True),
        schema='public')

    op.add_column('notificaciones',
        sa.Column('fecha_puesta_disposicion', sa.Date(), nullable=False),
        schema='public')

    # documento_id pasa a NULLABLE (ADR-034 §3) — UNIQUE ya existía (uq_notificaciones_documento).
    op.alter_column('notificaciones', 'documento_id', nullable=True, schema='public')

    # resultado pasa a NULLABLE (ADR-034 §4) — el CHECK debe admitir NULL.
    op.drop_constraint('ck_notificaciones_resultado', 'notificaciones', schema='public', type_='check')
    op.alter_column('notificaciones', 'resultado', nullable=True, schema='public')
    op.create_check_constraint(
        'ck_notificaciones_resultado', 'notificaciones',
        "resultado IS NULL OR resultado IN ('CORRECTA', 'INCORRECTA')",
        schema='public')

    # fecha_notificacion → fecha_resultado (ADR-034 §5), nullable.
    op.alter_column('notificaciones', 'fecha_notificacion',
        new_column_name='fecha_resultado', nullable=True, schema='public')


def downgrade():
    op.alter_column('notificaciones', 'fecha_resultado',
        new_column_name='fecha_notificacion', nullable=False, schema='public')

    op.drop_constraint('ck_notificaciones_resultado', 'notificaciones', schema='public', type_='check')
    op.alter_column('notificaciones', 'resultado', nullable=False, schema='public')
    op.create_check_constraint(
        'ck_notificaciones_resultado', 'notificaciones',
        "resultado IN ('CORRECTA', 'INCORRECTA')",
        schema='public')

    op.alter_column('notificaciones', 'documento_id', nullable=False, schema='public')

    op.drop_column('notificaciones', 'fecha_puesta_disposicion', schema='public')
    op.drop_column('notificaciones', 'identificador_envio', schema='public')

    op.drop_constraint('uq_notificaciones_tarea_id', 'notificaciones', schema='public', type_='unique')
    op.drop_constraint('fk_notificaciones_tarea', 'notificaciones', schema='public', type_='foreignkey')
    op.drop_column('notificaciones', 'tarea_id', schema='public')
