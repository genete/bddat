"""779_tener_por_desistido

Revision ID: 779_tener_por_desistido
Revises: 778b_dato_catalogo
Create Date: 2026-08-21

Issue #779 — el vencimiento del plazo de subsanación estaba tipificado
`PERDIDA_TRAMITE` (art. 73.3 LPACAP: se pierde un trámite, el procedimiento
sigue) cuando el art. 68.1 produce una consecuencia mucho más grave: se tiene
al solicitante por desistido de su petición, previa resolución expresa del
art. 21.1, y el procedimiento termina.

`efectos_plazo` no tenía código para esa figura. Se da de alta
`TENER_POR_DESISTIDO` (nombre elegido por Carlos, fiel a la dicción legal —
«se le tendrá por desistido» — y distinto del desistimiento voluntario del
art. 94, que es harina de otro costal: #783 lo coordinará si desdobla
`TipoResultadoFase.DESISTIDA`). Es solo dato informativo para el semáforo: el
desistimiento exige resolución expresa de una persona, no un efecto
automático que deba disparar el motor.

Única fila de `catalogo_plazos` con `PERDIDA_TRAMITE`: la de la subsanación
(`ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO`) — verificado en BD de
desarrollo antes de esta migración. No hay ninguna otra fila que de verdad
corresponda al art. 73.3 y deba conservar el efecto viejo.
"""
from alembic import op
import sqlalchemy as sa


revision = '779_tener_por_desistido'
down_revision = '778b_dato_catalogo'
branch_labels = None
depends_on = None


_CODIGO_NUEVO = 'TENER_POR_DESISTIDO'
_NOMBRE_NUEVO = 'Se tiene al solicitante por desistido (art. 68.1 LPACAP)'
_CAMINO_SUBSANACION = 'ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO'


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            INSERT INTO public.efectos_plazo (codigo, nombre)
            VALUES (:codigo, :nombre)
        """),
        {'codigo': _CODIGO_NUEVO, 'nombre': _NOMBRE_NUEVO},
    )

    conn.execute(
        sa.text("""
            UPDATE public.catalogo_plazos
            SET efecto_vencimiento_id = (
                SELECT id FROM public.efectos_plazo WHERE codigo = :codigo
            )
            WHERE tipo_elemento = 'TAREA'
              AND camino = :camino
        """),
        {'codigo': _CODIGO_NUEVO, 'camino': _CAMINO_SUBSANACION},
    )


def downgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            UPDATE public.catalogo_plazos
            SET efecto_vencimiento_id = (
                SELECT id FROM public.efectos_plazo WHERE codigo = 'PERDIDA_TRAMITE'
            )
            WHERE tipo_elemento = 'TAREA'
              AND camino = :camino
        """),
        {'camino': _CAMINO_SUBSANACION},
    )

    conn.execute(
        sa.text("""
            DELETE FROM public.efectos_plazo WHERE codigo = :codigo
        """),
        {'codigo': _CODIGO_NUEVO},
    )
