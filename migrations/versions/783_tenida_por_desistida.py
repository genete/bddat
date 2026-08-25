"""783_tenida_por_desistida

Revision ID: 783_tenida_por_desistida
Revises: b29f4e7f3d6b
Create Date: 2026-08-25

Issue #783 — `TipoResultadoFase.DESISTIDA` ("Desistida por el Solicitante")
nombraba en exclusiva el desistimiento voluntario del art. 94 LPACAP, pero
también se usaba para cerrar una fase por art. 68.1 (la Administración tiene
al solicitante por desistido tras no atender el requerimiento de subsanación).
Son dos figuras distintas por causa y por quién las provoca, y la resolución
que las declara debe motivarlas de forma distinta.

Se desdobla: `DESISTIDA` queda en exclusiva para el art. 94 (su nombre actual
ya es preciso para ese caso en solitario, no se toca); se da de alta
`TENIDA_POR_DESISTIDA` para el art. 68.1, coherente con el efecto_plazo
`TENER_POR_DESISTIDO` que #779 ya dio de alta en `efectos_plazo` para la misma
figura (sin repetir ahí la cita de artículo: ya consta en el nombre de ese
efecto).

Análisis de impacto (ver conversación #783): el context builder de la
resolución (`ContextoResolucion`) ya es agnóstico al código — toma
`resultado.codigo`/`resultado.nombre` directos del catálogo, sin lógica por
valor. `_check_cierre_fase` (invariantes_esftt.py) solo distingue
'DESFAVORABLE' del resto; el código nuevo cae en "el resto" igual que
'DESISTIDA' hoy, sin bloquear. `RESULTADO_FASE_FAVORABLE_CODIGOS` no incluye
ninguno de los dos. Ningún consumidor requiere cambio de código.
"""
from alembic import op
import sqlalchemy as sa


revision = '783_tenida_por_desistida'
down_revision = 'b29f4e7f3d6b'
branch_labels = None
depends_on = None


_CODIGO_NUEVO = 'TENIDA_POR_DESISTIDA'
_NOMBRE_NUEVO = 'Tenida por desistida'


def upgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            INSERT INTO public.tipos_resultados_fases (codigo, nombre)
            VALUES (:codigo, :nombre)
        """),
        {'codigo': _CODIGO_NUEVO, 'nombre': _NOMBRE_NUEVO},
    )


def downgrade():
    conn = op.get_bind()

    conn.execute(
        sa.text("""
            DELETE FROM public.tipos_resultados_fases WHERE codigo = :codigo
        """),
        {'codigo': _CODIGO_NUEVO},
    )
