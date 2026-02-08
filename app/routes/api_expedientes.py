"""API REST para listado de expedientes con paginación por cursor.

PROPÓSITO:
    Proveer endpoint JSON para scroll infinito en frontend.
    Usa paginación por cursor (ID) en lugar de offset para mejor rendimiento
    en datasets grandes.

ENDPOINTS:
    GET /api/expedientes - Listado paginado con filtros

PAGINACIÓN POR CURSOR:
    Ventajas vs OFFSET:
    - Rendimiento constante O(1) incluso con millones de registros
    - No sufre "page drift" si se insertan/borran registros durante navegación
    - Utiliza índice PRIMARY KEY (id) para búsqueda eficiente

    Funcionamiento:
    - cursor: ID del último expediente recibido en llamada anterior
    - limit: Número de registros a devolver (máx 100, default 50)
    - Query: WHERE id > cursor ORDER BY id ASC LIMIT limit
    - Si cursor=0 o ausente: primera página (sin filtro WHERE)

FILTROS:
    - search: Búsqueda parcial en numero_at o nombre titular (ILIKE)
    - estado: Filtro por estado del expediente (futuro: tabla estados)

RESPUESTA JSON:
    {
        "data": [expediente1, expediente2, ...],
        "next_cursor": 156,  # ID del último expediente devuelto
        "has_more": true,    # ¿Existen más registros?
        "total": 523         # Total de expedientes (con filtros aplicados)
    }

NOTAS:
    - Usa eager loading (joinedload) para evitar N+1 queries
    - Respeta convención snake_case en JSON
    - Total count se calcula solo si hay filtros (para mantener cache)

VERSIÓN: 1.0
FECHA: 2026-02-08
"""

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from app import db
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.tipos_expedientes import TipoExpediente

