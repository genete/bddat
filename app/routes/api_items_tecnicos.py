"""API REST para el catálogo de ítems técnicos del proyecto (#594).

ENDPOINTS:
    GET /api/items-tecnicos
        Listado scroll infinito: parámetros cursor + limit + search + estado.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
FECHA: 2026-07-06
ISSUE: #594 (ADR-023 — mismo patrón que #583 / api_requisitos_documentales)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.items_tecnicos import ItemTecnico

api_items_tecnicos_bp = Blueprint(
    'api_items_tecnicos', __name__, url_prefix='/api'
)


@api_items_tecnicos_bp.route('/items-tecnicos', methods=['GET'])
@login_required
@require_permiso('acceder_items_tecnicos')
def listar_items():
    """
    GET /api/items-tecnicos  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en descripción o artículo.
        estado (str: true/false/'')  : Filtro por activo. Default: todos.

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

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(ItemTecnico.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(ItemTecnico.descripcion).contains(patron)
                | func.lower(ItemTecnico.articulo).contains(patron)
            )
        if activo_raw == 'true':
            q = q.filter(ItemTecnico.activo == True)   # noqa: E712
        elif activo_raw == 'false':
            q = q.filter(ItemTecnico.activo == False)  # noqa: E712
        return q

    query = (
        aplicar_filtros(ItemTecnico.query)
        .options(
            joinedload(ItemTecnico.norma),
            joinedload(ItemTecnico.condiciones),
        )
        .order_by(ItemTecnico.orden.asc(), ItemTecnico.id.asc())
    )
    items = query.limit(limit + 1).all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = items[-1].id if items else cursor

    total = None
    if search_query or activo_raw:
        count_query = aplicar_filtros(db.session.query(func.count(ItemTecnico.id)))
        total = count_query.scalar()

    data = []
    for it in items:
        data.append({
            'id':              it.id,
            'descripcion':     it.descripcion,
            'norma':           it.norma.codigo if it.norma else None,
            'articulo':        it.articulo,
            'orden':           it.orden,
            'num_condiciones': len(it.condiciones),
            'activo':          it.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
