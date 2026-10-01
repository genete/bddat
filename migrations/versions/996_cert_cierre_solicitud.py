"""996_cert_cierre_solicitud — descripción del certificado de cierre de la solicitud (N6)

Revision ID: 996_cert_cierre_solicitud
Revises: 568_notificacion_edictal
Create Date: 2026-10-01

Issue #996 (N6), ADR-049 §F. El tipo `CERT_CIERRE_SOLICITUD` existe desde #778
(migración `778a_medida_unica`) pero nadie lo emitía, y su descripción seguía
diciendo lo que #930 y ADR-049 desmintieron: que constata la notificación a
todos los interesados, que ancla el fin del cómputo del plazo de la solicitud y
que su fecha es la del último acto. Desde #996 lo emite
`services/cert_cierre_solicitud.py`: resumen del plazo por acto, la instrucción
y copia de los certificados de cierre de las fases finalizadoras, sin fecha
propia.

Solo la descripción: la fila, la FK `solicitudes.documento_cierre_id` y la tabla
`certificados` ya existen. Por `codigo`, nunca por `id` (REGLAS_DESARROLLO
§migraciones), y sin condicionar al texto anterior: lo que se quiere es el texto
nuevo en toda instalación. Si la fila no estuviera, se aborta en vez de seguir
con 0 filas tocadas.
"""
from alembic import op
import sqlalchemy as sa


revision = '996_cert_cierre_solicitud'
down_revision = '568_notificacion_edictal'
branch_labels = None
depends_on = None

_CODIGO = 'CERT_CIERRE_SOLICITUD'

_DESCRIPCION = (
    'Certificado de cierre de la solicitud: constata, acto por acto, el plazo de '
    'resolver y si se resolvió y notificó al solicitante en plazo (ADR-049 §E), e '
    'incorpora la instrucción (CERT_FIN_INSTRUCCION) y copia literal de los '
    'certificados de cierre de sus fases finalizadoras. Solo se emite con todos los '
    'actos resueltos. No cierra ningún plazo. Ocupa solicitudes.documento_cierre_id; '
    'se retira con justificación. Fecha administrativa: ninguna; la emisión consta en '
    'certificados.generado_en.'
)

# La de `778a_medida_unica`, para el downgrade.
_DESCRIPCION_ANTERIOR = (
    'Certificado que constata que, respecto de todos los interesados, hubo '
    'notificación de la resolución o intento de notificación debidamente '
    'acreditado (art. 40.4 LPACAP), con lo que se entiende cumplida la '
    'obligación de resolver y notificar en plazo (art. 21.3.b). Ancla el fin '
    'del cómputo del plazo de la solicitud. Fecha administrativa: la del '
    'último de esos actos, retroactiva respecto de la emisión del certificado.'
)


def _fijar(descripcion: str) -> None:
    resultado = op.get_bind().execute(sa.text(
        'UPDATE public.tipos_documentos SET descripcion = :descripcion '
        'WHERE codigo = :codigo'
    ), {'codigo': _CODIGO, 'descripcion': descripcion})
    if resultado.rowcount != 1:
        raise RuntimeError(
            f'996_cert_cierre_solicitud: se esperaba una fila {_CODIGO!r} en '
            f'tipos_documentos y se tocaron {resultado.rowcount}'
        )


def upgrade():
    _fijar(_DESCRIPCION)


def downgrade():
    _fijar(_DESCRIPCION_ANTERIOR)
