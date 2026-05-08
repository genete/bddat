"""345_seed_tramites_tareas — secuencias de tareas por trámite

Revision ID: 345_seed_tramites_tareas
Revises: 345_tramites_tareas
Create Date: 2026-05-08

Issue #345 — Pobla tramites_tareas con las secuencias definidas en
ESTRUCTURA_FTT.json (fuente de verdad). Falla ruidosamente si algún
código de trámite o tarea no existe en BD.

RECEPCION_INFORME aparece en dos fases del JSON (CONSULTA_MINISTERIO y
COMPATIBILIDAD_AMBIENTAL) pero comparte el mismo registro en tipos_tramites;
el seed inserta una sola vez con la secuencia [INCORPORAR, ANALIZAR].
"""
from alembic import op
import sqlalchemy as sa


revision = '345_seed_tramites_tareas'
down_revision = '345_tramites_tareas'
branch_labels = None
depends_on = None

# (tipo_tramite.codigo, [tipo_tarea.codigo en orden 1-based])
# Fuente: ESTRUCTURA_FTT.json v5.6
_SECUENCIAS = [
    ('ANALISIS_DOCUMENTAL',        ['ANALIZAR']),
    ('REQUERIMIENTO_SUBSANACION',  ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ANALIZAR']),
    ('COMUNICACION_INICIO',        ['REDACTAR', 'FIRMAR', 'NOTIFICAR']),
    ('SOLICITUD_INFORME',          ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_INFORME',          ['INCORPORAR', 'ANALIZAR']),
    ('SOLICITUD_COMPATIBILIDAD',   ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('AUDIENCIA',                  ['INCORPORAR', 'ANALIZAR', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('CONSULTA_SEPARATA',          ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ANALIZAR']),
    ('CONSULTA_TRASLADO_TITULAR',  ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ANALIZAR']),
    ('CONSULTA_TRASLADO_ORGANISMO',['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ANALIZAR']),
    # ANUNCIO_*: doble ESPERAR_PLAZO (hasta publicación efectiva + plazo alegaciones)
    ('ANUNCIO_BOE',                ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ESPERAR_PLAZO']),
    ('ANUNCIO_BOP',                ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ESPERAR_PLAZO']),
    ('ANUNCIO_PRENSA',             ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR', 'ESPERAR_PLAZO']),
    ('TABLON_AYUNTAMIENTOS',       ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'INCORPORAR']),
    ('PORTAL_TRANSPARENCIA',       ['REDACTAR', 'FIRMAR', 'PUBLICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_ALEGACION',        ['INCORPORAR', 'ANALIZAR', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('ANALISIS_ALEGACIONES',       ['ANALIZAR']),
    ('SOLICITUD_FIGURA',           ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_FIGURA',           ['INCORPORAR', 'ANALIZAR']),
    ('REMISION_MEDIO_AMBIENTE',    ['REDACTAR', 'FIRMAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('RECEPCION_DICTAMEN',         ['INCORPORAR', 'ANALIZAR']),
    ('ELABORACION',                ['ANALIZAR', 'REDACTAR', 'FIRMAR']),
    ('NOTIFICACION',               ['REDACTAR', 'NOTIFICAR']),
    ('PUBLICACION',                ['REDACTAR', 'FIRMAR', 'PUBLICAR']),
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
