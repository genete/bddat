"""914_tipos_tramites_tareas — 11 trámites nuevos de RESOLUCION_DUP/DATOS_CATASTRALES

Revision ID: 914_tipos_tramites_tareas
Revises: 914_tipos_documentos_dup
Create Date: 2026-09-14

Issue #914, ADR-046 y DISEÑO_RESOLUCION_DUP.md §1-§2. No incluye ELABORACION
ni NOTIFICACION de RESOLUCION_DUP: son tipos_tramites ya existentes,
compartidos con RESOLUCION (mismo patrón que ADR-037/#725) — se vinculan a
la fase en la migración siguiente (fases_tramites), sin fila nueva aquí.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tipos_tramites_tareas'
down_revision = '914_tipos_documentos_dup'
branch_labels = None
depends_on = None

# (codigo, nombre, abrev, nombre_en_plantilla, [tareas en orden])
_TRAMITES = [
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 'Requerimiento de RBDA Definitiva',
     'REQ. RBDA DEF.', 'Requerimiento de RBDA Definitiva',
     ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('NOTIFICACION_ORGANISMOS', 'Notificación a Organismos',
     'NOTIF. ORGANISMOS', 'Notificación a Organismos',
     ['NOTIFICAR']),
    ('NOTIFICACION_INTERESADOS', 'Notificación a Interesados',
     'NOTIF. INTERESADOS', 'Notificación a Interesados',
     ['NOTIFICAR']),
    ('PUBLICACION_BOP', 'Publicación en BOP',
     'PUBLIC. BOP', 'Publicación en BOP',
     ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('PUBLICACION_BOJA', 'Publicación en BOJA',
     'PUBLIC. BOJA', 'Publicación en BOJA',
     ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('PUBLICACION_BOE', 'Publicación en BOE',
     'PUBLIC. BOE', 'Publicación en BOE',
     ['NOTIFICAR', 'ESPERAR_PLAZO', 'ESPERAR_PLAZO']),
    ('SOLICITUD_CATASTRALES', 'Solicitud de Datos Catastrales',
     'SOLIC. CATASTRALES', 'Solicitud de Datos Catastrales',
     ['ANALIZAR']),
    ('REQUERIMIENTO_CATASTRALES', 'Requerimiento de Datos Catastrales',
     'REQ. CATASTRALES', 'Requerimiento de Datos Catastrales',
     ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO', 'ANALIZAR']),
    ('REMISION_ACUERDO_DATOS', 'Remisión de Acuerdo de Cesión de Datos Catastrales',
     'REMIS. ACUERDO', 'Remisión de Acuerdo de Cesión de Datos',
     ['ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO']),
    ('ANALISIS_RBDA', 'Análisis de la RBDA',
     'ANÁLISIS RBDA', 'Análisis de la RBDA',
     ['ANALIZAR']),
    ('TOMA_RAZON_RBDA', 'Toma de Razón de la RBDA',
     'TOMA RAZÓN RBDA', 'Toma de Razón de la RBDA',
     ['ELABORAR', 'NOTIFICAR']),
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

    for codigo, nombre, abrev, nombre_en_plantilla, tareas in _TRAMITES:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_tramites (codigo, nombre, abrev, nombre_en_plantilla)
            VALUES (:codigo, :nombre, :abrev, :nombre_en_plantilla)
            ON CONFLICT DO NOTHING
        """), {'codigo': codigo, 'nombre': nombre, 'abrev': abrev,
               'nombre_en_plantilla': nombre_en_plantilla})

        tt_id = _get_id(conn, 'tipos_tramites', codigo)
        for orden, tarea_codigo in enumerate(tareas, start=1):
            ta_id = _get_id(conn, 'tipos_tareas', tarea_codigo)
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
                VALUES (:tt_id, :orden, :ta_id)
                ON CONFLICT DO NOTHING
            """), {'tt_id': tt_id, 'orden': orden, 'ta_id': ta_id})


def downgrade():
    conn = op.get_bind()
    for codigo, _nombre, _abrev, _npl, _tareas in _TRAMITES:
        conn.execute(sa.text("""
            DELETE FROM public.tramites_tareas
            WHERE tipo_tramite_id = (SELECT id FROM public.tipos_tramites WHERE codigo = :c)
        """), {'c': codigo})
        conn.execute(sa.text(
            "DELETE FROM public.tipos_tramites WHERE codigo = :c"
        ), {'c': codigo})
