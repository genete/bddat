"""API REST para proyectos.

ENDPOINTS:
    GET /api/proyectos
        Scroll infinito: parámetros cursor + limit + search + tipo_ia

VERSIÓN: 1.0
FECHA: 2026-02-21
ISSUE: #123
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from app import db
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.usuarios import Usuario
from app.models.tipos_ia import TipoIA

api_proyectos_bp = Blueprint('api_proyectos', __name__, url_prefix='/api')


@api_proyectos_bp.route('/proyectos', methods=['GET'])
@login_required
def listar_proyectos():
    """
    GET /api/proyectos — Listado paginado con cursor.

    Query Parameters:
        cursor  (int, default 0)   : ID del último proyecto recibido.
        limit   (int, default 50)  : Registros por página. Máx: 100.
        search  (str, mín 2 chars) : Búsqueda en título o número AT.
        tipo_ia (int)              : Filtro por instrumento ambiental (ID).
        estado  (int)              : Alias de tipo_ia (usado por ScrollInfinito genérico).

    Permisos:
        TRAMITADOR puro: solo ve proyectos de sus expedientes asignados.
        ADMIN/SUPERVISOR: ven todos.

    Respuesta JSON:
        {
            "data": [
                {
                    "id": 1,
                    "titulo": "Proyecto de línea AT",
                    "expediente_codigo": "AT-1",
                    "expediente_id": 104,
                    "tipo_ia": "AAU",
                    "responsable": "Juan García",
                    "fecha": "01/06/2025"
                }, ...
            ],
            "next_cursor": 45,
            "has_more": true,
            "total": 89   <- solo cuando hay filtros activos
        }
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

        # Acepta tanto 'tipo_ia' (semántico) como 'estado' (alias desde ScrollInfinito genérico)
        tipo_ia_id = (
            request.args.get('tipo_ia', type=int)
            or request.args.get('estado', type=int)
        )

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # --- Query base con joins ---
    query = (
        db.session.query(Proyecto)
        .join(Expediente)
        .outerjoin(Usuario, Expediente.responsable_id == Usuario.id)
        .outerjoin(TipoIA, Proyecto.ia_id == TipoIA.id)
    )

    # Filtro de permisos: TRAMITADOR solo ve sus expedientes
    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        query = query.filter(Expediente.responsable_id == current_user.id)

    # Cursor
    if cursor > 0:
        query = query.filter(Proyecto.id > cursor)

    # Búsqueda
    if search_query:
        patron = f'%{search_query}%'
        query = query.filter(
            or_(
                Proyecto.titulo.ilike(patron),
                db.cast(Expediente.numero_at, db.String).ilike(patron)
            )
        )

    # Filtro por instrumento ambiental
    if tipo_ia_id:
        query = query.filter(Proyecto.ia_id == tipo_ia_id)

    # --- Ejecutar con limit + 1 para detectar has_more ---
    query = query.order_by(Proyecto.id.asc())
    proyectos = query.limit(limit + 1).all()

    has_more = len(proyectos) > limit
    if has_more:
        proyectos = proyectos[:limit]

    next_cursor = proyectos[-1].id if proyectos else cursor

    # --- Total (solo cuando hay filtros activos) ---
    total = None
    if search_query or tipo_ia_id:
        count_query = (
            db.session.query(func.count(Proyecto.id))
            .join(Expediente)
            .outerjoin(TipoIA, Proyecto.ia_id == TipoIA.id)
        )
        if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
            count_query = count_query.filter(Expediente.responsable_id == current_user.id)
        if cursor > 0:
            count_query = count_query.filter(Proyecto.id > cursor)
        if search_query:
            patron = f'%{search_query}%'
            count_query = count_query.filter(
                or_(
                    Proyecto.titulo.ilike(patron),
                    db.cast(Expediente.numero_at, db.String).ilike(patron)
                )
            )
        if tipo_ia_id:
            count_query = count_query.filter(Proyecto.ia_id == tipo_ia_id)
        total = count_query.scalar()

    # --- Serializar ---
    data = []
    for p in proyectos:
        exp = p.expediente
        data.append({
            'id':                p.id,
            'titulo':            p.titulo,
            'expediente_codigo': f'AT-{exp.numero_at}' if exp else '-',
            'expediente_id':     exp.id if exp else None,
            'tipo_ia':           p.ia.siglas if p.ia else '-',
            'responsable':       exp.responsable.nombre if exp and exp.responsable else '-',
            'fecha':             p.fecha.strftime('%d/%m/%Y') if p.fecha else '-',
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
