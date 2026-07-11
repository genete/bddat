"""API REST para los catálogos estructurales ESFTT (#171).

ENDPOINTS:
    GET /api/tablas-maestras/<tipo>
        Listado scroll infinito: parámetros cursor + limit + search.
        <tipo> ∈ expediente | solicitud | fase | tramite | tarea.
        Devuelve {data, next_cursor, has_more, total?}
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import func, or_

from app import db
from app.decorators import require_permiso
from app.modules.tablas_maestras.config import TIPOS

api_tablas_maestras_bp = Blueprint('api_tablas_maestras', __name__, url_prefix='/api')


@api_tablas_maestras_bp.route('/tablas-maestras/<tipo>', methods=['GET'])
@login_required
@require_permiso('acceder_tablas_maestras')
def listar(tipo):
    cfg = TIPOS.get(tipo)
    if cfg is None:
        return jsonify({'error': 'Tipo de catálogo desconocido'}), 404

    model = cfg['model']
    id_col = getattr(model, cfg['id_field'])

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

    campos_texto = [c for c in cfg['campos'] if c[2] != 'bool']

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(model.id > cursor)
        if search_query:
            patron = f'%{search_query.lower()}%'
            condiciones = [func.lower(id_col).like(patron)]
            for campo, *_ in campos_texto:
                col = getattr(model, campo)
                condiciones.append(func.lower(col).like(patron))
            q = q.filter(or_(*condiciones))
        return q

    query = aplicar_filtros(model.query).order_by(model.id.asc())
    filas = query.limit(limit + 1).all()

    has_more = len(filas) > limit
    if has_more:
        filas = filas[:limit]
    next_cursor = filas[-1].id if filas else cursor

    total = None
    if search_query:
        total = aplicar_filtros(db.session.query(func.count(model.id))).scalar()

    data = []
    for fila in filas:
        valor_id = getattr(fila, cfg['id_field'])
        item = {
            'id': fila.id,
            'id_field': valor_id,
            'protegido': valor_id in cfg['protegidos'],
        }
        for campo, *_ in cfg['campos']:
            item[campo] = getattr(fila, campo)
        data.append(item)

    response = {'data': data, 'next_cursor': next_cursor, 'has_more': has_more}
    if total is not None:
        response['total'] = total
    return jsonify(response), 200
