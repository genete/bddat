"""776_plazo_elaborar_admision

Revision ID: 776_plazo_elaborar_admision
Revises: 776_plazo_notificar_generico
Create Date: 2026-08-22

Issue #776 — art. 21.4 LPACAP: la comunicación (o su tramo ELABORAR) debe
emitirse dentro de los diez días siguientes a la recepción de la solicitud
iniciadora. El disparo es distinto según haya habido o no un requerimiento
de subsanación previo en la fase ANALISIS_SOLICITUD:

- Sin requerimiento: desde la recepción de la solicitud (MODELO_SOLICITUD).
- Con requerimiento: desde la entrada de la última subsanación (SUBSANACION)
  — el reloj no puede contar desde una solicitud que se sabía incompleta.

Dos filas del mismo camino, discriminadas por `tipo_documento` en
campo_fecha (#788: filtra qué elementos son candidatos según el documento
que tienen realmente vinculado) — sin condiciones_plazo, porque el propio
documento vinculado por el hook #776 de mutaciones_arbol.py ya resuelve la
dualidad: solo uno de los dos tipos estará presente en cada expediente.

No se ancla en el Diagnostico (ADR-005/ADR-027: fecha_administrativa = NULL
por diseño, no es acto administrativo) sino en el documento que el
diagnóstico analizó, que sí la tiene.

Cierra con campo_fecha_cumplimiento={"rol":"PRODUCIDO"}: el plazo se cumple
cuando ELABORAR produce el oficio (dictar el acto), no antes (ADR-041 §D:
cada plazo se abre y se cierra en la misma tarea).

Mismo efecto que el plazo de NOTIFICAR (#776 anterior): RESPONSABILIDAD_
DISCIPLINARIA — plazo interno de la Administración, sin consecuencia para
el administrado ni para el procedimiento.
"""
import json

from alembic import op
import sqlalchemy as sa


revision = '776_plazo_elaborar_admision'
down_revision = '776_plazo_notificar_generico'
branch_labels = None
depends_on = None


_CAMINO = 'ANY/ANY/ANALISIS_SOLICITUD/COMUNICACION_INICIO_ADMISION/ELABORAR'


def upgrade():
    conn = op.get_bind()

    for tipo_documento, orden in (('MODELO_SOLICITUD', 100), ('SUBSANACION', 100)):
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
                    'Art. 21.4 LPACAP',
                    TRUE,
                    :orden
                )
            """),
            {
                'camino': _CAMINO,
                'campo_fecha': json.dumps({'rol': 'CONSUMIDO', 'tipo_documento': tipo_documento}),
                'campo_fecha_cumplimiento': json.dumps({'rol': 'PRODUCIDO'}),
                'orden': orden,
            },
        )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM public.catalogo_plazos WHERE tipo_elemento = 'TAREA' AND camino = :camino"),
        {'camino': _CAMINO},
    )
