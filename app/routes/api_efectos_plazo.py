"""API REST para el catálogo de efectos de plazo (#633).

ENDPOINTS:
    GET /api/efectos-plazo
        Listado scroll infinito: parámetros cursor + limit + search.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
ISSUE: #633 (ADR-023 — mismo patrón que #621 / api_tipos_documentos)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.decorators import require_permiso
from app.models.catalogo_plazos import CatalogoPlazo
from app.models.efectos_plazo import EfectoPlazo

api_efectos_plazo_bp = Blueprint(
    'api_efectos_plazo', __name__, url_prefix='/api'
)


@api_efectos_plazo_bp.route('/efectos-plazo', methods=['GET'])
@login_required
@require_permiso('acceder_efectos_plazo')
def listar_efectos():
    """
    GET /api/efectos-plazo  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en código o nombre.

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

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(EfectoPlazo.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(EfectoPlazo.codigo).contains(patron)
                | func.lower(EfectoPlazo.nombre).contains(patron)
            )
        return q

    query = (
        aplicar_filtros(EfectoPlazo.query)
        .order_by(EfectoPlazo.id.asc())
    )
    efectos = query.limit(limit + 1).all()

    has_more = len(efectos) > limit
    if has_more:
        efectos = efectos[:limit]

    next_cursor = efectos[-1].id if efectos else cursor

    total = None
    if search_query:
        count_query = aplicar_filtros(db.session.query(func.count(EfectoPlazo.id)))
        total = count_query.scalar()

    ids_en_uso = {
        row[0] for row in
        db.session.query(CatalogoPlazo.efecto_vencimiento_id)
        .filter(CatalogoPlazo.efecto_vencimiento_id.in_([e.id for e in efectos]))
        .distinct()
    } if efectos else set()

    data = []
    for e in efectos:
        data.append({
            'id':      e.id,
            'codigo':  e.codigo,
            'nombre':  e.nombre,
            'en_uso':  e.id in ids_en_uso,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
