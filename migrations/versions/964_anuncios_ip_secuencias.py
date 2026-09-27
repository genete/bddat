"""964_anuncios_ip_secuencias — BOJA, BOE y PRENSA como en ESTRUCTURA_FTT.json

Revision ID: 964_anuncios_ip_secuencias
Revises: 967_destinatario_notificacion
Create Date: 2026-09-27

Issue #964. El catálogo no seguía a `ESTRUCTURA_FTT.json` (fuente de verdad) en
tres anuncios de `INFORMACION_PUBLICA`:

- `ANUNCIO_BOJA` pierde el ELABORAR: el anuncio se sube a SIBOJA sin oficio.
  NOTIFICAR → ESPERAR_PLAZO → ESPERAR_PLAZO, el mapa de BOP sin su oficio.
- `ANUNCIO_BOE` y `ANUNCIO_PRENSA` pierden el NOTIFICAR: los publica el titular,
  a quien se lo comunica `ANUNCIO_TITULAR`. ESPERAR_PLAZO → ESPERAR_PLAZO: la
  primera (sin plazo, #789) recibe lo que notificó `ANUNCIO_TITULAR` y la
  cierra el justificante de publicación que aporta el titular
  (`JUSTIFICANTE_BOE` / `JUSTIFICANTE_PRENSA`, no `ANUNCIO_PUBLICADO`, que es
  el de BOP y BOJA); la segunda lo consume y cuenta el plazo de IP.

Por cada trámite se borran primero sus filas de `tramites_tareas_documentos`
(`fk_ttd_tramite_tarea` apunta a `tramites_tareas`), después las de
`tramites_tareas`, y se reescriben las dos: criterio de
`346_tramites_tareas_documentos`. Ninguna tabla operacional apunta a
`tramites_tareas`.

`catalogo_plazos`: la segunda espera de BOE y PRENSA se reconoce por el tipo de
documento que consume (788a), así que la clave cambia con el mapa; si no, el
plazo de IP dejaría de aplicarse. `ANUNCIO_BOP` no cambia y `ANUNCIO_BOJA`
sigue sin fila (#788 §10). Se actualizan las filas de la segunda espera de
cualquier camino (no solo `ANY/ANY/ANY/…`); si no hay ninguna, se aborta.

Todo se localiza por código, nunca por id (REGLAS_DESARROLLO §Migraciones).
"""
from alembic import op
import sqlalchemy as sa


revision = '964_anuncios_ip_secuencias'
down_revision = '967_destinatario_notificacion'
branch_labels = None
depends_on = None


# Secuencia de un trámite: [(orden, tarea, [(rol, tipo_documento, obligatorio), …]), …]
# tipo_documento None = tipo abierto (polimórfico): el justificante depende del canal.

def _boe_prensa_antes():
    return [
        (1, 'NOTIFICAR', [('ENTRADA', 'ANUNCIO_IP', True),
                          ('SALIDA', None, True)]),
        (2, 'ESPERAR_PLAZO', [('ENTRADA', None, False),
                              ('SALIDA', 'ANUNCIO_PUBLICADO', False)]),
        (3, 'ESPERAR_PLAZO', [('ENTRADA', 'ANUNCIO_PUBLICADO', True),
                              ('SALIDA', 'CERT_PLAZO_CUMPLIDO', False)]),
    ]


def _boe_prensa_despues(justificante):
    return [
        # 1.ª espera, sin plazo: llega lo que notificó ANUNCIO_TITULAR —su
        # justificante, de tipo abierto, y el oficio— y la cierra el
        # justificante de publicación que aporta el titular.
        (1, 'ESPERAR_PLAZO', [('ENTRADA', None, False),
                              ('ENTRADA', 'OFICIO_PUBLICAR_TITULAR', False),
                              ('SALIDA', justificante, False)]),
        # 2.ª espera: el plazo de IP, desde la publicación.
        (2, 'ESPERAR_PLAZO', [('ENTRADA', justificante, True),
                              ('SALIDA', 'CERT_PLAZO_CUMPLIDO', False)]),
    ]


_ANTES = {
    'ANUNCIO_BOJA': [
        (1, 'ELABORAR', [('ENTRADA', 'ANUNCIO_IP', True),
                         ('SALIDA', 'OFICIO_PUBLICAR_BOLETIN', True)]),
        (2, 'NOTIFICAR', [('ENTRADA', 'OFICIO_PUBLICAR_BOLETIN', True),
                          ('SALIDA', None, True)]),
        (3, 'ESPERAR_PLAZO', [('ENTRADA', None, False),
                              ('SALIDA', 'ANUNCIO_PUBLICADO', False)]),
        (4, 'ESPERAR_PLAZO', [('ENTRADA', 'ANUNCIO_PUBLICADO', True),
                              ('SALIDA', 'CERT_PLAZO_CUMPLIDO', False)]),
    ],
    'ANUNCIO_BOE': _boe_prensa_antes(),
    'ANUNCIO_PRENSA': _boe_prensa_antes(),
}

