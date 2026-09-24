"""930_plazo_acto_calculado — el plazo de resolver del acto se cumple con la notificación al titular

Revision ID: 930_plazo_acto_calculado
Revises: 927_entradas_multiples_dup
Create Date: 2026-09-24

Issue #930 (N2 de ADR-049 §E). El plazo máximo de resolver es de cada acto —el
tipo atómico de la solicitud—, no de la solicitud ni de la fase, y se cumple con
el documento que acredita la notificación al titular en la fase que resuelve el
acto (arts. 21.2 y 40.4 LPACAP). Hasta ahora las filas SOLICITUD cerraban con
`{"fk": "documento_cierre_id"}`, una FK que nadie escribe (0 de 11 solicitudes):
ningún plazo de resolver podía alcanzar CUMPLIDO.

Solo las 7 filas atómicas (D6): `ANY/AAP`, `ANY/AAC`, `ANY/DUP`, `ANY/AAT`,
`ANY/AE_PROVISIONAL`, `ANY/AE_DEFINITIVA` y `ANY/CIERRE` pasan a
`{"calculado": "documento_cumplimiento"}` (la propiedad del acto,
`ActoSolicitud.documento_cumplimiento`). Se localizan por nivel y forma del
camino —sin «+»—, nunca por id. Las 4 combinaciones (`+` en el camino) y las 3
filas de nivel FASE no se tocan: las retira N2b. Error si no se actualiza
ninguna fila; no se exige que sean exactamente 7.

Actualiza también el comentario de la columna (D8), con el mismo texto que el
`comment=` del modelo: el MCP de PostgreSQL lee el de la BD.

Sin CHECK de vocabulario (D7): lo sostienen los tests sobre las filas reales.

Downgrade simétrico: solo las filas SOLICITUD con `calculado` vuelven a
`documento_cierre_id`, y se restaura el comentario anterior.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '930_plazo_acto_calculado'
down_revision = '927_entradas_multiples_dup'
branch_labels = None
depends_on = None

_CALCULADO = '{"calculado": "documento_cumplimiento"}'
_FK_CIERRE = '{"fk": "documento_cierre_id"}'

_COMENTARIO_ANTES = (
    'Referencia al Documento.fecha_administrativa que acredita el cumplimiento: '
    '{"fk":"documento_cierre_id"} (SOLICITUD) o '
    '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
    'NULL = el plazo nunca alcanza CUMPLIDO (#778)'
)
_COMENTARIO_DESPUES = (
    'Referencia al Documento.fecha_administrativa que acredita el cumplimiento: '
    '{"calculado":"documento_cumplimiento"} (SOLICITUD atómica: documento que '
    'acredita la notificación al titular en la fase que resuelve el acto, ADR-049), '
    '{"fk":"documento_cierre_id"} (SOLICITUD combinada, hasta que se retire) o '
    '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
    'NULL = el plazo nunca alcanza CUMPLIDO (#778)'
)


def _comentar(nuevo, anterior):
    op.alter_column(
        'catalogo_plazos', 'campo_fecha_cumplimiento',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=True,
        comment=nuevo,
        existing_comment=anterior,
        schema='public',
    )


def upgrade():
    conn = op.get_bind()

    actualizadas = conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET campo_fecha_cumplimiento = CAST(:calculado AS jsonb)
        WHERE tipo_elemento = 'SOLICITUD' AND camino NOT LIKE '%+%'
    """), {'calculado': _CALCULADO})
    if actualizadas.rowcount == 0:
        raise RuntimeError(
            'No se encontró ninguna fila atómica de nivel SOLICITUD en catalogo_plazos — '
            'verificar que el seed 448 y siguientes siguen sembrando ANY/AAP, ANY/DUP...'
        )

    _comentar(_COMENTARIO_DESPUES, _COMENTARIO_ANTES)


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET campo_fecha_cumplimiento = CAST(:fk_cierre AS jsonb)
        WHERE tipo_elemento = 'SOLICITUD'
          AND campo_fecha_cumplimiento = CAST(:calculado AS jsonb)
    """), {'fk_cierre': _FK_CIERRE, 'calculado': _CALCULADO})

    _comentar(_COMENTARIO_ANTES, _COMENTARIO_DESPUES)
