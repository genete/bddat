"""914_tipos_documentos_dup — 10 documentos nuevos de RESOLUCION_DUP/DATOS_CATASTRALES

Revision ID: 914_tipos_documentos_dup
Revises: 914_tipos_fases_dup
Create Date: 2026-09-14

Issue #914, ADR-046 §G y DISEÑO_RESOLUCION_DUP.md §3. 8 documentos del diseño
original + 2 de REQUERIMIENTO_RBDA_DEFINITIVA (añadido después, procedimiento
interno del servicio).

De paso, generaliza la descripción de RESOLUCION (id 3... realmente el código
existente, ver catálogo): decisión de la sesión — RESOLUCION_DUP reutiliza el
mismo tipo_documento RESOLUCION que la autorización (no uno propio), porque
tramites_tareas_documentos tiene PK (tipo_tramite_id, orden_tarea, rol) y
RESOLUCION_DUP.ELABORACION comparte el tipo_tramite ELABORACION con
RESOLUCION — no puede declarar un tipo de documento de salida distinto para
la misma fila. Precedente: DOC_PROYECTO ya cubre variantes (reformado o no)
sin desdoblar tipo; el contexto (documentos_tarea → tarea → fase) es lo que
distingue de qué acto se trata, no el tipo de catálogo.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tipos_documentos_dup'
down_revision = '914_tipos_fases_dup'
branch_labels = None
depends_on = None

# (codigo, nombre, descripcion, origen)
_DOCUMENTOS = [
    ('RBDA', 'Relación de Bienes y Derechos Afectados',
     'Planos + afecciones por titular/propietario (no necesariamente parcela '
     'catastral) + valor numérico. Identificación NIF/DNI (persona física) o '
     'NIF+nombre (persona jurídica). Contenido no evaluado por BDDAT. Se '
     'publica en información pública (art. 144 RD 1955/2000).',
     'EXTERNO'),
    ('RBDA_DIRECCIONES', 'RBDA — Direcciones de notificación',
     'Mismo listado de afecciones que RBDA, sin planos, con la dirección de '
     'notificación de cada titular. No se publica.',
     'EXTERNO'),
    ('XML_PARA_CATASTRO', 'XML para Catastro',
     'XML aportado por el promotor que la Administración introduce en el '
     'Catastro para la mediación de datos catastrales.',
     'EXTERNO'),
    ('XML_DE_CATASTRO', 'XML de Catastro',
     'Resultado de la consulta al Catastro. Elaboración propia: los datos '
     'vienen del Catastro pero el fichero es artefacto de la Administración.',
     'INTERNO'),
    ('DR_DATOS_CATASTRALES', 'Declaración Responsable de Datos Catastrales',
     'Declaración responsable de tratamiento de datos personales, aportada '
     'por el promotor (origen o subsanación).',
     'EXTERNO'),
    ('ACUERDO_CESION_CATASTRALES', 'Acuerdo de Cesión de Datos Catastrales',
     'Firmado por el/la Delegado/a; fija las obligaciones de protección de '
     'datos personales (LOPD) para la mediación catastral.',
     'INTERNO'),
    ('OFICIO_REQUERIMIENTO_CATASTRALES', 'Oficio de Requerimiento de Datos Catastrales',
     'Requerimiento de subsanación cuando el diagnóstico de la solicitud de '
     'mediación catastral (o de una ronda anterior) resulta desfavorable.',
     'INTERNO'),
    ('OFICIO_TOMA_RAZON_RBDA', 'Oficio de Toma de Razón de la RBDA',
     'Cierra la fase DATOS_CATASTRALES y anuncia el inicio de información '
     'pública/consultas de la solicitud.',
     'INTERNO'),
    ('OFICIO_REQUERIMIENTO_RBDA_DEFINITIVA', 'Oficio de Requerimiento de RBDA Definitiva',
     'Requerimiento al promotor, previo a RESOLUCION_DUP.ELABORACION, para '
     'que aporte la RBDA definitiva o confirme la ya publicada en el anuncio '
     'de información pública. Advierte que, sin respuesta en plazo, se '
     'resuelve con la RBDA publicada.',
     'INTERNO'),
    ('RBDA_DEFINITIVA', 'RBDA Definitiva',
     'Solo parcelas a expropiar, con nombre de propietarios, DNI y '
     'direcciones — o confirmación de la RBDA ya publicada en información '
     'pública. Consumida por RESOLUCION_DUP.ELABORACION.ELABORAR.',
     'EXTERNO'),
]

_DESCRIPCION_RESOLUCION_ANTERIOR = (
    'Acto administrativo que concede o deniega la autorización solicitada. '
    'Fecha administrativa: fecha de firma.'
)
_DESCRIPCION_RESOLUCION_NUEVA = (
    'Acto administrativo resolutorio que concede, deniega o declara lo '
    'solicitado (autorización, declaración de utilidad pública...). Fecha '
    'administrativa: fecha de firma.'
)


def upgrade():
    conn = op.get_bind()
    for codigo, nombre, descripcion, origen in _DOCUMENTOS:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
            VALUES (:codigo, :nombre, :descripcion, :origen)
            ON CONFLICT DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'descripcion': descripcion,
               'origen': origen})

    conn.execute(sa.text("""
        UPDATE public.tipos_documentos SET descripcion = :nueva
        WHERE codigo = 'RESOLUCION' AND descripcion = :anterior
    """), {'nueva': _DESCRIPCION_RESOLUCION_NUEVA,
           'anterior': _DESCRIPCION_RESOLUCION_ANTERIOR})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE public.tipos_documentos SET descripcion = :anterior
        WHERE codigo = 'RESOLUCION' AND descripcion = :nueva
    """), {'anterior': _DESCRIPCION_RESOLUCION_ANTERIOR,
           'nueva': _DESCRIPCION_RESOLUCION_NUEVA})
    for codigo, _nombre, _descripcion, _origen in _DOCUMENTOS:
        conn.execute(sa.text(
            "DELETE FROM public.tipos_documentos WHERE codigo = :codigo"
        ), {'codigo': codigo})
