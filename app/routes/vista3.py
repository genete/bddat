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
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.utils.permisos import verificar_acceso_expediente
from app.services.motor_reglas import evaluar

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

    solicitudes_arbol = _construir_arbol(exp_id)
    resultados_fase = TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
    html = render_template(
        'vistas/vista3/_arbol_completo.html',
        solicitudes_arbol=solicitudes_arbol,
        resultados_fase=resultados_fase
    )
    return jsonify({'html': html, 'count': len(solicitudes_arbol)})


def _construir_arbol(expediente_id):
    """Construye árbol completo anidado de todos los niveles (para V3 tabs y acordeón)."""
    solicitudes_arbol = []
    for sol_data in _get_solicitudes_con_stats(expediente_id):
        fases_arbol = []
        for fase_data in _get_fases_con_stats(sol_data['obj'].id):
            tramites_arbol = []
            for tram_data in _get_tramites_con_stats(fase_data['obj'].id):
                tareas = _get_tareas_con_stats(tram_data['obj'].id)
                tareas_con_docs = [
                    {**t, 'documentos': _get_documentos_tarea(t['obj'].id)}
                    for t in tareas
                ]
                tramites_arbol.append({**tram_data, 'tareas': tareas_con_docs})
            fases_arbol.append({**fase_data, 'tramites': tramites_arbol})
        solicitudes_arbol.append({**sol_data, 'fases': fases_arbol})
    return solicitudes_arbol


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
            'codigo': fase.tipo_fase.codigo if fase.tipo_fase else '',
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
            'codigo': tramite.tipo_tramite.codigo if tramite.tipo_tramite else '',
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
            'codigo': tarea.tipo_tarea.codigo if tarea.tipo_tarea else '',
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
        nueva_fecha_solicitud = date.fromisoformat(request.form['fecha_solicitud']) if request.form.get('fecha_solicitud') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        # Hook FINALIZAR (fecha_fin: None → valor)
        res_eval = None
        if sol.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar('FINALIZAR', 'SOLICITUD', entidad_id=sol_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        sol.fecha_solicitud = nueva_fecha_solicitud
        sol.fecha_fin = nueva_fecha_fin
        if request.form.get('estado'):
            sol.estado = request.form['estado']
        sol.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_solicitudes_con_stats(sol.expediente_id)
        sol_data = next((s for s in result if s['obj'].id == sol_id), None)
        html = render_template('vistas/vista3/_acordeon_solicitud.html', sol_data=sol_data) if sol_data else ''
        advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval and res_eval.nivel == 'ADVERTIR' else None
        return jsonify({'ok': True, 'html': html, 'advertencia': advertencia})
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
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        # Hook INICIAR (fecha_inicio: None → valor)
        res_eval = None
        if fase.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar('INICIAR', 'FASE', entidad_id=fase_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        # Hook FINALIZAR (fecha_fin: None → valor)
        if fase.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar('FINALIZAR', 'FASE', entidad_id=fase_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        fase.fecha_inicio = nueva_fecha_inicio
        fase.fecha_fin = nueva_fecha_fin
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
        advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval and res_eval.nivel == 'ADVERTIR' else None
        return jsonify({'ok': True, 'html': html, 'advertencia': advertencia})
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
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        # Hook INICIAR (fecha_inicio: None → valor)
        res_eval = None
        if tramite.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar('INICIAR', 'TRAMITE', entidad_id=tram_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        # Hook FINALIZAR (fecha_fin: None → valor)
        if tramite.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar('FINALIZAR', 'TRAMITE', entidad_id=tram_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        tramite.fecha_inicio = nueva_fecha_inicio
        tramite.fecha_fin = nueva_fecha_fin
        tramite.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_tramites_con_stats(tramite.fase_id)
        tramite_data = next((t for t in result if t['obj'].id == tram_id), None)
        html = render_template('vistas/vista3/_acordeon_tramite.html', tramite_data=tramite_data) if tramite_data else ''
        advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval and res_eval.nivel == 'ADVERTIR' else None
        return jsonify({'ok': True, 'html': html, 'advertencia': advertencia})
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
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        # Hook INICIAR (fecha_inicio: None → valor)
        res_eval = None
        if tarea.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar('INICIAR', 'TAREA', entidad_id=tarea_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        # Hook FINALIZAR (fecha_fin: None → valor)
        if tarea.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar('FINALIZAR', 'TAREA', entidad_id=tarea_id)
            if not res_eval.permitido:
                return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

        tarea.fecha_inicio = nueva_fecha_inicio
        tarea.fecha_fin = nueva_fecha_fin
        tarea.notas = request.form.get('notas') or None
        db.session.commit()
        # Re-renderizar el acordeón para actualizar el DOM sin recargar
        result = _get_tareas_con_stats(tarea.tramite_id)
        tarea_data = next((t for t in result if t['obj'].id == tarea_id), None)
        documentos = _get_documentos_tarea(tarea_id)
        html = render_template('vistas/vista3/_acordeon_tarea.html', tarea_data=tarea_data,
                               documentos=documentos) if tarea_data else ''
        advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval and res_eval.nivel == 'ADVERTIR' else None
        return jsonify({'ok': True, 'html': html, 'advertencia': advertencia})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS POST — CREAR entidades
# ============================================

@bp.route('/expediente/<int:exp_id>/solicitudes/nueva', methods=['POST'])
@login_required
def crear_solicitud(exp_id):
    """Crea una nueva solicitud en el expediente indicado."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_ids = request.form.getlist('tipo_solicitud_id[]', type=int)
    fecha_str = request.form.get('fecha_solicitud')
    entidad_id = request.form.get('entidad_id', type=int) or expediente.titular_id
    if not tipo_ids or not fecha_str:
        return jsonify({'ok': False, 'error': 'tipo y fecha son obligatorios'}), 400

    try:
        fecha = date.fromisoformat(fecha_str)
    except ValueError:
        return jsonify({'ok': False, 'error': 'Fecha inválida'}), 400

    sol = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                    fecha_solicitud=fecha, estado='EN_TRAMITE')
    db.session.add(sol)
    db.session.flush()
    for tipo_id in tipo_ids:
        db.session.add(SolicitudTipo(solicitudid=sol.id, tiposolicitudid=tipo_id))
    db.session.commit()

    tipos_objs = TipoSolicitud.query.filter(TipoSolicitud.id.in_(tipo_ids)).all()
    tipos_str = '+'.join(t.siglas for t in tipos_objs) if tipos_objs else 'Nueva'
    return jsonify({'ok': True, 'id': sol.id, 'tipos_str': tipos_str})


@bp.route('/solicitud/<int:sol_id>/borrar', methods=['POST'])
@login_required
def borrar_solicitud(sol_id):
    """Elimina una solicitud si el motor de reglas lo permite."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar('BORRAR', 'SOLICITUD', entidad_id=sol_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    fase_ids = [f.id for f in Fase.query.filter_by(solicitud_id=sol_id).all()]
    if fase_ids:
        tram_ids = [t.id for t in Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).all()]
        if tram_ids:
            Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
        Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).delete()
    Fase.query.filter_by(solicitud_id=sol_id).delete()
    SolicitudTipo.query.filter_by(solicitudid=sol_id).delete()
    db.session.delete(sol)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/solicitud/<int:sol_id>/fases/nueva', methods=['POST'])
@login_required
def crear_fase(sol_id):
    """Crea una nueva fase en la solicitud indicada."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_fase_id = request.form.get('tipo_fase_id', type=int)
    if not tipo_fase_id:
        return jsonify({'ok': False, 'error': 'tipo_fase_id es obligatorio'}), 400
    if not TipoFase.query.get(tipo_fase_id):
        return jsonify({'ok': False, 'error': 'Tipo de fase no encontrado'}), 404

    res_eval = evaluar('CREAR', 'FASE', tipo_id=tipo_fase_id, padre_id=sol_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    fase = Fase(solicitud_id=sol_id, tipo_fase_id=tipo_fase_id)
    db.session.add(fase)
    db.session.commit()

    advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval.nivel == 'ADVERTIR' else None
    return jsonify({'ok': True, 'id': fase.id, 'advertencia': advertencia})


@bp.route('/fase/<int:fase_id>/tramites/nuevo', methods=['POST'])
@login_required
def crear_tramite(fase_id):
    """Crea un nuevo trámite en la fase indicada."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_tramite_id = request.form.get('tipo_tramite_id', type=int)
    if not tipo_tramite_id:
        return jsonify({'ok': False, 'error': 'tipo_tramite_id es obligatorio'}), 400
    if not TipoTramite.query.get(tipo_tramite_id):
        return jsonify({'ok': False, 'error': 'Tipo de trámite no encontrado'}), 404

    res_eval = evaluar('CREAR', 'TRAMITE', tipo_id=tipo_tramite_id, padre_id=fase_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tramite = Tramite(fase_id=fase_id, tipo_tramite_id=tipo_tramite_id)
    db.session.add(tramite)
    db.session.commit()

    advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval.nivel == 'ADVERTIR' else None
    return jsonify({'ok': True, 'id': tramite.id, 'advertencia': advertencia})


@bp.route('/tramite/<int:tram_id>/tareas/nueva', methods=['POST'])
@login_required
def crear_tarea(tram_id):
    """Crea una nueva tarea en el trámite indicado."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_tarea_id = request.form.get('tipo_tarea_id', type=int)
    if not tipo_tarea_id:
        return jsonify({'ok': False, 'error': 'tipo_tarea_id es obligatorio'}), 400
    if not TipoTarea.query.get(tipo_tarea_id):
        return jsonify({'ok': False, 'error': 'Tipo de tarea no encontrado'}), 404

    res_eval = evaluar('CREAR', 'TAREA', tipo_id=tipo_tarea_id, padre_id=tram_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tarea = Tarea(tramite_id=tram_id, tipo_tarea_id=tipo_tarea_id)
    db.session.add(tarea)
    db.session.commit()

    advertencia = {'mensaje': res_eval.mensaje, 'norma': res_eval.norma} if res_eval.nivel == 'ADVERTIR' else None
    return jsonify({'ok': True, 'id': tarea.id, 'advertencia': advertencia})


# ============================================
# ENDPOINTS POST — BORRAR entidades
# ============================================

@bp.route('/fase/<int:fase_id>/borrar', methods=['POST'])
@login_required
def borrar_fase(fase_id):
    """Elimina una fase si el motor de reglas lo permite."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar('BORRAR', 'FASE', entidad_id=fase_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tram_ids = [t.id for t in Tramite.query.filter_by(fase_id=fase_id).all()]
    if tram_ids:
        Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
    Tramite.query.filter_by(fase_id=fase_id).delete()
    db.session.delete(fase)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/tramite/<int:tram_id>/borrar', methods=['POST'])
@login_required
def borrar_tramite(tram_id):
    """Elimina un trámite si el motor de reglas lo permite."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar('BORRAR', 'TRAMITE', entidad_id=tram_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    Tarea.query.filter_by(tramite_id=tram_id).delete()
    db.session.delete(tramite)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/tarea/<int:tarea_id>/borrar', methods=['POST'])
@login_required
def borrar_tarea(tarea_id):
    """Elimina una tarea si el motor de reglas lo permite."""
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar('BORRAR', 'TAREA', entidad_id=tarea_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    db.session.delete(tarea)
    db.session.commit()
    return jsonify({'ok': True})


# ============================================
# ENDPOINTS POST — ACCIONES contextuales (INICIAR / FINALIZAR)
# ============================================

@bp.route('/solicitud/<int:sol_id>/iniciar', methods=['POST'])
@login_required
def iniciar_solicitud(sol_id):
    """Inicia una solicitud (establece fecha_solicitud = hoy) si el motor lo permite."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if sol.fecha_solicitud is not None:
        return jsonify({'ok': False, 'error': 'La solicitud ya tiene fecha de inicio'}), 422

    res_eval = evaluar('INICIAR', 'SOLICITUD', entidad_id=sol_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    sol.fecha_solicitud = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/solicitud/<int:sol_id>/finalizar', methods=['POST'])
@login_required
def finalizar_solicitud(sol_id):
    """Finaliza una solicitud (establece fecha_fin = hoy) si el motor lo permite."""
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if sol.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La solicitud ya está finalizada'}), 422

    res_eval = evaluar('FINALIZAR', 'SOLICITUD', entidad_id=sol_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    sol.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/fase/<int:fase_id>/iniciar', methods=['POST'])
@login_required
def iniciar_fase(fase_id):
    """Inicia una fase (establece fecha_inicio = hoy) si el motor lo permite."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if fase.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'La fase ya está iniciada'}), 422

    res_eval = evaluar('INICIAR', 'FASE', entidad_id=fase_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    fase.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/fase/<int:fase_id>/finalizar', methods=['POST'])
@login_required
def finalizar_fase(fase_id):
    """Finaliza una fase (establece fecha_fin = hoy) si el motor lo permite."""
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if fase.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La fase ya está finalizada'}), 422

    res_eval = evaluar('FINALIZAR', 'FASE', entidad_id=fase_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    fase.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/tramite/<int:tram_id>/iniciar', methods=['POST'])
@login_required
def iniciar_tramite(tram_id):
    """Inicia un trámite (establece fecha_inicio = hoy) si el motor lo permite."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tramite.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'El trámite ya está iniciado'}), 422

    res_eval = evaluar('INICIAR', 'TRAMITE', entidad_id=tram_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tramite.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/tramite/<int:tram_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tramite(tram_id):
    """Finaliza un trámite (establece fecha_fin = hoy) si el motor lo permite."""
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tramite.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'El trámite ya está finalizado'}), 422

    res_eval = evaluar('FINALIZAR', 'TRAMITE', entidad_id=tram_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tramite.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/tarea/<int:tarea_id>/iniciar', methods=['POST'])
@login_required
def iniciar_tarea(tarea_id):
    """Inicia una tarea (establece fecha_inicio = hoy) si el motor lo permite."""
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tarea.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'La tarea ya está iniciada'}), 422

    res_eval = evaluar('INICIAR', 'TAREA', entidad_id=tarea_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tarea.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})


@bp.route('/tarea/<int:tarea_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tarea(tarea_id):
    """Finaliza una tarea (establece fecha_fin = hoy) si el motor lo permite."""
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tarea.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La tarea ya está finalizada'}), 422

    res_eval = evaluar('FINALIZAR', 'TAREA', entidad_id=tarea_id)
    if not res_eval.permitido:
        return jsonify({'ok': False, 'error': res_eval.mensaje, 'norma': res_eval.norma}), 422

    tarea.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'mensaje': res_eval.mensaje})
