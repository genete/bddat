"""
API para Vista BC (breadcrumbs) — tramitación ESFTT.

Endpoints equivalentes a los que tenía el blueprint vista3 (eliminado en #309),
adaptados para el sistema BC: los editar_* no re-renderizan HTML porque el JS
bc-edicion.js actualiza el DOM directamente desde los valores del formulario.

Creado para resolver el bug #314.
"""
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
from app.models.documentos_tarea import DocumentoTarea
from app.models.entidad import Entidad
from app.models.organismos_expediente import OrganismoExpediente, ESTADOS_ORGANISMO, VIAS_ORGANISMO
from app.models.tramites_organismos import TramiteOrganismo
from app.utils.permisos import verificar_acceso_expediente
from app.services.assembler import evaluar_multi
from app.services.invariantes_esftt import check_invariante, _check_cierre_fase

bp = Blueprint('api_bc', __name__, url_prefix='/api/bc')


def _bloqueo(res_eval):
    """Respuesta de error cuando el motor bloquea la acción."""
    return jsonify({
        'ok': False,
        'motivo': res_eval.motivo,
        'error': res_eval.norma_compilada or 'Acción no permitida',
        'url_norma': res_eval.url_norma,
    }), 422


def _advertencia(res_eval):
    """Dict de advertencia para incluir en la respuesta ok (o None si no hay)."""
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {'motivo': res_eval.motivo, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma}
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
    entidad_id = request.form.get('entidad_id', type=int) or expediente.titular_id

    if not tipo_ids:
        return jsonify({'ok': False, 'error': 'Selecciona al menos un tipo de solicitud'}), 400
    if not entidad_id:
        return jsonify({'ok': False, 'error': 'El expediente no tiene titular asignado. Asígnelo antes de crear solicitudes.'}), 422

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
                            tipo_solicitud_id=tid_int)
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
    _hook_459_traslado_organismo(tipo_tramite, fase)
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
        sol.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        return jsonify({'ok': True})
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

    doc_resultado_raw = request.form.get('documento_resultado_id')
    nuevo_doc_resultado_id = int(doc_resultado_raw) if doc_resultado_raw else None

    if nuevo_doc_resultado_id and fase.documento_resultado_id is None:
        doc = Documento.query.get(nuevo_doc_resultado_id)
        if not doc or doc.expediente_id != fase.solicitud.expediente_id:
            return jsonify({'ok': False, 'error': 'Documento no válido para este expediente'}), 422

        resultado_id_raw = request.form.get('resultado_fase_id')
        if resultado_id_raw:
            tipo_res = TipoResultadoFase.query.get(int(resultado_id_raw))
            if tipo_res:
                res_inv = _check_cierre_fase(fase_id, tipo_res.codigo)
                if res_inv:
                    return _bloqueo(res_inv)

    try:
        resultado_id = request.form.get('resultado_fase_id')
        fase.resultado_fase_id = int(resultado_id) if resultado_id else None
        fase.documento_resultado_id = nuevo_doc_resultado_id
        fase.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        return jsonify({'ok': True})
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
        tramite.observaciones = request.form.get('observaciones') or None
        db.session.commit()
        return jsonify({'ok': True})
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
        # Documentos consumidos: lista de ids (campo repetido o CSV). Documento
        # producido: id único. Vínculos vía documentos_tarea con rol (ADR-010).
        consumidos_raw = request.form.getlist('documentos_consumidos_ids')
        if len(consumidos_raw) == 1 and ',' in consumidos_raw[0]:
            consumidos_raw = consumidos_raw[0].split(',')
        ids_consumidos = [int(x) for x in consumidos_raw if x.strip()]

        doc_producido_raw = request.form.get('documento_producido_id') or None
        id_producido = int(doc_producido_raw) if doc_producido_raw else None

        ids_todos = list(ids_consumidos) + ([id_producido] if id_producido else [])
        for doc_id in ids_todos:
            doc = Documento.query.get(doc_id)
            if not doc or doc.expediente_id != expediente.id:
                return jsonify({'ok': False, 'error': 'Documento no válido para este expediente'}), 422

        # Reconstruir los vínculos de la tarea
        tarea.vinculos_documento.clear()
        db.session.flush()
        for doc_id in dict.fromkeys(ids_consumidos):   # sin duplicados, orden estable
            tarea.vinculos_documento.append(
                DocumentoTarea(documento_id=doc_id, rol='CONSUMIDO'))
        if id_producido:
            tarea.vinculos_documento.append(
                DocumentoTarea(documento_id=id_producido, rol='PRODUCIDO'))

        tarea.notas = request.form.get('notas') or None
        _hook_458_analizar_separata(tarea, id_producido)
        db.session.commit()

        return jsonify({'ok': True})
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
# ENDPOINTS POST — ACCIONES FINALIZAR
# ============================================

