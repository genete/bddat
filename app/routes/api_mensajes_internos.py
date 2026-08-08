"""API REST de la bandeja de peticiones al Supervisor (#28, ADR-040).

ENDPOINTS:
    GET /api/mensajes-internos
        Listado scroll infinito: cursor + limit + search + estado + tipo.
        Devuelve {data, next_cursor, has_more, total?}
    GET /api/mensajes-internos/badge
        Número del sobre del topbar (bimodal según rol activo).

FILTRADO POR REMITENTE (ADR-040 §7):
    Quien no tiene `gestionar_mensajes_internos` solo ve las suyas, y ese filtro
    se aplica AQUÍ, a partir del permiso del rol activo. Nunca por un parámetro
    que envíe el front — no hay forma de pedir "las de otro".

ORDEN:
    Cursor por id ascendente, como el resto de listados del proyecto. Para una
    bandeja eso significa lo más antiguo primero, que es justo el orden en que
    conviene atender peticiones (y el que sirve idx_mi_pendientes).

VERSIÓN: 1.0
FECHA: 2026-08-08
ISSUE: #28 (ADR-023 — mismo patrón que #593 / api_catalogo_requerimientos)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.decorators import require_permiso
from app.models.mensajes_internos import MensajeInterno
from app.services import mensajes_internos as servicio
from app.utils.permisos import tiene_permiso

api_mensajes_internos_bp = Blueprint(
    'api_mensajes_internos', __name__, url_prefix='/api'
)


@api_mensajes_internos_bp.route('/mensajes-internos', methods=['GET'])
@login_required
@require_permiso('acceder_mensajes_internos')
def listar_mensajes():
    """
    GET /api/mensajes-internos  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)   : ID del último registro recibido.
        limit  (int, default 50)  : Registros por página. Máx: 100.
        search (str, mín 2 chars) : Búsqueda parcial en el payload.
        estado (str)              : pendiente | resuelto | acusado.
        tipo   (str)              : Código de tipo del registro del servicio.

    Returns:
        200 OK con JSON {data, next_cursor, has_more, total?}.
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

        estado = (request.args.get('estado') or '').strip().lower() or None
        tipo = (request.args.get('tipo') or '').strip() or None

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    puede_gestionar = tiene_permiso('gestionar_mensajes_internos')

    def aplicar_filtros(q):
        # Filtro de visibilidad — por permiso, no por parámetro (ADR-040 §7)
        if not puede_gestionar:
            q = q.filter(MensajeInterno.remitente_usuario_id == current_user.id)
        if cursor > 0:
            q = q.filter(MensajeInterno.id > cursor)
        if search_query:
            # El payload es JSONB y su forma varía por tipo: se busca sobre su
            # texto plano, que es lo único común a todos los tipos.
            q = q.filter(
                func.lower(func.cast(MensajeInterno.datos, db.Text))
                .contains(search_query.lower())
            )
        if estado == 'pendiente':
            q = q.filter(MensajeInterno.hecho.is_(False))
        elif estado == 'resuelto':
            q = q.filter(MensajeInterno.hecho.is_(True),
                         MensajeInterno.acusado_at.is_(None))
        elif estado == 'acusado':
            q = q.filter(MensajeInterno.acusado_at.isnot(None))
        if tipo is not None:
            q = q.filter(MensajeInterno.tipo == tipo)
        return q

    query = aplicar_filtros(MensajeInterno.query).order_by(MensajeInterno.id.asc())
    mensajes = query.limit(limit + 1).all()

    has_more = len(mensajes) > limit
    if has_more:
        mensajes = mensajes[:limit]

    next_cursor = mensajes[-1].id if mensajes else cursor

    total = None
    if search_query or estado or tipo is not None:
        count_query = aplicar_filtros(db.session.query(func.count(MensajeInterno.id)))
        total = count_query.scalar()

    data = []
    for m in mensajes:
        data.append({
            'id':             m.id,
            'tipo':           m.tipo,
            'tipo_label':     servicio.etiqueta_tipo(m.tipo),
            'resumen':        servicio.resumen(m),
            'remitente':      str(m.remitente) if m.remitente else '—',
            'es_propio':      m.remitente_usuario_id == current_user.id,
            'fecha':          m.created_at.strftime('%d/%m/%Y') if m.created_at else '',
            'estado':         m.estado,
            'estado_label':   servicio.ETIQUETAS_ESTADO.get(m.estado, m.estado),
            'resultado':      m.resultado,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200


@api_mensajes_internos_bp.route('/mensajes-internos/badge', methods=['GET'])
@login_required
@require_permiso('acceder_mensajes_internos')
def badge():
    """
    GET /api/mensajes-internos/badge  —  Número del sobre del topbar.

    Un solo entero, bimodal según el permiso del ROL ACTIVO (ADR-040 §7):
    quien gestiona cuenta las pendientes de todos más sus propias resueltas sin
    acusar; el resto, solo estas últimas.
    """
    total = servicio.contar_badge(
        current_user.id,
        tiene_permiso('gestionar_mensajes_internos'),
    )
    return jsonify({'total': total}), 200
