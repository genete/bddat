"""
Blueprint para Vista 3 — Tramitación con árbol de acordeones anidados (lazy loading).

Endpoints:
  GET /api/vista3/solicitud/<id>/fases   → acordeones de fases (HTML + count)
  GET /api/vista3/fase/<id>/tramites     → acordeones de trámites (HTML + count)
  GET /api/vista3/tramite/<id>/tareas    → acordeones de tareas (HTML + count)
  GET /api/vista3/expediente/<id>/arbol  → árbol completo pre-cargado (HTML + count)
"""
from datetime import date
from flask import Blueprint, jsonify, render_template, request
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
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.utils.permisos import verificar_acceso_expediente

bp = Blueprint('vista3', __name__, url_prefix='/api/vista3')


@bp.route('/solicitud/<int:sol_id>/fases')
@login_required
def get_fases(sol_id):
    """Fases de una solicitud como acordeones HTML."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'ver')
    if resultado:
        return jsonify({'error': 'Acceso denegado'}), 403

    fases = _get_fases_con_stats(sol_id)
    resultados_fase = TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
    html_parts = [
        render_template('vistas/vista3/_acordeon_fase.html', fase_data=fd,
                        resultados_fase=resultados_fase)
        for fd in fases
    ]
    return jsonify({'html': ''.join(html_parts), 'count': len(fases)})


@bp.route('/fase/<int:fase_id>/tramites')
@login_required
def get_tramites(fase_id):
    """Trámites de una fase como acordeones HTML."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'ver')
    if resultado:
        return jsonify({'error': 'Acceso denegado'}), 403

    tramites = _get_tramites_con_stats(fase_id)
    html_parts = [
        render_template('vistas/vista3/_acordeon_tramite.html', tramite_data=td)
        for td in tramites
    ]
    return jsonify({'html': ''.join(html_parts), 'count': len(tramites)})


@bp.route('/tramite/<int:tram_id>/tareas')
@login_required
def get_tareas(tram_id):
    """Tareas de un trámite como acordeones HTML."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'ver')
    if resultado:
        return jsonify({'error': 'Acceso denegado'}), 403

    tareas = _get_tareas_con_stats(tram_id)
    html_parts = [
        render_template(
            'vistas/vista3/_acordeon_tarea.html',
            tarea_data=td,
            documentos=_get_documentos_tarea(td['obj'].id)
        )
        for td in tareas
    ]
    return jsonify({'html': ''.join(html_parts), 'count': len(tareas)})


@bp.route('/expediente/<int:exp_id>/arbol')
@login_required
def get_arbol(exp_id):
    """Árbol completo del expediente — todos los niveles pre-cargados."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return jsonify({'error': 'Acceso denegado'}), 403

    # Construir estructura anidada completa
    solicitudes_arbol = []
    for sol_data in _get_solicitudes_con_stats(exp_id):
        fases_arbol = []
        for fase_data in _get_fases_con_stats(sol_data['obj'].id):
            tramites_arbol = []
            for tramite_data in _get_tramites_con_stats(fase_data['obj'].id):
                tareas = _get_tareas_con_stats(tramite_data['obj'].id)
                tareas_con_docs = [
                    {**t, 'documentos': _get_documentos_tarea(t['obj'].id)}
                    for t in tareas
                ]
                tramites_arbol.append({**tramite_data, 'tareas': tareas_con_docs})
            fases_arbol.append({**fase_data, 'tramites': tramites_arbol})
        solicitudes_arbol.append({**sol_data, 'fases': fases_arbol})

    resultados_fase = TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
    html = render_template(
        'vistas/vista3/_arbol_completo.html',
        solicitudes_arbol=solicitudes_arbol,
        resultados_fase=resultados_fase
    )
    return jsonify({'html': html, 'count': len(solicitudes_arbol)})


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


# ============================================
# ENDPOINTS POST — Edición SFTT
# ============================================

@bp.route('/solicitud/<int:sol_id>/editar', methods=['POST'])
@login_required
def editar_solicitud(sol_id):
    """Actualiza campos editables de una solicitud."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        sol.fecha_solicitud = date.fromisoformat(request.form['fecha_solicitud']) if request.form.get('fecha_solicitud') else None
        sol.fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None
        if request.form.get('estado'):
            sol.estado = request.form['estado']
        sol.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_solicitudes_con_stats(sol.expediente_id)
        sol_data = next((s for s in result if s['obj'].id == sol_id), None)
        html = render_template('vistas/vista3/_acordeon_solicitud.html', sol_data=sol_data) if sol_data else ''
        return jsonify({'ok': True, 'html': html})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/fase/<int:fase_id>/editar', methods=['POST'])
@login_required
def editar_fase(fase_id):
    """Actualiza campos editables de una fase."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        fase.fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        fase.fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None
        resultado_id = request.form.get('resultado_fase_id')
        fase.resultado_fase_id = int(resultado_id) if resultado_id else None
        fase.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_fases_con_stats(fase.solicitud_id)
        fase_data = next((f for f in result if f['obj'].id == fase_id), None)
        resultados_fase = TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
        html = render_template('vistas/vista3/_acordeon_fase.html', fase_data=fase_data,
                               resultados_fase=resultados_fase) if fase_data else ''
        return jsonify({'ok': True, 'html': html})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/tramite/<int:tram_id>/editar', methods=['POST'])
@login_required
def editar_tramite(tram_id):
    """Actualiza campos editables de un trámite."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        tramite.fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        tramite.fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None
        tramite.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_tramites_con_stats(tramite.fase_id)
        tramite_data = next((t for t in result if t['obj'].id == tram_id), None)
        html = render_template('vistas/vista3/_acordeon_tramite.html', tramite_data=tramite_data) if tramite_data else ''
        return jsonify({'ok': True, 'html': html})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/tarea/<int:tarea_id>/editar', methods=['POST'])
@login_required
def editar_tarea(tarea_id):
    """Actualiza campos editables de una tarea."""
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        tarea.fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        tarea.fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None
        tarea.notas = request.form.get('notas') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_tareas_con_stats(tarea.tramite_id)
        tarea_data = next((t for t in result if t['obj'].id == tarea_id), None)
        documentos = _get_documentos_tarea(tarea_id)
        html = render_template('vistas/vista3/_acordeon_tarea.html', tarea_data=tarea_data,
                               documentos=documentos) if tarea_data else ''
        return jsonify({'ok': True, 'html': html})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500
