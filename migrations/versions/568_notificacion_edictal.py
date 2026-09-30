"""568_notificacion_edictal — notificación edictal (art. 44 LPACAP)

Revision ID: 568_notificacion_edictal
Revises: 989_sede_solicitud
Create Date: 2026-09-30

Issue #568, ADR-052.

- Tres tipos de documento: `JUSTIFICANTE_POSTAL_2DO` (2.º intento postal
  fallido, consumido de la NOTIFICAR), `ANUNCIO_EDICTO` (el anuncio firmado) y
  `JUSTIFICANTE_EDICTO` (la remisión al BOE). `JUSTIFICANTE_POSTAL_2DO` entra
  como ENTRADA opcional en toda tarea que ya declara `JUSTIFICANTE_POSTAL_1ER`.
- El trámite transversal `NOTIFICACION_EDICTAL` (ELABORAR → NOTIFICAR →
  ESPERAR_PLAZO), en las 13 fases de `TRAMITES_TRANSVERSALES` de
  `ESTRUCTURA_FTT.json` v6.9, sin límite por fase. La lista va escrita aquí: una
  migración no lee ficheros que cambian después.
- `notificaciones.canal` admite `EDICTO` (§E) y se retira `numero_intento`, que
  sale de los documentos (§C).
- `notificacion_fuentes.tipo_fase_id` admite NULL = cualquier fase (§F). La
  unicidad pasa a dos índices parciales (con NULL, la restricción de antes no
  chocaría). Una fila: `NOTIFICACION_EDICTAL` · `BOLETIN`.

Todo por clave natural, nunca por id (REGLAS_DESARROLLO, #849). El downgrade
aborta si hay notificaciones con canal EDICTO, trámites edictales o fuentes con
fase vacía distintas de la sembrada aquí: no hay adónde devolverlos.
"""
from alembic import op
import sqlalchemy as sa


revision = '568_notificacion_edictal'
down_revision = '989_sede_solicitud'
branch_labels = None
depends_on = None

_TRAMITE = 'NOTIFICACION_EDICTAL'
_NORMA = 'Ley 39/2015, art. 44 y DA 3.ª'

# ESTRUCTURA_FTT.json v6.9, TRAMITES_TRANSVERSALES
_FASES = (
    'ANALISIS_SOLICITUD', 'DATOS_CATASTRALES', 'CONSULTAS', 'CONSULTA_MINISTERIO',
    'INFORMACION_PUBLICA', 'COMPATIBILIDAD_AMBIENTAL', 'FIGURA_AMBIENTAL_EXTERNA',
    'AAU_AAUS_INTEGRADA', 'RECONOCIMIENTO_INTERESADO', 'RESOLUCION', 'RESOLUCION_AAP',
    'RESOLUCION_AAC', 'RESOLUCION_DUP',
)

# (codigo, nombre, descripcion, origen)
_DOCUMENTOS = (
    ('JUSTIFICANTE_POSTAL_2DO', 'Acuse del segundo intento de notificación postal',
     'Acredita el segundo intento de entrega postal, fallido (una sola vez, en otra '
     'franja horaria, dentro de los tres días siguientes: art. 42.2 LPACAP). Habilita '
     'la notificación edictal (art. 44). Se vincula como consumido de la NOTIFICAR; '
     'nunca es el producido. Fecha administrativa: fecha del intento.',
     'EXTERNO'),
    ('ANUNCIO_EDICTO', 'Anuncio de notificación edictal',
     'Anuncio firmado para notificar en el BOE a los interesados que no se pudieron '
     'notificar (art. 44 y DA 3.ª LPACAP): uno solo para todos. Lo produce el ELABORAR '
     'de NOTIFICACION_EDICTAL y lo consume su NOTIFICAR. Fecha administrativa: fecha '
     'de firma.',
     'INTERNO'),
    ('JUSTIFICANTE_EDICTO', 'Justificante de remisión del anuncio al BOE',
     'Constancia del envío del anuncio edictal por el sistema telemático del BOE (DA '
     '3.ª.1 LPACAP). Justificante final de la NOTIFICAR de NOTIFICACION_EDICTAL, canal '
     'EDICTO. Fecha administrativa: fecha de remisión.',
     'EXTERNO'),
)

