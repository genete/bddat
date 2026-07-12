"""API REST para el catálogo de tipos de documento (#621).

ENDPOINTS:
    GET /api/tipos-documento
        Listado scroll infinito: parámetros cursor + limit + search + origen.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
ISSUE: #621 (ADR-023 — mismo patrón que #593 / api_catalogo_requerimientos)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS
from app.decorators import require_permiso
from app.models.tipos_documentos import TipoDocumento

api_tipos_documentos_bp = Blueprint(
    'api_tipos_documentos', __name__, url_prefix='/api'
)

_ORIGEN_LABELS = {
    'INTERNO': 'Interno',
    'EXTERNO': 'Externo',
    'AMBOS':   'Ambos',
}
_CODIGOS_PROTEGIDOS = set(REGISTROS_REQUERIDOS.get('TipoDocumento', []))


@api_tipos_documentos_bp.route('/tipos-documento', methods=['GET'])
@login_required
@require_permiso('acceder_tipos_documentos')
def listar_tipos():
    """
    GET /api/tipos-documento  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en código o nombre.
        origen (str)                 : Filtro por origen (INTERNO/EXTERNO/AMBOS).

    Returns:
        200 OK  con JSON {data, next_cursor, has_more, total?}.
        400 Bad Request si parámetros inválidos.
    """
    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'Cursor debe ser >= 0'}), 400

        limit = int(request.args.get('limit', 50))
        if limit < 1:
            return jsonify({'error': 'Limit debe ser >= 1'}), 400
        if limit > 100:
            limit = 100

        search_query = request.args.get('search', '').strip()
        if search_query and len(search_query) < 2:
            return jsonify({'error': 'Search debe tener al menos 2 caracteres'}), 400

        origen = request.args.get('origen', '').strip() or None

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(TipoDocumento.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(TipoDocumento.codigo).contains(patron)
                | func.lower(TipoDocumento.nombre).contains(patron)
            )
        if origen is not None:
            q = q.filter(TipoDocumento.origen == origen)
        return q

    query = (
        aplicar_filtros(TipoDocumento.query)
        .order_by(TipoDocumento.id.asc())
    )
    tipos = query.limit(limit + 1).all()

    has_more = len(tipos) > limit
    if has_more:
        tipos = tipos[:limit]

    next_cursor = tipos[-1].id if tipos else cursor

    total = None
    if search_query or origen is not None:
        count_query = aplicar_filtros(db.session.query(func.count(TipoDocumento.id)))
        total = count_query.scalar()

    data = []
    for t in tipos:
        data.append({
            'id':           t.id,
            'codigo':       t.codigo,
            'nombre':       t.nombre,
            'descripcion':  t.descripcion,
            'origen':       t.origen,
            'origen_label': _ORIGEN_LABELS.get(t.origen, t.origen),
            'protegido':    t.codigo in _CODIGOS_PROTEGIDOS,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
