"""API REST para entidades.

ENDPOINTS:
    GET /api/entidades
        Modo scroll infinito : parámetros cursor + limit + search + activo
        Modo autocomplete    : parámetro ?q=texto (mín 2 chars, máx 10 resultados)
                               Opcional: ?rol=titular|consultado|publicador
                               Devuelve {results: [{id, text}, ...]}
                               Pensado para selects de titular en wizard expediente.

    GET /api/entidades/consultables
        Entidades activas con rol_consultado=True y sus direcciones de notificación
        CONSULTADO activas. Parámetro opcional ?q (búsqueda por nombre, NIF o DIR3).
        Devuelve {results: [{id, nombre, nif, direcciones_consultado}, ...]}
        Pensado para el selector de organismos en formulario de expedientes (#396).

    GET /api/entidades/<titular_id>/autorizados
        Autorizados vigentes de un titular (incluye al propio titular).
        Devuelve {data: [{id, text}, ...]}

    GET /api/entidades/<titular_id>/candidatos-autorizacion
        Entidades activas que aún NO están autorizadas por el titular dado.
        Excluye al propio titular y a los ya autorizados con autorización activa.
        Devuelve {data: [{v, t}, ...]}  (formato SelectorBusqueda)

VERSIÓN: 1.3
FECHA: 2026-05-24
ISSUE: #137, #461
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from app import db
from app.models.entidad import Entidad
from app.models.autorizados_titular import AutorizadoTitular
from app.models.direccion_notificacion import DireccionNotificacion

api_entidades_bp = Blueprint('api_entidades', __name__, url_prefix='/api')


def _serializar_dir_consultado(d):
    """Serializa una DireccionNotificacion para el selector de organismos."""
    partes = d.direccion_formateada()
    lineas = [p for p in [partes.get('linea1'), partes.get('linea2')] if p]
    return {
        'id':          d.id,
        'descripcion': d.descripcion,
        'dir3':        d.codigo_dir3,
        'sir':         d.codigo_sir,
        'email':       d.email,
        'direccion':   ' — '.join(lineas) if lineas else None,
    }


def _serializar_consultable(e, dirs):
    """Serializa una Entidad con sus DireccionNotificacion CONSULTADO activas."""
    return {
        'id':                    e.id,
        'nombre':                e.nombre_completo,
        'nif':                   e.nif,
        'direcciones_consultado': [_serializar_dir_consultado(d) for d in dirs],
    }


def _dirs_consultado(entidad_id):
    """Devuelve las DireccionNotificacion activas con bit CONSULTADO (tipo_rol & 2)."""
    return (
        DireccionNotificacion.query
        .filter(
            DireccionNotificacion.entidad_id == entidad_id,
            DireccionNotificacion.activo == True,
            DireccionNotificacion.tipo_rol.op('&')(2) > 0,
        )
        .order_by(DireccionNotificacion.fecha_inicio.desc())
        .all()
    )


@api_entidades_bp.route('/entidades/consultables', methods=['GET'])
@login_required
def listar_consultables():
    """
    GET /api/entidades/consultables

    Entidades activas con rol_consultado=True y sus direcciones de notificación
    CONSULTADO activas. Diseñado para el selector de organismos en expedientes.

    Query Parameters:
        q (str, opcional, mín 2 chars): Búsqueda por nombre, NIF o código DIR3.
            Con q  → máx 10 resultados (typeahead).
            Sin q  → todas las consultables activas.

    Respuesta JSON:
        {
          "results": [
            {
              "id": 1,
              "nombre": "Ministerio de Industria",
              "nif": "S2801047B",
              "direcciones_consultado": [
                {
                  "id": 5,
                  "descripcion": "Sede Central",
                  "dir3": "EA0015285",
                  "sir": "E04926801",
                  "email": "notif@minind.gob.es",
                  "direccion": "Paseo de la Castellana, 160 — 28046 Madrid"
                }
              ]
            }
          ]
        }

    Returns:
        200 OK  con JSON.
        401 Unauthorized si no autenticado.
    """
    q = request.args.get('q', '').strip()

    if q and len(q) < 2:
        return jsonify({'results': []}), 200

    query = Entidad.query.filter(
        Entidad.rol_consultado == True,
        Entidad.activo == True,
    )

    if q:
        ids_con_dir3 = (
            db.session.query(DireccionNotificacion.entidad_id)
            .filter(
                DireccionNotificacion.activo == True,
                DireccionNotificacion.tipo_rol.op('&')(2) > 0,
                func.lower(DireccionNotificacion.codigo_dir3).contains(func.lower(q)),
            )
        )
        query = query.filter(
            or_(
                func.lower(Entidad.nombre_completo).contains(func.lower(q)),
                func.lower(Entidad.nif).contains(func.lower(q)),
                Entidad.id.in_(ids_con_dir3),
            )
        ).limit(10)

    entidades = query.order_by(Entidad.nombre_completo).all()

    results = [_serializar_consultable(e, _dirs_consultado(e.id)) for e in entidades]
    return jsonify({'results': results}), 200


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


@api_entidades_bp.route('/entidades/<int:titular_id>/autorizados', methods=['GET'])
@login_required
def listar_autorizados(titular_id):
    """
    GET /api/entidades/<titular_id>/autorizados

    Devuelve los autorizados vigentes de un titular, incluyendo al propio titular
    como primera opción (autoautorización implícita).

    Respuesta JSON:
        { "data": [{"id": 1, "text": "Nombre (NIF)"}, ...] }

    Returns:
        200 OK  con lista de autorizados (puede ser solo el titular si no hay más).
        404 Not Found si el titular no existe o no tiene rol_titular=True.
    """
    titular = Entidad.query.get(titular_id)
    if not titular or not titular.rol_titular:
        return jsonify({'error': 'Titular no encontrado'}), 404

    # Siempre incluir al propio titular como primera opción
    def _label(e):
        return f'{e.nombre_completo} ({e.nif})' if e.nif else e.nombre_completo

    data = [{'id': titular.id, 'text': _label(titular)}]

    # Añadir autorizados vigentes (distintos del titular)
    autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(titular_id, solo_activos=True)
    for aut in autorizaciones:
        if aut.autorizado:
            data.append({'id': aut.autorizado.id, 'text': _label(aut.autorizado)})

    return jsonify({'data': data}), 200


@api_entidades_bp.route('/entidades/<int:titular_id>/candidatos-autorizacion', methods=['GET'])
@login_required
def candidatos_autorizacion(titular_id):
    """
    GET /api/entidades/<titular_id>/candidatos-autorizacion

    Devuelve entidades activas que aún NO tienen autorización activa con el titular dado.
    Excluye al propio titular (autoautorización implícita, no necesita entrada en BD).

    Respuesta JSON:
        { "data": [{"v": "3", "t": "Nombre Entidad (NIF)"}, ...] }
        Formato {v, t} compatible con SelectorBusqueda.

    Returns:
        200 OK  con lista de candidatos.
        404 Not Found si el titular no existe o no tiene rol_titular.
    """
    titular = Entidad.query.get(titular_id)
    if not titular or not titular.rol_titular:
        return jsonify({'error': 'Titular no encontrado'}), 404

    # IDs de entidades ya autorizadas activamente
    ya_autorizados = {
        aut.autorizado_entidad_id
        for aut in AutorizadoTitular.query.filter_by(
            titular_entidad_id=titular_id, activo=True
        ).all()
    }
    # Excluir también al propio titular
    ya_autorizados.add(titular_id)

    candidatos = (
        Entidad.query
        .filter(Entidad.activo == True)
        .filter(Entidad.id.notin_(ya_autorizados))
        .order_by(Entidad.nombre_completo)
        .all()
    )

    def _label(e):
        return f'{e.nombre_completo} ({e.nif})' if e.nif else e.nombre_completo

    data = [{'v': str(e.id), 't': _label(e)} for e in candidatos]
    return jsonify({'data': data}), 200
