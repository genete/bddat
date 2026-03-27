"""API REST para el listado de seguimiento de solicitudes.

ENDPOINT:
    GET /api/expedientes/seguimiento — Listado paginado de solicitudes con estado de pistas.

    Params:
        cursor           (int,    default 0)           — Paginación por cursor
        limit            (int,    default 50, max 100) — Solicitudes por página
        ver              (str,    default "mis")        — "mis" | "todos"
        estado           (str,    default "EN_TRAMITE") — Estado BD o "todos"
        tipo_titular     (str,    opcional)             — Filtra por tipo de titular
        tipo_expediente_id (int,  opcional)             — Filtra por tipo de expediente

    Respuesta JSON:
        {
            "data": [{
                "id": 1, "expediente_id": 5, "num_at": 1234, "at_count": 2,
                "tipo_solicitud": "AAP_AAC", "fecha_solicitud": "2025-01-15",
                "estado_solicitud": "EN_TRAMITE", "color_solicitud": "",
                "titular_nombre": "...", "tipo_titular": "PROMOTOR",
                "proyecto_descripcion": "...",
                "pista_SOL": {"codigo": "PENDIENTE_ESTUDIO", "color": "rojo", "count": 1},
                "pista_CONSULTAS": null, "pista_MA": null, "pista_IP": null,
                "pista_RES": {"codigo": "PENDIENTE_TRAMITAR", "color": "rojo", "count": 1}
            }, ...],
            "next_cursor": 5,
            "has_more": true,
            "total": null
        }

VERSIÓN: 1.0
FECHA: 2026-03-27
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from app import db
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.entidad import Entidad
from app.services.seguimiento import estado_solicitud, fin_total

api_seguimiento_bp = Blueprint('api_seguimiento', __name__, url_prefix='/api')

# Estados válidos para el filtro
_ESTADOS_VALIDOS = {'EN_TRAMITE', 'RESUELTA', 'DESISTIDA', 'ARCHIVADA', 'todos'}
# Tipos de titular válidos
_TIPOS_TITULAR_VALIDOS = {'GRAN_DISTRIBUIDORA', 'DISTRIBUIDOR_MENOR', 'PROMOTOR', 'ORGANISMO_PUBLICO', 'OTRO'}


@api_seguimiento_bp.route('/expedientes/seguimiento', methods=['GET'])
@login_required
def listar_seguimiento():
    """
    GET /api/expedientes/seguimiento — Listado paginado de solicitudes con estado de pistas.

    Cada fila representa una solicitud (no un expediente): un AT puede aparecer varias
    veces si tiene múltiples solicitudes activas simultáneas (at_count > 1).
    """
    # -------------------------------------------------------------------------
    # 1. Parsear y validar parámetros
    # -------------------------------------------------------------------------
    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'cursor debe ser >= 0'}), 400

        limit = int(request.args.get('limit', 50))
        limit = min(max(limit, 1), 100)

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    ver              = request.args.get('ver', 'mis').strip()
    estado           = request.args.get('estado', 'EN_TRAMITE').strip()
    tipo_titular     = request.args.get('tipo_titular', '').strip()
    tipo_expediente_id_raw = request.args.get('tipo_expediente_id', '').strip()

    if ver not in ('mis', 'todos'):
        return jsonify({'error': 'ver debe ser "mis" o "todos"'}), 400
    if estado not in _ESTADOS_VALIDOS:
        return jsonify({'error': f'estado inválido. Válidos: {", ".join(sorted(_ESTADOS_VALIDOS))}'}), 400
    if tipo_titular and tipo_titular not in _TIPOS_TITULAR_VALIDOS:
        return jsonify({'error': f'tipo_titular inválido'}), 400

    tipo_expediente_id = None
    if tipo_expediente_id_raw:
        try:
            tipo_expediente_id = int(tipo_expediente_id_raw)
        except ValueError:
            return jsonify({'error': 'tipo_expediente_id debe ser entero'}), 400

    # -------------------------------------------------------------------------
    # 2. Construir filtros base (reutilizados para la query principal y at_count)
    # -------------------------------------------------------------------------
    filtros_base = []

    if ver == 'mis':
        filtros_base.append(Expediente.responsable_id == current_user.id)
    if estado != 'todos':
        filtros_base.append(Solicitud.estado == estado)
    if tipo_titular:
        filtros_base.append(Entidad.tipo_titular == tipo_titular)
    if tipo_expediente_id:
        filtros_base.append(Expediente.tipo_expediente_id == tipo_expediente_id)

    # -------------------------------------------------------------------------
    # 3. Query principal con eager loading para evitar N+1 en serialización
    # -------------------------------------------------------------------------
    query = (
        db.session.query(Solicitud)
        .join(Expediente, Solicitud.expediente_id == Expediente.id)
        .join(Entidad, Expediente.titular_id == Entidad.id, isouter=True)
        .options(
            joinedload(Solicitud.expediente).joinedload(Expediente.titular),
            joinedload(Solicitud.expediente).joinedload(Expediente.proyecto),
            joinedload(Solicitud.tipo_solicitud),
        )
        .filter(*filtros_base)
    )

    if cursor > 0:
        query = query.filter(Solicitud.id > cursor)

    query = query.order_by(Solicitud.id.asc())
    solicitudes_raw = query.limit(limit + 1).all()

    has_more = len(solicitudes_raw) > limit
    solicitudes = solicitudes_raw[:limit]

    next_cursor = solicitudes[-1].id if solicitudes else cursor

    # -------------------------------------------------------------------------
    # 4. at_count: cuántas solicitudes tiene cada expediente bajo los filtros
    #    activos (sin cursor, para reflejar el total real por AT)
    # -------------------------------------------------------------------------
    exp_ids_pagina = list({s.expediente_id for s in solicitudes})
    at_counts: dict[int, int] = {}
    if exp_ids_pagina:
        rows = (
            db.session.query(
                Solicitud.expediente_id,
                func.count(Solicitud.id).label('cnt')
            )
            .join(Expediente, Solicitud.expediente_id == Expediente.id)
            .join(Entidad, Expediente.titular_id == Entidad.id, isouter=True)
            .filter(
                Solicitud.expediente_id.in_(exp_ids_pagina),
                *filtros_base  # mismos filtros, sin cursor
            )
            .group_by(Solicitud.expediente_id)
            .all()
        )
        at_counts = {row.expediente_id: row.cnt for row in rows}

    # -------------------------------------------------------------------------
    # 5. Calcular estado de pistas y serializar
    # -------------------------------------------------------------------------
    data = []
    for sol in solicitudes:
        estados = estado_solicitud(sol.id)
        es_fin = fin_total(estados)

        if sol.estado != 'EN_TRAMITE':
            color_solicitud = 'verde'
        elif es_fin:
            color_solicitud = 'naranja'
        else:
            color_solicitud = ''

        expediente = sol.expediente
        titular = expediente.titular if expediente else None
        proyecto = expediente.proyecto if expediente else None

        data.append({
            'id':                    sol.id,
            'expediente_id':         expediente.id if expediente else None,
            'num_at':                expediente.numero_at if expediente else None,
            'at_count':              at_counts.get(expediente.id, 1) if expediente else 1,
            'tipo_solicitud':        sol.tipo_solicitud.siglas if sol.tipo_solicitud else '—',
            'fecha_solicitud':       sol.fecha_solicitud.isoformat() if sol.fecha_solicitud else None,
            'estado_solicitud':      sol.estado,
            'color_solicitud':       color_solicitud,
            'titular_nombre':        titular.nombre_completo if titular else '—',
            'tipo_titular':          titular.tipo_titular if titular else None,
            'proyecto_descripcion':  proyecto.descripcion if proyecto else '—',
            'pista_SOL':             _ser_pista(estados.get('SOL')),
            'pista_CONSULTAS':       _ser_pista(estados.get('CONSULTAS')),
            'pista_MA':              _ser_pista(estados.get('MA')),
            'pista_IP':              _ser_pista(estados.get('IP')),
            'pista_RES':             _ser_pista(estados.get('RES')),
        })

    return jsonify({
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
        'total':       None,  # costoso de calcular; el cliente lo infiere de has_more
    })


def _ser_pista(ep) -> dict | None:
    """Serializa un EstadoPista a dict JSON; None si la pista es N/A."""
    if ep is None:
        return None
    return {'codigo': ep.codigo, 'color': ep.color, 'count': ep.count}
