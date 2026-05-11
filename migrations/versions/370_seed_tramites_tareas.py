"""370_seed_tramites_tareas — re-seed completo v6.0, 30 trámites

Revision ID: 370_seed_tramites_tareas
Revises: 370_actualizar_tipos_tramites
Create Date: 2026-05-11

Issue #370 — Repobla tramites_tareas con las secuencias de ESTRUCTURA_FTT.json v6.0.
Sin referencias a REDACTAR, FIRMAR, INCORPORAR ni PUBLICAR.

RECEPCION_INFORME aparece en dos fases del JSON (CONSULTA_MINISTERIO y
COMPATIBILIDAD_AMBIENTAL) pero comparte el mismo registro en tipos_tramites;
el seed inserta una sola vez con la secuencia [ANALIZAR].
"""
from alembic import op
import sqlalchemy as sa


revision = '370_seed_tramites_tareas'
down_revision = '370_actualizar_tipos_tramites'
branch_labels = None
depends_on = None

# (tipo_tramite.codigo, [tipo_tarea.codigo en orden 1-based])
# Fuente: ESTRUCTURA_FTT.json v6.0
_SECUENCIAS = [
    # ANALISIS_SOLICITUD
    ('ANALISIS_DOCUMENTAL',             ['ANALIZAR']),
    ('REQUERIMIENTO_SUBSANACION',       ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']),
    ('COMUNICACION_INICIO',             ['ELABORAR', 'NOTIFICAR']),
    # CONSULTA_MINISTERIO
    ('SOLICITUD_INFORME',               ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_INFORME',               ['ANALIZAR']),
    # COMPATIBILIDAD_AMBIENTAL
    ('SOLICITUD_COMPATIBILIDAD',        ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('AUDIENCIA',                       ['ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    # RECEPCION_INFORME ya insertado arriba (comparte código entre fases)
    # CONSULTAS
    ('CONSULTA_SEPARATA',               ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']),
    ('CONSULTA_TRASLADO_TITULAR',       ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']),
    ('CONSULTA_TRASLADO_ORGANISMO',     ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']),
    # INFORMACION_PUBLICA
    ('REDACTAR_ANUNCIO',                ['ELABORAR']),
    # ANUNCIO_*: doble ESPERAR_PLAZO (hasta publicación efectiva + plazo alegaciones)
    ('ANUNCIO_BOE',                     ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('ANUNCIO_BOP',                     ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('ANUNCIO_PRENSA',                  ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('ANUNCIO_BOJA',                    ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('TABLON_AYUNTAMIENTOS',            ['NOTIFICAR', 'ESPERAR_PLAZO']),
    ('PORTAL_TRANSPARENCIA',            ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('ANUNCIO_TITULAR',                 ['ELABORAR', 'NOTIFICAR']),
    ('RECEPCION_ALEGACION',             ['ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('ANALISIS_ALEGACIONES',            ['ANALIZAR']),
    # FIGURA_AMBIENTAL_EXTERNA
    ('SOLICITUD_FIGURA',                ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_FIGURA',                ['ANALIZAR']),
    # AAU_AAUS_INTEGRADA
    ('REMISION_RESULTADO_IP_CONSULTAS', ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_DICTAMEN',              ['ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_PROPUESTA_INF_VINC',    ['ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_INFORME_VINCULANTE',    ['ANALIZAR']),
    ('DISCREPANCIA_INF_VINC',           ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    # RESOLUCION
    ('ELABORACION',                     ['ANALIZAR', 'ELABORAR']),
    ('NOTIFICACION',                    ['NOTIFICAR']),
    ('PUBLICACION',                     ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
]


def _get_id(conn, tabla, codigo):
    result = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"),
        {'c': codigo}
    )
    id_ = result.scalar()
    if id_ is None:
        raise ValueError(f"Código '{codigo}' no encontrado en {tabla} — migración abortada")
    return id_


def upgrade():
    conn = op.get_bind()

    for tramite_codigo, tareas in _SECUENCIAS:
        tt_id = _get_id(conn, 'tipos_tramites', tramite_codigo)
        for orden, tarea_codigo in enumerate(tareas, start=1):
            ta_id = _get_id(conn, 'tipos_tareas', tarea_codigo)
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
                VALUES (:tt_id, :orden, :ta_id)
                ON CONFLICT DO NOTHING
            """), {'tt_id': tt_id, 'orden': orden, 'ta_id': ta_id})


def downgrade():
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM public.tramites_tareas"))
