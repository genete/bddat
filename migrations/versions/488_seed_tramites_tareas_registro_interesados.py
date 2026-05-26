"""488_seed_tramites_tareas_registro_interesados

Revision ID: 488_seed_tramites_tareas_registro_interesados
Revises: 416_seed_plazos_tablon
Create Date: 2026-05-26

Issue #488 — REGISTRO_INTERESADOS se añadió a tipos_tramites en la migración
374_interesados_expediente pero sin su fila en tramites_tareas.

Fuente: ESTRUCTURA_FTT.json — patrón A → secuencia [ANALIZAR].
"""
from alembic import op
import sqlalchemy as sa


revision = '488_seed_tramites_tareas_registro_interesados'
down_revision = '416_seed_plazos_tablon'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    result = conn.execute(
        sa.text("SELECT id FROM public.tipos_tramites WHERE codigo = :c"),
        {'c': 'REGISTRO_INTERESADOS'}
    )
    tt_id = result.scalar()
    if tt_id is None:
        raise ValueError("TipoTramite 'REGISTRO_INTERESADOS' no encontrado — migración abortada")

    result = conn.execute(
        sa.text("SELECT id FROM public.tipos_tareas WHERE codigo = :c"),
        {'c': 'ANALIZAR'}
    )
    ta_id = result.scalar()
    if ta_id is None:
        raise ValueError("TipoTarea 'ANALIZAR' no encontrado — migración abortada")

    conn.execute(sa.text("""
        INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
        VALUES (:tt_id, 1, :ta_id)
        ON CONFLICT DO NOTHING
    """), {'tt_id': tt_id, 'ta_id': ta_id})


def downgrade():
    conn = op.get_bind()

    result = conn.execute(
        sa.text("SELECT id FROM public.tipos_tramites WHERE codigo = :c"),
        {'c': 'REGISTRO_INTERESADOS'}
    )
    tt_id = result.scalar()
    if tt_id is not None:
        conn.execute(
            sa.text("DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt_id"),
            {'tt_id': tt_id}
        )
