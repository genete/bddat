"""API REST para el catálogo de Normas y Variables del motor (#637, N083).

ENDPOINTS:
    GET /api/normas
        Listado scroll infinito: parámetros cursor + limit + search.
        Devuelve {data, next_cursor, has_more, total?}

    GET /api/catalogo-variables
        Listado scroll infinito: parámetros cursor + limit + search.
        Devuelve {data, next_cursor, has_more, total?}
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.decorators import require_permiso
from app.models.motor_reglas import CatalogoVariable, Norma
from app.services.variables import get_registry

api_normas_variables_bp = Blueprint(
    'api_normas_variables', __name__, url_prefix='/api'
)


@api_normas_variables_bp.route('/normas', methods=['GET'])
@login_required
@require_permiso('acceder_normas_variables')
def listar_normas():
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
            q = q.filter(Norma.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(Norma.codigo).contains(patron)
                | func.lower(Norma.titulo).contains(patron)
            )
        return q

    query = aplicar_filtros(Norma.query).order_by(Norma.id.asc())
    normas = query.limit(limit + 1).all()

    has_more = len(normas) > limit
    if has_more:
        normas = normas[:limit]

    next_cursor = normas[-1].id if normas else cursor

    total = None
    if search_query:
        total = aplicar_filtros(db.session.query(func.count(Norma.id))).scalar()

    data = [{
        'id':      n.id,
        'codigo':  n.codigo,
        'titulo':  n.titulo,
        'url_eli': n.url_eli,
    } for n in normas]

    response = {'data': data, 'next_cursor': next_cursor, 'has_more': has_more}
    if total is not None:
        response['total'] = total
    return jsonify(response), 200


@api_normas_variables_bp.route('/catalogo-variables', methods=['GET'])
@login_required
@require_permiso('acceder_normas_variables')
def listar_variables():
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
            q = q.filter(CatalogoVariable.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(CatalogoVariable.nombre).contains(patron)
                | func.lower(CatalogoVariable.etiqueta).contains(patron)
            )
        return q

    query = aplicar_filtros(CatalogoVariable.query).order_by(CatalogoVariable.id.asc())
    variables = query.limit(limit + 1).all()

    has_more = len(variables) > limit
    if has_more:
        variables = variables[:limit]

    next_cursor = variables[-1].id if variables else cursor

    total = None
    if search_query:
        total = aplicar_filtros(db.session.query(func.count(CatalogoVariable.id))).scalar()

    registry = get_registry()
    data = [{
        'id':           v.id,
        'nombre':       v.nombre,
        'etiqueta':     v.etiqueta,
        'tipo_dato':    v.tipo_dato,
        'norma_codigo': v.norma.codigo if v.norma else None,
        'activa':       v.activa,
        'en_registry':  v.nombre in registry,
    } for v in variables]

    response = {'data': data, 'next_cursor': next_cursor, 'has_more': has_more}
    if total is not None:
        response['total'] = total
    return jsonify(response), 200
