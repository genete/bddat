"""448_seed_plazos_resolucion

Revision ID: 448_seed_plazos_resolucion
Revises: 449_grant_organismos_expediente
Create Date: 2026-05-22

Issue #448 — HOTFIX del seed `catalogo_plazos` para la fase RESOLUCION.

CONTEXTO DEL BUG
================

La migración `c9379e09ae01_172_plazos_tablas_catalogo.py` (mayo 2026) intentó
seedar 7 plazos para la fase RESOLUCION pero el JOIN final con `tipos_fases`
usaba códigos compuestos (`RESOLUCION_AAP`, `RESOLUCION_AAC`, …) que **nunca
han existido** en BD — `tipos_fases` solo contiene el código genérico
`RESOLUCION`. El INSERT-SELECT devolvió 0 filas sin producir error y dejó
`catalogo_plazos` sin ningún plazo para la fase RESOLUCION.

Detalle en auditoría exhaustiva del 22/05/2026 y en el cuerpo del issue #448.

DISEÑO DEL FIX
==============

Modelado correcto:
  - Un único `tipos_fases.codigo='RESOLUCION'` (ya existe, id=8)
  - 7 entradas en `catalogo_plazos` con `tipo_elemento_codigo='RESOLUCION'`
  - Cada entrada cita una norma distinta del RD 1955/2000 (o derivadas)
  - Las condiciones diferencian por `tipo_solicitud` usando operador IN

Nueva variable `tipo_solicitud` (texto): devuelve la siglas literal del
tipo de solicitud en contexto (ej. 'AAP', 'AAP+AAC', 'CIERRE'). Las
condiciones de cada plazo enumeran con IN las combinaciones cubiertas
por la misma cita normativa.

Diferencias respecto al seed original (172):
  - Descartado `RESOLUCION_AE` (sin sufijo): no existe ese tipo_solicitud
    en BD (solo AE_PROVISIONAL y AE_DEFINITIVA).
  - Añadido DUP (3 meses, art. 145.4 RD 1955/2000): el procedimiento DUP
    autónomo no estaba en el seed 172.
  - Corregido CIERRE: art. 137 → art. 138 RD 1955/2000 (mod. RD 88/2026).
    Art. 137 corresponde al informe del operador, no a la resolución.
  - AAC consolida sus combinadas en una sola entrada (art. 131.7 fija el
    plazo conjunto): `IN ('AAC','AAP+AAC','AAP+AAC+DUP','AAC+DUP')`.
  - AE_DEFINITIVA+AAT consume el plazo del AE_DEFINITIVA (art. 132 ter).

Fuera de scope del hotfix (deuda de #247): plazos de RESOLUCION para
RAIPEE_PREVIA, RAIPEE_DEFINITIVA, RADNE, AMPLIACION_PLAZO, CORRECCION_ERRORES,
DESISTIMIENTO, RENUNCIA, RECURSO, INTERESADO, OTRO.
"""
from alembic import op
import sqlalchemy as sa


revision = '448_seed_plazos_resolucion'
down_revision = '449_grant_organismos_expediente'
branch_labels = None
depends_on = None


# (orden, plazo_valor, plazo_unidad, norma_origen, IN-list de siglas)
_PLAZOS_RESOLUCION = [
    (10, 1, 'MESES', 'Art. 132 bis RD 1955/2000 + DA 3ª LSE',
     ['AE_PROVISIONAL']),
    (20, 1, 'MESES', 'Art. 132 ter RD 1955/2000 + DA 3ª LSE',
     ['AE_DEFINITIVA', 'AE_DEFINITIVA+AAT']),
    (30, 3, 'MESES', 'Art. 128 RD 1955/2000',
     ['AAP']),
    (40, 3, 'MESES', 'Art. 131.7 RD 1955/2000',
     ['AAC', 'AAP+AAC', 'AAP+AAC+DUP', 'AAC+DUP']),
    (50, 3, 'MESES', 'Art. 133 RD 1955/2000',
     ['AAT']),
    (60, 3, 'MESES', 'Art. 138 RD 1955/2000 (mod. RD 88/2026)',
     ['CIERRE']),
    (70, 3, 'MESES', 'Art. 145.4 RD 1955/2000',
     ['DUP']),
]


def upgrade():
    conn = op.get_bind()

    # 1. Crear variable tipo_solicitud si no existe
    conn.execute(sa.text("""
        INSERT INTO public.catalogo_variables (nombre, etiqueta, tipo_dato, norma_id, activa)
        VALUES (
            'tipo_solicitud',
            'Siglas (literal) del tipo de solicitud en contexto. Combinaciones se mantienen unidas con +',
            'texto',
            NULL,
            TRUE
        )
        ON CONFLICT (nombre) DO NOTHING
    """))

    # 2. Insertar los 7 plazos + sus condiciones IN
    for orden, valor, unidad, norma, siglas_in in _PLAZOS_RESOLUCION:
        # Insertar plazo y recuperar id
        plazo_id = conn.execute(sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, tipo_elemento_id, tipo_elemento_codigo, campo_fecha,
                 plazo_valor, plazo_unidad,
                 efecto_vencimiento_id, norma_origen, orden, activo)
            SELECT
                'FASE',
                tf.id,
                'RESOLUCION',
                '{"fk": "documento_solicitud_id"}'::jsonb,
                :valor,
                :unidad,
                ep.id,
                :norma,
                :orden,
                TRUE
            FROM public.tipos_fases tf
            CROSS JOIN public.efectos_plazo ep
            WHERE tf.codigo = 'RESOLUCION'
              AND ep.codigo = 'SILENCIO_DESESTIMATORIO'
            RETURNING id
        """), {
            'valor': valor,
            'unidad': unidad,
            'norma': norma,
            'orden': orden,
        }).scalar()

        if plazo_id is None:
            raise RuntimeError(
                f"No se pudo insertar plazo RESOLUCION orden={orden}; "
                "verificar existencia de tipos_fases.RESOLUCION y "
                "efectos_plazo.SILENCIO_DESESTIMATORIO"
            )

        # Insertar la condición IN con la variable tipo_solicitud
        import json
        conn.execute(sa.text("""
            INSERT INTO public.condiciones_plazo
                (catalogo_plazo_id, variable_id, operador, valor, orden)
            SELECT
                :plazo_id,
                cv.id,
                'IN',
                CAST(:siglas_json AS jsonb),
                1
            FROM public.catalogo_variables cv
            WHERE cv.nombre = 'tipo_solicitud'
        """), {
            'plazo_id': plazo_id,
            'siglas_json': json.dumps(siglas_in),
        })


def downgrade():
    conn = op.get_bind()

    # 1. Eliminar condiciones de los plazos RESOLUCION sembrados aquí
    conn.execute(sa.text("""
        DELETE FROM public.condiciones_plazo
        WHERE catalogo_plazo_id IN (
            SELECT cp.id FROM public.catalogo_plazos cp
            WHERE cp.tipo_elemento = 'FASE'
              AND cp.tipo_elemento_codigo = 'RESOLUCION'
        )
    """))

    # 2. Eliminar las entradas de catalogo_plazos para FASE/RESOLUCION
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'FASE'
          AND tipo_elemento_codigo = 'RESOLUCION'
    """))

    # 3. Eliminar la variable tipo_solicitud
    conn.execute(sa.text("""
        DELETE FROM public.catalogo_variables WHERE nombre = 'tipo_solicitud'
    """))
