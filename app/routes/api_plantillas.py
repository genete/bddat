"""API REST para plantillas de escritos.

ENDPOINTS:
    GET /api/admin-plantillas
        Listado scroll infinito: parámetros cursor + limit + search + estado
        + tipo_documento + tipo_fase.
        Devuelve {data, next_cursor, has_more, total?}

VERSIÓN: 1.0
FECHA: 2026-06-15
ISSUE: #545 (ADR-023 — migración del listado de plantillas al patrón inspector)
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.plantillas import Plantilla

api_plantillas_bp = Blueprint('api_plantillas', __name__, url_prefix='/api')


@api_plantillas_bp.route('/admin-plantillas', methods=['GET'])
@login_required
@require_permiso('acceder_plantillas')
def listar_plantillas():
    """
    GET /api/admin-plantillas  —  Listado paginado con cursor.

    Query Parameters:
        cursor (int, default 0)      : ID del último registro recibido.
        limit  (int, default 50)     : Registros por página. Máx: 100.
        search (str, mín 2 chars)    : Búsqueda parcial en nombre o código.
        estado (str: true/false/'')  : Filtro por activo. Default: todos.
                                       (alias 'activo').
        tipo_documento (int)         : Filtro por tipo_documento_id.
        tipo_fase (int)              : Filtro por tipo_fase_id.

    Nota: el cursor pagina por id ascendente (consistente con #544). El orden
    alfabético por nombre exigiría cursor compuesto (nombre, id); se deja como
    mejora futura dado el volumen pequeño de plantillas.

    Returns:
        200 OK  con JSON {data, next_cursor, has_more, total?}.
        400 Bad Request si parámetros inválidos.
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

        # Acepta 'estado' (alias desde ScrollInfinito) o 'activo' (semántico)
        activo_raw = (request.args.get('estado') or request.args.get('activo') or '').strip().lower()

        # Filtros por catálogo: id numérico o vacío
        tipo_documento_raw = request.args.get('tipo_documento', '').strip()
        tipo_fase_raw      = request.args.get('tipo_fase', '').strip()
        tipo_documento_id  = int(tipo_documento_raw) if tipo_documento_raw else None
        tipo_fase_id       = int(tipo_fase_raw)      if tipo_fase_raw      else None

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # --- Filtros reutilizables (query de datos y de total) ---
    def aplicar_filtros(q):
        if cursor > 0:
            q = q.filter(Plantilla.id > cursor)
        if search_query:
            patron = func.lower(search_query)
            q = q.filter(
                or_(
                    func.lower(Plantilla.nombre).contains(patron),
                    func.lower(Plantilla.codigo).contains(patron),
                )
            )
        if activo_raw == 'true':
            q = q.filter(Plantilla.activo == True)   # noqa: E712
        elif activo_raw == 'false':
            q = q.filter(Plantilla.activo == False)  # noqa: E712
        if tipo_documento_id is not None:
            q = q.filter(Plantilla.tipo_documento_id == tipo_documento_id)
        if tipo_fase_id is not None:
            q = q.filter(Plantilla.tipo_fase_id == tipo_fase_id)
        return q

    # --- Query de datos: joinedload evita N+1 al serializar las relaciones ---
    query = (
        aplicar_filtros(Plantilla.query)
        .options(
            joinedload(Plantilla.tipo_documento),
            joinedload(Plantilla.tipo_expediente),
            joinedload(Plantilla.tipo_solicitud),
            joinedload(Plantilla.tipo_fase),
            joinedload(Plantilla.tipo_tramite),
        )
        .order_by(Plantilla.id.asc())
    )
    plantillas = query.limit(limit + 1).all()

    has_more = len(plantillas) > limit
    if has_more:
        plantillas = plantillas[:limit]

    next_cursor = plantillas[-1].id if plantillas else cursor

    # --- Total (solo cuando hay filtros activos) ---
    total = None
    if search_query or activo_raw or tipo_documento_id is not None or tipo_fase_id is not None:
        count_query = aplicar_filtros(db.session.query(func.count(Plantilla.id)))
        total = count_query.scalar()

    # --- Serializar (valores crudos; el render del listado decide el formato) ---
    data = []
    for p in plantillas:
        data.append({
            'id':             p.id,
            'nombre':         p.nombre,
            'variante':       p.variante,
            'descripcion':    p.descripcion,
            'codigo':         p.codigo,
            'tipo_documento': p.tipo_documento.nombre  if p.tipo_documento  else None,
            'tipo_expediente': p.tipo_expediente.tipo  if p.tipo_expediente else None,
            'tipo_solicitud': p.tipo_solicitud.siglas  if p.tipo_solicitud  else None,
            'tipo_fase':      p.tipo_fase.nombre       if p.tipo_fase       else None,
            'tipo_tramite':   p.tipo_tramite.nombre    if p.tipo_tramite    else None,
            'activo':         p.activo,
        })

    response = {
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    }
    if total is not None:
        response['total'] = total

    return jsonify(response), 200
