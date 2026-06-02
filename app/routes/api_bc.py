"""
API para Vista BC (breadcrumbs) — tramitación ESFTT.

Endpoints equivalentes a los que tenía el blueprint vista3 (eliminado en #309),
adaptados para el sistema BC: los editar_* no re-renderizan HTML porque el JS
bc-edicion.js actualiza el DOM directamente desde los valores del formulario.

Creado para resolver el bug #314.
"""
import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError
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
from app.services.assembler import evaluar_multi, build_sujeto
from app.services import bitacora as bitacora_svc
from app.services.motor_reglas import EvaluacionResult, PERMITIDO
from app.models.configuracion_sistema import ConfiguracionSistema
from app.services.invariantes_esftt import (
    check_invariante, _check_cierre_fase, RESULTADO_FASE_FAVORABLE_CODIGOS,
)
from app.services import mutaciones_arbol as svc

bp = Blueprint('api_bc', __name__, url_prefix='/api/bc')

log = logging.getLogger(__name__)


def _bloqueo(res_eval):
    """Respuesta de error cuando el motor bloquea la acción."""
    return jsonify({
        'ok': False,
        'motivo': res_eval.motivo,
        'error': res_eval.norma_compilada or 'Acción no permitida',
        'url_norma': res_eval.url_norma,
        'puede_escapar': res_eval.puede_escapar,
    }), 422


def _leer_bypass(form):
    """
    Lee bypass + justificacion del form de la petición.

    Devuelve (justificacion, None) si bypass=true con texto válido,
    (None, None) si bypass está ausente o es false,
    (None, respuesta_400) si bypass=true pero justificacion está vacía.
    """
    if form.get('bypass') not in ('true', '1', 'True'):
        return None, None
    justificacion = (form.get('justificacion') or '').strip()
    if not justificacion:
        return None, (jsonify({'ok': False, 'error': 'justificacion es obligatoria para el bypass'}), 400)
    return justificacion, None


def _advertencia(res_eval):
    """Dict de advertencia para incluir en la respuesta ok (o None si no hay)."""
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {'motivo': res_eval.motivo, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma}
    return None


def _aplicar_modo_global(res_eval: EvaluacionResult) -> EvaluacionResult:
    """Ajusta el resultado del motor según el modo global configurado en BD."""
    modo = ConfiguracionSistema.get('motor.modo_operacion', 'BLOQUEAR')
    if modo == 'INACTIVO':
        return PERMITIDO
    if modo == 'SOLO_ADVERTIR' and res_eval.nivel == 'BLOQUEAR':
        return EvaluacionResult(
            permitido=True, nivel='ADVERTIR',
            variables_trigger=res_eval.variables_trigger,
            norma_compilada=res_eval.norma_compilada,
            url_norma=res_eval.url_norma,
            motivo=res_eval.motivo,
        )
    return res_eval


def _evaluar(accion: str, expediente, *, objeto) -> EvaluacionResult:
    """Punto único de llamada al motor desde api_bc.py — aplica el modo global."""
    return _aplicar_modo_global(evaluar_multi(accion, expediente, objeto=objeto))


def _res_error(res):
    """Traduce ResultadoMutacion de error a respuesta HTTP 422."""
    return jsonify({'ok': False, 'error': res.error}), 422


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

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    tipos_a_crear = []
    for tid in tipo_ids:
        try:
            tid_int = int(tid)
        except (ValueError, TypeError):
            return jsonify({'ok': False, 'error': f'Tipo de solicitud inválido: {tid}'}), 400
        tipo = TipoSolicitud.query.get(tid_int)
        if not tipo:
            return jsonify({'ok': False, 'error': f'Tipo de solicitud {tid_int} no encontrado'}), 404
        tipos_a_crear.append(tipo)

    res = svc.crear_solicitud(expediente, tipos_a_crear, entidad_id, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True, 'ids': res.ids})


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

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.crear_fase(sol, tipo_fase, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True, 'id': res.ids[0], 'advertencia': res.advertencia})


