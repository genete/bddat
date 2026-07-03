"""API REST para el catálogo de requisitos documentales (#583).

ENDPOINTS:
    GET /api/admin-requisitos
        Listado scroll infinito: parámetros cursor + limit + search + estado
        + tipo_documento.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
FECHA: 2026-07-03
ISSUE: #583 (ADR-023 — mismo patrón que #545 / api_plantillas)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.requisitos_documentales import RequisitoDocumental

api_requisitos_documentales_bp = Blueprint(
    'api_requisitos_documentales', __name__, url_prefix='/api'
)


@api_requisitos_documentales_bp.route('/admin-requisitos', methods=['GET'])
@login_required
@require_permiso('acceder_requisitos_documentales')
def listar_requisitos():
    """
    GET /api/admin-requisitos  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en descripción legal o artículo.
        estado (str: true/false/'')  : Filtro por activo. Default: todos.
        tipo_documento (int)         : Filtro por tipo_documento_id.

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

        tipo_documento_raw = request.args.get('tipo_documento', '').strip()
        tipo_documento_id  = int(tipo_documento_raw) if tipo_documento_raw else None

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(RequisitoDocumental.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                or_(
                    func.lower(RequisitoDocumental.descripcion_legal).contains(patron),
                    func.lower(RequisitoDocumental.articulo).contains(patron),
                )
            )
        if activo_raw == 'true':
            q = q.filter(RequisitoDocumental.activo == True)   # noqa: E712
        elif activo_raw == 'false':
            q = q.filter(RequisitoDocumental.activo == False)  # noqa: E712
        if tipo_documento_id is not None:
            q = q.filter(RequisitoDocumental.tipo_documento_id == tipo_documento_id)
        return q

    query = (
        aplicar_filtros(RequisitoDocumental.query)
        .options(
            joinedload(RequisitoDocumental.tipo_documento),
            joinedload(RequisitoDocumental.norma),
            joinedload(RequisitoDocumental.condiciones),
        )
        .order_by(RequisitoDocumental.orden.asc(), RequisitoDocumental.id.asc())
    )
    requisitos = query.limit(limit + 1).all()

    has_more = len(requisitos) > limit
    if has_more:
        requisitos = requisitos[:limit]

    next_cursor = requisitos[-1].id if requisitos else cursor

    total = None
    if search_query or activo_raw or tipo_documento_id is not None:
        count_query = aplicar_filtros(db.session.query(func.count(RequisitoDocumental.id)))
        total = count_query.scalar()

    data = []
    for r in requisitos:
        data.append({
            'id':                r.id,
            'tipo_documento':    r.tipo_documento.nombre if r.tipo_documento else None,
            'descripcion_legal': r.descripcion_legal,
            'norma':             r.norma.codigo if r.norma else None,
            'articulo':          r.articulo,
            'orden':             r.orden,
            'num_condiciones':   len(r.condiciones),
            'activo':            r.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
