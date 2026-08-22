"""776_plazo_notificar_generico

Revision ID: 776_plazo_notificar_generico
Revises: 776_plantilla_comunicacion_inicio_admision
Create Date: 2026-08-22

Issue #776 — el art. 40 LPACAP fija 10 días hábiles para notificar un acto
desde que se dicta. Es un plazo transversal a TODAS las tareas NOTIFICAR del
catálogo ESFTT (22 tipos de trámite en BD de desarrollo a fecha de esta
migración: ANUNCIO_*, CONSULTA_*, REQUERIMIENTO_SUBSANACION,
COMUNICACION_INICIO_ADMISION, etc.), no solo de la tarea que este issue
introduce.

Encaja sin extender el vocabulario cerrado de catalogo_plazos (#788):
`campo_fecha={"rol":"CONSUMIDO"}` es el acto que la tarea hermana
(ELABORAR/ANALIZAR) produjo y NOTIFICAR consume; `campo_fecha_cumplimiento=
{"rol":"PRODUCIDO"}` es el justificante que la propia NOTIFICAR produce.

Efecto RESPONSABILIDAD_DISCIPLINARIA (art. 20.1 LPACAP: incumplir un plazo
administrativo es responsabilidad del funcionario, no del procedimiento ni
del administrado) — primer uso real de ese código en catalogo_plazos, dado
de alta en el seed original sin fila que lo usara todavía.

No suspende el plazo de la solicitud (suspende_plazo_solicitud=FALSE): el
art. 22 solo suspende por espera de un tercero; NOTIFICAR es acto propio de
la Administración y corre en paralelo, consumiendo el plazo global si se
demora — no lo detiene.
"""
from alembic import op
import sqlalchemy as sa


revision = '776_plazo_notificar_generico'
down_revision = '776_plantilla_comunicacion_inicio_admision'
branch_labels = None
depends_on = None


_CAMINO = 'ANY/ANY/ANY/ANY/NOTIFICAR'


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, camino, campo_fecha, campo_fecha_cumplimiento,
                 suspende_plazo_solicitud, plazo_valor, plazo_unidad,
                 efecto_vencimiento_id, norma_origen, activo, orden)
            VALUES (
                'TAREA',
                :camino,
                CAST(:campo_fecha AS jsonb),
                CAST(:campo_fecha_cumplimiento AS json),
                FALSE,
                10,
                'DIAS_HABILES',
                (SELECT id FROM public.efectos_plazo WHERE codigo = 'RESPONSABILIDAD_DISCIPLINARIA'),
                'Art. 40 LPACAP',
                TRUE,
                100
            )
        """),
        {
            'camino': _CAMINO,
            'campo_fecha': '{"rol": "CONSUMIDO"}',
            'campo_fecha_cumplimiento': '{"rol": "PRODUCIDO"}',
        },
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM public.catalogo_plazos WHERE tipo_elemento = 'TAREA' AND camino = :camino"),
        {'camino': _CAMINO},
    )
