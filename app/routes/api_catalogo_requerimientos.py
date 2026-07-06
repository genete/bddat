"""API REST para el catálogo de requerimientos (#593).

ENDPOINTS:
    GET /api/catalogo-requerimientos
        Listado scroll infinito: parámetros cursor + limit + search + estado
        + categoria.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
FECHA: 2026-07-06
ISSUE: #593 (ADR-023 — mismo patrón que #583 / api_requisitos_documentales)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.decorators import require_permiso
from app.models.catalogo_requerimientos import CatalogoRequerimiento

api_catalogo_requerimientos_bp = Blueprint(
    'api_catalogo_requerimientos', __name__, url_prefix='/api'
)

_CATEGORIA_LABELS = {
    'documental':     'Documental',
    'tecnica':        'Técnica',
    'administrativa': 'Administrativa',
    'tasas':          'Tasas',
}


@api_catalogo_requerimientos_bp.route('/catalogo-requerimientos', methods=['GET'])
@login_required
@require_permiso('acceder_catalogo_requerimientos')
def listar_requerimientos():
    """
    GET /api/catalogo-requerimientos  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en el texto.
        estado (str: true/false/'')  : Filtro por activo. Default: todos.
        categoria (str)              : Filtro por categoria.

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

        activo_raw = (request.args.get('estado') or '').strip().lower()
        categoria = request.args.get('categoria', '').strip() or None

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(CatalogoRequerimiento.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(func.lower(CatalogoRequerimiento.texto).contains(patron))
        if activo_raw == 'true':
            q = q.filter(CatalogoRequerimiento.activo == True)   # noqa: E712
        elif activo_raw == 'false':
            q = q.filter(CatalogoRequerimiento.activo == False)  # noqa: E712
        if categoria is not None:
            q = q.filter(CatalogoRequerimiento.categoria == categoria)
        return q

    query = (
        aplicar_filtros(CatalogoRequerimiento.query)
        .order_by(CatalogoRequerimiento.id.asc())
    )
    requerimientos = query.limit(limit + 1).all()

    has_more = len(requerimientos) > limit
    if has_more:
        requerimientos = requerimientos[:limit]

    next_cursor = requerimientos[-1].id if requerimientos else cursor

    total = None
    if search_query or activo_raw or categoria is not None:
        count_query = aplicar_filtros(db.session.query(func.count(CatalogoRequerimiento.id)))
        total = count_query.scalar()

    data = []
    for r in requerimientos:
        data.append({
            'id':              r.id,
            'texto':           r.texto,
            'categoria':       r.categoria,
            'categoria_label': _CATEGORIA_LABELS.get(r.categoria, r.categoria),
            'num_usos':        r.usos.count(),
            'activo':          r.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
