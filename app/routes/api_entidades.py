"""API REST para entidades.

ENDPOINTS:
    GET /api/entidades
        Modo scroll infinito : parámetros cursor + limit + search + activo
        Modo autocomplete    : parámetro ?q=texto (mín 2 chars, máx 10 resultados)
                               Opcional: ?rol=titular|consultado|publicador
                               Devuelve {results: [{id, text}, ...]}
                               Pensado para selects de titular en wizard expediente.

VERSIÓN: 1.1
FECHA: 2026-02-19
ISSUE: #61
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from app import db
from app.models.entidad import Entidad

api_entidades_bp = Blueprint('api_entidades', __name__, url_prefix='/api')


@api_entidades_bp.route('/entidades', methods=['GET'])
@login_required
def listar_entidades():
    """
    GET /api/entidades  —  Listado paginado con cursor + modo autocomplete.

    MODO AUTOCOMPLETE (?q=texto):
        Activo cuando se pasa el parámetro 'q' (mín 2 chars).
        Devuelve máx. 10 resultados: [{"id": 1, "text": "Nombre (NIF)"}]
        Filtra solo entidades activas.

        Parámetro opcional 'rol':
            rol=titular    → solo entidades con rol_titular=True
            rol=consultado → solo entidades con rol_consultado=True
            rol=publicador → solo entidades con rol_publicador=True
            (omitido o valor desconocido → sin filtro extra, retrocompatible)

    MODO SCROLL INFINITO (sin 'q'):
        Query Parameters:
            cursor (int, default 0)     : ID del último registro recibido.
            limit  (int, default 50)    : Registros por página. Máx: 100.
            search (str, mín 2 chars)   : Búsqueda parcial en nombre_completo o nif.
            activo (str: true/false/'') : Filtro por estado activo. Default: todos.

        Respuesta JSON:
            {
                "data": [
                    {
                        "id": 1,
                        "nombre_completo": "ENDESA DISTRIBUCIÓN S.A.",
                        "nif": "A82091102",
                        "roles": "Titular / Consultado",
                        "activo": true
                    }, ...
                ],
                "next_cursor": 45,
                "has_more": true,
                "total": 89   <- solo si hay filtros activos
            }

    Returns:
        200 OK  con JSON en ambos modos.
        400 Bad Request si parámetros inválidos.
        401 Unauthorized si no autenticado.
    """

    # =========================================================================
    # MODO AUTOCOMPLETE (?q=texto)
    # =========================================================================
    q = request.args.get('q', '').strip()
    if q:
        if len(q) < 2:
            return jsonify({'results': []}), 200

        rol = request.args.get('rol', '').strip().lower()

        query = (
            Entidad.query
            .filter(Entidad.activo == True)
            .filter(
                or_(
                    func.lower(Entidad.nombre_completo).contains(func.lower(q)),
                    func.lower(Entidad.nif).contains(func.lower(q))
                )
            )
        )

        # Filtro opcional por rol (retrocompatible: sin rol = sin restricción)
        if rol == 'titular':
            query = query.filter(Entidad.rol_titular == True)
        elif rol == 'consultado':
            query = query.filter(Entidad.rol_consultado == True)
        elif rol == 'publicador':
            query = query.filter(Entidad.rol_publicador == True)

        entidades = query.order_by(Entidad.nombre_completo).limit(10).all()

        results = []
        for e in entidades:
            label = e.nombre_completo
            if e.nif:
                label += f' ({e.nif})'
            results.append({'id': e.id, 'text': label})

        return jsonify({'results': results}), 200

    # =========================================================================
    # MODO SCROLL INFINITO
    # =========================================================================

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

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # --- Query base ---
    query = Entidad.query

    # Cursor
    if cursor > 0:
        query = query.filter(Entidad.id > cursor)

    # Búsqueda
    if search_query:
        query = query.filter(
            or_(
                func.lower(Entidad.nombre_completo).contains(func.lower(search_query)),
                func.lower(Entidad.nif).contains(func.lower(search_query))
            )
        )

    # Filtro activo
    if activo_raw == 'true':
        query = query.filter(Entidad.activo == True)
    elif activo_raw == 'false':
        query = query.filter(Entidad.activo == False)

    # --- Ejecutar con limit + 1 para detectar has_more ---
    query = query.order_by(Entidad.id.asc())
    entidades = query.limit(limit + 1).all()

    has_more = len(entidades) > limit
    if has_more:
        entidades = entidades[:limit]

    next_cursor = entidades[-1].id if entidades else cursor

    # --- Total (solo cuando hay filtros activos) ---
    total = None
    if search_query or activo_raw:
        count_query = db.session.query(func.count(Entidad.id))
        if cursor > 0:
            count_query = count_query.filter(Entidad.id > cursor)
        if search_query:
            count_query = count_query.filter(
                or_(
                    func.lower(Entidad.nombre_completo).contains(func.lower(search_query)),
                    func.lower(Entidad.nif).contains(func.lower(search_query))
                )
            )
        if activo_raw == 'true':
            count_query = count_query.filter(Entidad.activo == True)
        elif activo_raw == 'false':
            count_query = count_query.filter(Entidad.activo == False)
        total = count_query.scalar()

    # --- Serializar ---
    data = []
    for e in entidades:
        roles = []
        if e.rol_titular:    roles.append('Titular')
        if e.rol_consultado: roles.append('Consultado')
        if e.rol_publicador: roles.append('Publicador')

        data.append({
            'id':             e.id,
            'nombre_completo': e.nombre_completo,
            'nif':             e.nif or '-',
            'roles':           ' / '.join(roles) if roles else '-',
            'activo':          e.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
