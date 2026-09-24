"""796_suspension_solo_causa_a — solo la causa a) del art. 22.1 suspende el plazo de resolver

Revision ID: 796_suspension_solo_causa_a
Revises: 931_nivel_acto
Create Date: 2026-09-24

Issue #796. La suspensión del art. 22.1 LPACAP es potestativa («se podrá
suspender»): sin acuerdo y sin comunicación, no existe. De las cuatro causas que
tocan a BDDAT solo una la lleva dentro del propio acto que la origina:

- 22.1.a `REQUERIMIENTO_SUBSANACION`: el oficio del requerimiento ya advierte de
  la suspensión y la levanta el propio titular al contestar (o el plazo
  concedido). Sigue suspendiendo, sin cambios.
- 22.1.d `SOLICITUD_INFORME`, `CONSULTA_SEPARATA`: exige acuerdo y dos
  comunicaciones a los interesados (petición y recepción del informe), que en la
  práctica no se hacen. Contar una suspensión que jurídicamente no existe
  esconde un plazo vencido —silencio desestimatorio— al tramitador; la
  asimetría del riesgo pide no computarla. Deja de suspender.

El mecanismo de cómputo lee `suspende_plazo_solicitud` sin distinguir causas,
así que el cambio es solo de dato: se apaga la marca en las filas de causa d).
Se localizan por camino, nunca por id (`CONSULTA_SEPARATA` tiene dos filas con
el mismo camino). La marca sigue siendo editable en la administración del
catálogo: es dato normativo, no invariante.

Downgrade: vuelve a encender la marca en esos caminos (los que tenían
`suspende_plazo_solicitud = TRUE` en la BD de desarrollo el 24/09/2026).
"""
from alembic import op
import sqlalchemy as sa


revision = '796_suspension_solo_causa_a'
down_revision = '931_nivel_acto'
branch_labels = None
depends_on = None

# Causa d) del art. 22.1: nivel TAREA, plazo de un tercero (informe/consulta).
_CAMINOS_CAUSA_D = (
    'ANY/ANY/CONSULTA_MINISTERIO/SOLICITUD_INFORME/ESPERAR_PLAZO',
    'ANY/ANY/ANY/CONSULTA_SEPARATA/ESPERAR_PLAZO',
)


def _marcar(valor: bool) -> None:
    conn = op.get_bind()
    for camino in _CAMINOS_CAUSA_D:
        conn.execute(
            sa.text("""
                UPDATE public.catalogo_plazos
                SET suspende_plazo_solicitud = :valor
                WHERE tipo_elemento = 'TAREA'
                  AND camino = :camino
            """),
            {'valor': valor, 'camino': camino},
        )


def upgrade():
    _marcar(False)


def downgrade():
    _marcar(True)
