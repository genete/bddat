"""928b_ttd_multiples_entradas — id PK + índice único funcional; ENTRADA de N1

Revision ID: 928b_ttd_multiples_entradas
Revises: 928a_justificantes_notificacion
Create Date: 2026-09-22

Issue #928 (N1), ADR-049 §B/§2. `tramites_tareas_documentos` pasa de PK
compuesta (tipo_tramite_id, orden_tarea, rol) a `id SERIAL` + índice único
funcional sobre (tipo_tramite_id, orden_tarea, rol, COALESCE(tipo_documento_id, 0)):
sigue impidiendo el duplicado exacto (mismo tipo, o dos polimórficas) pero
admite varias filas ENTRADA distintas en el mismo paso — necesario porque los
tres justificantes previos de notificación conviven con el documento a
notificar en la misma ENTRADA de NOTIFICAR. Al añadir la columna SERIAL,
Postgres numera las filas existentes: no hace falta `setval`.

Añade las filas ENTRADA (obligatorio=false) de los tres tipos nuevos de 928a
en los 11 trámites cuyo NOTIFICAR va al titular u otro interesado (§2, D8,
confirmado por Carlos 21/09/2026, corregido 23/09/2026): NOTIFICACION,
NOTIFICACION_INTERESADOS, COMUNICACION_INICIO_ADMISION,
REQUERIMIENTO_SUBSANACION, REQUERIMIENTO_RBDA_DEFINITIVA,
REQUERIMIENTO_CATASTRALES, CONSULTA_TRASLADO_TITULAR, ANUNCIO_TITULAR,
TOMA_RAZON_RBDA, RECEPCION_ALEGACION, REMISION_ACUERDO_DATOS. El resto
(organismos, Medio Ambiente, publicaciones, portal) se deja fuera a
propósito: cada fila exacta añadida a una ENTRADA vuelve ambigua la
sugerencia de tipo de la Despensa (`sugerencia_documento.py:63`,
`len(tipos_exactos) != 1` → en blanco), coste aceptado solo donde el usuario
elige el tipo.

`CONSULTA_SEPARATA` **no** entra, corrección sobre el D8 original: notifica a
un organismo (envío de la separata, `DISEÑO_CONSULTAS_ORGANISMOS.md` §4), no
al titular ni a otro interesado — el pre-ADR la incluyó por descuido con la
salvedad "(cuando va por Notifica)", que confunde canal con destinatario.
"""
from alembic import op
import sqlalchemy as sa


revision = '928b_ttd_multiples_entradas'
down_revision = '928a_justificantes_notificacion'
branch_labels = None
depends_on = None

_TIPOS_DOC_NUEVOS = (
    'JUSTIFICANTE_NOTIFICA_DISPOSICION',
    'JUSTIFICANTE_POSTAL_1ER',
    'JUSTIFICANTE_SEDE',
)

# (código de trámite, orden_tarea de su NOTIFICAR) — verificado en BD real, 22/09/2026
_TRAMITES_NOTIFICAR_TITULAR = (
    ('NOTIFICACION', 1),
    ('NOTIFICACION_INTERESADOS', 1),
    ('COMUNICACION_INICIO_ADMISION', 2),
    ('REQUERIMIENTO_SUBSANACION', 2),
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 2),
    ('REQUERIMIENTO_CATASTRALES', 2),
    ('CONSULTA_TRASLADO_TITULAR', 2),
    ('ANUNCIO_TITULAR', 2),
    ('TOMA_RAZON_RBDA', 2),
    ('RECEPCION_ALEGACION', 3),
    ('REMISION_ACUERDO_DATOS', 2),
)


def upgrade():
    conn = op.get_bind()

    op.execute('ALTER TABLE public.tramites_tareas_documentos DROP CONSTRAINT pk_ttd')
    op.execute('ALTER TABLE public.tramites_tareas_documentos ADD COLUMN id SERIAL')
    op.execute('ALTER TABLE public.tramites_tareas_documentos ADD CONSTRAINT pk_ttd PRIMARY KEY (id)')
    op.execute("""
        CREATE UNIQUE INDEX uq_ttd_paso_tipo_documento
        ON public.tramites_tareas_documentos
        (tipo_tramite_id, orden_tarea, rol, COALESCE(tipo_documento_id, 0))
    """)

    for tramite_codigo, orden_tarea in _TRAMITES_NOTIFICAR_TITULAR:
        for tipo_doc_codigo in _TIPOS_DOC_NUEVOS:
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas_documentos
                    (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
                SELECT tt.id, :orden_tarea, 'ENTRADA', td.id, false
                FROM public.tipos_tramites tt, public.tipos_documentos td
                WHERE tt.codigo = :tramite_codigo AND td.codigo = :tipo_doc_codigo
                ON CONFLICT DO NOTHING
            """), {
                'tramite_codigo': tramite_codigo,
                'orden_tarea': orden_tarea,
                'tipo_doc_codigo': tipo_doc_codigo,
            })


def downgrade():
    conn = op.get_bind()

    for tramite_codigo, orden_tarea in _TRAMITES_NOTIFICAR_TITULAR:
        conn.execute(sa.text("""
            DELETE FROM public.tramites_tareas_documentos ttd
            USING public.tipos_tramites tt, public.tipos_documentos td
            WHERE ttd.tipo_tramite_id = tt.id
              AND ttd.tipo_documento_id = td.id
              AND tt.codigo = :tramite_codigo
              AND ttd.orden_tarea = :orden_tarea
              AND ttd.rol = 'ENTRADA'
              AND td.codigo = ANY(:tipos_nuevos)
        """), {
            'tramite_codigo': tramite_codigo,
            'orden_tarea': orden_tarea,
            'tipos_nuevos': list(_TIPOS_DOC_NUEVOS),
        })

    op.execute('DROP INDEX public.uq_ttd_paso_tipo_documento')
    op.execute('ALTER TABLE public.tramites_tareas_documentos DROP CONSTRAINT pk_ttd')
    op.execute('ALTER TABLE public.tramites_tareas_documentos DROP COLUMN id')
    op.execute("""
        ALTER TABLE public.tramites_tareas_documentos
        ADD CONSTRAINT pk_ttd PRIMARY KEY (tipo_tramite_id, orden_tarea, rol)
    """)
