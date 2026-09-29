"""969_una_notificacion_dup — RESOLUCION_DUP notifica desde un solo NOTIFICACION

Revision ID: 969_una_notificacion_dup
Revises: 968_fuentes_destinatarios
Create Date: 2026-09-29

Issue #969 (N5a-3), ADR-051 §G.

`NOTIFICACION_ORGANISMOS` y `NOTIFICACION_INTERESADOS` se retiran del catálogo:
con las fuentes de #968 el trámite `NOTIFICACION` de `RESOLUCION_DUP` ya sabe a
qué grupos va (solicitante, organismos, propietarios e interesados), como el de
`RESOLUCION`, `RESOLUCION_AAP` y `RESOLUCION_AAC`. Enmienda ADR-046 §C.

Se borra por código y de fuera adentro, el orden inverso al de su alta:
`notificacion_fuentes`, `tramites_tareas_documentos` (`fk_ttd_tramite_tarea`
apunta a `tramites_tareas`), `tramites_tareas`, `fases_tramites` y, al final,
`tipos_tramites`. Nunca por id (REGLAS_DESARROLLO, #849).

Se aborta, sin tocar nada, si algún dato de operación cuelga de los dos tipos
(trámites ya creados, plantillas, filas de `catalogo_plazos`): borrar el tipo
dejaría el árbol de esos expedientes sin catálogo. Los datos de operación de
desarrollo no se migran (ADR-051, «Consecuencias»): se borran los expedientes
que los usen y se recrean con los scripts de `scripts/expedientes_dummy/`.

El downgrade los devuelve tal como los dejó 968: mismas filas, mismas entradas
documentales y las mismas fuentes que sembró #968.
"""
from alembic import op
import sqlalchemy as sa


revision = '969_una_notificacion_dup'
down_revision = '968_fuentes_destinatarios'
branch_labels = None
depends_on = None

_FASE = 'RESOLUCION_DUP'
_RD_148_2 = 'RD 1955/2000, art. 148.2'

# (codigo, nombre, abrev, nombre_en_plantilla, ((fuente, norma), ...),
#  ((rol, tipo_documento, obligatorio), ...)) — el trámite tiene una sola tarea,
# NOTIFICAR, en orden 1. `tipo_documento` None = tipo abierto (polimórfico).
_TRAMITES = (
    ('NOTIFICACION_ORGANISMOS', 'Notificación a Organismos', 'NOTIF. ORGANISMOS',
     'Notificación a Organismos',
     (('ORGANISMOS_CONSULTADOS', _RD_148_2),),
     (('ENTRADA', 'RESOLUCION', True),
      ('SALIDA', None, True))),
    ('NOTIFICACION_INTERESADOS', 'Notificación a Interesados', 'NOTIF. INTERESADOS',
     'Notificación a Interesados',
     (('PROPIETARIOS_DUP', _RD_148_2), ('INTERESADOS_RECONOCIDOS', _RD_148_2)),
     (('ENTRADA', 'RESOLUCION', True),
      ('SALIDA', None, True),
      ('ENTRADA', 'JUSTIFICANTE_NOTIFICA_DISPOSICION', False),
      ('ENTRADA', 'JUSTIFICANTE_POSTAL_1ER', False),
      ('ENTRADA', 'JUSTIFICANTE_SEDE', False))),
)


def _tid(conn, tabla, codigo):
    """Id de un registro de catálogo por su código; aborta si no existe."""
    resultado = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"), {'c': codigo}
    ).scalar()
    if resultado is None:
        raise ValueError(f"'{codigo}' no encontrado en {tabla} — migración abortada")
    return resultado


