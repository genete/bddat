"""API REST para usuarios.

ENDPOINTS:
    GET /api/usuarios
        Listado scroll infinito : parámetros cursor + limit + search + activo + rol
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
FECHA: 2026-06-14
ISSUE: #544 (ADR-023 — migración del listado de usuarios al patrón inspector)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from app import db
from app.models.usuarios import Usuario, Rol
from app.decorators import require_permiso

api_usuarios_bp = Blueprint('api_usuarios', __name__, url_prefix='/api')


@api_usuarios_bp.route('/usuarios', methods=['GET'])
@login_required
@require_permiso('acceder_usuarios')
def listar_usuarios():
    """
    GET /api/usuarios  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)     : ID del último registro recibido.
        limit  (int, default 50)    : Registros por página. Máx: 100.
        search (str, mín 2 chars)   : Búsqueda parcial en siglas, nombre o apellidos.
        activo (str: true/false/'') : Filtro por estado activo. Default: todos.
                                      (alias 'estado' desde ScrollInfinito).
        rol    (str)                : Filtro por nombre de rol (ADMIN, SUPERVISOR…).

    Respuesta JSON:
        {
            "data": [
                {
                    "id": 1,
                    "siglas": "CGL",
                    "nombre_completo": "Carlos García López",
                    "roles": "ADMIN / SUPERVISOR",
                    "activo": true
                }, ...
            ],
            "next_cursor": 45,
            "has_more": true,
            "total": 12   <- solo si hay filtros activos
        }

    Returns:
        200 OK  con JSON.
        400 Bad Request si parámetros inválidos.
        401 Unauthorized si no autenticado.
    """

    # --- Parsear parámetros ---
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

        # Acepta tanto 'activo' (semántico) como 'estado' (alias desde ScrollInfinito)
        activo_raw = (request.args.get('activo') or request.args.get('estado') or '').strip().lower()
        rol_filtro = request.args.get('rol', '').strip()

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # --- Construir filtros reutilizables (para query de datos y de total) ---
    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(Usuario.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                or_(
                    func.lower(Usuario.siglas).contains(patron),
                    func.lower(Usuario.nombre).contains(patron),
                    func.lower(Usuario.apellido1).contains(patron),
                    func.lower(Usuario.apellido2).contains(patron),
                )
            )
        if activo_raw == 'true':
            q = q.filter(Usuario.activo == True)
        elif activo_raw == 'false':
            q = q.filter(Usuario.activo == False)
        # Filtro por rol: join con la tabla intermedia solo si se solicita
        # (no hacerlo sin filtro excluiría a usuarios sin roles)
        if rol_filtro:
            q = q.join(Usuario.roles).filter(Rol.nombre == rol_filtro)
        return q

    # --- Query de datos: limit + 1 para detectar has_more ---
    query = aplicar_filtros(Usuario.query).order_by(Usuario.id.asc())
    usuarios = query.limit(limit + 1).all()

    has_more = len(usuarios) > limit
    if has_more:
        usuarios = usuarios[:limit]

    next_cursor = usuarios[-1].id if usuarios else cursor

    # --- Total (solo cuando hay filtros activos) ---
    total = None
    if search_query or activo_raw or rol_filtro:
        count_query = aplicar_filtros(db.session.query(func.count(func.distinct(Usuario.id))))
        total = count_query.scalar()

    # --- Serializar ---
    data = []
    for u in usuarios:
        nombre_completo = ' '.join(
            p for p in [u.nombre, u.apellido1, u.apellido2] if p
        )
        roles = ' / '.join(r.nombre for r in u.roles) if u.roles else '-'
        data.append({
            'id':              u.id,
            'siglas':          u.siglas,
            'nombre_completo': nombre_completo,
            'roles':           roles,
            'activo':          u.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