# (orden, tarea, ((rol, tipo_documento, obligatorio), ...)) — None = tipo abierto
_TAREAS = (
    (1, 'ELABORAR', (('ENTRADA', None, True), ('SALIDA', 'ANUNCIO_EDICTO', True))),
    (2, 'NOTIFICAR', (('ENTRADA', 'ANUNCIO_EDICTO', True),
                      ('SALIDA', 'JUSTIFICANTE_EDICTO', True))),
    (3, 'ESPERAR_PLAZO', (('ENTRADA', 'JUSTIFICANTE_EDICTO', True),
                          ('SALIDA', 'ANUNCIO_PUBLICADO', True))),
)

_CANALES_ANTES = ('NOTIFICA', 'BANDEJA', 'SIR', 'POSTAL')
_CANALES = _CANALES_ANTES + ('EDICTO',)


def _tid(conn, tabla, codigo):
    """Id de un registro de catálogo por su código; aborta si no existe."""
    resultado = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"), {'c': codigo}
    ).scalar()
    if resultado is None:
        raise ValueError(f"'{codigo}' no encontrado en {tabla} — migración abortada")
    return resultado


def _check_canal(canales):
    lista = ', '.join(f"'{c}'" for c in canales)
    op.drop_constraint('ck_notificaciones_canal', 'notificaciones', schema='public')
    op.create_check_constraint('ck_notificaciones_canal', 'notificaciones',
                               f'canal IN ({lista})', schema='public')


