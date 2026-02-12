"""API REST para expedientes.

ENDPOINTS:
    1. GET /api/expedientes - Listado paginado con cursor (scroll infinito)
    2. GET /api/expedientes/<id>/jerarquia - Estructura completa para Vista V3 Tramitación

VERSIÓN: 2.0
FECHA: 2026-02-12
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from app import db
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.tipos_expedientes import TipoExpediente
from app.models import (
    Solicitud, Fase, TipoSolicitud, TipoFase,
    Proyecto, TipoIA, Usuario, SolicitudTipo
)

# Blueprint para API
api_bp = Blueprint('api', __name__, url_prefix='/api')


# =============================================================================
# ENDPOINT 1: Listado paginado (scroll infinito)
# =============================================================================

@api_bp.route('/expedientes', methods=['GET'])
@login_required
def listar_expedientes():
    """
    Endpoint GET /api/expedientes - Listado paginado con cursor.

    PROPÓSITO:
        Proveer endpoint JSON para scroll infinito en frontend.
        Usa paginación por cursor (ID) en lugar de offset para mejor rendimiento
        en datasets grandes.

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
        - search: Búsqueda parcial en numero_at o nombre_completo del titular (ILIKE)
        - estado: Filtro por estado del expediente (futuro: tabla estados)

    RESPUESTA JSON:
        {
            "data": [expediente1, expediente2, ...],
            "next_cursor": 156,  # ID del último expediente devuelto
            "has_more": true,    # ¿Existen más registros?
            "total": 523         # Total de expedientes (con filtros aplicados)
        }

    Query Parameters:
        cursor (int, opcional): ID del último expediente recibido. Default: 0 (primera página)
        limit (int, opcional): Registros por página. Min 1, max 100. Default: 50
        search (str, opcional): Búsqueda parcial. Mínimo 2 caracteres.
        estado (str, opcional): Filtro por estado (mock por ahora).

    Returns:
        JSON con data, next_cursor, has_more, total (opcional)
        HTTP Status: 200 OK, 400 Bad Request, 401 Unauthorized
    """

    # ==========================================================================
    # PASO 1: Parsear y validar parámetros
    # ==========================================================================

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

        estado_filter = request.args.get('estado', '').strip()

    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    # ==========================================================================
    # PASO 2: Construir query base con eager loading
    # ==========================================================================

    query = db.session.query(Expediente).options(
        joinedload(Expediente.titular),
        joinedload(Expediente.tipo_expediente),
        joinedload(Expediente.responsable)
    )

    # ==========================================================================
    # PASO 3: Aplicar cursor (paginación)
    # ==========================================================================

    if cursor > 0:
        query = query.filter(Expediente.id > cursor)

    # ==========================================================================
    # PASO 4: Aplicar filtros opcionales
    # ==========================================================================

    search_numero = None

    if search_query:
        try:
            search_numero = int(search_query)
        except ValueError:
            pass

        filtros_busqueda = []

        if search_numero is not None:
            filtros_busqueda.append(Expediente.numero_at == search_numero)

        filtros_busqueda.append(
            Expediente.titular.has(
                func.lower(Entidad.nombre_completo).contains(func.lower(search_query))
            )
        )

        query = query.filter(or_(*filtros_busqueda))

    if estado_filter:
        estados_validos = ['borrador', 'tramitacion', 'finalizado', 'archivado']
        if estado_filter.lower() not in estados_validos:
            return jsonify({'error': f'Estado inválido. Válidos: {", ".join(estados_validos)}'}), 400

    # ==========================================================================
    # PASO 5: Ejecutar query con limit + 1
    # ==========================================================================

    query = query.order_by(Expediente.id.asc())
    expedientes = query.limit(limit + 1).all()

    has_more = len(expedientes) > limit
    if has_more:
        expedientes = expedientes[:limit]

    next_cursor = expedientes[-1].id if expedientes else cursor

    # ==========================================================================
    # PASO 6: Calcular total (solo si hay filtros)
    # ==========================================================================

    total = None
    if search_query or estado_filter:
        count_query = db.session.query(func.count(Expediente.id))
        
        if cursor > 0:
            count_query = count_query.filter(Expediente.id > cursor)
        
        if search_query:
            filtros_busqueda = []
            if search_numero is not None:
                filtros_busqueda.append(Expediente.numero_at == search_numero)
            
            filtros_busqueda.append(
                db.session.query(Expediente).join(Entidad, Expediente.titular_id == Entidad.id).filter(
                    func.lower(Entidad.nombre_completo).contains(func.lower(search_query))
                ).exists()
            )
            count_query = count_query.filter(or_(*filtros_busqueda))
        
        total = count_query.scalar()

    # ==========================================================================
    # PASO 7: Serializar a JSON
    # ==========================================================================

    data = []
    for exp in expedientes:
        if exp.responsable:
            nombre_responsable = f"{exp.responsable.apellido1 or ''} {exp.responsable.apellido2 or ''}, {exp.responsable.nombre or ''}".strip()
            nombre_responsable = ' '.join(nombre_responsable.split())
            if nombre_responsable.startswith(','):
                nombre_responsable = nombre_responsable[1:].strip()
        else:
            nombre_responsable = 'Sin asignar'
        
        expediente_dict = {
            'id': exp.id,
            'numero_at': exp.numero_at,
            'titular': exp.titular.nombre_completo if exp.titular else 'Sin titular',
            'tipo_expediente': exp.tipo_expediente.tipo if exp.tipo_expediente else 'Sin tipo',
            'responsable': nombre_responsable,
            'heredado': exp.heredado if exp.heredado is not None else False
        }
        data.append(expediente_dict)

    # ==========================================================================
    # PASO 8: Respuesta JSON
    # ==========================================================================

    response = {
        'data': data,
        'next_cursor': next_cursor,
        'has_more': has_more
    }

    if total is not None:
        response['total'] = total

    return jsonify(response), 200


# =============================================================================
# ENDPOINT 2: Jerarquía completa para Vista V3 Tramitación
# =============================================================================

@api_bp.route('/expedientes/<int:expediente_id>/jerarquia', methods=['GET'])
@login_required
def get_jerarquia_expediente(expediente_id):
    """
    Endpoint GET /api/expedientes/<id>/jerarquia - Estructura jerárquica para Vista V3.

    PROPÓSITO:
        Devolver estructura completa de un expediente para renderizar acordeones de Vista V3:
        - Panel contexto fijo: Expediente + Proyecto
        - Acordeón principal: Solicitudes + Fases

    ESTRUCTURA JSON:
        {
            "expediente": {
                "id": 104,
                "numero_at": 1,
                "codigo": "AT-1",
                "titular": {"id": 6, "nombre": "...", "nif": "..."},
                "responsable": {"id": 2, "siglas": "CLG", "nombre_completo": "..."},
                "tipo_expediente_id": null,
                "heredado": false
            },
            "proyecto": {
                "id": 105,
                "titulo": "...",
                "descripcion": "...",
                "fecha": "2026-02-11",
                "finalidad": "...",
                "emplazamiento": "...",
                "tipo_ia": {"id": 1, "siglas": "EIA", "descripcion": "..."}
            },
            "solicitudes": [
                {
                    "id": 1,
                    "codigo": "SOL-1",
                    "tipos": "AAP + AAC",
                    "fecha_solicitud": "2025-06-15",
                    "fecha_fin": "2025-09-20",
                    "estado": "RESUELTA",
                    "num_fases": 6,
                    "fases": [
                        {
                            "id": 1,
                            "codigo": "REGISTRO_SOLICITUD",
                            "nombre": "Registro de Solicitud",
                            "fecha_inicio": "2025-06-15",
                            "fecha_fin": "2025-06-15",
                            "estado": "completada",
                            "observaciones": "..."
                        }
                    ]
                }
            ]
        }

    Path Parameters:
        expediente_id (int): ID del expediente

    Returns:
        JSON con expediente, proyecto, solicitudes
        HTTP Status: 200 OK, 404 Not Found, 401 Unauthorized
    """
    
    # Verificar que el expediente existe
    expediente = Expediente.query.get_or_404(expediente_id)
    
    # =====================================================
    # EXPEDIENTE - Datos básicos
    # =====================================================
    titular = None
    if expediente.titular_id:
        entidad = Entidad.query.get(expediente.titular_id)
        if entidad:
            titular = {
                'id': entidad.id,
                'nombre': entidad.nombre_completo,
                'nif': entidad.nif
            }
    
    responsable = None
    if expediente.responsable_id:
        usuario = Usuario.query.get(expediente.responsable_id)
        if usuario:
            responsable = {
                'id': usuario.id,
                'siglas': usuario.siglas,
                'nombre_completo': f"{usuario.nombre} {usuario.apellido1 or ''}".strip()
            }
    
    expediente_data = {
        'id': expediente.id,
        'numero_at': expediente.numero_at,
        'codigo': f'AT-{expediente.numero_at}',
        'titular': titular,
        'responsable': responsable,
        'tipo_expediente_id': expediente.tipo_expediente_id,
        'heredado': expediente.heredado
    }
    
    # =====================================================
    # PROYECTO - Datos asociados al expediente (relación 1:1)
    # =====================================================
    proyecto_data = None
    if expediente.proyecto_id:
        proyecto = Proyecto.query.get(expediente.proyecto_id)
        if proyecto:
            tipo_ia = None
            if proyecto.ia_id:
                ia = TipoIA.query.get(proyecto.ia_id)
                if ia:
                    tipo_ia = {
                        'id': ia.id,
                        'siglas': ia.siglas,
                        'descripcion': ia.descripcion
                    }
            
            proyecto_data = {
                'id': proyecto.id,
                'titulo': proyecto.titulo,
                'descripcion': proyecto.descripcion,
                'fecha': proyecto.fecha.isoformat() if proyecto.fecha else None,
                'finalidad': proyecto.finalidad,
                'emplazamiento': proyecto.emplazamiento,
                'tipo_ia': tipo_ia
            }
    
    # =====================================================
    # SOLICITUDES + FASES - Jerarquía para acordeón
    # =====================================================
    solicitudes = Solicitud.query.filter_by(
        expediente_id=expediente_id
    ).order_by(Solicitud.fecha_solicitud).all()
    
    solicitudes_data = []
    for solicitud in solicitudes:
        # Obtener tipos de solicitud (tabla many-to-many)
        tipos_solicitud = (
            TipoSolicitud.query
            .join(SolicitudTipo, TipoSolicitud.id == SolicitudTipo.tiposolicitudid)
            .filter(SolicitudTipo.solicitudid == solicitud.id)
            .all()
        )
        
        tipos_str = ' + '.join([ts.siglas for ts in tipos_solicitud]) if tipos_solicitud else 'Sin tipo'
        
        # Obtener fases de la solicitud
        fases = Fase.query.filter_by(
            solicitud_id=solicitud.id
        ).order_by(Fase.fecha_inicio).all()
        
        fases_data = []
        for fase in fases:
            tipo_fase = TipoFase.query.get(fase.tipo_fase_id)
            
            fase_data = {
                'id': fase.id,
                'codigo': tipo_fase.codigo if tipo_fase else 'SIN_CODIGO',
                'nombre': tipo_fase.nombre if tipo_fase else 'Sin nombre',
                'fecha_inicio': fase.fecha_inicio.isoformat() if fase.fecha_inicio else None,
                'fecha_fin': fase.fecha_fin.isoformat() if fase.fecha_fin else None,
                'estado': 'completada' if fase.fecha_fin else 'en-curso',
                'observaciones': fase.observaciones
            }
            fases_data.append(fase_data)
        
        # Construir objeto solicitud
        solicitud_data = {
            'id': solicitud.id,
            'codigo': f'SOL-{solicitud.id}',
            'tipos': tipos_str,
            'fecha_solicitud': solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else None,
            'fecha_fin': solicitud.fecha_fin.isoformat() if solicitud.fecha_fin else None,
            'estado': solicitud.estado,
            'num_fases': len(fases_data),
            'fases': fases_data
        }
        solicitudes_data.append(solicitud_data)
    
    # =====================================================
    # RESPUESTA FINAL
    # =====================================================
    response = {
        'expediente': expediente_data,
        'proyecto': proyecto_data,
        'solicitudes': solicitudes_data
    }
    
    return jsonify(response), 200
