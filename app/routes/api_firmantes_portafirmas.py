"""API REST para el catálogo de firmantes de Port@firmas (#728).

ENDPOINTS:
    GET /api/firmantes-portafirmas
        Listado scroll infinito: parámetros cursor + limit + search.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
ISSUE: #728 (ADR-023 — mismo patrón que #621 / api_tipos_documentos)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func

from app import db
from app.decorators import require_permiso
from app.models.organo_propio import FirmantePortafirmas, UnidadOrganoPropio

api_firmantes_portafirmas_bp = Blueprint(
    'api_firmantes_portafirmas', __name__, url_prefix='/api'
)


@api_firmantes_portafirmas_bp.route('/firmantes-portafirmas', methods=['GET'])
@login_required
@require_permiso('acceder_firmantes_portafirmas')
def listar_firmantes():
    """
    GET /api/firmantes-portafirmas  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en nombre, DNI o cargo.

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
            q = q.filter(FirmantePortafirmas.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(FirmantePortafirmas.nombre).contains(patron)
                | func.lower(FirmantePortafirmas.dni).contains(patron)
                | func.lower(FirmantePortafirmas.cargo).contains(patron)
            )
        return q

    query = (
        aplicar_filtros(FirmantePortafirmas.query)
        .order_by(FirmantePortafirmas.id.asc())
    )
    firmantes = query.limit(limit + 1).all()

    has_more = len(firmantes) > limit
    if has_more:
        firmantes = firmantes[:limit]

    next_cursor = firmantes[-1].id if firmantes else cursor

    total = None
    if search_query:
        count_query = aplicar_filtros(db.session.query(func.count(FirmantePortafirmas.id)))
        total = count_query.scalar()

    unidades_por_id = {
        u.id: u for u in
        UnidadOrganoPropio.query.filter(
            UnidadOrganoPropio.id.in_([f.unidad_organo_id for f in firmantes])
        )
    } if firmantes else {}

    data = []
    for f in firmantes:
        unidad = unidades_por_id.get(f.unidad_organo_id)
        data.append({
            'id':                f.id,
            'nombre':            f.nombre,
            'cargo':             f.cargo,
            'dni':               f.dni,
            'unidad_provincia':  (unidad.provincia or 'Servicios centrales') if unidad else None,
            'vigente':           f.vigente,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