_CODIGOS_TRASLADO = frozenset({'CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR'})
_FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS = frozenset({'RESOLUCION', 'AAU_AAUS_INTEGRADA'})


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

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.crear_tramite(fase, tipo_tramite, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True, 'id': res.ids[0], 'advertencia': res.advertencia})


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

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.crear_tarea(tramite, tipo_tarea, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True, 'id': res.ids[0], 'advertencia': res.advertencia})


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

    res = svc.editar_solicitud(sol, observaciones=request.form.get('observaciones'))
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/fase/<int:fase_id>/editar', methods=['POST'])
@login_required
def editar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    doc_resultado_raw = request.form.get('documento_resultado_id')
    nuevo_doc_resultado_id = int(doc_resultado_raw) if doc_resultado_raw else None
    resultado_id = request.form.get('resultado_fase_id')
    resultado_fase_id = int(resultado_id) if resultado_id else None

    res = svc.editar_fase(fase, resultado_fase_id=resultado_fase_id,
                          documento_resultado_id=nuevo_doc_resultado_id,
                          observaciones=request.form.get('observaciones'))
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/tramite/<int:tram_id>/editar', methods=['POST'])
@login_required
def editar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    res = svc.editar_tramite(tramite, observaciones=request.form.get('observaciones'))
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/tarea/<int:tarea_id>/editar', methods=['POST'])
@login_required
def editar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    consumidos_raw = request.form.getlist('documentos_consumidos_ids')
    if len(consumidos_raw) == 1 and ',' in consumidos_raw[0]:
        consumidos_raw = consumidos_raw[0].split(',')
    ids_consumidos = [int(x) for x in consumidos_raw if x.strip()]

    doc_producido_raw = request.form.get('documento_producido_id') or None
    id_producido = int(doc_producido_raw) if doc_producido_raw else None

    res = svc.editar_tarea(tarea, documentos_consumidos_ids=ids_consumidos,
                           documento_producido_id=id_producido,
                           notas=request.form.get('notas'))
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


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

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.borrar_solicitud(sol, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/fase/<int:fase_id>/borrar', methods=['POST'])
@login_required
def borrar_fase(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.borrar_fase(fase, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/tramite/<int:tram_id>/borrar', methods=['POST'])
@login_required
def borrar_tramite(tram_id):
    tramite = Tramite.query.get_or_404(tram_id)
    resultado = verificar_acceso_expediente(tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.borrar_tramite(tramite, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
    return jsonify({'ok': True})


@bp.route('/tarea/<int:tarea_id>/borrar', methods=['POST'])
@login_required
def borrar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    res = svc.borrar_tarea(tarea, justificacion=justificacion)
    if res.bloqueo:
        return _bloqueo(res.bloqueo)
    if not res.ok:
        return _res_error(res)
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
        'traslado_titular_vencido': _traslado_titular_vencido(oe),
    }


def _traslado_titular_vencido(oe) -> bool:
    """True si el CONSULTA_TRASLADO_TITULAR más reciente del organismo tiene plazo VENCIDO.

    Llamada con variables={} para evitar recursión en _compilar_variables (#475).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    from app.models.tramites import Tramite as _Tramite
    from app.models.tipos_tramites import TipoTramite
    from app.services import plazos

    vinculo = (
        TramiteOrganismo.query
        .join(_Tramite, TramiteOrganismo.tramite_id == _Tramite.id)
        .join(TipoTramite, _Tramite.tipo_tramite_id == TipoTramite.id)
        .filter(
            TramiteOrganismo.organismo_expediente_id == oe.id,
            TipoTramite.codigo == 'CONSULTA_TRASLADO_TITULAR',
        )
        .order_by(TramiteOrganismo.tramite_id.desc())
        .first()
    )
    if vinculo is None:
        return False
    ep = plazos.obtener_estado_plazo(vinculo.tramite, 'TRAMITE', variables={})
    return ep.estado == 'VENCIDO'


# ============================================
# ENDPOINT — crear trámite de traslado (#471)
# ============================================

@bp.route('/fase/<int:fase_id>/consultas/traslado/nuevo', methods=['POST'])
@login_required
def crear_traslado(fase_id):
    """Crea un trámite CONSULTA_TRASLADO_* y lo vincula al OrganismoExpediente.

    form:
        organismo_expediente_id  int   Registro OrganismoExpediente destino
        tipo                     str   'ORGANISMO' | 'TITULAR'
    """
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403
    return _ejecutar_crear_traslado(fase, request.form)


def _ejecutar_crear_traslado(fase, form):
    """Núcleo de crear_traslado, separado para facilitar tests."""
    expediente = fase.solicitud.expediente

    tipo = form.get('tipo', '').upper()
    if tipo not in ('ORGANISMO', 'TITULAR'):
        return jsonify({'ok': False, 'error': "tipo debe ser 'ORGANISMO' o 'TITULAR'"}), 400

    oe_id = form.get('organismo_expediente_id', type=int)
    if not oe_id:
        return jsonify({'ok': False, 'error': 'organismo_expediente_id es obligatorio'}), 400

    oe = OrganismoExpediente.query.get(oe_id)
    if not oe or oe.expediente_id != expediente.id:
        return jsonify({'ok': False, 'error': 'Organismo no encontrado en el expediente'}), 404

    codigo = f'CONSULTA_TRASLADO_{tipo}'
    try:
        tipo_tramite = TipoTramite.query.filter_by(codigo=codigo).first()
        if tipo_tramite is None:
            log.warning('crear_traslado: TipoTramite %s no encontrado en catálogo', codigo)
            return jsonify({'ok': False, 'error': f'Tipo de trámite {codigo} no configurado'}), 500
    except (OperationalError, ProgrammingError):
        log.warning('crear_traslado: tabla tipos_tramites no disponible')
        return jsonify({'ok': False, 'error': 'Error de configuración del catálogo'}), 500

    justificacion, err = _leer_bypass(form)
    if err:
        return err

    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'fase': fase, 'tipo_tramite': tipo_tramite,
                                    'organismo_expediente': oe})
        if not res_eval.permitido:
            return _bloqueo(res_eval)
    else:
        res_eval = PERMITIDO

    try:
        tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
        db.session.add(tramite)
        db.session.flush()
        db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))

        if justificacion:
            sujeto = build_sujeto(expediente, {'fase': fase, 'tipo_tramite': tipo_tramite})
            bitacora_svc.registrar(
                current_user.id, 'CREAR', 'tramites', tramite.id,
                detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
            )

        db.session.commit()
        return jsonify({'ok': True, 'id': tramite.id, 'advertencia': _advertencia(res_eval)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


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


# ============================================
# HELPERS — acción en bloque enviar consultas (#462)
# ============================================

def _calcular_plazo_consulta(expediente, solicitud) -> int:
    """30 días general; 15 si AAC pura + AAP previa favorable (art. 131.1 párr. 2 RD 1955/2000)."""
    if not (solicitud.contiene_tipo('AAC')
            and not solicitud.contiene_tipo('AAP')
            and not solicitud.contiene_tipo('DUP')):
        return 30
    for sol in expediente.solicitudes:
        if sol is solicitud:
            continue
        if not sol.contiene_tipo('AAP'):
            continue
        for fase_sol in sol.fases:
            if (fase_sol.tipo_fase
                    and fase_sol.tipo_fase.es_finalizadora
                    and fase_sol.finalizada
                    and fase_sol.resultado_fase
                    and fase_sol.resultado_fase.codigo in RESULTADO_FASE_FAVORABLE_CODIGOS):
                return 15
    return 30


# ============================================
# ENDPOINT — acción en bloque «Enviar consultas» (#462)
# ============================================

@bp.route('/fase/<int:fase_id>/consultas/enviar', methods=['POST'])
@login_required
def enviar_consultas(fase_id):
    fase = Fase.query.get_or_404(fase_id)
    resultado = verificar_acceso_expediente(fase.solicitud.expediente, 'editar')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    expediente = fase.solicitud.expediente
    solicitud = fase.solicitud

    try:
        tipo_tramite = TipoTramite.query.filter_by(codigo='CONSULTA_SEPARATA').first()
        if tipo_tramite is None:
            log.warning('enviar_consultas: TipoTramite CONSULTA_SEPARATA no encontrado en catálogo')
            return jsonify({'ok': False, 'error': 'Tipo de trámite CONSULTA_SEPARATA no configurado'}), 500
    except (OperationalError, ProgrammingError):
        log.warning('enviar_consultas: tabla tipos_tramites no disponible')
        return jsonify({'ok': False, 'error': 'Error de configuración del catálogo'}), 500

    justificacion, err = _leer_bypass(request.form)
    if err:
        return err

    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente, objeto={'fase': fase, 'tipo_tramite': tipo_tramite})
        if not res_eval.permitido:
            return _bloqueo(res_eval)
    else:
        res_eval = PERMITIDO

    pendientes = [
        oe for oe in expediente.organismos
        if oe.via == 'consulta' and oe.estado == 'pendiente'
    ]

    plazo = _calcular_plazo_consulta(expediente, solicitud)
    objeto_sujeto = {'fase': fase, 'tipo_tramite': tipo_tramite}

    try:
        ids = []
        for oe in pendientes:
            tramite = Tramite(fase_id=fase_id, tipo_tramite_id=tipo_tramite.id)
            db.session.add(tramite)
            db.session.flush()
            db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
            oe.estado = 'separata_enviada'
            oe.plazo_legal_dias = plazo
            ids.append(tramite.id)

            if justificacion:
                sujeto = build_sujeto(expediente, objeto_sujeto)
                bitacora_svc.registrar(
                    current_user.id, 'CREAR', 'tramites', tramite.id,
                    detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
                )

        db.session.commit()
        return jsonify({'ok': True, 'ids': ids, 'advertencia': _advertencia(res_eval)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

