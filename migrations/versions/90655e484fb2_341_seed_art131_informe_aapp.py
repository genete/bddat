"""341_seed_art131_consultas_plazos

Revision ID: 90655e484fb2
Revises: 2da48740db54
Create Date: 2026-04-30 11:01:41.465245

Issue #341 sesión 5 — Seed de plazos condicionados en la fase CONSULTAS
(art. 131.1 párr. 2 RD 1955/2000):
  - Dos entradas en catalogo_plazos para FASE/CONSULTAS:
      orden=10  → 15 días naturales (condicionada: AAP previa favorable + AAC pura)
      orden=100 → 30 días naturales (fallback general)
  - Dos condiciones en condiciones_plazo para la entrada de 15 días.

CONSULTAS (id=4) ya existe en tipos_fases — no se crea ninguna fase nueva.
"""
from alembic import op
import sqlalchemy as sa


revision = '90655e484fb2'
down_revision = '2da48740db54'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # B.1 Entrada condicionada — 15 días naturales (orden=10)
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, campo_fecha,
             plazo_valor, plazo_unidad,
             efecto_vencimiento_id, norma_origen, orden, activo)
        SELECT
            'FASE',
            tf.id,
            '{"fk": "documento_solicitud_id"}'::jsonb,
            15,
            'DIAS_NATURALES',
            ep.id,
            'Art. 131.1 párr. 2 RD 1955/2000 — plazo reducido con AAP previa favorable',
            10,
            TRUE
        FROM public.tipos_fases tf
        CROSS JOIN public.efectos_plazo ep
        WHERE tf.codigo = 'CONSULTAS'
          AND ep.codigo = 'CONFORMIDAD_PRESUNTA'
    """))

    # B.2 Entrada fallback — 30 días naturales (orden=100)
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_plazos
            (tipo_elemento, tipo_elemento_id, campo_fecha,
             plazo_valor, plazo_unidad,
             efecto_vencimiento_id, norma_origen, orden, activo)
        SELECT
            'FASE',
            tf.id,
            '{"fk": "documento_solicitud_id"}'::jsonb,
            30,
            'DIAS_NATURALES',
            ep.id,
            'Art. 131.1 párr. 1 RD 1955/2000 — plazo general de consultas en AAP/AAC',
            100,
            TRUE
        FROM public.tipos_fases tf
        CROSS JOIN public.efectos_plazo ep
        WHERE tf.codigo = 'CONSULTAS'
          AND ep.codigo = 'CONFORMIDAD_PRESUNTA'
    """))

    # C. Condiciones para la entrada de 15 días (AND implícito)
    conn.execute(sa.text("""
        INSERT INTO public.condiciones_plazo
            (catalogo_plazo_id, variable_id, operador, valor, orden)
        SELECT
            cp.id,
            cv.id,
            'EQ',
            'true'::jsonb,
            cond.orden
        FROM public.catalogo_plazos cp
        JOIN public.tipos_fases tf ON tf.id = cp.tipo_elemento_id
        CROSS JOIN (
            VALUES
                ('tiene_solicitud_aap_favorable', 1),
                ('es_solicitud_aac_pura',          2)
        ) AS cond(nombre_var, orden)
        JOIN public.catalogo_variables cv ON cv.nombre = cond.nombre_var
        WHERE tf.codigo = 'CONSULTAS'
          AND cp.orden = 10
          AND cp.tipo_elemento = 'FASE'
    """))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE catalogo_plazo_id IN (
            SELECT cp.id FROM public.catalogo_plazos cp
            JOIN public.tipos_fases tf ON tf.id = cp.tipo_elemento_id
            WHERE tf.codigo = 'CONSULTAS'
        )
    """))

    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento_id = (
            SELECT id FROM public.tipos_fases WHERE codigo = 'CONSULTAS'
        )
        AND tipo_elemento = 'FASE'
    """))
