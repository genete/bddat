"""947_cert_cumplimiento_fase — tipo documental del certificado de cumplimiento (N4)

Revision ID: 947_cert_cumplimiento_fase
Revises: 932_certificados_tipo_fase
Create Date: 2026-09-24

Issue #947 (N4), ADR-049 §E/§F. El certificado que constata la notificación al
titular de lo que resuelve una fase finalizadora, citando el documento que la
acredita. Desde su emisión el plazo de resolver de los actos de esa fase se lee
de él (`sellos.documento_cumplimiento_sellado`) y el documento citado queda
protegido.

Solo la fila de catálogo: la tabla `certificados` ya tiene `tipo` y `fase_id`
desde #932 (N3). Por `codigo`, nunca por `id` (REGLAS_DESARROLLO §migraciones).
"""
from alembic import op
import sqlalchemy as sa


revision = '947_cert_cumplimiento_fase'
down_revision = '932_certificados_tipo_fase'
branch_labels = None
depends_on = None

_CODIGO = 'CERT_CUMPLIMIENTO_FASE'
_NOMBRE = 'Certificado de cumplimiento de la fase'
_DESCRIPCION = (
    'Certificado que constata la notificación al titular de lo que resuelve una '
    'fase finalizadora, citando el documento que la acredita (art. 40.4 LPACAP; '
    'ADR-049 §E/§F). Desde su emisión el plazo de resolver de los actos de esa '
    'fase se lee de él y el documento citado queda protegido. Fecha '
    'administrativa: ninguna — el certificado no tiene fecha propia; la emisión '
    'consta en certificados.generado_en y la fecha que cuenta es la del '
    'documento citado.'
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
