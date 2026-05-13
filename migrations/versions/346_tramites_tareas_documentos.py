"""346_tramites_tareas_documentos — mapa semántico de documentos por tarea

Revision ID: 346_tramites_tareas_documentos
Revises: 337_seed_tipos_documentos
Create Date: 2026-05-13

Issue #346 — Tabla tramites_tareas_documentos:
- Corrige secuencias erróneas en tramites_tareas (BOP, BOJA, TABLON, AUDIENCIA)
- Crea tabla tramites_tareas_documentos con PK (tipo_tramite_id, orden_tarea, rol)
- Pobla el mapa semántico completo (inventario §4 del plan)

Decisiones de diseño:
- tipo_documento_id = NULL → polimórfico (cualquier tipo válido en runtime)
- PK de 3 cols: un documento principal por rol; N:M diferido a #380
- AUDIENCIA renombrado conceptualmente a COMUNICACION_AUDIENCIA en docs;
  el código en BD sigue siendo AUDIENCIA hasta que una migración dedicada lo cambie
"""
from alembic import op
import sqlalchemy as sa


revision = '346_tramites_tareas_documentos'
down_revision = '337_seed_tipos_documentos'
branch_labels = None
depends_on = None


def _tid(conn, tabla, codigo):
    """Obtiene el id de un registro por código; aborta si no existe."""
    result = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"),
        {'c': codigo}
    ).scalar()
    if result is None:
        raise ValueError(f"'{codigo}' no encontrado en {tabla} — migración abortada")
    return result


def _fix_tramites_tareas(conn):
    """
    Corrige las cuatro secuencias que el seed v6.0 dejó incompletas o erróneas.
    El JSON de origen omitía ELABORAR en BOP/BOJA/TABLON y AUDIENCIA tenía
    la secuencia de v5.x (4 tareas). Ver plan #346 §8 y §5-C/D.
    """
    ta_elab = _tid(conn, 'tipos_tareas', 'ELABORAR')
    ta_noti = _tid(conn, 'tipos_tareas', 'NOTIFICAR')
    ta_ep   = _tid(conn, 'tipos_tareas', 'ESPERAR_PLAZO')

    # ANUNCIO_BOP y ANUNCIO_BOJA: insertar ELABORAR(1), renumerar NOTIFICAR→2, EP→3,4
    for codigo in ('ANUNCIO_BOP', 'ANUNCIO_BOJA'):
        tt_id = _tid(conn, 'tipos_tramites', codigo)
        conn.execute(sa.text(
            "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
        ), {'tt': tt_id})
        for orden, ta_id in [(1, ta_elab), (2, ta_noti), (3, ta_ep), (4, ta_ep)]:
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
                VALUES (:tt, :o, :ta)
            """), {'tt': tt_id, 'o': orden, 'ta': ta_id})

    # TABLON_AYUNTAMIENTOS: insertar ELABORAR(1), renumerar NOTIFICAR→2, EP→3
    tt_tab = _tid(conn, 'tipos_tramites', 'TABLON_AYUNTAMIENTOS')
    conn.execute(sa.text(
        "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
    ), {'tt': tt_tab})
    for orden, ta_id in [(1, ta_elab), (2, ta_noti), (3, ta_ep)]:
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, :o, :ta)
        """), {'tt': tt_tab, 'o': orden, 'ta': ta_id})

    # AUDIENCIA: eliminar tareas 2-4 (ELABORAR, NOTIFICAR, ESPERAR_PLAZO),
    # dejar solo ANALIZAR(1) — alineado con COMUNICACION_AUDIENCIA del plan
    tt_aud = _tid(conn, 'tipos_tramites', 'AUDIENCIA')
    conn.execute(sa.text("""
        DELETE FROM public.tramites_tareas
        WHERE tipo_tramite_id = :tt AND orden > 1
    """), {'tt': tt_aud})


