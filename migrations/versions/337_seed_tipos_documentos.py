"""337_seed_tipos_documentos — seed completo del catálogo de tipos de documentos

Revision ID: 337_seed_tipos_documentos
Revises: 373_cert_fin_instruccion
Create Date: 2026-05-13

Issue #337 — Pobla tipos_documentos con el catálogo completo definido en
docs/referencia/TIPOS_DOCUMENTOS_CATALOGO.md. Usa ON CONFLICT DO NOTHING
para ser idempotente con los tipos ya presentes (OTROS, DR_NO_DUP,
CERT_FIN_INSTRUCCION insertados en migraciones anteriores).
"""
from alembic import op
import sqlalchemy as sa


revision = '337_seed_tipos_documentos'
down_revision = '373_cert_fin_instruccion'
branch_labels = None
depends_on = None

# (codigo, nombre, origen)
_TIPOS = [
    # Justificantes de notificación
    ('JUSTIFICANTE_NOTIFICA',    'Justificante Notifica-PNT',                        'EXTERNO'),
    ('JUSTIFICANTE_BANDEJA',     'Justificante BandeJA',                             'EXTERNO'),
    ('JUSTIFICANTE_SIR',         'Justificante SIR / ARIES',                         'EXTERNO'),
    ('JUSTIFICANTE_POSTAL',      'Justificante notificación postal',                  'EXTERNO'),
    # Justificantes de publicación
    ('JUSTIFICANTE_BOE',         'Justificante publicación BOE',                      'EXTERNO'),
    ('JUSTIFICANTE_BOP',         'Justificante publicación BOP',                      'EXTERNO'),
    ('JUSTIFICANTE_BOJA',        'Justificante publicación BOJA',                     'EXTERNO'),
    ('JUSTIFICANTE_PRENSA',      'Justificante publicación prensa',                   'EXTERNO'),
    ('JUSTIFICANTE_TABLON',      'Certificado de exposición en tablón',               'EXTERNO'),
    ('JUSTIFICANTE_PORTAL',      'URL de acto de exposición en portal de transparencia', 'EXTERNO'),
    # Documentos internos generados por el motor
    ('CERT_PLAZO_CUMPLIDO',      'Certificado de plazo cumplido',                     'INTERNO'),
    ('DIAGNOSTICO',              'Diagnóstico de análisis',                           'INTERNO'),
    # ANALISIS_SOLICITUD
    ('OFICIO_REQUERIMIENTO',     'Oficio de requerimiento de subsanación',            'INTERNO'),
    ('SUBSANACION',              'Documentación de subsanación del titular',           'EXTERNO'),
    ('OFICIO_INICIO',            'Oficio de comunicación de inicio de expediente',    'INTERNO'),
    # CONSULTA_MINISTERIO
    ('OFICIO_114_RD1955',        'Oficio de solicitud de informe preceptivo al Ministerio (art. 114 RD 1955/2000)', 'INTERNO'),
    ('INFORME_114_RD1955',       'Informe preceptivo del Ministerio (art. 114 RD 1955/2000)', 'EXTERNO'),
    # COMPATIBILIDAD_AMBIENTAL
    ('DOC_SOLICITUD_AAU',        'Solicitud de autorización ambiental unificada (modelo oficial)', 'EXTERNO'),
    ('OFICIO_COMPATIBILIDAD_AMBIENTAL', 'Oficio de remisión de solicitud de compatibilidad ambiental', 'INTERNO'),
    ('INFORME_COMPATIBILIDAD_AMBIENTAL', 'Informe de compatibilidad ambiental del órgano ambiental', 'EXTERNO'),
    ('DOC_COMUNICACION_AUDIENCIA', 'Escrito de comunicación de audiencia al interesado', 'EXTERNO'),
    # CONSULTAS
    ('DOC_SEPARATA',             'Separata del proyecto aportada por el solicitante', 'EXTERNO'),
    ('OFICIO_SEPARATA',          'Oficio de consulta a organismo sectorial',           'INTERNO'),
    ('RESPUESTA_ORGANISMO',      'Respuesta del organismo sectorial a la consulta',    'EXTERNO'),
    ('OFICIO_TRASLADO_RESPUESTA', 'Oficio de traslado de respuesta del organismo al titular', 'INTERNO'),
    ('RESPUESTA_TITULAR',        'Respuesta del titular a los reparos del organismo',  'EXTERNO'),
    ('OFICIO_TRASLADO_REPAROS',  'Oficio de traslado de reparos del titular al organismo sectorial', 'INTERNO'),
    # INFORMACION_PUBLICA
    ('DOC_PROYECTO',             'Proyecto técnico del titular',                       'EXTERNO'),
    ('ANUNCIO_IP',               'Anuncio de información pública',                     'INTERNO'),
    ('OFICIO_PUBLICAR_TITULAR',  'Oficio de publicación de anuncio al titular',        'INTERNO'),
    ('OFICIO_PUBLICAR_BOLETIN',  'Oficio de remisión de anuncio al boletín oficial',   'INTERNO'),
    ('ANUNCIO_PUBLICADO',        'Copia del anuncio publicado en boletín oficial',     'EXTERNO'),
    ('OFICIO_TABLON',            'Oficio de solicitud de exposición en tablón de ayuntamiento', 'INTERNO'),
    ('CERT_PLAZO_TABLON',        'Certificado de exposición en tablón de ayuntamiento', 'EXTERNO'),
    ('ALEGACION_IP',             'Alegación de información pública',                   'EXTERNO'),
    ('OFICIO_TRASLADO_ALEGACION', 'Oficio de traslado de alegación al titular',        'INTERNO'),
    ('RESPUESTA_TITULAR_ALEGACION', 'Respuesta del titular a la alegación',            'EXTERNO'),
    # FIGURA_AMBIENTAL_EXTERNA
    ('OFICIO_SOLICITUD_FIGURA',  'Oficio de solicitud de figura ambiental externa',    'INTERNO'),
    ('FIGURA_AMBIENTAL_EXTERNA', 'Figura ambiental externa obtenida por el promotor',  'EXTERNO'),
    # RESOLUCION
    ('RESOLUCION',               'Resolución de autorización administrativa',          'INTERNO'),
    ('RESOLUCION_PUBLICADA',     'Resolución publicada en boletín oficial',            'EXTERNO'),
    # AAU_AAUS_INTEGRADA
    ('CERT_FIN_IP_CONSULTAS',    'Certificado de fin de IP y consultas',               'INTERNO'),
    ('OFICIO_RESULTADO_IP_CON',  'Oficio de remisión del resultado de IP y consultas al órgano ambiental', 'INTERNO'),
    ('DOC_DICTAMEN_AMBIENTAL',   'Dictamen ambiental del órgano ambiental',            'EXTERNO'),
    ('OFICIO_OBS_DICTAMEN',      'Oficio de observaciones al dictamen ambiental',      'INTERNO'),
    ('DOC_PROPUESTA_INF_VINC',   'Propuesta de informe vinculante del órgano ambiental', 'EXTERNO'),
    ('OFICIO_OBS_PROP_INF_VINC', 'Oficio de observaciones a la propuesta de informe vinculante', 'INTERNO'),
    ('DOC_INFORME_VINCULANTE',   'Informe vinculante del órgano ambiental',            'EXTERNO'),
    ('OFICIO_DISCREPANCIA_INF_VINC', 'Oficio de planteamiento de discrepancia sobre el informe vinculante', 'INTERNO'),
    ('RESOLUCION_DISCREPANCIA_INF_VINC', 'Resolución del Consejo de Gobierno sobre discrepancia en informe vinculante', 'EXTERNO'),
]


def upgrade():
    conn = op.get_bind()
    for codigo, nombre, origen in _TIPOS:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, origen)
            VALUES (:codigo, :nombre, :origen)
            ON CONFLICT (codigo) DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'origen': origen})


def downgrade():
    conn = op.get_bind()
    codigos = [t[0] for t in _TIPOS]
    conn.execute(
        sa.text("DELETE FROM public.tipos_documentos WHERE codigo = ANY(:codigos)"),
        {'codigos': codigos}
    )
