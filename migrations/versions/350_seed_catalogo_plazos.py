"""350_seed_catalogo_plazos

Revision ID: 350_seed_catalogo_plazos
Revises: 350_variable_tipo_tramite
Create Date: 2026-05-07

Issue #350 — Seed de plazos para tareas ESPERAR_PLAZO.
Seis entradas condicionadas por tipo_tramite (EQ), una por tipo de
trámite que genera espera de respuesta de interesado o de AAPP.

norma_origen con PLACEHOLDER donde la cita exacta de artículo está pendiente.
"""
from alembic import op
import sqlalchemy as sa


revision = '350_seed_catalogo_plazos'
down_revision = '350_variable_tipo_tramite'
branch_labels = None
depends_on = None

# (tipo_tramite_codigo, plazo_valor, plazo_unidad, efecto_codigo, norma_origen)
_PLAZOS = [
    (
        'REQUERIMIENTO_SUBSANACION', 10, 'DIAS_HABILES', 'PERDIDA_TRAMITE',
        'PLACEHOLDER - pendiente cita exacta (Art. 68.1 LPACAP)',
    ),
    (
        'AUDIENCIA', 15, 'DIAS_HABILES', 'NINGUNO',
        'PLACEHOLDER - pendiente cita exacta (Art. 82.2 LPACAP)',
    ),
    (
        'SOLICITUD_INFORME', 10, 'DIAS_HABILES', 'SIN_EFECTO_AUTOMATICO',
        'PLACEHOLDER - pendiente cita exacta (Art. 80.2 LPACAP)',
    ),
    (
        'ANUNCIO_BOE', 30, 'DIAS_NATURALES', 'SIN_EFECTO_AUTOMATICO',
        'PLACEHOLDER - pendiente cita exacta (Art. 83 LPACAP / Art. 131 RD1955/2000)',
    ),
    (
        'ANUNCIO_BOP', 30, 'DIAS_NATURALES', 'SIN_EFECTO_AUTOMATICO',
        'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_BOP)',
    ),
    (
        'ANUNCIO_PRENSA', 30, 'DIAS_NATURALES', 'SIN_EFECTO_AUTOMATICO',
        'PLACEHOLDER - pendiente cita exacta (Art. 131 RD1955/2000 ANUNCIO_PRENSA)',
    ),
]


def upgrade():
    conn = op.get_bind()

    for tt_codigo, plazo_valor, plazo_unidad, efecto_codigo, norma in _PLAZOS:
        result = conn.execute(sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, tipo_elemento_id, tipo_elemento_codigo, campo_fecha,
                 plazo_valor, plazo_unidad,
                 efecto_vencimiento_id, norma_origen, orden, activo)
            SELECT
                'TAREA',
                tt.id,
                'ESPERAR_PLAZO',
                '{"fk": "documento_usado_id"}'::jsonb,
                :plazo_valor,
                :plazo_unidad,
                ep.id,
                :norma,
                10,
                TRUE
            FROM public.tipos_tareas tt
            CROSS JOIN public.efectos_plazo ep
            WHERE tt.codigo = 'ESPERAR_PLAZO'
              AND ep.codigo = :efecto_codigo
            RETURNING id
        """), {
            'plazo_valor': plazo_valor,
            'plazo_unidad': plazo_unidad,
            'efecto_codigo': efecto_codigo,
            'norma': norma,
        })
        plazo_id = result.scalar()

        if plazo_id:
            conn.execute(sa.text("""
                INSERT INTO public.condiciones_plazo
                    (catalogo_plazo_id, variable_id, operador, valor, orden)
                SELECT
                    :plazo_id,
                    cv.id,
                    'EQ',
                    to_jsonb(CAST(:tt_codigo AS TEXT)),
                    1
                FROM public.catalogo_variables cv
                WHERE cv.nombre = 'tipo_tramite'
            """), {'plazo_id': plazo_id, 'tt_codigo': tt_codigo})


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE catalogo_plazo_id IN (
            SELECT id FROM public.catalogo_plazos
            WHERE tipo_elemento = 'TAREA'
              AND tipo_elemento_codigo = 'ESPERAR_PLAZO'
        )
    """))

    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'TAREA'
          AND tipo_elemento_codigo = 'ESPERAR_PLAZO'
    """))