# Inventario completo §4.
# Formato: (tramite_codigo, orden_tarea, rol, doc_codigo_o_None, obligatorio)
# doc_codigo_o_None = None → tipo_documento_id = NULL (polimórfico)
_MAPA = [
    # ── ANALISIS_SOLICITUD ──────────────────────────────────────────────────

    # ANALISIS_DOCUMENTAL
    ('ANALISIS_DOCUMENTAL',           1, 'ENTRADA', None,                    False),
    ('ANALISIS_DOCUMENTAL',           1, 'SALIDA',  'DIAGNOSTICO',           True),

    # REQUERIMIENTO_SUBSANACION
    ('REQUERIMIENTO_SUBSANACION',     1, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('REQUERIMIENTO_SUBSANACION',     1, 'SALIDA',  'OFICIO_REQUERIMIENTO',  True),
    ('REQUERIMIENTO_SUBSANACION',     2, 'ENTRADA', 'OFICIO_REQUERIMIENTO',  True),
    ('REQUERIMIENTO_SUBSANACION',     2, 'SALIDA',  None,                    True),
    ('REQUERIMIENTO_SUBSANACION',     3, 'ENTRADA', None,                    True),
    ('REQUERIMIENTO_SUBSANACION',     3, 'SALIDA',  'SUBSANACION',           False),
    ('REQUERIMIENTO_SUBSANACION',     4, 'ENTRADA', 'SUBSANACION',           False),
    ('REQUERIMIENTO_SUBSANACION',     4, 'SALIDA',  'DIAGNOSTICO',           True),

    # COMUNICACION_INICIO
    ('COMUNICACION_INICIO',           1, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('COMUNICACION_INICIO',           1, 'SALIDA',  'OFICIO_INICIO',         True),
    ('COMUNICACION_INICIO',           2, 'ENTRADA', 'OFICIO_INICIO',         True),
    ('COMUNICACION_INICIO',           2, 'SALIDA',  None,                    True),

    # ── CONSULTA_MINISTERIO ─────────────────────────────────────────────────

    # SOLICITUD_INFORME
    ('SOLICITUD_INFORME',             1, 'ENTRADA', None,                    False),
    ('SOLICITUD_INFORME',             1, 'SALIDA',  'OFICIO_114_RD1955',     True),
    ('SOLICITUD_INFORME',             2, 'ENTRADA', 'OFICIO_114_RD1955',     True),
    ('SOLICITUD_INFORME',             2, 'SALIDA',  None,                    True),
    ('SOLICITUD_INFORME',             3, 'ENTRADA', None,                    True),
    ('SOLICITUD_INFORME',             3, 'SALIDA',  'INFORME_114_RD1955',    False),

    # RECEPCION_INFORME (compartido entre CONSULTA_MINISTERIO y COMPATIBILIDAD_AMBIENTAL)
    ('RECEPCION_INFORME',             1, 'ENTRADA', 'INFORME_114_RD1955',    True),
    ('RECEPCION_INFORME',             1, 'SALIDA',  'DIAGNOSTICO',           True),

    # ── COMPATIBILIDAD_AMBIENTAL ────────────────────────────────────────────

    # SOLICITUD_COMPATIBILIDAD
    ('SOLICITUD_COMPATIBILIDAD',      1, 'ENTRADA', 'DOC_SOLICITUD_AAU',     False),
    ('SOLICITUD_COMPATIBILIDAD',      1, 'SALIDA',  'OFICIO_COMPATIBILIDAD_AMBIENTAL', True),
    ('SOLICITUD_COMPATIBILIDAD',      2, 'ENTRADA', 'OFICIO_COMPATIBILIDAD_AMBIENTAL', True),
    ('SOLICITUD_COMPATIBILIDAD',      2, 'SALIDA',  None,                    True),
    ('SOLICITUD_COMPATIBILIDAD',      3, 'ENTRADA', None,                    False),  # plazo=0
    ('SOLICITUD_COMPATIBILIDAD',      3, 'SALIDA',  'INFORME_COMPATIBILIDAD_AMBIENTAL', False),

    # AUDIENCIA (= COMUNICACION_AUDIENCIA en docs; código BD: AUDIENCIA)
    ('AUDIENCIA',                     1, 'ENTRADA', 'DOC_COMUNICACION_AUDIENCIA', False),
    ('AUDIENCIA',                     1, 'SALIDA',  'DIAGNOSTICO',           True),

    # ── CONSULTAS ───────────────────────────────────────────────────────────

    # CONSULTA_SEPARATA
    ('CONSULTA_SEPARATA',             1, 'ENTRADA', 'DOC_SEPARATA',          False),
    ('CONSULTA_SEPARATA',             1, 'SALIDA',  'OFICIO_SEPARATA',       True),
    ('CONSULTA_SEPARATA',             2, 'ENTRADA', 'OFICIO_SEPARATA',       True),
    ('CONSULTA_SEPARATA',             2, 'SALIDA',  None,                    True),
    ('CONSULTA_SEPARATA',             3, 'ENTRADA', None,                    False),
    ('CONSULTA_SEPARATA',             3, 'SALIDA',  'RESPUESTA_ORGANISMO',   False),
    ('CONSULTA_SEPARATA',             4, 'ENTRADA', 'RESPUESTA_ORGANISMO',   False),
    ('CONSULTA_SEPARATA',             4, 'SALIDA',  'DIAGNOSTICO',           True),

    # CONSULTA_TRASLADO_TITULAR
    ('CONSULTA_TRASLADO_TITULAR',     1, 'ENTRADA', 'RESPUESTA_ORGANISMO',   True),
    ('CONSULTA_TRASLADO_TITULAR',     1, 'SALIDA',  'OFICIO_TRASLADO_RESPUESTA', True),
    ('CONSULTA_TRASLADO_TITULAR',     2, 'ENTRADA', 'OFICIO_TRASLADO_RESPUESTA', True),
    ('CONSULTA_TRASLADO_TITULAR',     2, 'SALIDA',  None,                    True),
    ('CONSULTA_TRASLADO_TITULAR',     3, 'ENTRADA', None,                    False),
    ('CONSULTA_TRASLADO_TITULAR',     3, 'SALIDA',  'RESPUESTA_TITULAR',     False),
    ('CONSULTA_TRASLADO_TITULAR',     4, 'ENTRADA', 'RESPUESTA_TITULAR',     False),
    ('CONSULTA_TRASLADO_TITULAR',     4, 'SALIDA',  'DIAGNOSTICO',           True),

    # CONSULTA_TRASLADO_ORGANISMO
    ('CONSULTA_TRASLADO_ORGANISMO',   1, 'ENTRADA', 'RESPUESTA_TITULAR',     True),
    ('CONSULTA_TRASLADO_ORGANISMO',   1, 'SALIDA',  'OFICIO_TRASLADO_REPAROS', True),
    ('CONSULTA_TRASLADO_ORGANISMO',   2, 'ENTRADA', 'OFICIO_TRASLADO_REPAROS', True),
    ('CONSULTA_TRASLADO_ORGANISMO',   2, 'SALIDA',  None,                    True),
    ('CONSULTA_TRASLADO_ORGANISMO',   3, 'ENTRADA', None,                    False),
    ('CONSULTA_TRASLADO_ORGANISMO',   3, 'SALIDA',  'RESPUESTA_ORGANISMO',   False),
    ('CONSULTA_TRASLADO_ORGANISMO',   4, 'ENTRADA', 'RESPUESTA_ORGANISMO',   False),
    ('CONSULTA_TRASLADO_ORGANISMO',   4, 'SALIDA',  'DIAGNOSTICO',           True),

    # ── INFORMACION_PUBLICA ─────────────────────────────────────────────────

    # REDACTAR_ANUNCIO
    ('REDACTAR_ANUNCIO',              1, 'ENTRADA', 'DOC_PROYECTO',          False),
    ('REDACTAR_ANUNCIO',              1, 'SALIDA',  'ANUNCIO_IP',            True),

    # ANUNCIO_BOE y ANUNCIO_PRENSA: [NOTIFICAR(1), EP(2), EP(3)]
    ('ANUNCIO_BOE',                   1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('ANUNCIO_BOE',                   1, 'SALIDA',  None,                    True),
    ('ANUNCIO_BOE',                   2, 'ENTRADA', None,                    False),
    ('ANUNCIO_BOE',                   2, 'SALIDA',  'ANUNCIO_PUBLICADO',     False),
    ('ANUNCIO_BOE',                   3, 'ENTRADA', 'ANUNCIO_PUBLICADO',     True),
    ('ANUNCIO_BOE',                   3, 'SALIDA',  'CERT_PLAZO_CUMPLIDO',   False),

    ('ANUNCIO_PRENSA',                1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('ANUNCIO_PRENSA',                1, 'SALIDA',  None,                    True),
    ('ANUNCIO_PRENSA',                2, 'ENTRADA', None,                    False),
    ('ANUNCIO_PRENSA',                2, 'SALIDA',  'ANUNCIO_PUBLICADO',     False),
    ('ANUNCIO_PRENSA',                3, 'ENTRADA', 'ANUNCIO_PUBLICADO',     True),
    ('ANUNCIO_PRENSA',                3, 'SALIDA',  'CERT_PLAZO_CUMPLIDO',   False),

    # ANUNCIO_BOP y ANUNCIO_BOJA: [ELABORAR(1), NOTIFICAR(2), EP(3), EP(4)]
    # (secuencia corregida en _fix_tramites_tareas)
    ('ANUNCIO_BOP',                   1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('ANUNCIO_BOP',                   1, 'SALIDA',  'OFICIO_PUBLICAR_BOLETIN', True),
    ('ANUNCIO_BOP',                   2, 'ENTRADA', 'OFICIO_PUBLICAR_BOLETIN', True),
    ('ANUNCIO_BOP',                   2, 'SALIDA',  None,                    True),
    ('ANUNCIO_BOP',                   3, 'ENTRADA', None,                    False),
    ('ANUNCIO_BOP',                   3, 'SALIDA',  'ANUNCIO_PUBLICADO',     False),
    ('ANUNCIO_BOP',                   4, 'ENTRADA', 'ANUNCIO_PUBLICADO',     True),
    ('ANUNCIO_BOP',                   4, 'SALIDA',  'CERT_PLAZO_CUMPLIDO',   False),

    ('ANUNCIO_BOJA',                  1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('ANUNCIO_BOJA',                  1, 'SALIDA',  'OFICIO_PUBLICAR_BOLETIN', True),
    ('ANUNCIO_BOJA',                  2, 'ENTRADA', 'OFICIO_PUBLICAR_BOLETIN', True),
    ('ANUNCIO_BOJA',                  2, 'SALIDA',  None,                    True),
    ('ANUNCIO_BOJA',                  3, 'ENTRADA', None,                    False),
    ('ANUNCIO_BOJA',                  3, 'SALIDA',  'ANUNCIO_PUBLICADO',     False),
    ('ANUNCIO_BOJA',                  4, 'ENTRADA', 'ANUNCIO_PUBLICADO',     True),
    ('ANUNCIO_BOJA',                  4, 'SALIDA',  'CERT_PLAZO_CUMPLIDO',   False),

    # TABLON_AYUNTAMIENTOS: [ELABORAR(1), NOTIFICAR(2), EP(3)]
    # (secuencia corregida en _fix_tramites_tareas)
    ('TABLON_AYUNTAMIENTOS',          1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('TABLON_AYUNTAMIENTOS',          1, 'SALIDA',  'OFICIO_TABLON',         True),
    ('TABLON_AYUNTAMIENTOS',          2, 'ENTRADA', 'OFICIO_TABLON',         True),
    ('TABLON_AYUNTAMIENTOS',          2, 'SALIDA',  None,                    True),
    ('TABLON_AYUNTAMIENTOS',          3, 'ENTRADA', None,                    False),
    ('TABLON_AYUNTAMIENTOS',          3, 'SALIDA',  'CERT_PLAZO_TABLON',     False),

    # PORTAL_TRANSPARENCIA: §5-E — patrón C simplificado
    ('PORTAL_TRANSPARENCIA',          1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('PORTAL_TRANSPARENCIA',          1, 'SALIDA',  None,                    True),
    ('PORTAL_TRANSPARENCIA',          2, 'ENTRADA', None,                    True),
    ('PORTAL_TRANSPARENCIA',          2, 'SALIDA',  'JUSTIFICANTE_PORTAL',   False),
    ('PORTAL_TRANSPARENCIA',          3, 'ENTRADA', 'JUSTIFICANTE_PORTAL',   False),
    ('PORTAL_TRANSPARENCIA',          3, 'SALIDA',  'CERT_PLAZO_CUMPLIDO',   False),

    # ANUNCIO_TITULAR
    ('ANUNCIO_TITULAR',               1, 'ENTRADA', 'ANUNCIO_IP',            True),
    ('ANUNCIO_TITULAR',               1, 'SALIDA',  'OFICIO_PUBLICAR_TITULAR', True),
    ('ANUNCIO_TITULAR',               2, 'ENTRADA', 'OFICIO_PUBLICAR_TITULAR', True),
    ('ANUNCIO_TITULAR',               2, 'SALIDA',  None,                    True),

    # RECEPCION_ALEGACION
    ('RECEPCION_ALEGACION',           1, 'ENTRADA', 'ALEGACION_IP',          True),
    ('RECEPCION_ALEGACION',           1, 'SALIDA',  'DIAGNOSTICO',           True),
    ('RECEPCION_ALEGACION',           2, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('RECEPCION_ALEGACION',           2, 'SALIDA',  'OFICIO_TRASLADO_ALEGACION', True),
    ('RECEPCION_ALEGACION',           3, 'ENTRADA', 'OFICIO_TRASLADO_ALEGACION', True),
    ('RECEPCION_ALEGACION',           3, 'SALIDA',  None,                    True),
    ('RECEPCION_ALEGACION',           4, 'ENTRADA', None,                    False),
    ('RECEPCION_ALEGACION',           4, 'SALIDA',  'RESPUESTA_TITULAR_ALEGACION', False),

    # ANALISIS_ALEGACIONES
    ('ANALISIS_ALEGACIONES',          1, 'ENTRADA', None,                    False),
    ('ANALISIS_ALEGACIONES',          1, 'SALIDA',  'DIAGNOSTICO',           True),

    # ── FIGURA_AMBIENTAL_EXTERNA ────────────────────────────────────────────

    # SOLICITUD_FIGURA
    ('SOLICITUD_FIGURA',              1, 'ENTRADA', 'DOC_PROYECTO',          False),
    ('SOLICITUD_FIGURA',              1, 'SALIDA',  'OFICIO_SOLICITUD_FIGURA', True),
    ('SOLICITUD_FIGURA',              2, 'ENTRADA', 'OFICIO_SOLICITUD_FIGURA', True),
    ('SOLICITUD_FIGURA',              2, 'SALIDA',  None,                    True),
    ('SOLICITUD_FIGURA',              3, 'ENTRADA', None,                    False),  # plazo=0
    ('SOLICITUD_FIGURA',              3, 'SALIDA',  'FIGURA_AMBIENTAL_EXTERNA', False),

    # RECEPCION_FIGURA
    ('RECEPCION_FIGURA',              1, 'ENTRADA', 'FIGURA_AMBIENTAL_EXTERNA', True),
    ('RECEPCION_FIGURA',              1, 'SALIDA',  'DIAGNOSTICO',           True),

    # ── AAU_AAUS_INTEGRADA ──────────────────────────────────────────────────

    # REMISION_RESULTADO_IP_CONSULTAS
    ('REMISION_RESULTADO_IP_CONSULTAS', 1, 'ENTRADA', 'CERT_FIN_IP_CONSULTAS', False),
    ('REMISION_RESULTADO_IP_CONSULTAS', 1, 'SALIDA',  'OFICIO_RESULTADO_IP_CON', True),
    ('REMISION_RESULTADO_IP_CONSULTAS', 2, 'ENTRADA', 'OFICIO_RESULTADO_IP_CON', True),
    ('REMISION_RESULTADO_IP_CONSULTAS', 2, 'SALIDA',  None,                    True),
    ('REMISION_RESULTADO_IP_CONSULTAS', 3, 'ENTRADA', None,                    False),  # plazo=0
    ('REMISION_RESULTADO_IP_CONSULTAS', 3, 'SALIDA',  'DOC_DICTAMEN_AMBIENTAL', False),

    # RECEPCION_DICTAMEN
    ('RECEPCION_DICTAMEN',            1, 'ENTRADA', 'DOC_DICTAMEN_AMBIENTAL', True),
    ('RECEPCION_DICTAMEN',            1, 'SALIDA',  'DIAGNOSTICO',           True),
    ('RECEPCION_DICTAMEN',            2, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('RECEPCION_DICTAMEN',            2, 'SALIDA',  'OFICIO_OBS_DICTAMEN',   True),
    ('RECEPCION_DICTAMEN',            3, 'ENTRADA', 'OFICIO_OBS_DICTAMEN',   True),
    ('RECEPCION_DICTAMEN',            3, 'SALIDA',  None,                    True),
    ('RECEPCION_DICTAMEN',            4, 'ENTRADA', None,                    False),  # plazo=0
    ('RECEPCION_DICTAMEN',            4, 'SALIDA',  'DOC_PROPUESTA_INF_VINC', False),

    # RECEPCION_PROPUESTA_INF_VINC
    ('RECEPCION_PROPUESTA_INF_VINC',  1, 'ENTRADA', 'DOC_PROPUESTA_INF_VINC', True),
    ('RECEPCION_PROPUESTA_INF_VINC',  1, 'SALIDA',  'DIAGNOSTICO',           True),
    ('RECEPCION_PROPUESTA_INF_VINC',  2, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('RECEPCION_PROPUESTA_INF_VINC',  2, 'SALIDA',  'OFICIO_OBS_PROP_INF_VINC', True),
    ('RECEPCION_PROPUESTA_INF_VINC',  3, 'ENTRADA', 'OFICIO_OBS_PROP_INF_VINC', True),
    ('RECEPCION_PROPUESTA_INF_VINC',  3, 'SALIDA',  None,                    True),
    ('RECEPCION_PROPUESTA_INF_VINC',  4, 'ENTRADA', None,                    False),  # plazo=0
    ('RECEPCION_PROPUESTA_INF_VINC',  4, 'SALIDA',  'DOC_INFORME_VINCULANTE', False),

    # RECEPCION_INFORME_VINCULANTE
    ('RECEPCION_INFORME_VINCULANTE',  1, 'ENTRADA', 'DOC_INFORME_VINCULANTE', True),
    ('RECEPCION_INFORME_VINCULANTE',  1, 'SALIDA',  'DIAGNOSTICO',           True),

    # DISCREPANCIA_INF_VINC
    ('DISCREPANCIA_INF_VINC',         1, 'ENTRADA', 'DIAGNOSTICO',           False),
    ('DISCREPANCIA_INF_VINC',         1, 'SALIDA',  'OFICIO_DISCREPANCIA_INF_VINC', True),
    ('DISCREPANCIA_INF_VINC',         2, 'ENTRADA', 'OFICIO_DISCREPANCIA_INF_VINC', True),
    ('DISCREPANCIA_INF_VINC',         2, 'SALIDA',  None,                    True),
    ('DISCREPANCIA_INF_VINC',         3, 'ENTRADA', None,                    False),
    ('DISCREPANCIA_INF_VINC',         3, 'SALIDA',  'RESOLUCION_DISCREPANCIA_INF_VINC', False),

    # ── RESOLUCION ──────────────────────────────────────────────────────────

    # ELABORACION: solo ELABORAR(1), consume CERT_FIN_INSTRUCCION
    ('ELABORACION',                   1, 'ENTRADA', 'CERT_FIN_INSTRUCCION',  True),
    ('ELABORACION',                   1, 'SALIDA',  'RESOLUCION',            True),

    # NOTIFICACION
    ('NOTIFICACION',                  1, 'ENTRADA', 'RESOLUCION',            True),
    ('NOTIFICACION',                  1, 'SALIDA',  None,                    True),

    # PUBLICACION
    ('PUBLICACION',                   1, 'ENTRADA', 'RESOLUCION',            True),
    ('PUBLICACION',                   1, 'SALIDA',  'OFICIO_PUBLICAR_BOLETIN', True),
    ('PUBLICACION',                   2, 'ENTRADA', 'OFICIO_PUBLICAR_BOLETIN', True),
    ('PUBLICACION',                   2, 'SALIDA',  None,                    True),
    ('PUBLICACION',                   3, 'ENTRADA', None,                    False),
    ('PUBLICACION',                   3, 'SALIDA',  'RESOLUCION_PUBLICADA',  False),
]


def upgrade():
    conn = op.get_bind()

    # 1. Corregir secuencias erróneas en tramites_tareas
    _fix_tramites_tareas(conn)

    # 2. Crear tabla tramites_tareas_documentos
    op.create_table(
        'tramites_tareas_documentos',
        sa.Column('tipo_tramite_id', sa.Integer(), nullable=False),
        sa.Column('orden_tarea',     sa.SmallInteger(), nullable=False),
        sa.Column('rol',             sa.Text(), nullable=False),
        sa.Column('tipo_documento_id', sa.Integer(), nullable=True),
        sa.Column('obligatorio',     sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(
            ['tipo_tramite_id'], ['public.tipos_tramites.id'],
            name='fk_ttd_tipo_tramite'
        ),
        sa.ForeignKeyConstraint(
            ['tipo_documento_id'], ['public.tipos_documentos.id'],
            name='fk_ttd_tipo_documento'
        ),
        sa.PrimaryKeyConstraint('tipo_tramite_id', 'orden_tarea', 'rol', name='pk_ttd'),
        schema='public'
    )

    op.execute("GRANT SELECT ON public.tramites_tareas_documentos TO claude_desktop")

    # 3. Seed del mapa semántico
    for tramite_cod, orden, rol, doc_cod, obligatorio in _MAPA:
        tt_id = _tid(conn, 'tipos_tramites', tramite_cod)
        td_id = _tid(conn, 'tipos_documentos', doc_cod) if doc_cod else None
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas_documentos
                (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
            VALUES (:tt, :o, :rol, :td, :oblig)
        """), {
            'tt': tt_id, 'o': orden, 'rol': rol,
            'td': td_id, 'oblig': obligatorio
        })


def downgrade():
    op.drop_table('tramites_tareas_documentos', schema='public')

    conn = op.get_bind()
    ta_noti = _tid(conn, 'tipos_tareas', 'NOTIFICAR')
    ta_ep   = _tid(conn, 'tipos_tareas', 'ESPERAR_PLAZO')
    ta_anal = _tid(conn, 'tipos_tareas', 'ANALIZAR')
    ta_elab = _tid(conn, 'tipos_tareas', 'ELABORAR')

    # Revertir ANUNCIO_BOP y ANUNCIO_BOJA a [NOTIFICAR(1), EP(2), EP(3)]
    for codigo in ('ANUNCIO_BOP', 'ANUNCIO_BOJA'):
        tt_id = _tid(conn, 'tipos_tramites', codigo)
        conn.execute(sa.text(
            "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
        ), {'tt': tt_id})
        for orden, ta_id in [(1, ta_noti), (2, ta_ep), (3, ta_ep)]:
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
                VALUES (:tt, :o, :ta)
            """), {'tt': tt_id, 'o': orden, 'ta': ta_id})

    # Revertir TABLON_AYUNTAMIENTOS a [NOTIFICAR(1), EP(2)]
    tt_tab = _tid(conn, 'tipos_tramites', 'TABLON_AYUNTAMIENTOS')
    conn.execute(sa.text(
        "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
    ), {'tt': tt_tab})
    for orden, ta_id in [(1, ta_noti), (2, ta_ep)]:
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, :o, :ta)
        """), {'tt': tt_tab, 'o': orden, 'ta': ta_id})

    # Revertir AUDIENCIA a [ANALIZAR(1), ELABORAR(2), NOTIFICAR(3), EP(4)]
    tt_aud = _tid(conn, 'tipos_tramites', 'AUDIENCIA')
    conn.execute(sa.text(
        "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
    ), {'tt': tt_aud})
    for orden, ta_id in [(1, ta_anal), (2, ta_elab), (3, ta_noti), (4, ta_ep)]:
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, :o, :ta)
        """), {'tt': tt_aud, 'o': orden, 'ta': ta_id})
