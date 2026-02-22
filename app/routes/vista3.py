"""
Blueprint para Vista 3 - Tramitación con navegación jerárquica tipo stack.

Endpoint:
- POST /api/vista3/context - Renderiza HTML completo según navigation_stack
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.solicitudes_tipos import SolicitudTipo
from app.utils.permisos import verificar_acceso_expediente

bp = Blueprint('vista3', __name__, url_prefix='/api/vista3')


@bp.route('/context', methods=['POST'])
@login_required
def get_context():
    """
    Recibe navigation_stack y devuelve HTML completo.
    
    Entrada JSON:
    {
        "stack": [
            {"type": "expediente", "id": 1},
            {"type": "solicitud", "id": 123},
            {"type": "fase", "id": 456}
        ]
    }
    
    Salida JSON:
    {
        "html": "<div>...</div>",
        "breadcrumb": "Expediente 1 > Solicitud 123 > Fase 456"
    }
    """
    data = request.get_json()
    stack = data.get('stack', [])
    
    if not stack:
        return jsonify({'error': 'Stack vacío'}), 400
    
    # Primer nivel siempre es expediente
    expediente_ctx = stack[0]
    if expediente_ctx['type'] != 'expediente':
        return jsonify({'error': 'Primer nivel debe ser expediente'}), 400
    
    expediente = Expediente.query.get_or_404(expediente_ctx['id'])
    
    # Verificar acceso
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    # Renderizar cada nivel del stack
    html_sections = []
    breadcrumb_parts = []
    
    for idx, level in enumerate(stack):
        is_active = (idx == len(stack) - 1)
        level_index = idx
        
        if level['type'] == 'expediente':
            html_sections.append(
                render_template(
                    'vistas/vista3/_expediente_body.html',
                    expediente=expediente
                )
            )
            breadcrumb_parts.append(f"EXP-{expediente.numero_at}")
        
        elif level['type'] == 'solicitudes':
            solicitudes = _get_solicitudes_con_stats(expediente.id)
            html_sections.append(
                render_template(
                    'vistas/vista3/_solicitudes_accordion.html',
                    solicitudes=solicitudes,
                    is_active=is_active,
                    level_index=level_index
                )
            )
            breadcrumb_parts.append("Solicitudes")
        
        elif level['type'] == 'solicitud':
            solicitud = Solicitud.query.get_or_404(level['id'])
            
            # Obtener tipos de la solicitud
            tipos_solicitud = (
                TipoSolicitud.query
                .join(SolicitudTipo, TipoSolicitud.id == SolicitudTipo.tiposolicitudid)
                .filter(SolicitudTipo.solicitudid == solicitud.id)
                .all()
            )
            tipos_str = '+'.join([ts.siglas for ts in tipos_solicitud]) if tipos_solicitud else 'SIN TIPO'
            
            fases = _get_fases_con_stats(solicitud.id) if is_active else []
            html_sections.append(
                render_template(
                    'vistas/vista3/_solicitud_accordion.html',
                    solicitud=solicitud,
                    tipos_str=tipos_str,
                    fases=fases,
                    is_active=is_active,
                    level_index=level_index
                )
            )
            breadcrumb_parts.append(f"SOL-{solicitud.id}")
        
        elif level['type'] == 'fase':
            fase = Fase.query.get_or_404(level['id'])
            tramites = _get_tramites_con_stats(fase.id) if is_active else []
            html_sections.append(
                render_template(
                    'vistas/vista3/_fase_accordion.html',
                    fase=fase,
                    tramites=tramites,
                    is_active=is_active,
                    level_index=level_index
                )
            )
            breadcrumb_parts.append(f"FASE-{fase.tipo_fase.nombre if fase.tipo_fase else fase.id}")
        
        elif level['type'] == 'tramite':
            tramite = Tramite.query.get_or_404(level['id'])
            tareas = _get_tareas_con_stats(tramite.id) if is_active else []
            html_sections.append(
                render_template(
                    'vistas/vista3/_tramite_accordion.html',
                    tramite=tramite,
                    tareas=tareas,
                    is_active=is_active,
                    level_index=level_index
                )
            )
            breadcrumb_parts.append(f"TRAM-{tramite.tipo_tramite.nombre if tramite.tipo_tramite else tramite.id}")
        
        elif level['type'] == 'tarea':
            tarea = Tarea.query.get_or_404(level['id'])
            documentos = _get_documentos_tarea(tarea.id) if is_active else []
            html_sections.append(
                render_template(
                    'vistas/vista3/_tarea_accordion.html',
                    tarea=tarea,
                    documentos=documentos,
                    is_active=is_active,
                    level_index=level_index
                )
            )
            breadcrumb_parts.append(f"TAR-{tarea.tipo_tarea.nombre if tarea.tipo_tarea else tarea.id}")
    
    return jsonify({
        'html': ''.join(html_sections),
        'breadcrumb': ' > '.join(breadcrumb_parts),
        'breadcrumb_items': breadcrumb_parts
    })


# ============================================
# HELPERS - Queries con stats calculadas
# ============================================

def _get_solicitudes_con_stats(expediente_id):
    """Obtiene solicitudes con contadores de fases y trámites."""
    solicitudes = Solicitud.query.filter_by(expediente_id=expediente_id).all()
    
    result = []
    for sol in solicitudes:
        # Contar fases
        total_fases = Fase.query.filter_by(solicitud_id=sol.id).count()
        fases_completadas = Fase.query.filter_by(
            solicitud_id=sol.id
        ).filter(Fase.fecha_fin.isnot(None)).count()
        
        # Contar trámites a través de fases
        total_tramites = db.session.query(func.count(Tramite.id)).join(
            Fase, Tramite.fase_id == Fase.id
        ).filter(Fase.solicitud_id == sol.id).scalar() or 0
        
        tramites_completados = db.session.query(func.count(Tramite.id)).join(
            Fase, Tramite.fase_id == Fase.id
        ).filter(
            Fase.solicitud_id == sol.id,
            Tramite.fecha_fin.isnot(None)
        ).scalar() or 0
        
        # Obtener tipos de solicitud usando join con tabla intermedia
        tipos_solicitud = (
            TipoSolicitud.query
            .join(SolicitudTipo, TipoSolicitud.id == SolicitudTipo.tiposolicitudid)
            .filter(SolicitudTipo.solicitudid == sol.id)
            .all()
        )
        tipos = '+'.join([ts.siglas for ts in tipos_solicitud]) if tipos_solicitud else 'SIN TIPO'
        
        result.append({
            'obj': sol,
            'tipos_str': tipos,
            'fases_completadas': fases_completadas,
            'total_fases': total_fases,
            'tramites_completados': tramites_completados,
            'total_tramites': total_tramites
        })
    
    return result


def _get_fases_con_stats(solicitud_id):
    """Obtiene fases con contadores de trámites."""
    fases = Fase.query.filter_by(solicitud_id=solicitud_id).all()
    
    result = []
    for fase in fases:
        total_tramites = Tramite.query.filter_by(fase_id=fase.id).count()
        tramites_completados = Tramite.query.filter_by(
            fase_id=fase.id
        ).filter(Tramite.fecha_fin.isnot(None)).count()
        
        result.append({
            'obj': fase,
            'nombre': fase.tipo_fase.nombre if fase.tipo_fase else f'Fase {fase.id}',
            'tramites_completados': tramites_completados,
            'total_tramites': total_tramites,
            'estado': 'Finalizada' if fase.fecha_fin else 'En curso' if fase.fecha_inicio else 'Pendiente'
        })
    
    return result


def _get_tramites_con_stats(fase_id):
    """Obtiene trámites con contadores de tareas."""
    tramites = Tramite.query.filter_by(fase_id=fase_id).all()
    
    result = []
    for tramite in tramites:
        total_tareas = Tarea.query.filter_by(tramite_id=tramite.id).count()
        tareas_completadas = Tarea.query.filter_by(
            tramite_id=tramite.id
        ).filter(Tarea.fecha_fin.isnot(None)).count()
        
        result.append({
            'obj': tramite,
            'nombre': tramite.tipo_tramite.nombre if tramite.tipo_tramite else f'Trámite {tramite.id}',
            'tareas_completadas': tareas_completadas,
            'total_tareas': total_tareas,
            'estado': 'Finalizado' if tramite.fecha_fin else 'En curso' if tramite.fecha_inicio else 'Pendiente'
        })
    
    return result


def _get_tareas_con_stats(tramite_id):
    """Obtiene tareas con contadores de documentos."""
    tareas = Tarea.query.filter_by(tramite_id=tramite_id).all()
    
    result = []
    for tarea in tareas:
        # Contar documentos asociados (usado + producido)
        docs_count = 0
        if tarea.documento_usado_id:
            docs_count += 1
        if tarea.documento_producido_id:
            docs_count += 1
        
        result.append({
            'obj': tarea,
            'nombre': tarea.tipo_tarea.nombre if tarea.tipo_tarea else f'Tarea {tarea.id}',
            'documentos_count': docs_count,
            'estado': 'Finalizada' if tarea.fecha_fin else 'En curso' if tarea.fecha_inicio else 'Pendiente'
        })
    
    return result


def _get_documentos_tarea(tarea_id):
    """Obtiene documentos de una tarea (usado y producido)."""
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return []
    
    docs = []
    if tarea.documento_usado:
        docs.append({
            'obj': tarea.documento_usado,
            'tipo_relacion': 'Documento usado'
        })
    if tarea.documento_producido:
        docs.append({
            'obj': tarea.documento_producido,
            'tipo_relacion': 'Documento producido'
        })
    
    return docs
