"""API REST para el catálogo de plazos legales (#632).

ENDPOINTS:
    GET /api/catalogo-plazos
        Listado scroll infinito: parámetros cursor + limit + search + estado + nivel.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
ISSUE: #632 (ADR-023 — mismo patrón que #583/#594)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.catalogo_plazos import CatalogoPlazo

api_catalogo_plazos_bp = Blueprint(
    'api_catalogo_plazos', __name__, url_prefix='/api'
)

# Solo los niveles con plazo posible desde #788 — Fase y Trámite no portan
# fecha administrativa y la tabla no tiene filas de esos niveles.
_NIVELES_VALIDOS = {'SOLICITUD', 'TAREA'}


@api_catalogo_plazos_bp.route('/catalogo-plazos', methods=['GET'])
@login_required
@require_permiso('acceder_catalogo_plazos')
def listar_catalogo_plazos():
    """
    GET /api/catalogo-plazos  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en camino o norma_origen.
        estado (str: true/false/'')  : Filtro por activo. Default: todos.
        nivel  (str: SOLICITUD/TAREA/'')              : Filtro por tipo_elemento.

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
        nivel_raw = (request.args.get('nivel') or '').strip().upper()
        if nivel_raw and nivel_raw not in _NIVELES_VALIDOS:
            return jsonify({'error': 'Nivel inválido'}), 400

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(CatalogoPlazo.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            # Búsqueda sobre el camino completo (#785): encuentra por cualquier
            # nivel —trámite padre, fase, siglas— no solo por el tipo hoja.
            q = q.filter(
                func.lower(CatalogoPlazo.camino).contains(patron)
                | func.lower(CatalogoPlazo.norma_origen).contains(patron)
            )
        if activo_raw == 'true':
            q = q.filter(CatalogoPlazo.activo == True)   # noqa: E712
        elif activo_raw == 'false':
            q = q.filter(CatalogoPlazo.activo == False)  # noqa: E712
        if nivel_raw:
            q = q.filter(CatalogoPlazo.tipo_elemento == nivel_raw)
        return q

    query = (
        aplicar_filtros(CatalogoPlazo.query)
        .options(
            joinedload(CatalogoPlazo.efecto_plazo),
            joinedload(CatalogoPlazo.condiciones),
        )
        .order_by(CatalogoPlazo.tipo_elemento.asc(), CatalogoPlazo.orden.asc(), CatalogoPlazo.id.asc())
    )
    items = query.limit(limit + 1).all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = items[-1].id if items else cursor

    total = None
    if search_query or activo_raw or nivel_raw:
        count_query = aplicar_filtros(db.session.query(func.count(CatalogoPlazo.id)))
        total = count_query.scalar()

    data = []
    for cp in items:
        data.append({
            'id':               cp.id,
            'tipo_elemento':    cp.tipo_elemento,
            'camino':           cp.camino,
            'hoja':             cp.hoja,
            'plazo':            f'{cp.plazo_valor} {cp.plazo_unidad}',
            'efecto':           cp.efecto_plazo.nombre if cp.efecto_plazo else None,
            'norma_origen':     cp.norma_origen,
            'num_condiciones':  len(cp.condiciones),
            'orden':            cp.orden,
            'activo':           cp.activo,
            # Qué plazos paran el reloj de la solicitud es dato de catálogo desde
            # #778, y se ve en el listado: es lo que distingue una espera que
            # aprieta el plazo de una que lo para.
            'suspende':         cp.suspende_plazo_solicitud,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
