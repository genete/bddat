"""679_requerimientos_solicitud

Revision ID: 5156c1858a25
Revises: 21967b85be5f
Create Date: 2026-07-22

Issue #679 (ADR-033 §7) — eleva el eje libre de defectos de `tarea_id` a
`solicitud_id` (mismo criterio que `documentos_requisito` y
`coberturas_item_tecnico`) y añade `resuelto` — marca manual del técnico,
porque un requerimiento libre no tiene contra qué casar automáticamente.
"""
from alembic import op
import sqlalchemy as sa

revision = '5156c1858a25'
down_revision = '21967b85be5f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'requerimientos_tarea',
        sa.Column('solicitud_id', sa.Integer(), nullable=True,
                  comment='FK a solicitudes — solicitud en la que se registra el requerimiento'),
        schema='public',
    )
    op.execute("""
        UPDATE public.requerimientos_tarea rt
        SET solicitud_id = f.solicitud_id
        FROM public.tareas t
        JOIN public.tramites tr ON tr.id = t.tramite_id
        JOIN public.fases f ON f.id = tr.fase_id
        WHERE rt.tarea_id = t.id
    """)
    op.alter_column('requerimientos_tarea', 'solicitud_id', nullable=False, schema='public')
    op.create_foreign_key(
        'fk_requerimientos_tarea_solicitud', 'requerimientos_tarea', 'solicitudes',
        ['solicitud_id'], ['id'], source_schema='public', referent_schema='public',
        ondelete='CASCADE',
    )
    op.create_index('idx_requerimientos_tarea_solicitud',
                     'requerimientos_tarea', ['solicitud_id'], schema='public')

    op.drop_index('idx_requerimientos_tarea_tarea', table_name='requerimientos_tarea', schema='public')
    op.drop_constraint('fk_requerimientos_tarea_tarea', 'requerimientos_tarea',
                        schema='public', type_='foreignkey')
    op.drop_column('requerimientos_tarea', 'tarea_id', schema='public')

    op.add_column(
        'requerimientos_tarea',
        sa.Column('resuelto', sa.Boolean(), nullable=False, server_default='false',
                  comment='Marca manual del técnico: requerimiento libre cerrado. Un '
                          'requerimiento libre no tiene contra qué casar automáticamente '
                          '(a diferencia de documental/técnico), su cierre es un juicio.'),
        schema='public',
    )


def downgrade():
    op.drop_column('requerimientos_tarea', 'resuelto', schema='public')

    op.add_column(
        'requerimientos_tarea',
        sa.Column('tarea_id', sa.Integer(), nullable=True,
                  comment='FK a TAREAS. Tarea ANALIZAR contenedora'),
        schema='public',
    )
    op.execute("""
        UPDATE public.requerimientos_tarea rt
        SET tarea_id = (
            SELECT t.id
            FROM public.tareas t
            JOIN public.tramites tr ON tr.id = t.tramite_id
            JOIN public.fases f ON f.id = tr.fase_id
            JOIN public.tipos_tareas tt ON tt.id = t.tipo_tarea_id
            WHERE f.solicitud_id = rt.solicitud_id AND tt.codigo = 'ANALIZAR'
            ORDER BY t.id DESC
            LIMIT 1
        )
    """)
    op.alter_column('requerimientos_tarea', 'tarea_id', nullable=False, schema='public')
    op.create_foreign_key(
        'fk_requerimientos_tarea_tarea', 'requerimientos_tarea', 'tareas',
        ['tarea_id'], ['id'], source_schema='public', referent_schema='public',
        ondelete='CASCADE',
    )
    op.create_index('idx_requerimientos_tarea_tarea',
                     'requerimientos_tarea', ['tarea_id'], schema='public')

    op.drop_index('idx_requerimientos_tarea_solicitud', table_name='requerimientos_tarea', schema='public')
    op.drop_constraint('fk_requerimientos_tarea_solicitud', 'requerimientos_tarea',
                        schema='public', type_='foreignkey')
    op.drop_column('requerimientos_tarea', 'solicitud_id', schema='public')
