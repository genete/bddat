"""500_seed_abrev_esftt — poblar abrev en catálogos ESFTT (vista de árbol)

Revision ID: 500_seed_abrev_esftt
Revises: 685e93a0c79e
Create Date: 2026-05-30

Issue #500 — Vista de árbol del expediente (ADR-016).
Pobla `abrev` (etiqueta corta en MAYÚSCULAS) en tipos_fases / tipos_tramites /
tipos_tareas para que los nodos del árbol muestren texto corto. Las solicitudes
usan `siglas` (no necesitan abrev). Donde abrev queda NULL, el front cae a `nombre`.
"""
from alembic import op
import sqlalchemy as sa


revision = '500_seed_abrev_esftt'
down_revision = '685e93a0c79e'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # --- Fases ---
    conn.execute(sa.text("""
        UPDATE public.tipos_fases AS t SET abrev = v.abrev
        FROM (VALUES
          ('AAU_AAUS_INTEGRADA',        'AAU/AAUS'),
          ('ANALISIS_SOLICITUD',        'ANÁLISIS SOL.'),
          ('COMPATIBILIDAD_AMBIENTAL',  'COMPAT. AMB.'),
          ('CONSULTA_MINISTERIO',       'CONSULTA MIN.'),
          ('CONSULTAS',                 'CONSULTAS'),
          ('FIGURA_AMBIENTAL_EXTERNA',  'INSTR. AMB. EXT.'),
          ('INFORMACION_PUBLICA',       'INF. PÚBLICA'),
          ('RECONOCIMIENTO_INTERESADO', 'REC. INTERESADO'),
          ('RESOLUCION',                'RESOLUCIÓN')
        ) AS v(codigo, abrev)
        WHERE t.codigo = v.codigo
    """))

    # --- Trámites ---
    conn.execute(sa.text("""
        UPDATE public.tipos_tramites AS t SET abrev = v.abrev
        FROM (VALUES
          ('ANALISIS_ALEGACIONES',           'ANÁL. ALEGAC.'),
          ('ANALISIS_DOCUMENTAL',            'ANÁLISIS DOC.'),
          ('ANUNCIO_BOE',                    'ANUNCIO BOE'),
          ('ANUNCIO_BOJA',                   'ANUNCIO BOJA'),
          ('ANUNCIO_BOP',                    'ANUNCIO BOP'),
          ('ANUNCIO_PRENSA',                 'ANUNCIO PRENSA'),
          ('ANUNCIO_TITULAR',                'NOTIF. TITULAR'),
          ('COMUNICACION_AUDIENCIA',         'COM. AUDIENCIA'),
          ('COMUNICACION_INICIO',            'COM. INICIO'),
          ('CONSULTA_SEPARATA',              'SEPARATA'),
          ('CONSULTA_TRASLADO_ORGANISMO',    'TRASLADO ORG.'),
          ('CONSULTA_TRASLADO_TITULAR',      'TRASLADO TIT.'),
          ('DISCREPANCIA_INF_VINC',          'DISCREPANCIA IV'),
          ('ELABORACION',                    'ELAB. RESOLUCIÓN'),
          ('NOTIFICACION',                   'NOTIF. RESOL.'),
          ('PORTAL_TRANSPARENCIA',           'PORTAL TRANSP.'),
          ('PUBLICACION',                    'PUB. RESOLUCIÓN'),
          ('RECEPCION_ALEGACION',            'REC. ALEGACIÓN'),
          ('RECEPCION_DICTAMEN',             'REC. DICTAMEN'),
          ('RECEPCION_FIGURA',               'REC. INSTRUMENTO'),
          ('RECEPCION_INFORME',              'REC. INFORME'),
          ('RECEPCION_INFORME_VINCULANTE',   'REC. INF. VINC.'),
          ('RECEPCION_PROPUESTA_INF_VINC',   'REC. PROP. IV'),
          ('REDACTAR_ANUNCIO',               'REDACCIÓN ANUNCIO'),
          ('REGISTRO_INTERESADOS',           'REG. INTERESADOS'),
          ('REMISION_RESULTADO_IP_CONSULTAS','REMISIÓN A MA'),
          ('REQUERIMIENTO_SUBSANACION',      'REQ. SUBSANACIÓN'),
          ('SOLICITUD_COMPATIBILIDAD',       'SOL. COMPATIB.'),
          ('SOLICITUD_FIGURA',               'SOL. INSTRUMENTO'),
          ('SOLICITUD_INFORME',              'SOL. INFORME'),
          ('TABLON_AYUNTAMIENTOS',           'TABLÓN AYUNT.')
        ) AS v(codigo, abrev)
        WHERE t.codigo = v.codigo
    """))

    # --- Tareas (ANÁLISIS/PLAZO/NOTIFICAR ya existían; ELABORAR es nuevo) ---
    conn.execute(sa.text("""
        UPDATE public.tipos_tareas AS t SET abrev = v.abrev
        FROM (VALUES
          ('ANALIZAR',      'ANÁLISIS'),
          ('ELABORAR',      'ELABORAR'),
          ('ESPERAR_PLAZO', 'PLAZO'),
          ('NOTIFICAR',     'NOTIFICAR')
        ) AS v(codigo, abrev)
        WHERE t.codigo = v.codigo
    """))


def downgrade():
    conn = op.get_bind()
    # Fases: todas vuelven a NULL salvo RECONOCIMIENTO_INTERESADO (tenía "Rec. Interesado").
    conn.execute(sa.text(
        "UPDATE public.tipos_fases SET abrev = NULL WHERE codigo <> 'RECONOCIMIENTO_INTERESADO'"))
    conn.execute(sa.text(
        "UPDATE public.tipos_fases SET abrev = 'Rec. Interesado' WHERE codigo = 'RECONOCIMIENTO_INTERESADO'"))
    # Trámites: todos eran NULL.
    conn.execute(sa.text("UPDATE public.tipos_tramites SET abrev = NULL"))
    # Tareas: solo ELABORAR era NULL (las otras 3 ya existían — no se tocan).
    conn.execute(sa.text("UPDATE public.tipos_tareas SET abrev = NULL WHERE codigo = 'ELABORAR'"))