def _colgando(conn, codigo):
    """Qué datos de operación o de catálogo cuelgan de un trámite que se va a
    retirar y no se pueden borrar sin dejar algo sin catálogo."""
    tt_id = conn.execute(
        sa.text("SELECT id FROM public.tipos_tramites WHERE codigo = :c"), {'c': codigo}
    ).scalar()
    if tt_id is None:
        return []
    colgando = []
    for tabla, etiqueta in (('tramites', 'trámites de expedientes'),
                            ('plantillas', 'plantillas')):
        n = conn.execute(
            sa.text(f"SELECT COUNT(*) FROM public.{tabla} WHERE tipo_tramite_id = :t"),
            {'t': tt_id}).scalar()
        if n:
            colgando.append(f'{n} {etiqueta}')
    caminos = conn.execute(sa.text("""
        SELECT camino FROM public.catalogo_plazos
        WHERE split_part(camino, '/', 4) = :c
    """), {'c': codigo}).scalars().all()
    if caminos:
        colgando.append(f'filas de catalogo_plazos ({", ".join(caminos)})')
    return colgando


def upgrade():
    conn = op.get_bind()

    problemas = [f'{codigo}: {", ".join(c)}'
                 for codigo, *_ in _TRAMITES if (c := _colgando(conn, codigo))]
    if problemas:
        raise RuntimeError(
            'Hay datos colgando de los trámites que se retiran ('
            + '; '.join(problemas) + '). Borra esos expedientes de desarrollo y '
            'recréalos con scripts/expedientes_dummy/ antes de migrar — migración abortada')

    for codigo, *_ in _TRAMITES:
        tt_id = _tid(conn, 'tipos_tramites', codigo)
        # `fases_tramites` sin filtrar por fase: si el tipo estuviera en otra,
        # borrar el tipo fallaría con la FK en vez de dejarla sin trámite.
        for tabla in ('notificacion_fuentes', 'tramites_tareas_documentos',
                      'tramites_tareas', 'fases_tramites'):
            conn.execute(sa.text(
                f"DELETE FROM public.{tabla} WHERE tipo_tramite_id = :tt"), {'tt': tt_id})
        conn.execute(sa.text("DELETE FROM public.tipos_tramites WHERE id = :tt"),
                     {'tt': tt_id})


def downgrade():
    conn = op.get_bind()
    tf_id = _tid(conn, 'tipos_fases', _FASE)
    ta_id = _tid(conn, 'tipos_tareas', 'NOTIFICAR')

    for codigo, nombre, abrev, nombre_en_plantilla, fuentes, documentos in _TRAMITES:
        conn.execute(sa.text("""
            INSERT INTO public.tipos_tramites (codigo, nombre, abrev, nombre_en_plantilla)
            VALUES (:c, :n, :a, :p)
        """), {'c': codigo, 'n': nombre, 'a': abrev, 'p': nombre_en_plantilla})
        tt_id = _tid(conn, 'tipos_tramites', codigo)

        conn.execute(sa.text("""
            INSERT INTO public.fases_tramites (tipo_fase_id, tipo_tramite_id, cardinalidad_maxima)
            VALUES (:tf, :tt, 1)
        """), {'tf': tf_id, 'tt': tt_id})
        conn.execute(sa.text("""
            INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
            VALUES (:tt, 1, :ta)
        """), {'tt': tt_id, 'ta': ta_id})
        for rol, doc_codigo, obligatorio in documentos:
            td_id = _tid(conn, 'tipos_documentos', doc_codigo) if doc_codigo else None
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas_documentos
                    (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
                VALUES (:tt, 1, :rol, :td, :oblig)
            """), {'tt': tt_id, 'rol': rol, 'td': td_id, 'oblig': obligatorio})
        for orden, (fuente, norma) in enumerate(fuentes, start=1):
            conn.execute(sa.text("""
                INSERT INTO public.notificacion_fuentes
                    (tipo_fase_id, tipo_tramite_id, fuente, norma, orden)
                VALUES (:tf, :tt, :f, :n, :o)
            """), {'tf': tf_id, 'tt': tt_id, 'f': fuente, 'n': norma, 'o': orden})
