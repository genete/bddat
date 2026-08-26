"""
consultas_organismos.py — Lógica de organismos consultados y sus consultas (#247, #462, #471, #475).

Rescatada de `app/routes/api_bc.py` al retirar aquel blueprint (#577): las rutas
HTTP estaban muertas desde #519 (murieron con las vistas BC que las llamaban),
pero la lógica de dominio no lo está — el plazo del art. 131.1 RD 1955/2000, el
traslado a organismo/titular y el envío en bloque de separatas son reglas del
trámite de consultas, no de aquella pantalla.

Reconectadas a UI real en #396 bloque 5 (ADR-042 §C): `crear_traslado` y
`enviar_consultas` devuelven `ResultadoMutacion` (mismo contrato que
`mutaciones_arbol.py`) en vez de las tuplas `(jsonify(...), status)` heredadas
literalmente del blueprint — la conversión que el docstring histórico de este
módulo dejaba pendiente "a la espera de caller vivo".
"""
import logging
from typing import Optional

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
from app.services.invariantes_esftt import check_invariante
from app.services.vocabulario_esftt import check_vocabulario_tramite
# ResultadoMutacion y sus helpers viven en mutaciones_arbol.py (ADR-016 S3b-0);
# reutilizados aquí en vez de duplicar la dataclass (#396 bloque 5: este módulo
# se alinea con el mismo contrato de retorno que el resto de mutaciones ESFTT).
from app.services.mutaciones_arbol import (
    ResultadoMutacion, _advertencia_dict, _bloquea, _registrar_advertencia,
)

log = logging.getLogger(__name__)


# ============================================
# Serialización de organismos_expediente (#247)
# ============================================

# Sentinel: distingue "no me han pasado el trámite precomputado, resuélvelo tú"
# de "ya sé que no hay ninguno" (None es un valor legítimo). Ver serializar_organismos_fase.
_SIN_PRECOMPUTAR = object()


def serializar_org_exp(oe, tramite_traslado_titular=_SIN_PRECOMPUTAR):
    """Serializa OrganismoExpediente a dict para la API.

    `tramite_traslado_titular`: ver traslado_titular_vencido() — permite evitar
    el N+1 al serializar varios organismos de una fase (serializar_organismos_fase).
    """
    return {
        'id': oe.id,
        'organismo_id': oe.organismo_id,
        'nombre_completo': oe.organismo.nombre_completo if oe.organismo else None,
        'nif': oe.organismo.nif if oe.organismo else None,
        'via': oe.via,
        'resultado': oe.resultado,
        'plazo_legal_dias': oe.plazo_legal_dias,
        'condicionados_doc_id': oe.condicionados_doc_id,
        'traslado_titular_vencido': traslado_titular_vencido(oe, tramite_traslado_titular),
    }


