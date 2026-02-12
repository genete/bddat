"""
API REST para expedientes - Vista V3 Tramitación
Endpoint que devuelve jerarquía completa: Expediente + Proyecto + Solicitudes + Fases
"""
from flask import Blueprint, jsonify
from app.models import (
    Expediente, Solicitud, Fase, Entidad, TipoSolicitud, TipoFase,
    Proyecto, TipoIA, Usuario
)
from app.models import SolicitudTipo

bp_api_expedientes = Blueprint('api_expedientes', __name__, url_prefix='/api/expedientes')


@bp_api_expedientes.route('/<int:expediente_id>/jerarquia', methods=['GET'])
def get_jerarquia_expediente(expediente_id):
    """
    Devuelve la estructura jerárquica completa de un expediente para Vista V3:
    - Datos del expediente (número AT, titular, responsable)
    - Datos del proyecto asociado (título, finalidad, emplazamiento)
    - Solicitudes con sus tipos
    - Fases de cada solicitud
    
    Retorna JSON optimizado para renderizar:
    - Panel contexto fijo (expediente + proyecto)
    - Acordeón principal (solicitudes > fases)
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
