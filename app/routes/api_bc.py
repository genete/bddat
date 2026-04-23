"""
API para Vista BC (breadcrumbs) — tramitación ESFTT.

Endpoints equivalentes a los que tenía el blueprint vista3 (eliminado en #309),
adaptados para el sistema BC: los editar_* no re-renderizan HTML porque el JS
bc-edicion.js actualiza el DOM directamente desde los valores del formulario.

Creado para resolver el bug #314.
"""
from datetime import date
from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.utils.permisos import verificar_acceso_expediente
from app.services.assembler import evaluar_multi

bp = Blueprint('api_bc', __name__, url_prefix='/api/bc')


def _bloqueo(res_eval):
    """Respuesta de error cuando el motor bloquea la acción."""
    return jsonify({
        'ok': False,
        'error': res_eval.norma_compilada or 'Acción no permitida',
        'url_norma': res_eval.url_norma,
    }), 422


def _advertencia(res_eval):
    """Dict de advertencia para incluir en la respuesta ok (o None si no hay)."""
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma}
    return None


# ============================================
# ENDPOINTS POST — CREAR entidades
# ============================================

@bp.route('/expediente/<int:exp_id>/solicitudes/nueva', methods=['POST'])
@login_required
def crear_solicitud(exp_id):
    """Crea una o varias solicitudes en el expediente (multi-select de tipos)."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    # El template envía tipo_solicitud_id[] (multi-select)
    tipo_ids = request.form.getlist('tipo_solicitud_id[]') or request.form.getlist('tipo_solicitud_id')
    fecha_str = request.form.get('fecha_solicitud')
    entidad_id = request.form.get('entidad_id', type=int) or expediente.titular_id

    if not tipo_ids:
        return jsonify({'ok': False, 'error': 'Selecciona al menos un tipo de solicitud'}), 400
    if not entidad_id:
        return jsonify({'ok': False, 'error': 'El expediente no tiene titular asignado. Asígnelo antes de crear solicitudes.'}), 422

    if fecha_str:
        try:
            fecha = date.fromisoformat(fecha_str)
        except ValueError:
            return jsonify({'ok': False, 'error': 'Fecha inválida'}), 400
    else:
        fecha = None

    creadas = []
    try:
        for tid in tipo_ids:
            try:
                tid_int = int(tid)
            except (ValueError, TypeError):
                return jsonify({'ok': False, 'error': f'Tipo de solicitud inválido: {tid}'}), 400
            tipo = TipoSolicitud.query.get(tid_int)
            if not tipo:
                return jsonify({'ok': False, 'error': f'Tipo de solicitud {tid_int} no encontrado'}), 404
            sol = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                            tipo_solicitud_id=tid_int,
                            fecha_solicitud=fecha, estado='EN_TRAMITE')
            db.session.add(sol)
            creadas.append(sol)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    ids = [s.id for s in creadas]
    return jsonify({'ok': True, 'ids': ids})


@bp.route('/solicitud/<int:sol_id>/fases/nueva', methods=['POST'])
@login_required
def crear_fase(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_fase_id = request.form.get('tipo_fase_id', type=int)
    if not tipo_fase_id:
        return jsonify({'ok': False, 'error': 'tipo_fase_id es obligatorio'}), 400
    tipo_fase = TipoFase.query.get(tipo_fase_id)
    if not tipo_fase:
        return jsonify({'ok': False, 'error': 'Tipo de fase no encontrado'}), 404

    res_eval = evaluar_multi('CREAR', sol.expediente, objeto={'solicitud': sol, 'tipo_fase': tipo_fase})
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    fase = Fase(solicitud_id=sol_id, tipo_fase_id=tipo_fase_id)
    db.session.add(fase)
    db.session.commit()

    return jsonify({'ok': True, 'id': fase.id, 'advertencia': _advertencia(res_eval)})


@bp.route('/fase/<int:fase_id>/tramites/nuevo', methods=['POST'])
@login_required
def crear_tramite(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_tramite_id = request.form.get('tipo_tramite_id', type=int)
    if not tipo_tramite_id:
        return jsonify({'ok': False, 'error': 'tipo_tramite_id es obligatorio'}), 400
    tipo_tramite = TipoTramite.query.get(tipo_tramite_id)
    if not tipo_tramite:
        return jsonify({'ok': False, 'error': 'Tipo de trámite no encontrado'}), 404

    res_eval = evaluar_multi('CREAR', fase.solicitud.expediente, objeto={'fase': fase, 'tipo_tramite': tipo_tramite})
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tramite = Tramite(fase_id=fase_id, tipo_tramite_id=tipo_tramite_id)
    db.session.add(tramite)
    db.session.commit()

    return jsonify({'ok': True, 'id': tramite.id, 'advertencia': _advertencia(res_eval)})


@bp.route('/tramite/<int:tram_id>/tareas/nueva', methods=['POST'])
@login_required
def crear_tarea(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    tipo_tarea_id = request.form.get('tipo_tarea_id', type=int)
    if not tipo_tarea_id:
        return jsonify({'ok': False, 'error': 'tipo_tarea_id es obligatorio'}), 400
    tipo_tarea = TipoTarea.query.get(tipo_tarea_id)
    if not tipo_tarea:
        return jsonify({'ok': False, 'error': 'Tipo de tarea no encontrado'}), 404

    res_eval = evaluar_multi('CREAR', tramite.fase.solicitud.expediente, objeto={'tramite': tramite, 'tipo_tarea': tipo_tarea})
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tarea = Tarea(tramite_id=tram_id, tipo_tarea_id=tipo_tarea_id)
    db.session.add(tarea)
    db.session.commit()

    return jsonify({'ok': True, 'id': tarea.id, 'advertencia': _advertencia(res_eval)})


# ============================================
# ENDPOINTS POST — EDITAR entidades
# (el JS bc-edicion.js actualiza el DOM directamente — no se re-renderiza HTML)
# ============================================

@bp.route('/solicitud/<int:sol_id>/editar', methods=['POST'])
@login_required
def editar_solicitud(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        res_eval = None
        if sol.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar_multi('FINALIZAR', sol.expediente, objeto=sol)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        sol.fecha_fin = nueva_fecha_fin
        if request.form.get('estado'):
            sol.estado = request.form['estado']
        sol.observaciones = request.form.get('observaciones') or None
        db.session.commit()

        return jsonify({'ok': True, 'advertencia': _advertencia(res_eval)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/fase/<int:fase_id>/editar', methods=['POST'])
@login_required
def editar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        res_eval = None
        if fase.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar_multi('INICIAR', fase.solicitud.expediente, objeto=fase)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        if fase.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar_multi('FINALIZAR', fase.solicitud.expediente, objeto=fase)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        fase.fecha_inicio = nueva_fecha_inicio
        fase.fecha_fin = nueva_fecha_fin
        resultado_id = request.form.get('resultado_fase_id')
        fase.resultado_fase_id = int(resultado_id) if resultado_id else None
        fase.observaciones = request.form.get('observaciones') or None
        db.session.commit()

        return jsonify({'ok': True, 'advertencia': _advertencia(res_eval)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/tramite/<int:tram_id>/editar', methods=['POST'])
@login_required
def editar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    try:
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        res_eval = None
        if tramite.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar_multi('INICIAR', tramite.fase.solicitud.expediente, objeto=tramite)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        if tramite.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar_multi('FINALIZAR', tramite.fase.solicitud.expediente, objeto=tramite)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        tramite.fecha_inicio = nueva_fecha_inicio
        tramite.fecha_fin = nueva_fecha_fin
        tramite.observaciones = request.form.get('observaciones') or None
        db.session.commit()

        return jsonify({'ok': True, 'advertencia': _advertencia(res_eval)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/tarea/<int:tarea_id>/editar', methods=['POST'])
@login_required
def editar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    expediente = tarea.tramite.fase.solicitud.expediente

    try:
        nueva_fecha_inicio = date.fromisoformat(request.form['fecha_inicio']) if request.form.get('fecha_inicio') else None
        nueva_fecha_fin = date.fromisoformat(request.form['fecha_fin']) if request.form.get('fecha_fin') else None

        doc_usado_raw     = request.form.get('documento_usado_id') or None
        doc_producido_raw = request.form.get('documento_producido_id') or None
        nuevo_doc_usado_id     = int(doc_usado_raw)     if doc_usado_raw     else None
        nuevo_doc_producido_id = int(doc_producido_raw) if doc_producido_raw else None

        for doc_id in filter(None, [nuevo_doc_usado_id, nuevo_doc_producido_id]):
            doc = Documento.query.get(doc_id)
            if not doc or doc.expediente_id != expediente.id:
                return jsonify({'ok': False, 'error': 'Documento no válido para este expediente'}), 422

        tarea.documento_usado_id     = nuevo_doc_usado_id
        tarea.documento_producido_id = nuevo_doc_producido_id

        res_eval = None
        if tarea.fecha_inicio is None and nueva_fecha_inicio is not None:
            res_eval = evaluar_multi('INICIAR', expediente, objeto=tarea)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        if tarea.fecha_fin is None and nueva_fecha_fin is not None:
            res_eval = evaluar_multi('FINALIZAR', expediente, objeto=tarea)
            if not res_eval.permitido:
                return _bloqueo(res_eval)

        tarea.fecha_inicio = nueva_fecha_inicio
        tarea.fecha_fin = nueva_fecha_fin
        tarea.notas = request.form.get('notas') or None
        db.session.commit()

        return jsonify({'ok': True, 'advertencia': _advertencia(res_eval)})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'Este documento ya está asignado como producido a otra tarea'}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================
# ENDPOINTS POST — BORRAR entidades
# ============================================

@bp.route('/solicitud/<int:sol_id>/borrar', methods=['POST'])
@login_required
def borrar_solicitud(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar_multi('BORRAR', sol.expediente, objeto=sol)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    fase_ids = [f.id for f in Fase.query.filter_by(solicitud_id=sol_id).all()]
    if fase_ids:
        tram_ids = [t.id for t in Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).all()]
        if tram_ids:
            Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
        Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).delete()
    Fase.query.filter_by(solicitud_id=sol_id).delete()
    db.session.delete(sol)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/fase/<int:fase_id>/borrar', methods=['POST'])
@login_required
def borrar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar_multi('BORRAR', fase.solicitud.expediente, objeto=fase)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

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
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar_multi('BORRAR', tramite.fase.solicitud.expediente, objeto=tramite)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    Tarea.query.filter_by(tramite_id=tram_id).delete()
    db.session.delete(tramite)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/tarea/<int:tarea_id>/borrar', methods=['POST'])
@login_required
def borrar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res_eval = evaluar_multi('BORRAR', tarea.tramite.fase.solicitud.expediente, objeto=tarea)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    db.session.delete(tarea)
    db.session.commit()
    return jsonify({'ok': True})


# ============================================
# ENDPOINTS POST — ACCIONES contextuales (INICIAR / FINALIZAR)
# ============================================

@bp.route('/solicitud/<int:sol_id>/iniciar', methods=['POST'])
@login_required
def iniciar_solicitud(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if sol.fecha_solicitud is not None:
        return jsonify({'ok': False, 'error': 'La solicitud ya tiene fecha de inicio'}), 422

    res_eval = evaluar_multi('INICIAR', sol.expediente, objeto=sol)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    sol.fecha_solicitud = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/solicitud/<int:sol_id>/finalizar', methods=['POST'])
@login_required
def finalizar_solicitud(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if sol.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La solicitud ya está finalizada'}), 422

    res_eval = evaluar_multi('FINALIZAR', sol.expediente, objeto=sol)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    sol.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/fase/<int:fase_id>/iniciar', methods=['POST'])
@login_required
def iniciar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if fase.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'La fase ya está iniciada'}), 422

    res_eval = evaluar_multi('INICIAR', fase.solicitud.expediente, objeto=fase)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    fase.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/fase/<int:fase_id>/finalizar', methods=['POST'])
@login_required
def finalizar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if fase.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La fase ya está finalizada'}), 422

    res_eval = evaluar_multi('FINALIZAR', fase.solicitud.expediente, objeto=fase)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    fase.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/tramite/<int:tram_id>/iniciar', methods=['POST'])
@login_required
def iniciar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tramite.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'El trámite ya está iniciado'}), 422

    res_eval = evaluar_multi('INICIAR', tramite.fase.solicitud.expediente, objeto=tramite)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tramite.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/tramite/<int:tram_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tramite.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'El trámite ya está finalizado'}), 422

    res_eval = evaluar_multi('FINALIZAR', tramite.fase.solicitud.expediente, objeto=tramite)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tramite.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/tarea/<int:tarea_id>/iniciar', methods=['POST'])
@login_required
def iniciar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tarea.fecha_inicio is not None:
        return jsonify({'ok': False, 'error': 'La tarea ya está iniciada'}), 422

    res_eval = evaluar_multi('INICIAR', tarea.tramite.fase.solicitud.expediente, objeto=tarea)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tarea.fecha_inicio = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})


@bp.route('/tarea/<int:tarea_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tarea.fecha_fin is not None:
        return jsonify({'ok': False, 'error': 'La tarea ya está finalizada'}), 422

    res_eval = evaluar_multi('FINALIZAR', tarea.tramite.fase.solicitud.expediente, objeto=tarea)
    if not res_eval.permitido:
        return _bloqueo(res_eval)

    tarea.fecha_fin = date.today()
    db.session.commit()
    return jsonify({'ok': True, 'nivel': res_eval.nivel, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma})
