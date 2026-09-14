"""914_tramites_tareas_docs — documentos consumidos/producidos de los trámites nuevos

Revision ID: 914_tramites_tareas_docs
Revises: 914_fases_tramites_dup
Create Date: 2026-09-14

Issue #914. Cobertura completa (test_346_mapa_documentos.py, #346): todo
NOTIFICAR necesita fila SALIDA y todo ESPERAR_PLAZO fila ENTRADA, aunque sea
con tipo_documento_id NULL ("polimórfico") — la ausencia de fila no es
válida, a diferencia de lo que asumía la primera versión de esta migración.
ELABORAR/ANALIZAR llevan el tipo de documento concreto que fija el diseño
(DISEÑO_RESOLUCION_DUP.md §1-§2). No toca ELABORACION/NOTIFICACION de
RESOLUCION_DUP (compartidos con RESOLUCION, ya poblados).

PK real (tipo_tramite_id, orden_tarea, rol): una sola fila por (trámite,
tarea, rol), no una lista. REMISION_ACUERDO_DATOS.ELABORAR consume
XML_DE_CATASTRO + DR_DATOS_CATASTRALES (dos documentos igual de necesarios)
y ANALISIS_RBDA.ANALIZAR consume RBDA + RBDA_DIRECCIONES — no se declara
ENTRADA para estos dos por no poder representar ambos sin elegir
arbitrariamente uno.

NULL polimórfico (sin tipo de documento concreto, mismo patrón que otros
trámites del catálogo — p.ej. NOTIFICACION genérica no declara SALIDA):
  - Todo NOTIFICAR sin oficio propio que elaborar antes (el trámite no tiene
    ELABORAR, o su ELABORAR ya generó lo que se remite): justificante
    genérico, medio de notificación variable.
  - Los ESPERAR_PLAZO cuya entrada es ese mismo justificante genérico.
Con tipo documental concreto:
  - PUBLICACION_BOP/BOJA/BOE: la primera ESPERAR_PLAZO produce ANUNCIO_PUBLICADO
    (la administración introduce manualmente la fecha de publicación efectiva
    — mismo patrón que ANUNCIO_BOP/BOJA de INFORMACION_PUBLICA); la segunda
    lo consume para contar el plazo de vigencia.
"""
from alembic import op
import sqlalchemy as sa


revision = '914_tramites_tareas_docs'
down_revision = '914_fases_tramites_dup'
branch_labels = None
depends_on = None

# (tipo_tramite.codigo, orden_tarea, rol, tipo_documento.codigo | None, obligatorio)
_FILAS = [
    # --- RESOLUCION_DUP ---
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 1, 'SALIDA', 'OFICIO_REQUERIMIENTO_RBDA_DEFINITIVA', True),
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 2, 'SALIDA', None, True),
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 3, 'ENTRADA', None, True),
    ('REQUERIMIENTO_RBDA_DEFINITIVA', 3, 'SALIDA', 'RBDA_DEFINITIVA', False),

    ('NOTIFICACION_ORGANISMOS', 1, 'ENTRADA', 'RESOLUCION', True),
    ('NOTIFICACION_ORGANISMOS', 1, 'SALIDA', None, True),
    ('NOTIFICACION_INTERESADOS', 1, 'ENTRADA', 'RESOLUCION', True),
    ('NOTIFICACION_INTERESADOS', 1, 'SALIDA', None, True),

    ('PUBLICACION_BOP', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOP', 1, 'SALIDA', None, True),
    ('PUBLICACION_BOP', 2, 'ENTRADA', None, True),
    ('PUBLICACION_BOP', 2, 'SALIDA', 'ANUNCIO_PUBLICADO', True),
    ('PUBLICACION_BOP', 3, 'ENTRADA', 'ANUNCIO_PUBLICADO', True),

    ('PUBLICACION_BOJA', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOJA', 1, 'SALIDA', None, True),
    ('PUBLICACION_BOJA', 2, 'ENTRADA', None, True),
    ('PUBLICACION_BOJA', 2, 'SALIDA', 'ANUNCIO_PUBLICADO', True),
    ('PUBLICACION_BOJA', 3, 'ENTRADA', 'ANUNCIO_PUBLICADO', True),

    ('PUBLICACION_BOE', 1, 'ENTRADA', 'RESOLUCION', True),
    ('PUBLICACION_BOE', 1, 'SALIDA', None, True),
    ('PUBLICACION_BOE', 2, 'ENTRADA', None, True),
    ('PUBLICACION_BOE', 2, 'SALIDA', 'ANUNCIO_PUBLICADO', True),
    ('PUBLICACION_BOE', 3, 'ENTRADA', 'ANUNCIO_PUBLICADO', True),

    # --- DATOS_CATASTRALES ---
    ('SOLICITUD_CATASTRALES', 1, 'SALIDA', 'DIAGNOSTICO', True),

    ('REQUERIMIENTO_CATASTRALES', 1, 'SALIDA', 'OFICIO_REQUERIMIENTO_CATASTRALES', True),
    ('REQUERIMIENTO_CATASTRALES', 2, 'SALIDA', None, True),
    ('REQUERIMIENTO_CATASTRALES', 3, 'ENTRADA', None, True),
    ('REQUERIMIENTO_CATASTRALES', 4, 'SALIDA', 'DIAGNOSTICO', True),

    ('REMISION_ACUERDO_DATOS', 1, 'SALIDA', 'ACUERDO_CESION_CATASTRALES', True),
    ('REMISION_ACUERDO_DATOS', 2, 'SALIDA', None, True),
    ('REMISION_ACUERDO_DATOS', 3, 'ENTRADA', None, True),

    ('ANALISIS_RBDA', 1, 'SALIDA', 'DIAGNOSTICO', True),

    ('TOMA_RAZON_RBDA', 1, 'SALIDA', 'OFICIO_TOMA_RAZON_RBDA', True),
    ('TOMA_RAZON_RBDA', 2, 'SALIDA', None, True),
]


def _get_id(conn, tabla, codigo):
    if codigo is None:
        return None
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
