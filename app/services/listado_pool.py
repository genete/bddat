"""Listado del pool de documentos de un expediente: consulta paginada y su fila (#881, ADR-053 §F).

El pool pasa a ser un listado estándar (scroll infinito con cursor, `FiltrosListado`, clic en la
fila → inspector). Este módulo es lo que sirve `GET /api/expedientes/<id>/documentos`, y está
aquí y no en la ruta para que lo lean también la página (las extensiones del selector) y, en su
día, quien necesite una fila del pool.

- **Orden y cursor.** El más reciente primero (`id` descendente, como el pool de siempre). El
  cursor es el `id` del último documento recibido y `0` es «desde arriba»: la siguiente página
  son los de `id` menor.
- **La fila** es la fila común de ADR-053 §E (`detalle_nodo.documento_fila`: nombre, tipo, fecha
  en ISO, asunto, marcas y apertura) más lo propio del pool: la extensión y los usos
  (`usos_documento`: cuáles son y cuántos), que la columna de usos pinta como número con el
  desglose al pasar el ratón.
- **Los filtros** son los del pool de antes, ahora en el servidor: texto (nombre o asunto),
  extensión, tipo y prioridad. El nombre y la extensión se calculan **en SQL** con la misma regla
  que `Documento.nombre_visible()` —`nombre_fichero`; en un `bddat://`, el nombre del tipo; en una
  URL externa, su último tramo sin `?` ni `#`—, porque filtrar en Python obligaría a traer todo el
  pool. Son dos implementaciones de una regla: si cambia `nombre_visible`, cambia aquí
  (`extension_de` y `_nombre_sql`).
- **`total`** va siempre (no solo con filtros, como en los listados de catálogo): el pool de un
  expediente es acotado y es una sola consulta de recuento.
"""
from __future__ import annotations

from sqlalchemy import case, func, null, or_

from app import db
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services.detalle_nodo import documento_fila, opciones_fila_documento
from app.services.usos_documento import opciones_usos_documento, usos_de_documentos

LIMITE_POR_DEFECTO = 50
LIMITE_MAXIMO = 100

PRIORIDADES = ('', '0', '1')   # todas · no prioritarios · prioritarios


def extension_de(documento) -> str:
    """Extensión del nombre que se enseña, en minúsculas, o `''`. Un `bddat://` no tiene:
    su nombre es el del tipo y lo que haya tras el último punto no es una extensión."""
    if (documento.url or '').startswith('bddat://'):
        return ''
    partes = documento.nombre_visible().rsplit('.', 1)
    return partes[1].lower() if len(partes) == 2 and partes[1] else ''


# ---------------------------------------------------------------------------
# La misma regla de nombre y extensión, en SQL
# ---------------------------------------------------------------------------

def _es_bddat():
    return Documento.url.like('bddat://%')


def _ultimo_tramo_de_la_url():
    """«doc.pdf» de `https://sede/x/doc.pdf?id=3#a`: sin ruta, sin `?` y sin `#`."""
    sin_ruta = func.regexp_replace(Documento.url, '^.*/', '')
    return func.split_part(func.split_part(sin_ruta, '?', 1), '#', 1)


def _nombre_sql():
    """`Documento.nombre_visible()` en SQL (necesita el join con `TipoDocumento`). No cubre el
    último recurso de `nombre_visible` («Documento <id>», para una url que acaba en `/`)."""
    return case(
        (func.coalesce(Documento.nombre_fichero, '') != '', Documento.nombre_fichero),
        (_es_bddat(), TipoDocumento.nombre),
        else_=_ultimo_tramo_de_la_url(),
    )


def _extension_sql():
    """`extension_de` en SQL: NULL si no hay (un `bddat://` o un nombre sin punto)."""
    return case(
        (_es_bddat(), null()),
        else_=func.lower(func.substring(_nombre_sql(), r'\.([^.]+)$')),
    )


def _consulta(expediente_id, *, search, ext, tipo, prioridad):
    consulta = (
        Documento.query
        .outerjoin(TipoDocumento, TipoDocumento.id == Documento.tipo_doc_id)
        .filter(Documento.expediente_id == expediente_id)
    )
    if search:
        consulta = consulta.filter(or_(
            _nombre_sql().icontains(search, autoescape=True),
            Documento.asunto.icontains(search, autoescape=True),
        ))
    if ext:
        consulta = consulta.filter(_extension_sql() == ext.lower())
    if tipo is not None:
        consulta = consulta.filter(Documento.tipo_doc_id == tipo)
    if prioridad == '1':
        consulta = consulta.filter(Documento.prioridad > 0)
    elif prioridad == '0':
        consulta = consulta.filter(or_(Documento.prioridad.is_(None), Documento.prioridad <= 0))
    return consulta


def extensiones_del_pool(expediente_id) -> list:
    """Las extensiones que hay en el pool del expediente, ordenadas: las opciones del filtro
    de extensión. Salen de los documentos y no de una lista fija, como siempre."""
    extension = _extension_sql()
    filas = (
        db.session.query(extension)
        .select_from(Documento)
        .outerjoin(TipoDocumento, TipoDocumento.id == Documento.tipo_doc_id)
        .filter(Documento.expediente_id == expediente_id)
        .distinct()
        .all()
    )
    return sorted(f[0] for f in filas if f[0])


def fila_pool(expediente_id, documento, usos) -> dict:
    """La fila del listado: la común (ADR-053 §E) y lo propio del pool."""
    return {
        **documento_fila(expediente_id, documento, estricto=False),
        'extension': extension_de(documento),
        'n_usos': len(usos),
        'usos': usos,
    }


def pagina_pool(expediente_id, *, cursor=0, limit=LIMITE_POR_DEFECTO, search='', ext='',
                tipo=None, prioridad='') -> dict:
    """Una página del pool: `{data, next_cursor, has_more, total}`, el contrato de
    `ScrollInfinito`. Los parámetros llegan ya validados (`cursor` ≥ 0, `limit` entre 1 y
    `LIMITE_MAXIMO`, `tipo` un id o `None`, `prioridad` uno de `PRIORIDADES`).

    El eager loading cubre la fila (tipo, marcas) y los usos: una consulta por relación y no
    por documento. El recuento ignora el cursor: es el total de lo que filtran los criterios.
    """
    filtrada = _consulta(expediente_id, search=search, ext=ext, tipo=tipo, prioridad=prioridad)
    total = filtrada.with_entities(func.count(Documento.id)).scalar()

    pagina = filtrada.options(*opciones_fila_documento(), *opciones_usos_documento())
    if cursor > 0:
        pagina = pagina.filter(Documento.id < cursor)
    documentos = pagina.order_by(Documento.id.desc()).limit(limit + 1).all()

    hay_mas = len(documentos) > limit
    documentos = documentos[:limit]
    usos = usos_de_documentos(documentos)
    return {
        'data': [fila_pool(expediente_id, d, usos[d.id]) for d in documentos],
        'next_cursor': documentos[-1].id if documentos else cursor,
        'has_more': hay_mas,
        'total': total,
    }