@bp.route('/solicitud/<int:sol_id>/finalizar', methods=['POST'])
@login_required
def finalizar_solicitud(sol_id):
    sol = Solicitud.query.get_or_404(sol_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if sol.estado == 'RESUELTA':
        return jsonify({'ok': False, 'error': 'La solicitud ya está resuelta'}), 422
    return jsonify({'ok': True})


@bp.route('/fase/<int:fase_id>/finalizar', methods=['POST'])
@login_required
def finalizar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if fase.finalizada:
        return jsonify({'ok': False, 'error': 'La fase ya está finalizada'}), 422
    return jsonify({'ok': True})


@bp.route('/tramite/<int:tram_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tramite.finalizado:
        return jsonify({'ok': False, 'error': 'El trámite ya está finalizado'}), 422
    return jsonify({'ok': True})


@bp.route('/tarea/<int:tarea_id>/finalizar', methods=['POST'])
@login_required
def finalizar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    if tarea.ejecutada:
        return jsonify({'ok': False, 'error': 'La tarea ya está finalizada'}), 422

    res_inv = check_invariante('FINALIZAR', 'TAREA', tarea_id)
    if res_inv:
        return _bloqueo(res_inv)

    return jsonify({'ok': True})


# ============================================
# HELPERS CRUD organismos (testables sin Flask)
# ============================================

def _serializar_org_exp(oe):
    """Serializa OrganismoExpediente a dict para la API."""
    return {
        'id': oe.id,
        'organismo_id': oe.organismo_id,
        'nombre_completo': oe.organismo.nombre_completo if oe.organismo else None,
        'nif': oe.organismo.nif if oe.organismo else None,
        'via': oe.via,
        'estado': oe.estado,
        'plazo_legal_dias': oe.plazo_legal_dias,
        'condicionados_doc_id': oe.condicionados_doc_id,
    }


def _hook_458_analizar_separata(tarea, id_producido):
    """Hook #458: al producir diagnóstico en CONSULTA_SEPARATA pasa el organismo a en_tramitacion."""
    if (id_producido is not None
            and tarea.tipo_tarea.codigo == 'ANALIZAR'
            and tarea.tramite.tipo_tramite.codigo == 'CONSULTA_SEPARATA'):
        vinculo = TramiteOrganismo.query.filter_by(tramite_id=tarea.tramite_id).first()
        if vinculo:
            vinculo.organismo_expediente.estado = 'en_tramitacion'


def _hook_459_traslado_organismo(tipo_tramite, fase):
    """Hook #459: guard para CONSULTA_TRASLADO_ORGANISMO.

    La vinculación del trámite a su OrganismoExpediente en tramites_organismos
    se implementará en #471.
    """
    if tipo_tramite.codigo != 'CONSULTA_TRASLADO_ORGANISMO':
        return


# ============================================
# ENDPOINTS — CRUD organismos_expediente (#247)
# ============================================

@bp.route('/expediente/<int:exp_id>/organismos', methods=['GET'])
@login_required
def listar_organismos(exp_id):
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    oes = OrganismoExpediente.query.filter_by(expediente_id=exp_id).all()
    return jsonify({'ok': True, 'organismos': [_serializar_org_exp(oe) for oe in oes]})


@bp.route('/expediente/<int:exp_id>/organismos', methods=['POST'])
@login_required
def crear_organismo(exp_id):
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    organismo_id = request.form.get('organismo_id', type=int)
    via = request.form.get('via')
    documento_id = request.form.get('documento_id', type=int)
    plazo_legal_dias = request.form.get('plazo_legal_dias', type=int)

    if not organismo_id:
        return jsonify({'ok': False, 'error': 'organismo_id es obligatorio'}), 400

    entidad = Entidad.query.get(organismo_id)
    if not entidad or not entidad.rol_consultado:
        return jsonify({'ok': False, 'error': 'El organismo no existe o no tiene rol consultado'}), 422

    if via not in VIAS_ORGANISMO:
        return jsonify({'ok': False, 'error': f'via debe ser uno de: {", ".join(VIAS_ORGANISMO)}'}), 400

    duplicado = OrganismoExpediente.query.filter_by(
        expediente_id=exp_id, organismo_id=organismo_id
    ).first()
    if duplicado:
        return jsonify({'ok': False, 'error': 'Este organismo ya está añadido al expediente'}), 409

    try:
        oe = OrganismoExpediente(
            expediente_id=exp_id,
            organismo_id=organismo_id,
            via=via,
            documento_id=documento_id,
            plazo_legal_dias=plazo_legal_dias,
        )
        db.session.add(oe)
        db.session.commit()
        return jsonify({'ok': True, 'id': oe.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/expediente/<int:exp_id>/organismos/<int:oid>', methods=['PATCH'])
@login_required
def editar_organismo(exp_id, oid):
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    oe = OrganismoExpediente.query.filter_by(id=oid, expediente_id=exp_id).first_or_404()

    estado = request.form.get('estado')
    if estado not in ESTADOS_ORGANISMO:
        return jsonify({'ok': False, 'error': f'estado debe ser uno de: {", ".join(ESTADOS_ORGANISMO)}'}), 422

    try:
        oe.estado = estado
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/expediente/<int:exp_id>/organismos/<int:oid>', methods=['DELETE'])
@login_required
def borrar_organismo(exp_id, oid):
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    oe = OrganismoExpediente.query.filter_by(id=oid, expediente_id=exp_id).first_or_404()

    try:
        db.session.delete(oe)
        db.session.commit()
        return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

