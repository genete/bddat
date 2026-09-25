"""956_cert_cierre_fase — tipo documental del certificado de cierre de la fase finalizadora (N4b)

Revision ID: 956_cert_cierre_fase
Revises: 947_cert_cumplimiento_fase
Create Date: 2026-09-25

Issue #956 (N4b), ADR-049 §F. El certificado que cierra una fase finalizadora:
constata que está hecho todo lo que el expediente registra como obligatorio en
ella —incluida la notificación al titular, que acredita el CERT_CUMPLIMIENTO_FASE
de #947— y relata los escapes salvados. Ocupa `fases.documento_resultado_id`:
emitirlo es cerrar la fase; se deshace reabriéndola.

Solo la fila de catálogo: la tabla `certificados` ya tiene `tipo` y `fase_id`
desde #932 (N3). Por `codigo`, nunca por `id` (REGLAS_DESARROLLO §migraciones).
"""
from alembic import op
import sqlalchemy as sa


revision = '956_cert_cierre_fase'
down_revision = '947_cert_cumplimiento_fase'
branch_labels = None
depends_on = None

_CODIGO = 'CERT_CIERRE_FASE'
_NOMBRE = 'Certificado de cierre de la fase'
_DESCRIPCION = (
    'Certificado que cierra una fase finalizadora: constata que está hecho todo lo '
    'que el expediente registra como obligatorio en ella, incluida la notificación '
    'al titular (CERT_CUMPLIMIENTO_FASE), y relata los escapes salvados. Ocupa '
    'fases.documento_resultado_id; se deshace reabriendo la fase (ADR-049 §F). '
    'Fecha administrativa: ninguna; la emisión consta en certificados.generado_en.'
)


def upgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
        VALUES (:codigo, :nombre, :descripcion, 'INTERNO')
        ON CONFLICT DO NOTHING
    """), {'codigo': _CODIGO, 'nombre': _NOMBRE, 'descripcion': _DESCRIPCION})


def downgrade():
    op.get_bind().execute(sa.text(
        "DELETE FROM public.tipos_documentos WHERE codigo = :codigo"
    ), {'codigo': _CODIGO})