_DESPUES = {
    'ANUNCIO_BOJA': [
        # Sin oficio: el NOTIFICAR sube el anuncio a SIBOJA y produce su acuse.
        (1, 'NOTIFICAR', [('ENTRADA', 'ANUNCIO_IP', True),
                          ('SALIDA', None, True)]),
        (2, 'ESPERAR_PLAZO', [('ENTRADA', None, False),
                              ('SALIDA', 'ANUNCIO_PUBLICADO', False)]),
        (3, 'ESPERAR_PLAZO', [('ENTRADA', 'ANUNCIO_PUBLICADO', True),
                              ('SALIDA', 'CERT_PLAZO_CUMPLIDO', False)]),
    ],
    'ANUNCIO_BOE': _boe_prensa_despues('JUSTIFICANTE_BOE'),
    'ANUNCIO_PRENSA': _boe_prensa_despues('JUSTIFICANTE_PRENSA'),
}

# Trámite → tipo de documento que consume su segunda espera tras la migración.
_CLAVE_PLAZO = {
    'ANUNCIO_BOE': 'JUSTIFICANTE_BOE',
    'ANUNCIO_PRENSA': 'JUSTIFICANTE_PRENSA',
}


def _tid(conn, tabla, codigo):
    """Id de un registro de catálogo por su código; aborta si no existe."""
    resultado = conn.execute(
        sa.text(f"SELECT id FROM public.{tabla} WHERE codigo = :c"), {'c': codigo}
    ).scalar()
    if resultado is None:
        raise ValueError(f"'{codigo}' no encontrado en {tabla} — migración abortada")
    return resultado


def _reescribir(conn, secuencias):
    for tramite_codigo, pasos in secuencias.items():
        tt_id = _tid(conn, 'tipos_tramites', tramite_codigo)
        conn.execute(sa.text(
            "DELETE FROM public.tramites_tareas_documentos WHERE tipo_tramite_id = :tt"
        ), {'tt': tt_id})
        conn.execute(sa.text(
            "DELETE FROM public.tramites_tareas WHERE tipo_tramite_id = :tt"
        ), {'tt': tt_id})
        for orden, tarea_codigo, documentos in pasos:
            conn.execute(sa.text("""
                INSERT INTO public.tramites_tareas (tipo_tramite_id, orden, tipo_tarea_id)
                VALUES (:tt, :o, :ta)
            """), {'tt': tt_id, 'o': orden, 'ta': _tid(conn, 'tipos_tareas', tarea_codigo)})
            for rol, doc_codigo, obligatorio in documentos:
                td_id = _tid(conn, 'tipos_documentos', doc_codigo) if doc_codigo else None
                conn.execute(sa.text("""
                    INSERT INTO public.tramites_tareas_documentos
                        (tipo_tramite_id, orden_tarea, rol, tipo_documento_id, obligatorio)
                    VALUES (:tt, :o, :rol, :td, :oblig)
                """), {'tt': tt_id, 'o': orden, 'rol': rol, 'td': td_id, 'oblig': obligatorio})


def _cambiar_clave_plazo(conn, tramite_codigo, de, a):
    """La segunda espera del trámite pasa a reconocerse por `a` en vez de `de`.
    Localiza por los dos últimos segmentos del camino (trámite y tarea), sea
    cual sea el resto."""
    n = conn.execute(sa.text("""
        UPDATE public.catalogo_plazos
        SET campo_fecha = jsonb_set(campo_fecha, '{tipo_documento}', to_jsonb(CAST(:a AS text)))
        WHERE tipo_elemento = 'TAREA'
          AND split_part(camino, '/', 4) = :tramite
          AND split_part(camino, '/', 5) = 'ESPERAR_PLAZO'
          AND campo_fecha ->> 'rol' = 'CONSUMIDO'
          AND campo_fecha ->> 'tipo_documento' = :de
    """), {'tramite': tramite_codigo, 'de': de, 'a': a}).rowcount
    if n == 0:
        raise RuntimeError(
            f'catalogo_plazos: ninguna fila de {tramite_codigo}/ESPERAR_PLAZO con '
            f'tipo_documento {de} — migración abortada')


def upgrade():
    conn = op.get_bind()
    _reescribir(conn, _DESPUES)
    for tramite_codigo, justificante in _CLAVE_PLAZO.items():
        _cambiar_clave_plazo(conn, tramite_codigo, 'ANUNCIO_PUBLICADO', justificante)


def downgrade():
    conn = op.get_bind()
    for tramite_codigo, justificante in _CLAVE_PLAZO.items():
        _cambiar_clave_plazo(conn, tramite_codigo, justificante, 'ANUNCIO_PUBLICADO')
    _reescribir(conn, _ANTES)
