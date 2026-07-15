"""API REST para el catálogo de reglas del motor (#170, N016).

ENDPOINTS:
    GET /api/reglas-motor
        Listado scroll infinito: parámetros cursor + limit + search + accion + efecto + estado.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
ISSUE: #170 (ADR-023 — mismo patrón que #632/#583/#594)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.motor_reglas import ReglaMotor

api_reglas_motor_bp = Blueprint(
    'api_reglas_motor', __name__, url_prefix='/api'
)

_ACCIONES_VALIDAS = {'CREAR', 'BORRAR'}
_EFECTOS_VALIDOS = {'BLOQUEAR', 'ADVERTIR'}


@api_reglas_motor_bp.route('/reglas-motor', methods=['GET'])
@login_required
@require_permiso('acceder_reglas_motor')
def listar_reglas_motor():
    """
    GET /api/reglas-motor  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en sujeto o descripcion.
        estado (str: true/false/'')  : Filtro por activa. Default: todos.
        accion (str: CREAR/BORRAR/'')    : Filtro por acción.
        efecto (str: BLOQUEAR/ADVERTIR/''): Filtro por efecto.

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

        activa_raw = (request.args.get('estado') or '').strip().lower()
        accion_raw = (request.args.get('accion') or '').strip().upper()
        efecto_raw = (request.args.get('efecto') or '').strip().upper()
        if accion_raw and accion_raw not in _ACCIONES_VALIDAS:
            return jsonify({'error': 'Acción inválida'}), 400
        if efecto_raw and efecto_raw not in _EFECTOS_VALIDOS:
            return jsonify({'error': 'Efecto inválido'}), 400

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(ReglaMotor.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                func.lower(ReglaMotor.sujeto).contains(patron)
                | func.lower(ReglaMotor.descripcion).contains(patron)
            )
        if activa_raw == 'true':
            q = q.filter(ReglaMotor.activa == True)   # noqa: E712
        elif activa_raw == 'false':
            q = q.filter(ReglaMotor.activa == False)  # noqa: E712
        if accion_raw:
            q = q.filter(ReglaMotor.accion == accion_raw)
        if efecto_raw:
            q = q.filter(ReglaMotor.efecto == efecto_raw)
        return q

    query = (
        aplicar_filtros(ReglaMotor.query)
        .options(
            joinedload(ReglaMotor.norma),
            joinedload(ReglaMotor.condiciones),
            joinedload(ReglaMotor.excepciones),
        )
        .order_by(ReglaMotor.accion.asc(), ReglaMotor.sujeto.asc(), ReglaMotor.id.asc())
    )
    items = query.limit(limit + 1).all()

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = items[-1].id if items else cursor

    total = None
    if search_query or activa_raw or accion_raw or efecto_raw:
        count_query = aplicar_filtros(db.session.query(func.count(ReglaMotor.id)))
        total = count_query.scalar()

    data = []
    for r in items:
        data.append({
            'id':              r.id,
            'accion':          r.accion,
            'sujeto':          r.sujeto,
            'efecto':          r.efecto,
            'norma':           r.norma.codigo if r.norma else None,
            'prioridad':       r.prioridad,
            'num_condiciones': len(r.condiciones),
            'num_excepciones': len(r.excepciones),
            'descripcion':     r.descripcion,
            'activa':          r.activa,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