def upgrade():
    conn = op.get_bind()

    # --- Tipos de documento ---
    for codigo, nombre, descripcion, origen in _DOCUMENTOS:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_documentos (codigo, nombre, descripcion, origen)
            VALUES (:c, :n, :d, :o)
        """), {'c': codigo, 'n': nombre, 'd': descripcion, 'o': origen})

    # El 2.º intento fallido entra donde ya entra el 1.º
    conn.execute(sa.text("""
        INSERT INTO public.tramites_tareas_documentos
            (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
        SELECT ttd.tipo_tramite_id, ttd.orden_tarea, 'ENTRADA', dos.id, false
        FROM public.tramites_tareas_documentos ttd
        JOIN public.tipos_documentos uno ON uno.id = ttd.tipo_documento_id
                                        AND uno.codigo = 'JUSTIFICANTE_POSTAL_1ER'
        CROSS JOIN public.tipos_documentos dos
        WHERE dos.codigo = 'JUSTIFICANTE_POSTAL_2DO' AND ttd.rol = 'ENTRADA'
    """))

    # --- Trámite transversal ---
    conn.execute(sa.text("""
        INSERT INTO public.tipos_tramites (codigo, nombre, abrev, nombre_en_plantilla)
        VALUES (:c, 'Notificación edictal', 'EDICTO', 'Notificación edictal')
    """), {'c': _TRAMITE})
    tt_id = _tid(conn, 'tipos_tramites', _TRAMITE)
    for fase in _FASES:
        conn.execute(sa.text("""
            INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id, cardinalidad_maxima)
            VALUES (:tf, :tt, NULL)
        """), {'tf': _tid(conn, 'tipos_fases', fase), 'tt': tt_id})
    for orden, tarea, documentos in _TAREAS:
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, :o, :ta)
        """), {'tt': tt_id, 'o': orden, 'ta': _tid(conn, 'tipos_tareas', tarea)})
        for rol, doc, obligatorio in documentos:
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas_documentos
                    (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
                VALUES (:tt, :o, :rol, :td, :ob)
            """), {'tt': tt_id, 'o': orden, 'rol': rol,
                   'td': _tid(conn, 'tipos_documentos', doc) if doc else None,
                   'ob': obligatorio})

    # --- notificacion_fuentes: fase vacía = cualquier fase ---
    op.alter_column('notificacion_fuentes', 'tipo_fase_id', nullable=True, schema='public')
    op.drop_constraint('uq_notificacion_fuentes', 'notificacion_fuentes', schema='public')
    op.create_index('uq_notificacion_fuentes', 'notificacion_fuentes',
                    ['tipo_fase_id', 'tipo_tramite_id', 'fuente'], unique=True,
                    schema='public', postgresql_where=sa.text('tipo_fase_id IS NOT NULL'))
    op.create_index('uq_notificacion_fuentes_cualquier_fase', 'notificacion_fuentes',
                    ['tipo_tramite_id', 'fuente'], unique=True,
                    schema='public', postgresql_where=sa.text('tipo_fase_id IS NULL'))
    conn.execute(sa.text("""
        INSERT INTO public.notificacion_fuentes (tipo_fase_id, tipo_tramite_id, fuente, norma, orden)
        VALUES (NULL, :tt, 'BOLETIN', :n, 1)
    """), {'tt': tt_id, 'n': _NORMA})

    # --- notificaciones: canal EDICTO; fuera numero_intento ---
    _check_canal(_CANALES)
    op.drop_constraint('ck_notificaciones_intento_postal', 'notificaciones', schema='public')
    op.drop_constraint('ck_notificaciones_numero_intento', 'notificaciones', schema='public')
    op.drop_column('notificaciones', 'numero_intento', schema='public')


def downgrade():
    conn = op.get_bind()
    tt_id = _tid(conn, 'tipos_tramites', _TRAMITE)

    problemas = []
    if conn.execute(sa.text(
            "SELECT COUNT(*) FROM public.notificaciones WHERE canal = 'EDICTO'")).scalar():
        problemas.append('notificaciones con canal EDICTO')
    if conn.execute(sa.text(
            "SELECT COUNT(*) FROM public.tramites WHERE tipo_tramite_id = :tt"),
            {'tt': tt_id}).scalar():
        problemas.append(f'trámites {_TRAMITE}')
    if conn.execute(sa.text("""
            SELECT COUNT(*) FROM public.notificacion_fuentes
            WHERE tipo_fase_id IS NULL AND tipo_tramite_id <> :tt
        """), {'tt': tt_id}).scalar():
        problemas.append('fuentes con fase vacía de otros trámites')
    docs = conn.execute(sa.text("""
        SELECT COUNT(*) FROM public.documentos d JOIN public.tipos_documentos td
          ON td.id = d.tipo_doc_id
        WHERE td.codigo IN ('JUSTIFICANTE_POSTAL_2DO', 'ANUNCIO_EDICTO', 'JUSTIFICANTE_EDICTO')
    """)).scalar()
    if docs:
        problemas.append(f'{docs} documentos de los tipos nuevos')
    if problemas:
        raise RuntimeError('No se puede deshacer 568: ' + '; '.join(problemas)
                           + ' — migración abortada')

    # numero_intento: 2 donde consta el 2.º intento... no puede constar (sin
    # documentos del tipo, comprobado arriba), así que 1 para todas.
    op.add_column('notificaciones', sa.Column(
        'numero_intento', sa.SmallInteger(), nullable=False, server_default='1',
        comment='1 o 2 — habilita regla LPACAP de dos intentos'), schema='public')
    op.alter_column('notificaciones', 'numero_intento', server_default=None, schema='public')
    op.create_check_constraint('ck_notificaciones_numero_intento', 'notificaciones',
                               'numero_intento IN (1, 2)', schema='public')
    op.create_check_constraint('ck_notificaciones_intento_postal', 'notificaciones',
                               "canal = 'POSTAL' OR numero_intento = 1", schema='public')
    _check_canal(_CANALES_ANTES)

    conn.execute(sa.text(
        "DELETE FROM public.notificacion_fuentes WHERE tipo_tramite_id = :tt"), {'tt': tt_id})
    op.drop_index('uq_notificacion_fuentes_cualquier_fase', 'notificacion_fuentes',
                  schema='public')
    op.drop_index('uq_notificacion_fuentes', 'notificacion_fuentes', schema='public')
    op.create_unique_constraint('uq_notificacion_fuentes', 'notificacion_fuentes',
                                ['tipo_fase_id', 'tipo_tramite_id', 'fuente'],
                                schema='public')
    op.alter_column('notificacion_fuentes', 'tipo_fase_id', nullable=False, schema='public')

    for tabla in ('tramites_tareas_documentos', 'tramites_tareas', 'fases_tramites'):
        conn.execute(sa.text(
            f"DELETE FROM public.{tabla} WHERE tipo_tramite_id = :tt"), {'tt': tt_id})
    conn.execute(sa.text("DELETE FROM public.tipos_tramites WHERE id = :tt"), {'tt': tt_id})
    conn.execute(sa.text("""
        DELETE FROM public.tramites_tareas_documentos
        WHERE tipo_documento_id IN (SELECT id FROM public.tipos_documentos
                                    WHERE codigo = 'JUSTIFICANTE_POSTAL_2DO')
    """))
    for codigo, *_ in _DOCUMENTOS:
        conn.execute(sa.text("DELETE FROM public.tipos_documentos WHERE codigo = :c"),
                     {'c': codigo})
