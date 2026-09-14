"""914_tramites_tareas_docs — documentos consumidos/producidos de los trámites nuevos

Revision ID: 914_tramites_tareas_docs
Revises: 914_fases_tramites_dup
Create Date: 2026-09-14

Issue #914. Solo declara lo que el diseño fija con precisión (DISEÑO_RESOLUCION_DUP.md
§1-§2): la salida de cada ELABORAR/ANALIZAR, y las entradas que son un
documento concreto y específico (no un genérico difuso como "la solicitud
presentada" — ANALISIS_DOCUMENTAL tampoco lo declara pese a consumirlo).
No toca ELABORACION/NOTIFICACION de RESOLUCION_DUP (compartidos con
RESOLUCION, ya poblados).

PK real (tipo_tramite_id, orden_tarea, rol): una sola fila por (trámite,
tarea, rol), no una lista. REMISION_ACUERDO_DATOS.ELABORAR consume
XML_DE_CATASTRO + DR_DATOS_CATASTRALES (dos documentos igual de necesarios)
y ANALISIS_RBDA.ANALIZAR consume RBDA + RBDA_DIRECCIONES — no se declara
ninguna ENTRADA para estos dos por no poder representar ambos sin elegir
arbitrariamente uno.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tramites_tareas_docs'
down_revision = '914_fases_tramites_dup'
branch_labels = None
depends_on = None

# (tipo_tramite.codigo, orden_tarea, rol, tipo_documento.codigo, obligatorio)
_FILAS = [
    # RESOLUCION_DUP
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 1, 'SALIDA', 'OFICIO_REQUERIMIENTO_RBDA_DEFINITIVA', True),
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 3, 'SALIDA', 'RBDA_DEFINITIVA', False),
    ('NOTIFICACION_ORGANISMOS', 1, 'ENTRADA', 'RESOLUCION', True),
    ('NOTIFICACION_INTERESADOS', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOP', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOJA', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOE', 1, 'ENTRADA', 'RESOLUCION', True),
    # DATOS_CATASTRALES
    ('SOLICITUD_CATASTRALES', 1, 'SALIDA', 'DIAGNOSTICO', True),
    ('REQUERIMIENTO_CATASTRALES', 1, 'SALIDA', 'OFICIO_REQUERIMIENTO_CATASTRALES', True),
    ('REQUERIMIENTO_CATASTRALES', 4, 'SALIDA', 'DIAGNOSTICO', True),
    ('REMISION_ACUERDO_DATOS', 1, 'SALIDA', 'ACUERDO_CESION_CATASTRALES', True),
    ('ANALISIS_RBDA', 1, 'SALIDA', 'DIAGNOSTICO', True),
    ('TOMA_RAZON_RBDA', 1, 'SALIDA', 'OFICIO_TOMA_RAZON_RBDA', True),
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
    for tramite_codigo, orden_tarea, rol, doc_codigo, obligatorio in _FILAS:
        tt_id = _get_id(conn, 'tipos_tramites', tramite_codigo)
        td_id = _get_id(conn, 'tipos_documentos', doc_codigo)
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas_documentos
                (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
            VALUES (:tt_id, :orden, :rol, :td_id, :obligatorio)
            ON CONFLICT (tipo_tramite_id, orden_tarea, rol) DO NOTHING
        """), {'tt_id': tt_id, 'orden': orden_tarea, 'rol': rol,
               'td_id': td_id, 'obligatorio': obligatorio})


def downgrade():
    conn = op.get_bind()
    for tramite_codigo, orden_tarea, rol, _doc_codigo, _obligatorio in _FILAS:
        conn.execute(sa.text("""
            DELETE FROM public.tramites_tareas_documentos
            WHERE tipo_tramite_id = (SELECT id FROM public.tipos_tramites WHERE codigo = :c)
              AND orden_tarea = :orden AND rol = :rol
        """), {'c': tramite_codigo, 'orden': orden_tarea, 'rol': rol})
