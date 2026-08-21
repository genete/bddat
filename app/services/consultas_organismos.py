"""
consultas_organismos.py — Lógica de organismos consultados y sus consultas (#247, #462, #471, #475).

Rescatada de `app/routes/api_bc.py` al retirar aquel blueprint (#577): las rutas
HTTP estaban muertas desde #519 (murieron con las vistas BC que las llamaban),
pero la lógica de dominio no lo está — el plazo del art. 131.1 RD 1955/2000, el
traslado a organismo/titular y el envío en bloque de separatas son reglas del
trámite de consultas, no de aquella pantalla.

Sin consumidor HTTP hoy: quedan aquí, con sus tests, a la espera de la UI de
consultas que las reconecte.

Nota de contrato: estas funciones devuelven tuplas `(jsonify(...), status)`,
heredadas literalmente del blueprint. Es el mismo camino B de #500 que produjo
`mutaciones_arbol.py`, pero sin su paso de conversión a `ResultadoMutacion`: sin
caller vivo, rediseñar el retorno sería diseñar en abstracto. Al reconectarlas a
una UI, esa conversión es lo primero que toca.
"""
import logging

from flask import jsonify
from flask_login import current_user
from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db
from app.models.organismos_expediente import OrganismoExpediente
from app.models.tramites import Tramite
from app.models.tramites_organismos import TramiteOrganismo
from app.models.tipos_tramites import TipoTramite
from app.services.assembler import build_sujeto
from app.services import bitacora as bitacora_svc
from app.services.motor_reglas import PERMITIDO
from app.services.motor_modo_global import evaluar_con_modo_global as _evaluar
from app.services.invariantes_esftt import RESULTADO_FASE_FAVORABLE_CODIGOS
from app.utils.api_respuestas import bloqueo, leer_bypass, advertencia

log = logging.getLogger(__name__)


# ============================================
# Serialización de organismos_expediente (#247)
# ============================================

def serializar_org_exp(oe):
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
        'traslado_titular_vencido': traslado_titular_vencido(oe),
    }


def traslado_titular_vencido(oe) -> bool:
    """True si el CONSULTA_TRASLADO_TITULAR más reciente del organismo tiene plazo VENCIDO.

    El plazo se evalúa sobre la tarea ESPERAR_PLAZO del trámite, no sobre el
    trámite (#788): el nivel TRAMITE no porta fecha administrativa y dejó de
    existir en catalogo_plazos. Bajar hasta ella es navegación del árbol
    (`Tramite.tarea_espera`), no una entrada del servicio de plazos (#778).
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
    espera = vinculo.tramite.tarea_espera if vinculo.tramite else None
    if espera is None:
        return False
    # variables={} evita recursión en _compilar_variables (#475): la entrada de
    # CONSULTA_TRASLADO_TITULAR no tiene condiciones, así que da el mismo
    # resultado que el contexto completo.
    return plazos.obtener_estado_plazo_tarea(espera, variables={}).estado == 'VENCIDO'


# ============================================
# Trámite de traslado a organismo / titular (#471)
# ============================================

def crear_traslado(fase, form):
    """Crea un trámite CONSULTA_TRASLADO_* y lo vincula al OrganismoExpediente.

    form:
        organismo_expediente_id  int   Registro OrganismoExpediente destino
        tipo                     str   'ORGANISMO' | 'TITULAR'
    """
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

    justificacion, err = leer_bypass(form)
    if err:
        return err

    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'fase': fase, 'tipo_tramite': tipo_tramite,
                                    'organismo_expediente': oe})
        if not res_eval.permitido:
            return bloqueo(res_eval)
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
        return jsonify({'ok': True, 'id': tramite.id, 'advertencia': advertencia(res_eval)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================
# Acción en bloque «Enviar consultas» (#462)
# ============================================

def calcular_plazo_consulta(expediente, solicitud) -> int:
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


def enviar_consultas(fase, form):
    """Crea una CONSULTA_SEPARATA por cada organismo vía consulta aún pendiente."""
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

    justificacion, err = leer_bypass(form)
    if err:
        return err

    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente, objeto={'fase': fase, 'tipo_tramite': tipo_tramite})
        if not res_eval.permitido:
            return bloqueo(res_eval)
    else:
        res_eval = PERMITIDO

    pendientes = [
        oe for oe in expediente.organismos
        if oe.via == 'consulta' and oe.estado == 'pendiente'
    ]

    plazo = calcular_plazo_consulta(expediente, solicitud)
    objeto_sujeto = {'fase': fase, 'tipo_tramite': tipo_tramite}

    try:
        ids = []
        for oe in pendientes:
            tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
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
        return jsonify({'ok': True, 'ids': ids, 'advertencia': advertencia(res_eval)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500
