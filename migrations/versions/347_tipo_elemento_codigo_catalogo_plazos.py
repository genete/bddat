"""347_tipo_elemento_codigo_catalogo_plazos

Revision ID: 347a0b1c2d3e
Revises: 90655e484fb2
Create Date: 2026-05-03

Issue #347 — Fix polimorfismo en catalogo_plazos:
  - Añade tipo_elemento_codigo (VARCHAR, NOT NULL) con backfill desde la tabla
    de tipos referenciada. El servicio plazos.py pasa a filtrar por
    (tipo_elemento, tipo_elemento_codigo) en lugar del ID frágil autoincremental.
  - tipo_elemento_id se marca DEPRECATED (columna conservada hasta issue posterior).
  - Índices actualizados para la nueva columna.
"""
from alembic import op
import sqlalchemy as sa


revision = '347a0b1c2d3e'
down_revision = '90655e484fb2'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Añadir columna nullable para poder hacer backfill
    op.add_column(
        'catalogo_plazos',
        sa.Column(
            'tipo_elemento_codigo',
            sa.String(60),
            nullable=True,
            comment='Código estable del tipo (reemplaza tipo_elemento_id — DEPRECATED)',
        ),
        schema='public',
    )

    # 2. Backfill desde las tablas de tipos según tipo_elemento
    conn = op.get_bind()

    # TipoSolicitud usa 'siglas' como identificador estable (no tiene columna 'codigo')
    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos cp
        SET tipo_elemento_codigo = ts.siglas
        FROM public.tipos_solicitudes ts
        WHERE cp.tipo_elemento = 'SOLICITUD'
          AND cp.tipo_elemento_id = ts.id
    """))

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos cp
        SET tipo_elemento_codigo = tf.codigo
        FROM public.tipos_fases tf
        WHERE cp.tipo_elemento = 'FASE'
          AND cp.tipo_elemento_id = tf.id
    """))

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos cp
        SET tipo_elemento_codigo = tt.codigo
        FROM public.tipos_tramites tt
        WHERE cp.tipo_elemento = 'TRAMITE'
          AND cp.tipo_elemento_id = tt.id
    """))

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos cp
        SET tipo_elemento_codigo = tta.codigo
        FROM public.tipos_tareas tta
        WHERE cp.tipo_elemento = 'TAREA'
          AND cp.tipo_elemento_id = tta.id
    """))

    # 3. Marcar NOT NULL tras el backfill
    op.alter_column(
        'catalogo_plazos',
        'tipo_elemento_codigo',
        nullable=False,
        schema='public',
    )

    # 4. Añadir comentario DEPRECATED a tipo_elemento_id
    op.alter_column(
        'catalogo_plazos',
        'tipo_elemento_id',
        comment='DEPRECATED — usar tipo_elemento_codigo. Se eliminará en issue posterior.',
        schema='public',
    )

    # 5. Índice sobre la nueva columna
    op.create_index(
        'idx_catalogo_plazos_tipo_codigo',
        'catalogo_plazos',
        ['tipo_elemento', 'tipo_elemento_codigo'],
        schema='public',
    )
    op.create_index(
        'idx_catalogo_plazos_tipo_codigo_orden',
        'catalogo_plazos',
        ['tipo_elemento', 'tipo_elemento_codigo', 'orden'],
        schema='public',
    )


def downgrade():
    op.drop_index('idx_catalogo_plazos_tipo_codigo_orden', table_name='catalogo_plazos', schema='public')
    op.drop_index('idx_catalogo_plazos_tipo_codigo', table_name='catalogo_plazos', schema='public')
    op.drop_column('catalogo_plazos', 'tipo_elemento_codigo', schema='public')
