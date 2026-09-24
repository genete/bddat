"""931_nivel_acto — el plazo de resolver solo por acto: fuera combinaciones y fases, SOLICITUD → ACTO

Revision ID: 931_nivel_acto
Revises: 930_plazo_acto_calculado
Create Date: 2026-09-24

Issue #931 (N2b de ADR-049 §E), la mitad destructiva de #930. El plazo de
resolver es de cada acto —el tipo atómico de la solicitud— y #930 dejó las 7
filas atómicas midiéndolo; las demás filas del plazo de resolver quedaron sin
uso y se retiran aquí (D4):

1. Las 4 combinaciones (`+` en el camino: `ANY/AAP+AAC`, `ANY/AAP+AAC+DUP`,
   `ANY/AAC+DUP`, `ANY/AE_DEFINITIVA+AAT`). Además de redundantes, engañaban:
   daban un único plazo a una solicitud que pide varios actos, y escondían
   que la DUP son 6 meses y no 3.
2. Las 3 de nivel FASE (`ANY/ANY/RESOLUCION_DUP|AAP|AAC`, ADR-048): el plazo
   no puede colgar de una fase que no existe mientras corre.
3. El nivel de las 7 que quedan pasa de SOLICITUD a ACTO, que es lo que son
   desde #930.

El CHECK de `tipo_elemento` no admite un estado intermedio, así que se quita
antes de tocar los datos y se pone el nuevo (`ACTO`, `TAREA`) después. Las
filas se localizan por nivel y forma del camino, nunca por id; guardas de «al
menos una», no de número exacto (mismo criterio que #930, D6). Ninguna de las
7 filas borradas tiene condiciones (y `condiciones_plazo` cuelga con CASCADE).

Comentarios de columna (D13), con el mismo texto que el `comment=` del modelo
—el MCP de PostgreSQL lee el de la BD—: `catalogo_plazos.tipo_elemento`,
`catalogo_plazos.campo_fecha_cumplimiento` (nombraba las combinaciones «hasta
que se retire») y `solicitudes.documento_cierre_id` (decía que el certificado
de cierre ancla el fin del plazo de resolver; desde #930 ningún plazo lo usa).

Downgrade simétrico e idempotente: renombra ACTO → SOLICITUD, reinserta las 7
filas con los valores que tenían (verificados en la BD de desarrollo el
24/09/2026) solo si su camino no existe ya, restaura el CHECK y los tres
comentarios.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '931_nivel_acto'
down_revision = '930_plazo_acto_calculado'
branch_labels = None
depends_on = None

_CHECK = 'ck_catalogo_plazos_tipo_elemento'
_CHECK_ANTES = "tipo_elemento IN ('SOLICITUD', 'FASE', 'TAREA')"
_CHECK_DESPUES = "tipo_elemento IN ('ACTO', 'TAREA')"

_EFECTO = 'SILENCIO_DESESTIMATORIO'
_FK_SOLICITUD = '{"fk": "documento_solicitud_id"}'
_FK_CIERRE = '{"fk": "documento_cierre_id"}'

# Filas que retira el upgrade, para reinsertarlas en el downgrade.
# (tipo_elemento, camino, plazo_valor, norma_origen, orden, campo_fecha_cumplimiento)
_RETIRADAS = [
    ('SOLICITUD', 'ANY/AAP+AAC',           3, 'Art. 131.7 RD 1955/2000', 40, _FK_CIERRE),
    ('SOLICITUD', 'ANY/AAP+AAC+DUP',       3, 'Art. 131.7 RD 1955/2000', 40, _FK_CIERRE),
    ('SOLICITUD', 'ANY/AAC+DUP',           3, 'Art. 131.7 RD 1955/2000', 40, _FK_CIERRE),
    ('SOLICITUD', 'ANY/AE_DEFINITIVA+AAT', 1, 'Art. 132 ter RD 1955/2000 + DA 3ª LSE', 20, _FK_CIERRE),
    ('FASE',      'ANY/ANY/RESOLUCION_DUP', 6, 'Art. 148.1 RD 1955/2000', 40, None),
    ('FASE',      'ANY/ANY/RESOLUCION_AAP', 3, 'Art. 128 RD 1955/2000',   40, None),
    ('FASE',      'ANY/ANY/RESOLUCION_AAC', 3, 'Art. 131.7 RD 1955/2000', 40, None),
]

# (tabla, columna, tipo, nullable, comentario antes, comentario después)
_COMENTARIOS = [
    ('catalogo_plazos', 'tipo_elemento', sa.String(20), False,
     'SOLICITUD | FASE | TRAMITE | TAREA',
     'Nivel de la fila del catálogo: ACTO | TAREA (#931)'),
    ('catalogo_plazos', 'campo_fecha_cumplimiento',
     postgresql.JSONB(astext_type=sa.Text()), True,
     'Referencia al Documento.fecha_administrativa que acredita el cumplimiento: '
     '{"calculado":"documento_cumplimiento"} (SOLICITUD atómica: documento que '
     'acredita la notificación al titular en la fase que resuelve el acto, ADR-049), '
     '{"fk":"documento_cierre_id"} (SOLICITUD combinada, hasta que se retire) o '
     '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
     'NULL = el plazo nunca alcanza CUMPLIDO (#778)',
     'Referencia al Documento.fecha_administrativa que acredita el cumplimiento: '
     '{"calculado":"documento_cumplimiento"} (ACTO: documento que acredita la '
     'notificación al titular en la fase que resuelve el acto, ADR-049) o '
     '{"rol":"CONSUMIDO|PRODUCIDO"[,"tipo_documento":"..."]} (TAREA). '
     'NULL = el plazo nunca alcanza CUMPLIDO (#778)'),
    ('solicitudes', 'documento_cierre_id', sa.Integer(), True,
     'FK a DOCUMENTOS. Certificado de cierre de la solicitud: ancla la fecha '
     'de fin del plazo para resolver y notificar (#778)',
     'FK a DOCUMENTOS. Certificado de cierre de la solicitud (CERT_CIERRE_SOLICITUD): '
     'deja constancia, por acto, de la resolución y su notificación (ADR-049). '
     'No cierra ningún plazo: el de resolver es de cada acto (#930)'),
]


def _comentar(despues: bool):
    for tabla, columna, tipo, nullable, antes, nuevo in _COMENTARIOS:
        op.alter_column(
            tabla, columna,
            existing_type=tipo,
            existing_nullable=nullable,
            comment=nuevo if despues else antes,
            existing_comment=antes if despues else nuevo,
            schema='public',
        )


def upgrade():
    conn = op.get_bind()

    op.drop_constraint(_CHECK, 'catalogo_plazos', schema='public', type_='check')

    combinaciones = conn.execute(sa.text("""
        DELETE FROM public.catalogo_plazos
        WHERE tipo_elemento = 'SOLICITUD' AND camino LIKE '%+%'
    """))
    if combinaciones.rowcount == 0:
        raise RuntimeError(
            'No se encontró ninguna fila de combinación (SOLICITUD con «+» en el camino) '
            'que retirar en catalogo_plazos'
        )

    fases = conn.execute(sa.text(
        "DELETE FROM public.catalogo_plazos WHERE tipo_elemento = 'FASE'"
    ))
    if fases.rowcount == 0:
        raise RuntimeError('No se encontró ninguna fila de nivel FASE que retirar en catalogo_plazos')

    renombradas = conn.execute(sa.text(
        "UPDATE public.catalogo_plazos SET tipo_elemento = 'ACTO' WHERE tipo_elemento = 'SOLICITUD'"
    ))
    if renombradas.rowcount == 0:
        raise RuntimeError(
            'No se encontró ninguna fila de nivel SOLICITUD que renombrar a ACTO — '
            'verificar que el seed 448 y siguientes siguen sembrando ANY/AAP, ANY/DUP...'
        )

    op.create_check_constraint(_CHECK, 'catalogo_plazos', _CHECK_DESPUES, schema='public')

    _comentar(despues=True)


def downgrade():
    conn = op.get_bind()

    op.drop_constraint(_CHECK, 'catalogo_plazos', schema='public', type_='check')

    conn.execute(sa.text(
        "UPDATE public.catalogo_plazos SET tipo_elemento = 'SOLICITUD' WHERE tipo_elemento = 'ACTO'"
    ))

    efecto_id = conn.execute(sa.text(
        'SELECT id FROM public.efectos_plazo WHERE codigo = :codigo'
    ), {'codigo': _EFECTO}).scalar()
    if efecto_id is None:
        raise ValueError(f"Efecto '{_EFECTO}' no encontrado en efectos_plazo")

    for tipo, camino, valor, norma, orden, cumplimiento in _RETIRADAS:
        # catalogo_plazos no tiene UNIQUE sobre camino: idempotencia por
        # comprobación previa, como #892.
        ya_existe = conn.execute(sa.text(
            'SELECT 1 FROM public.catalogo_plazos WHERE camino = :camino'
        ), {'camino': camino}).scalar()
        if ya_existe:
            continue
        conn.execute(sa.text("""
            INSERT INTO public.catalogo_plazos
                (tipo_elemento, camino, plazo_valor, plazo_unidad, efecto_vencimiento_id,
                 norma_origen, orden, suspende_plazo_solicitud, campo_fecha,
                 campo_fecha_cumplimiento)
            VALUES
                (:tipo, :camino, :valor, 'MESES', :efecto_id,
                 :norma, :orden, FALSE, CAST(:campo_fecha AS jsonb),
                 CAST(:cumplimiento AS jsonb))
        """), {
            'tipo': tipo, 'camino': camino, 'valor': valor, 'efecto_id': efecto_id,
            'norma': norma, 'orden': orden, 'campo_fecha': _FK_SOLICITUD,
            'cumplimiento': cumplimiento,
        })

    op.create_check_constraint(_CHECK, 'catalogo_plazos', _CHECK_ANTES, schema='public')

    _comentar(despues=False)