def _tramites_traslado_titular_recientes(organismo_expediente_ids: list) -> dict:
    """Para cada id de OrganismoExpediente, su trámite CONSULTA_TRASLADO_TITULAR
    vinculado más reciente (o ausente si no tiene). Una sola query batch — evita
    el N+1 de resolver el vínculo organismo por organismo (#396 bloque 4, ADR-042 §B).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    from app.models.tramites import Tramite as _Tramite
    from app.models.tipos_tramites import TipoTramite

    if not organismo_expediente_ids:
        return {}

    filas = (
        TramiteOrganismo.query
        .join(_Tramite, TramiteOrganismo.tramite_id == _Tramite.id)
        .join(TipoTramite, _Tramite.tipo_tramite_id == TipoTramite.id)
        .filter(
            TramiteOrganismo.organismo_expediente_id.in_(organismo_expediente_ids),
            TipoTramite.codigo == 'CONSULTA_TRASLADO_TITULAR',
        )
        .order_by(TramiteOrganismo.tramite_id.desc())
        .all()
    )
    resultado = {}
    for vinculo in filas:
        # Recorrido desc: la primera fila vista por organismo es la más reciente.
        resultado.setdefault(vinculo.organismo_expediente_id, vinculo.tramite)
    return resultado


def serializar_organismos_fase(fase) -> list:
    """Serializa todos los organismos de una fase, en bloque (#396 bloque 4, ADR-042 §B).

    Resuelve `traslado_titular_vencido` con una sola query batch en vez de una
    por organismo — es la optimización que el propio serializar_org_exp() no
    puede hacer por sí sola al servir un organismo individual.
    """
    organismos = sorted(fase.organismos, key=lambda o: o.id)
    if not organismos:
        return []
    por_organismo = _tramites_traslado_titular_recientes([oe.id for oe in organismos])
    return [
        serializar_org_exp(oe, por_organismo.get(oe.id))
        for oe in organismos
    ]


def traslado_titular_vencido(oe, tramite_traslado_titular=_SIN_PRECOMPUTAR) -> bool:
    """True si el CONSULTA_TRASLADO_TITULAR más reciente del organismo tiene plazo VENCIDO.

    El plazo se evalúa sobre la tarea ESPERAR_PLAZO del trámite, no sobre el
    trámite (#788): el nivel TRAMITE no porta fecha administrativa y dejó de
    existir en catalogo_plazos. Bajar hasta ella es navegación del árbol
    (`Tramite.tarea_espera`), no una entrada del servicio de plazos (#778).

    `tramite_traslado_titular`: si se pasa (incluido None explícito = "ya sé que
    no hay vínculo"), se usa directamente y se ahorra la query de búsqueda —
    permite a serializar_organismos_fase resolverlo en bloque para N organismos.
    Sin pasarlo, se comporta igual que siempre (una query propia).
    """
    from app.services import plazos

    if tramite_traslado_titular is _SIN_PRECOMPUTAR:
        from app.models.tramites_organismos import TramiteOrganismo
        from app.models.tramites import Tramite as _Tramite
        from app.models.tipos_tramites import TipoTramite

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
        tramite_traslado_titular = vinculo.tramite if vinculo else None

    if tramite_traslado_titular is None:
        return False
    espera = tramite_traslado_titular.tarea_espera
    if espera is None:
        return False
    # variables={} evita recursión en _compilar_variables (#475): la entrada de
    # CONSULTA_TRASLADO_TITULAR no tiene condiciones, así que da el mismo
    # resultado que el contexto completo.
    return plazos.obtener_estado_plazo_tarea(espera, variables={}).estado == 'VENCIDO'


# ============================================
# Trámite de traslado a organismo / titular (#471)
# ============================================

def _leer_justificacion_bypass(form) -> tuple[Optional[str], Optional[ResultadoMutacion]]:
    """Bypass del motor (#324/#616), forma ResultadoMutacion en vez de HTTP directo
    (`app.utils.api_respuestas.leer_bypass` devuelve una Response — no vale aquí,
    este módulo ya no jsonifica sus propios errores, #396 bloque 5).

    Devuelve (justificacion, None) o (None, ResultadoMutacion de error).
    """
    if form.get('bypass') not in ('true', '1', 'True', True):
        return None, None
    justificacion = (form.get('justificacion') or '').strip()
    if not justificacion:
        return None, ResultadoMutacion(ok=False, error='justificacion es obligatoria para el bypass')
    return justificacion, None


def crear_traslado(fase, form) -> ResultadoMutacion:
    """Crea un trámite CONSULTA_TRASLADO_* y lo vincula al OrganismoExpediente.

    form:
        organismo_expediente_id  int   Registro OrganismoExpediente destino
        tipo                     str   'ORGANISMO' | 'TITULAR'
    """
    expediente = fase.solicitud.expediente

    tipo = form.get('tipo', '').upper()
    if tipo not in ('ORGANISMO', 'TITULAR'):
        return ResultadoMutacion(ok=False, error="tipo debe ser 'ORGANISMO' o 'TITULAR'")

    # form.get(..., type=int) es API de MultiDict (request.form clásico); esta
    # función también recibe dicts planos desde la ruta JSON moderna (#396
    # bloque 5) — conversión tolerante a ambos en vez de asumir MultiDict.
    oe_id_raw = form.get('organismo_expediente_id')
    try:
        oe_id = int(oe_id_raw) if oe_id_raw is not None else None
    except (TypeError, ValueError):
        oe_id = None
    if not oe_id:
        return ResultadoMutacion(ok=False, error='organismo_expediente_id es obligatorio')

    oe = OrganismoExpediente.query.get(oe_id)
    if not oe or oe.expediente_id != expediente.id:
        return ResultadoMutacion(ok=False, error='Organismo no encontrado en el expediente')

    codigo = f'CONSULTA_TRASLADO_{tipo}'
    try:
        tipo_tramite = TipoTramite.query.filter_by(codigo=codigo).first()
        if tipo_tramite is None:
            log.warning('crear_traslado: TipoTramite %s no encontrado en catálogo', codigo)
            return ResultadoMutacion(ok=False, error=f'Tipo de trámite {codigo} no configurado')
    except (OperationalError, ProgrammingError):
        log.warning('crear_traslado: tabla tipos_tramites no disponible')
        return ResultadoMutacion(ok=False, error='Error de configuración del catálogo')

    justificacion, err = _leer_justificacion_bypass(form)
    if err:
        return err

    # Comprobaciones que mutaciones_arbol.crear_tramite ya hace y esta función,
    # heredada literal de api_bc.py, no hacía (#396 bloque 5): sellado de fase y
    # vocabulario ESFTT (ADR-037 §B) — fases_tramites no limita hoy la cardinalidad
    # de CONSULTA_TRASLADO_* (repetible por diseño, ver DISEÑO_CONSULTAS_ORGANISMOS.md
    # §6 bis), así que en la práctica actual solo el sellado puede bloquear aquí.
    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_vocab = check_vocabulario_tramite(fase, tipo_tramite)
    if _bloquea(res_vocab, justificacion):
        return ResultadoMutacion(ok=False, bloqueo=res_vocab)

    objeto_sujeto = {'fase': fase, 'tipo_tramite': tipo_tramite, 'organismo_expediente': oe}
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente, objeto=objeto_sujeto)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
    db.session.add(tramite)
    db.session.flush()
    db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))

    if justificacion:
        sujeto = build_sujeto(expediente, objeto_sujeto)
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tramites', tramite.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )
    elif res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, objeto_sujeto)
        _registrar_advertencia('CREAR', 'tramites', tramite.id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tramite.id], advertencia=_advertencia_dict(res_eval))


# ============================================
# Acción en bloque «Enviar consultas» (#462)
# ============================================

def calcular_plazo_consulta(fase) -> int:
    """Plazo legal de la separata a organismos (art. 131.1 párr. 2 RD 1955/2000):
    30 días general, 15 si la solicitud es AAC pura con una AAP previa favorable.

    Lee directamente `catalogo_plazos` (entradas 143/144, ESPERAR_PLAZO de
    CONSULTA_SEPARATA) en vez de reimplementar la norma en Python (#396 bloque 5):
    antes esta función duplicaba, a mano, exactamente las mismas dos condiciones
    (`es_solicitud_aac_pura`, `tiene_solicitud_aap_favorable`) que ya son
    variables reales del motor (`app/services/variables/calculado.py`) y ya
    condicionan esas dos filas del catálogo — la norma solo debe vivir una vez.

    No hay tarea real todavía (se llama antes de crear la separata, para
    congelar el plazo en `oe.plazo_legal_dias`): se construye un elemento TAREA
    sintético con `SimpleNamespace` — nunca tocado por la sesión de BD, mismo
    espíritu que el stub transiente de `mutaciones_arbol.crear_fase` — con el
    camino que tendría la tarea real, y se reutiliza el selector interno de
    plazos.py en vez de duplicar también la lógica de selección de entrada.
    """
    from types import SimpleNamespace

    from sqlalchemy.exc import OperationalError, ProgrammingError

    from app.models.tipos_tareas import TipoTarea
    from app.services import plazos
    from app.services.assembler import ExpedienteContext
    from app.services.variables import get_registry

    try:
        tipo_tarea = TipoTarea.query.filter_by(codigo='ESPERAR_PLAZO').first()
        tipo_tramite_separata = TipoTramite.query.filter_by(codigo='CONSULTA_SEPARATA').first()
    except (OperationalError, ProgrammingError) as exc:
        log.warning('calcular_plazo_consulta: catálogo no disponible — %s', exc)
        return 30
    if tipo_tarea is None or tipo_tramite_separata is None:
        log.warning(
            'calcular_plazo_consulta: TipoTarea ESPERAR_PLAZO o TipoTramite '
            'CONSULTA_SEPARATA no encontrado en catálogo — 30 días por defecto')
        return 30

    solicitud = fase.solicitud
    tramite_stub = SimpleNamespace(fase=fase, tipo_tramite=tipo_tramite_separata)
    tarea_stub = SimpleNamespace(tramite=tramite_stub, tipo_tarea=tipo_tarea)

    registry = get_registry()
    ctx = ExpedienteContext(solicitud.expediente, objeto=solicitud)
    variables = {
        'es_solicitud_aac_pura': registry['es_solicitud_aac_pura'](ctx),
        'tiene_solicitud_aap_favorable': registry['tiene_solicitud_aap_favorable'](ctx),
    }

    entrada = plazos._seleccionar_catalogo(tarea_stub, 'TAREA', variables)
    return entrada.plazo_valor if entrada else 30


def organismos_pendientes_separata(fase) -> list:
    """Organismos vía consulta de la fase que aún no tienen ninguna
    CONSULTA_SEPARATA vinculada — "pendiente" ya no es un resultado almacenado
    (#396 bloque 1): es estructural, no de estado. `organismo_expediente_id` es
    PK única de toda la tabla (no solo de esta fase), así que no hace falta
    cruzar también por fase_id para no mezclar rondas — cada fila pertenece a
    una sola fase por construcción.

    Pública: la usan tanto enviar_consultas() como el inspector (recuento en el
    rótulo del botón «Enviar consultas pendientes (N)», #396 bloque 5).
    """
    ids_con_separata = {
        row[0] for row in (
            db.session.query(TramiteOrganismo.organismo_expediente_id)
            .join(Tramite, TramiteOrganismo.tramite_id == Tramite.id)
            .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
            .filter(TipoTramite.codigo == 'CONSULTA_SEPARATA')
        )
    }
    return [
        oe for oe in fase.organismos
        if oe.via == 'consulta' and oe.id not in ids_con_separata
    ]


def enviar_consultas(fase, form) -> ResultadoMutacion:
    """Crea una CONSULTA_SEPARATA por cada organismo vía consulta aún pendiente.

    Idempotente por construcción: una segunda pulsación no repite las separatas
    ya creadas (organismos_pendientes_separata las excluye), así que sirve tanto
    para el primer envío como para recoger organismos nuevos de una ronda
    posterior — sin distinguir ambos casos en el front (ADR-042 §C).
    """
    expediente = fase.solicitud.expediente

    try:
        tipo_tramite = TipoTramite.query.filter_by(codigo='CONSULTA_SEPARATA').first()
        if tipo_tramite is None:
            log.warning('enviar_consultas: TipoTramite CONSULTA_SEPARATA no encontrado en catálogo')
            return ResultadoMutacion(ok=False, error='Tipo de trámite CONSULTA_SEPARATA no configurado')
    except (OperationalError, ProgrammingError):
        log.warning('enviar_consultas: tabla tipos_tramites no disponible')
        return ResultadoMutacion(ok=False, error='Error de configuración del catálogo')

    justificacion, err = _leer_justificacion_bypass(form)
    if err:
        return err

    pendientes = organismos_pendientes_separata(fase)
    if not pendientes:
        return ResultadoMutacion(ok=True, ids=[])

    # Mismas comprobaciones que mutaciones_arbol.crear_tramite (#396 bloque 5):
    # sellado de fase y vocabulario ESFTT. Una sola vez para el lote — todos los
    # trámites que se van a crear son del mismo tipo bajo la misma fase.
    res_inv = check_invariante('MUTAR', 'FASE', fase.id)
    if res_inv:
        return ResultadoMutacion(ok=False, bloqueo=res_inv)

    res_vocab = check_vocabulario_tramite(fase, tipo_tramite)
    if _bloquea(res_vocab, justificacion):
        return ResultadoMutacion(ok=False, bloqueo=res_vocab)

    objeto_sujeto = {'fase': fase, 'tipo_tramite': tipo_tramite}
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente, objeto=objeto_sujeto)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    # El plazo legal se calcula una vez para todo el lote (mismo art. 131.1,
    # misma solicitud) y se congela en cada organismo — es el valor del oficio
    # en el momento de enviarlo, no se recalcula después (DISEÑO_CONSULTAS_
    # ORGANISMOS.md §7).
    plazo = calcular_plazo_consulta(fase)

    ids = []
    for oe in pendientes:
        tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
        db.session.add(tramite)
        db.session.flush()
        db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
        oe.plazo_legal_dias = plazo
        ids.append(tramite.id)

        if justificacion:
            sujeto = build_sujeto(expediente, objeto_sujeto)
            bitacora_svc.registrar(
                current_user.id, 'CREAR', 'tramites', tramite.id,
                detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
            )

    if not justificacion and res_eval.nivel == 'ADVERTIR':
        sujeto = build_sujeto(expediente, objeto_sujeto)
        # Una advertencia por lote, no por organismo — el motivo es el mismo
        # (crear CONSULTA_SEPARATA bajo esta fase), no algo específico de cada oe.
        for tramite_id in ids:
            _registrar_advertencia('CREAR', 'tramites', tramite_id, sujeto, res_eval)

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=ids, advertencia=_advertencia_dict(res_eval))
