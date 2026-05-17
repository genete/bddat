"""366_comunicacion_audiencia — renombrar AUDIENCIA → COMUNICACION_AUDIENCIA

Revision ID: 366_comunicacion_audiencia
Revises: 393_alegantes
Create Date: 2026-05-17

Issue #366 — El trámite AUDIENCIA en COMPATIBILIDAD_AMBIENTAL estaba mal concebido.
El órgano sustantivo no elabora ni responde — solo registra la comunicación de MA
(IC 1/2022, IV.3.3). La fuente de verdad (ESTRUCTURA_FTT.json) fue corregida en el
commit 724193d (#346). Esta migración sincroniza la BD con ese diseño.

Cambios:
- tipos_tramites: codigo AUDIENCIA → COMUNICACION_AUDIENCIA, nombre actualizado
- catalogo_plazos: eliminar el plazo de 15 días ESPERAR_PLAZO para AUDIENCIA
  (COMUNICACION_AUDIENCIA solo tiene ANALIZAR — no hay ESPERAR_PLAZO)
- condiciones_plazo: eliminar la condición asociada al plazo anterior
- tramites_tareas: sin cambios (ya contiene solo ANALIZAR tras migración #346)
"""
from alembic import op
import sqlalchemy as sa


revision = '366_comunicacion_audiencia'
down_revision = '393_alegantes'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # 1. Renombrar tipos_tramites
    conn.execute(sa.text("""
        UPDATE public.tipos_tramites
           SET codigo = 'COMUNICACION_AUDIENCIA',
               nombre = 'Comunicación de audiencia al interesado'
         WHERE codigo = 'AUDIENCIA'
    """))

    # 2. Eliminar plazo de 15 días ESPERAR_PLAZO que pertenecía al antiguo AUDIENCIA.
    #    El valor en condiciones_plazo es JSON text: to_jsonb('AUDIENCIA').
    row = conn.execute(sa.text("""
        SELECT cp.id
          FROM public.catalogo_plazos cp
          JOIN public.condiciones_plazo cond ON cond.catalogo_plazo_id = cp.id
          JOIN public.catalogo_variables cv    ON cv.id = cond.variable_id
         WHERE cv.nombre  = 'tipo_tramite'
           AND cond.valor::text = '"AUDIENCIA"'
         LIMIT 1
    """)).fetchone()

    if row:
        plazo_id = row[0]
        conn.execute(sa.text(
            "DELETE FROM public.condiciones_plazo WHERE catalogo_plazo_id = :pid"
        ), {'pid': plazo_id})
        conn.execute(sa.text(
            "DELETE FROM public.catalogo_plazos WHERE id = :pid"
        ), {'pid': plazo_id})

    op.execute("GRANT SELECT ON public.tipos_tramites TO claude_desktop")


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE public.tipos_tramites
           SET codigo = 'AUDIENCIA',
               nombre = 'Audiencia'
         WHERE codigo = 'COMUNICACION_AUDIENCIA'
    """))
    # El plazo no se restaura: era diseño incorrecto.