# Blueprint para API
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/expedientes', methods=['GET'])
def listar_expedientes():
    """
    Endpoint GET /api/expedientes - Listado paginado con cursor.

    Query Parameters:
        cursor (int, opcional): ID del último expediente recibido.
                               Default: 0 (primera página)
        limit (int, opcional): Registros por página. Min 1, max 100.
                              Default: 50
        search (str, opcional): Búsqueda parcial en numero_at o titular.
                               Mínimo 2 caracteres.
        estado (str, opcional): Filtro por estado (futuro: integrar con tabla estados).
                               Por ahora: mock para testing frontend.

    Returns:
        JSON:
            {
                "data": [
                    {
                        "id": 1,
                        "numero_at": 123,
                        "titular": "Empresa S.L.",
                        "tipo_expediente": "Línea Aérea",
                        "responsable": "Juan Pérez",
                        "heredado": false
                    },
                    ...
                ],
                "next_cursor": 156,
                "has_more": true,
                "total": 523
            }

        HTTP Status:
            200: OK
            400: Bad Request (parámetros inválidos)
            500: Error interno del servidor

    Ejemplo de uso desde JavaScript:
        // Primera página
        fetch('/api/expedientes?limit=50')

        // Segunda página (usar next_cursor de respuesta anterior)
        fetch('/api/expedientes?cursor=50&limit=50')

        // Con filtros
        fetch('/api/expedientes?search=empresa&estado=tramitacion&limit=30')
    """

    # ==========================================================================
    # PASO 1: Parsear y validar parámetros
    # ==========================================================================

    try:
        # Cursor: ID del último expediente (default 0 = primera página)
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'Cursor debe ser >= 0'}), 400

        # Limit: Registros por página (default 50, max 100)
        limit = int(request.args.get('limit', 50))
        if limit < 1:
            return jsonify({'error': 'Limit debe ser >= 1'}), 400
        if limit > 100:
            limit = 100  # Cap máximo por seguridad

        # Search: Búsqueda parcial (mínimo 2 caracteres)
        search_query = request.args.get('search', '').strip()
        if search_query and len(search_query) < 2:
            return jsonify({'error': 'Search debe tener al menos 2 caracteres'}), 400

        # Estado: Filtro por estado (futuro: tabla estados)
        # Por ahora mock para testing frontend
        estado_filter = request.args.get('estado', '').strip()

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # ==========================================================================
    # PASO 2: Construir query base con eager loading
    # ==========================================================================

    query = db.session.query(Expediente).options(
        joinedload(Expediente.titular),           # Eager load titular
        joinedload(Expediente.tipo_expediente),   # Eager load tipo
        joinedload(Expediente.responsable)        # Eager load responsable
    )

    # ==========================================================================
    # PASO 3: Aplicar cursor (paginación)
    # ==========================================================================

    if cursor > 0:
        query = query.filter(Expediente.id > cursor)

    # ==========================================================================
    # PASO 4: Aplicar filtros opcionales
    # ==========================================================================

    # Filtro de búsqueda: numero_at o nombre titular
    if search_query:
        # Convertir búsqueda a número si es posible (para numero_at)
        search_numero = None
        try:
            search_numero = int(search_query)
        except ValueError:
            pass

        # Búsqueda en numero_at (exacto) o titular (parcial, case-insensitive)
        filtros_busqueda = []

        if search_numero is not None:
            filtros_busqueda.append(Expediente.numero_at == search_numero)

        # Búsqueda en nombre del titular (JOIN con Entidad)
        # Nota: Entidad.nombre_completo es property, no columna
        # Buscar en razon_social (empresas) o apellidos/nombre (personas)
        filtros_busqueda.append(
            db.session.query(Entidad).filter(
                Entidad.id == Expediente.titular_id,
                or_(
                    func.lower(Entidad.razon_social).contains(func.lower(search_query)),
                    func.lower(Entidad.apellidos).contains(func.lower(search_query)),
                    func.lower(Entidad.nombre).contains(func.lower(search_query))
                )
            ).exists()
        )

        query = query.filter(or_(*filtros_busqueda))

    # Filtro de estado (mock por ahora)
    # TODO: Integrar con tabla tramitacion.fases cuando esté implementada
    if estado_filter:
        # Por ahora no aplicamos filtro real, solo validamos valores conocidos
        estados_validos = ['borrador', 'tramitacion', 'finalizado', 'archivado']
        if estado_filter.lower() not in estados_validos:
            return jsonify({'error': f'Estado inválido. Válidos: {", ".join(estados_validos)}'}), 400

    # ==========================================================================
    # PASO 5: Ejecutar query con limit + 1 (para detectar has_more)
    # ==========================================================================

    # Ordenar por ID ascendente (necesario para cursor)
    query = query.order_by(Expediente.id.asc())

    # Obtener limit + 1 registros (el extra nos dice si hay más)
    expedientes = query.limit(limit + 1).all()

    # Detectar si hay más páginas
    has_more = len(expedientes) > limit

    # Ajustar a límite solicitado
    if has_more:
        expedientes = expedientes[:limit]

    # ==========================================================================
    # PASO 6: Calcular next_cursor
    # ==========================================================================

    next_cursor = expedientes[-1].id if expedientes else cursor

    # ==========================================================================
    # PASO 7: Calcular total (solo si hay filtros, para optimizar)
    # ==========================================================================

    # Total count es costoso en tablas grandes, solo calcularlo si hay filtros
    # Si no hay filtros, frontend puede asumir "muchos" sin mostrar número exacto
    total = None
    if search_query or estado_filter:
        # Recrear query sin limit para count
        count_query = db.session.query(func.count(Expediente.id))
        if cursor > 0:
            count_query = count_query.filter(Expediente.id > cursor)
        if search_query:
            # Replicar filtro de búsqueda
            filtros_busqueda = []
            if search_numero is not None:
                filtros_busqueda.append(Expediente.numero_at == search_numero)
            filtros_busqueda.append(
                db.session.query(Entidad).filter(
                    Entidad.id == Expediente.titular_id,
                    or_(
                        func.lower(Entidad.razon_social).contains(func.lower(search_query)),
                        func.lower(Entidad.apellidos).contains(func.lower(search_query)),
                        func.lower(Entidad.nombre).contains(func.lower(search_query))
                    )
                ).exists()
            )
            count_query = count_query.filter(or_(*filtros_busqueda))
        total = count_query.scalar()

    # ==========================================================================
    # PASO 8: Serializar a JSON
    # ==========================================================================

    data = []
    for exp in expedientes:
        # Serializar expediente
        expediente_dict = {
            'id': exp.id,
            'numero_at': exp.numero_at,
            'titular': exp.titular.nombre_completo if exp.titular else 'Sin titular',
            'tipo_expediente': exp.tipo_expediente.nombre if exp.tipo_expediente else 'Sin tipo',
            'responsable': f"{exp.responsable.apellidos}, {exp.responsable.nombre}" if exp.responsable else 'Sin asignar',
            'heredado': exp.heredado if exp.heredado is not None else False,
            # Futuro: añadir campos de estado, fechas, etc.
            # 'estado': exp.fase_actual.tipo_fase.nombre if exp.fase_actual else 'Sin estado',
            # 'fecha_presentacion': exp.fecha_presentacion.isoformat() if exp.fecha_presentacion else None,
            # 'vencimiento': calcular_vencimiento(exp)
        }
        data.append(expediente_dict)

    # ==========================================================================
    # PASO 9: Respuesta JSON
    # ==========================================================================

    response = {
        'data': data,
        'next_cursor': next_cursor,
        'has_more': has_more
    }

    # Añadir total solo si se calculó
    if total is not None:
        response['total'] = total

    return jsonify(response), 200


# =============================================================================
# HELPERS (futuro: mover a utils si crecen)
# =============================================================================

def calcular_vencimiento(expediente):
    """
    Calcula fecha de vencimiento del expediente según normativa.

    TODO: Implementar lógica real según:
        - Tipo de expediente
        - Fase actual
        - Normativa aplicable (Ley 39/2015, etc.)
        - Suspensiones/interrupciones del plazo

    Args:
        expediente (Expediente): Instancia del expediente

    Returns:
        str: Fecha en formato ISO (YYYY-MM-DD) o None
    """
    # Por ahora retornar None (mock)
    return None
