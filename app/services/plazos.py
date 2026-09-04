"""
Servicio de plazos administrativos — BDDAT.

Un plazo es UNA SOLA MEDIDA (ADR-041, #778). Dada la entrada de catalogo_plazos
y el elemento donde se aplica, produce cuatro fechas:

    disparo       fecha administrativa del documento que la entrada señala como
                  origen del cómputo (campo_fecha)
    vencimiento   disparo + valor del plazo, computado según el art. 30 LPACAP
    cumplimiento  fecha administrativa del documento que acredita el
                  cumplimiento (campo_fecha_cumplimiento), si existe
    parada        la primera de tres: cumplimiento, vencimiento u hoy

La cuarta es la que resuelve todo, y sus tres candidatas significan cosas
distintas: gana el cumplimiento → llegó lo que se esperaba; gana el vencimiento →
se agotó el plazo concedido y el procedimiento prosigue (art. 22.1.d in fine);
gana hoy → el plazo sigue corriendo.

Dos entradas, no cuatro literales de nivel (#788, ADR-041 §G):

    obtener_estado_plazo_tarea(tarea)          el plazo de una tarea
    obtener_estado_plazo_solicitud(solicitud)  el plazo de la solicitud, que ya
                                               incluye la suspensión

Solo la Solicitud y la Tarea portan fecha administrativa —la primera por
`documento_solicitud_id`, la segunda por `documentos_tarea` (ADR-010)—, así que
solo ellas pueden tener plazo. La Fase y el Trámite son taxonomía ESFTT, no
figuras jurídicas: los plazos legales se enganchan a actos, y los actos son
solicitudes y tareas. Una función llamada «plazo de un trámite» reintroduciría
por la puerta de atrás el nivel que #788 eliminó, así que no existe: bajar de un
trámite a su tarea de espera es navegación del árbol (`Tramite.tarea_espera`).

La suspensión no es un mecanismo aparte (#778):
    Es el plazo de un tercero visto desde la solicitud, y la propia ley lo dice
    al fijar cuándo termina —art. 22.1.a: «por el tiempo que medie entre la
    notificación del requerimiento y su efectivo cumplimiento por el
    destinatario, o, en su defecto, por el del plazo concedido»—, que es el menor
    de los dos: exactamente la parada. El plazo de la solicitud se mide como
    cualquier otro; luego se recorren sus tareas, se retienen las que tienen
    entrada marcada como suspensora, cada una aporta el intervalo
    [disparo, parada], los solapados se funden (el art. 22 suspende «el
    transcurso del plazo máximo legal para resolver», en singular: un reloj no se
    para dos veces) y los días hábiles de la unión empujan el vencimiento.

    Consecuencia directa: el tope existe por construcción. Ninguna suspensión
    puede crecer sin límite, porque su parada nunca pasa del vencimiento. Antes
    de #778 el cálculo de suspensiones no consultaba el catálogo en ningún
    momento —tenía la lista de trámites escrita en el código— y por eso, sin
    respuesta del interesado, el cierre se quedaba en «hoy» y se recalculaba cada
    día: la fecha límite se alejaba un día por cada día que pasaba y el
    expediente no vencía nunca.

Qué suspende es dato del catálogo, no una lista en el código:
    Que la petición de un informe preceptivo suspenda el plazo para resolver
    cambia cuando cambia la ley y es citable a artículo concreto (art. 22.1.a y
    22.1.d) — dato normativo, y va donde ya viven el valor del plazo y su efecto
    (test de ADR-037). Corolario buscado: un plazo sin entrada en el catálogo no
    suspende nada.

    Tampoco hay topes escritos aquí. El art. 22.1.d añade que la suspensión «no
    podrá exceder en ningún caso de tres meses», límite que en la práctica no
    muerde —todos los plazos de informe que BDDAT maneja son de tres meses o
    menos— y que se vigila al dar de alta la entrada, no en el cómputo.

Identificación estructural (#785):
    El catálogo se identifica por camino SFTT, no por el literal del tipo hoja:
    los consumidores no tienen que inyectar variables que reexpongan la posición
    del elemento en el árbol. Por eso el resultado es correcto sin `ctx` ni
    `variables` siempre que las entradas candidatas no tengan condiciones de
    supuesto legal — el caso de todas las de ESPERAR_PLAZO.

plazo_valor=0 no es un caso soportado (#789):
    ESTRUCTURA_FTT.md usa la notación EP(0) para varios ESPERAR_PLAZO sin plazo
    legal (dictamen/propuesta/informe vinculante de AAU_AAUS_INTEGRADA,
    SOLICITUD_FIGURA, la primera espera de los ANUNCIO_*). Se decidió a
    propósito NO traducir esa convención en una fila de catalogo_plazos con
    plazo_valor=0: la ausencia de fila ya produce SIN_PLAZO, que en
    estado_dominio.py escala a PENDIENTE_TRAMITAR — rojo permanente hasta que
    llega el documento. Sin plazo cierto no hay fecha en la que el sistema
    pueda escalar la alerta por sí solo, así que el rojo persistente (en vez
    de un gris de "espera pasiva") es la señal correcta para que el
    tramitador no pierda de vista el seguimiento. `calcular_fecha_fin()` no
    contempla plazo_valor=0 y no debe empezar a hacerlo por esto.
"""
from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)

UMBRAL_ALERTA = 5  # días hábiles (DISEÑO_FECHAS_PLAZOS.md §2.4)

# Estados corriendo: el plazo aún no se ha cumplido ni agotado. Sirve también
# para decidir si una suspensión sigue viva — no hace falta guardar ningún flag
# «abierto», la propia medida lo dice (ADR-041 §Consecuencias).
_CORRIENDO = ('EN_PLAZO', 'PROXIMO_VENCER')

# Relación ORM que expone el identificador estable del tipo (sin FK BD)
_TIPO_REL_CAMPO = {
    'SOLICITUD': 'tipo_solicitud',
    'FASE':      'tipo_fase',
    'TRAMITE':   'tipo_tramite',
    'TAREA':     'tipo_tarea',
}

# Atributo del modelo tipo que contiene el identificador estable.
# TipoSolicitud usa 'siglas'; el resto usa 'codigo'.
_TIPO_CODIGO_ATTR = {
    'SOLICITUD': 'siglas',
    'FASE':      'codigo',
    'TRAMITE':   'codigo',
    'TAREA':     'codigo',
}

# Nº de segmentos del camino ESFTT por nivel (#785). El matching exige longitud
# idéntica, igual que en motor_reglas, así que la longitud codifica el nivel.
#
# Solo los dos niveles que portan fecha (#788). Los dos diccionarios de arriba
# SÍ conservan sus entradas de FASE y TRAMITE: no son niveles de fila, los usa
# compilar_camino para construir los segmentos de ascendencia del camino de 5
# segmentos de una tarea.
_SEGMENTOS_CAMINO = {'SOLICITUD': 2, 'TAREA': 5}


@dataclass
class EstadoPlazo:
    estado: str                        # 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER'
                                       # | 'VENCIDO' | 'CUMPLIDO'
    efecto: str                        # 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA'
                                       # | 'SILENCIO_DESESTIMATORIO' | 'CADUCIDAD_PROCEDIMIENTO'
                                       # | 'TENER_POR_DESISTIDO' | 'PERDIDA_TRAMITE' | 'APERTURA_RECURSO'
                                       # | 'PRESCRIPCION_CONDICIONADO' | 'CONFORMIDAD_PRESUNTA'
                                       # | 'SIN_EFECTO_AUTOMATICO'
    fecha_limite: Optional[date]       # el VENCIMIENTO (nombre histórico, §3.5 del
                                       # diseño): último día hábil dentro del plazo.
                                       # En la solicitud, ya con las suspensiones
                                       # sumadas. None si SIN_PLAZO
    dias_restantes: Optional[int]      # None si SIN_PLAZO o CUMPLIDO; negativo si VENCIDO
    fecha_disparo: Optional[date] = None
    fecha_cumplimiento: Optional[date] = None
    fecha_parada: Optional[date] = None
    plazo_valor: Optional[int] = None      # valor de la entrada de catálogo aplicada
    plazo_unidad: Optional[str] = None     # 'DIAS_HABILES' | 'DIAS_NATURALES' | 'MESES' | 'ANOS'
    norma_origen: Optional[str] = None     # cita de la entrada de catálogo aplicada
    efecto_nombre: Optional[str] = None    # nombre legible de `efecto` (EfectoPlazo.nombre)

    @property
    def cumplido_fuera_de_plazo(self) -> bool:
        """«Cumplido fuera de plazo» no es un valor del vocabulario: se lee de las
        dos fechas que el servicio ya devuelve. El vocabulario no crece por algo
        derivable sin ambigüedad (ADR-041 §C)."""
        return bool(
            self.fecha_cumplimiento and self.fecha_limite
            and self.fecha_cumplimiento > self.fecha_limite
        )


@dataclass
class EstadoPlazoSolicitud(EstadoPlazo):
    """El plazo de la solicitud, único suspendible (art. 22, #788).

    `suspendido` es dato aparte y NO un valor del estado, porque es ortogonal: un
    plazo puede estar suspendido y a la vez próximo a vencer.
    """
    suspendido: bool = False
    suspendido_desde: Optional[date] = None   # inicio del bloque fusionado que llega
                                              # a hoy; puede ser anterior a la causa
                                              # viva más antigua
    dias_suspendidos: int = 0                 # días hábiles de la unión de intervalos
    fecha_limite_sin_suspender: Optional[date] = None


@dataclass(frozen=True)
class _Medida:
    """Las cuatro fechas de un plazo. Interno: fuera se ve como EstadoPlazo."""
    disparo: date
    vencimiento: date
    cumplimiento: Optional[date]
    parada: date


_SIN_PLAZO = EstadoPlazo(
    estado='SIN_PLAZO',
    efecto='NINGUNO',
    fecha_limite=None,
    dias_restantes=None,
)

_SIN_PLAZO_SOLICITUD = EstadoPlazoSolicitud(
    estado='SIN_PLAZO',
    efecto='NINGUNO',
    fecha_limite=None,
    dias_restantes=None,
)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def obtener_estado_plazo_tarea(tarea, ctx=None, variables=None) -> EstadoPlazo:
    """
    Estado del plazo legal de una tarea.

    Args:
        tarea:     Instancia ORM de Tarea. None o dict → SIN_PLAZO sin tocar BD.
        ctx:       ExpedienteContext. Construye variables internamente
                   (excluyendo estado_plazo/efecto_plazo para evitar recursión).
        variables: Dict de variables pre-construido. Tiene precedencia sobre ctx.
                   Sin ctx ni variables → dict vacío (solo entradas sin condiciones).
    """
    if tarea is None or isinstance(tarea, dict):
        return _SIN_PLAZO
    if _get_tipo_elemento_codigo(tarea, 'TAREA') is None:
        return _SIN_PLAZO

    entrada = _seleccionar_catalogo(tarea, 'TAREA', _variables_de(ctx, variables))
    if entrada is None:
        return _SIN_PLAZO

    disparo = _resolver_campo_fecha(tarea, entrada.campo_fecha or {})
    if disparo is None:
        return _SIN_PLAZO

    hoy = _hoy()
    inhabiles = _obtener_inhabiles_bd(disparo, hoy + timedelta(days=_margen_dias([entrada])))
    medida = _medir(tarea, entrada, disparo, inhabiles, hoy)

    estado, dias = _leer_estado(medida, hoy, inhabiles)
    return EstadoPlazo(
        estado=estado,
        efecto=_efecto(entrada),
        fecha_limite=medida.vencimiento,
        dias_restantes=dias,
        fecha_disparo=medida.disparo,
        fecha_cumplimiento=medida.cumplimiento,
        fecha_parada=medida.parada,
        **_metadatos_entrada(entrada),
    )


def obtener_estado_plazo_solicitud(solicitud, ctx=None, variables=None) -> EstadoPlazoSolicitud:
    """
    Estado del plazo máximo para resolver y notificar (art. 21.3 LPACAP), ya con
    las suspensiones del art. 22 aplicadas.

    Es el único plazo suspendible: los de nivel TAREA son de un tercero
    (organismo, DGPEM), del interesado (art. 68.1) o períodos que han de
    transcurrir — nada que suspender (#788).
    """
    if solicitud is None or isinstance(solicitud, dict):
        return _SIN_PLAZO_SOLICITUD
    if _get_tipo_elemento_codigo(solicitud, 'SOLICITUD') is None:
        return _SIN_PLAZO_SOLICITUD

    entrada = _seleccionar_catalogo(solicitud, 'SOLICITUD', _variables_de(ctx, variables))
    if entrada is None:
        return _SIN_PLAZO_SOLICITUD

    disparo = _resolver_campo_fecha(solicitud, entrada.campo_fecha or {})
    if disparo is None:
        return _SIN_PLAZO_SOLICITUD

    hoy = _hoy()
    # Las causas de suspensión se identifican ANTES de cargar el calendario para
    # que el rango cubra también sus disparos: no se presupone que ninguno sea
    # anterior al de la solicitud, aunque en un expediente sano no lo sea.
    causas = _causas_suspension(solicitud)
    fecha_ini = min([disparo] + [d for _, _, d in causas])
    inhabiles = _obtener_inhabiles_bd(
        fecha_ini,
        hoy + timedelta(days=_margen_dias([entrada] + [e for _, e, _ in causas])),
    )

    bloques = _fusionar_intervalos([
        _intervalo_de(tarea, entrada_tarea, disparo_tarea, inhabiles, hoy)
        for tarea, entrada_tarea, disparo_tarea in causas
    ])
    dias_suspendidos = _dias_suspendidos(bloques, inhabiles)
    vivo = next((b for b in bloques if b['vivo']), None)

    medida = _medir(solicitud, entrada, disparo, inhabiles, hoy)
    limite = _aplicar_suspensiones(medida.vencimiento, bloques, inhabiles)
    medida_efectiva = replace(
        medida,
        vencimiento=limite,
        parada=min(d for d in (medida.cumplimiento, limite, hoy) if d is not None),
    )

    estado, dias = _leer_estado(medida_efectiva, hoy, inhabiles)
    return EstadoPlazoSolicitud(
        estado=estado,
        efecto=_efecto(entrada),
        fecha_limite=limite,
        dias_restantes=dias,
        fecha_disparo=medida_efectiva.disparo,
        fecha_cumplimiento=medida_efectiva.cumplimiento,
        fecha_parada=medida_efectiva.parada,
        suspendido=vivo is not None,
        suspendido_desde=vivo['inicio'] if vivo else None,
        dias_suspendidos=dias_suspendidos,
        fecha_limite_sin_suspender=medida.vencimiento,
        **_metadatos_entrada(entrada),
    )


# ---------------------------------------------------------------------------
# La medida — funciones puras (testables sin BD)
# ---------------------------------------------------------------------------

def _medir(elemento, entrada, disparo: date, inhabiles: frozenset, hoy: date) -> _Medida:
    """Las cuatro fechas del plazo de `elemento` según `entrada`.

    `disparo` llega ya resuelto porque el llamador lo necesita antes, para acotar
    el rango del calendario de inhábiles.
    """
    vencimiento = calcular_fecha_fin(
        disparo, entrada.plazo_valor, entrada.plazo_unidad, inhabiles
    )
    cumplimiento = _resolver_cumplimiento(elemento, entrada)
    parada = min(d for d in (cumplimiento, vencimiento, hoy) if d is not None)
    return _Medida(disparo=disparo, vencimiento=vencimiento,
                   cumplimiento=cumplimiento, parada=parada)


def _leer_estado(medida: _Medida, hoy: date, inhabiles: frozenset) -> tuple[str, Optional[int]]:
    """Estado y días restantes a partir de la medida. Cinco valores (ADR-041 §C).

    `dias_restantes` es None en CUMPLIDO: «quedan N días» ya no significa nada, y
    si llegó tarde o a tiempo se lee comparando cumplimiento con vencimiento
    (EstadoPlazo.cumplido_fuera_de_plazo).
    """
    if medida.cumplimiento is not None:
        return 'CUMPLIDO', None
    if hoy > medida.vencimiento:
        return 'VENCIDO', -_dias_habiles_entre(
            medida.vencimiento + timedelta(days=1), hoy, inhabiles
        )
    dias = _dias_habiles_entre(hoy, medida.vencimiento, inhabiles)
    return ('PROXIMO_VENCER' if dias <= UMBRAL_ALERTA else 'EN_PLAZO'), dias


def calcular_fecha_fin(
    fecha_acto: date,
    plazo_valor: int,
    plazo_unidad: str,
    inhabiles: frozenset,
) -> date:
    """
    Calcula la fecha límite (último día hábil inclusive) dado el acto y el plazo.

    Art. 30 LPACAP:
    - El cómputo empieza el día siguiente al acto (art. 30.1).
    - DIAS_HABILES: suma plazo_valor días saltando fines de semana e inhábiles.
      El último día es siempre hábil por construcción (art. 30.2).
    - DIAS_NATURALES: suma plazo_valor días naturales; si cae en inhábil,
      prorroga al primer hábil siguiente (art. 30.5).
    - MESES: mismo día ordinal en el mes de vencimiento (art. 30.4).
      Si ese día no existe → último día del mes. Prorroga si inhábil (art. 30.5).
    - ANOS: mismo día y mes en el año de vencimiento. Prorroga si inhábil (art. 30.5).

    Args:
        fecha_acto:  Fecha del acto administrativo que inicia el cómputo.
        plazo_valor: Valor numérico del plazo.
        plazo_unidad: 'DIAS_HABILES' | 'DIAS_NATURALES' | 'MESES' | 'ANOS'.
        inhabiles:   Conjunto de fechas inhábiles (festivos de calendario).
    """
    if plazo_unidad == 'DIAS_HABILES':
        cursor = fecha_acto
        dias = 0
        while dias < plazo_valor:
            cursor += timedelta(days=1)
            if _es_habil(cursor, inhabiles):
                dias += 1
        return cursor

    if plazo_unidad == 'DIAS_NATURALES':
        return _primer_habil_desde(fecha_acto + timedelta(days=plazo_valor), inhabiles)

    if plazo_unidad == 'MESES':
        total_meses = fecha_acto.month - 1 + plazo_valor
        año_dest = fecha_acto.year + total_meses // 12
        mes_dest = total_meses % 12 + 1
        dia_dest = min(fecha_acto.day, calendar.monthrange(año_dest, mes_dest)[1])
        return _primer_habil_desde(date(año_dest, mes_dest, dia_dest), inhabiles)

    if plazo_unidad == 'ANOS':
        año_dest = fecha_acto.year + plazo_valor
        dia_dest = min(fecha_acto.day, calendar.monthrange(año_dest, fecha_acto.month)[1])
        return _primer_habil_desde(date(año_dest, fecha_acto.month, dia_dest), inhabiles)

    raise ValueError(f'plazo_unidad desconocida: {plazo_unidad!r}')


# ---------------------------------------------------------------------------
# Suspensiones — la misma medida, vista desde la solicitud (art. 22 LPACAP)
# ---------------------------------------------------------------------------

def _causas_suspension(solicitud) -> list[tuple]:
    """Tareas de la solicitud cuya entrada de catálogo suspende, ya con su disparo.

    Devuelve [(tarea, entrada, disparo)]. Recorre solicitud → fases → trámites →
    tareas: el art. 22 suspende «el plazo máximo legal para resolver un
    procedimiento y notificar la resolución», que es el plazo de esta solicitud y
    ninguno más.

    Las entradas de nivel TAREA se cargan UNA vez y se pasan al matcher: si no,
    cada tarea del expediente repetiría la misma query.

    Las condiciones se evalúan con dict vacío, igual que hacía el atajo por
    trámite: las únicas entradas con condiciones son las dos de CONSULTA_SEPARATA
    y su reserva sin condiciones da el mismo resultado que el contexto completo.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    try:
        entradas = _cargar_entradas('TAREA')
        if not any(e.suspende_plazo_solicitud for e in entradas):
            return []   # ninguna fila suspende: no hay nada que recorrer

        causas = []
        for fase in getattr(solicitud, 'fases', None) or []:
            for tramite in getattr(fase, 'tramites', None) or []:
                for tarea in getattr(tramite, 'tareas', None) or []:
                    entrada = _seleccionar_catalogo(tarea, 'TAREA', {}, entradas=entradas)
                    if entrada is None or not entrada.suspende_plazo_solicitud:
                        continue
                    disparo = _resolver_campo_fecha(tarea, entrada.campo_fecha or {})
                    if disparo is None:
                        continue    # preparado pero aún no notificado: nada que suspender
                    causas.append((tarea, entrada, disparo))
        return causas
    except (OperationalError, ProgrammingError) as exc:
        log.warning('plazos: error recorriendo causas de suspensión (%s)', exc)
        return []


def _intervalo_de(tarea, entrada, disparo: date, inhabiles: frozenset, hoy: date) -> dict:
    """Intervalo suspendido que aporta una tarea suspensora: [disparo, parada].

    `vivo` sale del estado de la propia espera —sigue corriendo— y no de «no tiene
    fecha de cierre», que era lo que antes dejaba crecer la suspensión sin límite.
    """
    medida = _medir(tarea, entrada, disparo, inhabiles, hoy)
    estado, _ = _leer_estado(medida, hoy, inhabiles)
    return {'inicio': medida.disparo, 'fin': medida.parada, 'vivo': estado in _CORRIENDO}


def _fusionar_intervalos(intervalos: list) -> list:
    """Une los intervalos solapados o contiguos en una sola cobertura.

    Jurídicamente el reloj se para una vez: lo que el art. 22 suspende es «el
    transcurso del plazo máximo legal para resolver», en singular. Sumar por
    separado los días de un requerimiento vivo y de las separatas que están
    fuera al mismo tiempo —situación normal— contaría dos veces los días comunes.

    Vivos y cerrados se funden JUNTOS, en una sola pasada. En dos bolsas
    separadas el solape entre un cerrado y un vivo se duplicaría: separata
    notificada el 1-feb y contestada el 1-abr, más requerimiento notificado el
    1-mar y sin contestar, dan 2 + 2 = 4 meses por bolsas cuando la verdad es la
    unión, 1-feb → hoy.

    El bloque resultante hereda `vivo` de cualquiera de sus componentes, de modo
    que su `inicio` responde a «¿desde cuándo lleva parado el plazo de forma
    continua?» — que puede ser anterior al disparador vivo más antiguo.
    """
    if not intervalos:
        return []

    fusionados = []
    for actual in sorted(intervalos, key=lambda i: (i['inicio'], i['fin'])):
        previo = fusionados[-1] if fusionados else None
        # Contiguo cuenta como solapado: entre el día de cierre de uno y el
        # siguiente natural no hay plazo que corra.
        if previo is not None and actual['inicio'] <= previo['fin'] + timedelta(days=1):
            previo['fin'] = max(previo['fin'], actual['fin'])
            previo['vivo'] = previo['vivo'] or actual['vivo']
        else:
            fusionados.append(dict(actual))

    return fusionados


def _dias_suspendidos(bloques: list, inhabiles: frozenset) -> int:
    """Días hábiles de la unión de bloques, contados como (A, B].

    La norma habla de una diferencia, no de un recuento inclusivo — «por el
    tiempo que medie entre la notificación… y su efectivo cumplimiento»
    (art. 22.1.a), «entre la petición… y la recepción del informe» (art. 22.1.d).
    Del día 1 al 10 median 9 días, no 10. Encaja además con el art. 30.3, que
    arranca el cómputo el día siguiente.
    """
    return sum(
        _dias_habiles_entre(b['inicio'] + timedelta(days=1), b['fin'], inhabiles)
        for b in bloques
    )


def _aplicar_suspensiones(fecha_limite: date, bloques: list, inhabiles: frozenset) -> date:
    """Empuja la fecha límite tantos días hábiles como duren las suspensiones.

    Espera la lista ya fusionada: aquí se suma, y sumar bloques solapados
    contaría dos veces los días comunes.
    """
    dias_suspension = _dias_suspendidos(bloques, inhabiles)
    if dias_suspension <= 0:
        return fecha_limite
    cursor = fecha_limite
    dias = 0
    while dias < dias_suspension:
        cursor += timedelta(days=1)
        if _es_habil(cursor, inhabiles):
            dias += 1
    return cursor


# ---------------------------------------------------------------------------
# Utilidades internas — cómputo
# ---------------------------------------------------------------------------

def _es_habil(fecha: date, inhabiles: frozenset) -> bool:
    return fecha.weekday() < 5 and fecha not in inhabiles


def _primer_habil_desde(fecha: date, inhabiles: frozenset) -> date:
    """Art. 30.5: si el último día cae en inhábil, prorroga al primer hábil siguiente."""
    while not _es_habil(fecha, inhabiles):
        fecha += timedelta(days=1)
    return fecha


def _dias_habiles_entre(fecha_ini: date, fecha_fin: date, inhabiles: frozenset) -> int:
    """Cuenta días hábiles en [fecha_ini, fecha_fin] ambos inclusive."""
    if fecha_fin < fecha_ini:
        return 0
    cursor = fecha_ini
    cuenta = 0
    while cursor <= fecha_fin:
        if _es_habil(cursor, inhabiles):
            cuenta += 1
        cursor += timedelta(days=1)
    return cuenta


def _margen_dias(entradas: list) -> int:
    """Días naturales a cargar del calendario más allá de hoy.

    Generoso a propósito: un plazo largo con suspensiones puede aterrizar muy
    lejos, y un festivo no cargado desplazaría la fecha límite.
    """
    valores = [getattr(e, 'plazo_valor', 0) or 0 for e in entradas]
    return max(max(valores, default=0) * 60, 400)


# ---------------------------------------------------------------------------
# Utilidades internas — catálogo
# ---------------------------------------------------------------------------

def _variables_de(ctx, variables) -> dict:
    """Dict de variables para evaluar condiciones de catálogo.

    `variables` tiene precedencia sobre `ctx`; sin ninguno, dict vacío — solo
    aplican entonces las entradas sin condiciones.
    """
    if variables is not None:
        return variables
    if ctx is None:
        return {}
    from app.services.assembler import _compilar_variables
    return _compilar_variables(ctx, excluir={'estado_plazo', 'efecto_plazo'})


def _efecto(entrada) -> str:
    return entrada.efecto_plazo.codigo if entrada.efecto_plazo else 'SIN_EFECTO_AUTOMATICO'


def _metadatos_entrada(entrada) -> dict:
    """Campos de la entrada de catálogo aplicada, para consumidores (Context
    Builders) que necesitan citarla en un escrito sin repetir la selección
    (#776: art. 21.4 LPACAP exige informar del plazo máximo, su norma y el
    efecto del silencio)."""
    return {
        'plazo_valor': entrada.plazo_valor,
        'plazo_unidad': entrada.plazo_unidad,
        'norma_origen': entrada.norma_origen,
        'efecto_nombre': entrada.efecto_plazo.nombre if entrada.efecto_plazo else None,
    }


def _evaluar_condiciones_plazo(condiciones, variables: dict) -> bool:
    """
    Evalúa lista de condiciones con AND implícito.

    Sin condiciones → siempre True.
    Variable ausente en dict → False (decisión F de IMPLEMENTACION_341.md). Se
    registra a nivel debug: es el camino normal cuando se pregunta sin contexto
    (el recorrido de causas de suspensión pasa por aquí una vez por tarea), y la
    entrada de reserva sin condiciones recoge el caso.
    """
    from app.services.operadores import _OPERADORES

    for cond in sorted(condiciones, key=lambda c: c.orden):
        nombre = cond.variable.nombre
        if nombre not in variables:
            log.debug('plazos: variable ausente en dict de condiciones: %s', nombre)
            return False
        op_fn = _OPERADORES.get(cond.operador)
        if op_fn is None:
            log.warning('plazos: operador desconocido en condicion_plazo: %s', cond.operador)
            return False
        try:
            if not bool(op_fn(variables[nombre], cond.valor)):
                return False
        except Exception as exc:
            log.warning('plazos: error evaluando %s %s %r: %s',
                        nombre, cond.operador, cond.valor, exc)
            return False
    return True


def compilar_camino(elemento, tipo_elemento: str) -> Optional[str]:
    """
    Compila el camino SFTT concreto del elemento, de exterior a interior (#785).

    Recorre la ascendencia por el ORM —ya cargada en memoria por los eager-loads
    de los consumidores, así que no añade queries— y produce el camino real que
    se casa contra `catalogo_plazos.camino`:

        TAREA      → 'Distribucion/AAP/ANALISIS_SOLICITUD/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO'
        SOLICITUD  → 'Distribucion/AAP'

    Un tipo_elemento sin plazo posible (FASE, TRAMITE) devuelve None: no hay
    longitud de camino que le corresponda desde #788.

    Nunca produce 'ANY': eso es comodín del patrón, no de la realidad (mismo
    principio que assembler._compilar_sujeto). Un eslabón que no se puede
    resolver produce '?', que solo casa contra 'ANY' en esa posición.

    Se compila aquí y no en assembler._compilar_sujeto a propósito: aquel para
    en TRAMITE y le pasan Tareas en cuatro sitios; alargarlo rompería el matching
    de todas las reglas de 4 segmentos del motor.
    """
    n = _SEGMENTOS_CAMINO.get(tipo_elemento)
    if n is None:
        return None

    # Ascendencia: del elemento hacia fuera, luego se invierte.
    tarea = elemento if tipo_elemento == 'TAREA' else None
    tramite = elemento if tipo_elemento == 'TRAMITE' else getattr(tarea, 'tramite', None)
    fase = elemento if tipo_elemento == 'FASE' else getattr(tramite, 'fase', None)
    solicitud = elemento if tipo_elemento == 'SOLICITUD' else getattr(fase, 'solicitud', None)
    expediente = getattr(solicitud, 'expediente', None)

    tipo_exp = getattr(expediente, 'tipo_expediente', None)
    segmentos = [getattr(tipo_exp, 'tipo', None)]

    if n >= 2:
        segmentos.append(_codigo_de_tipo(solicitud, 'SOLICITUD'))
    if n >= 3:
        segmentos.append(_codigo_de_tipo(fase, 'FASE'))
    if n >= 4:
        segmentos.append(_codigo_de_tipo(tramite, 'TRAMITE'))
    if n >= 5:
        segmentos.append(_codigo_de_tipo(tarea, 'TAREA'))

    return '/'.join(_segmento(s) for s in segmentos)


def _segmento(valor) -> str:
    """Normaliza un segmento del camino.

    Cualquier cosa que no sea un string no vacío es un eslabón irresoluble y se
    marca '?', que solo casa contra 'ANY' en esa posición. Un tipo mal poblado no
    debe tumbar el cálculo del plazo (REGLAS_DESARROLLO §Servicios con catálogo).
    """
    return valor if isinstance(valor, str) and valor else '?'


def _codigo_de_tipo(elemento, tipo_elemento: str) -> Optional[str]:
    """Identificador estable del tipo de un elemento ESFTT ('siglas' o 'codigo')."""
    if elemento is None:
        return None
    return _get_tipo_elemento_codigo(elemento, tipo_elemento)


def _cargar_entradas(tipo_elemento: str) -> list:
    """Entradas activas del catálogo para un nivel, con condiciones eager-cargadas.

    Query única. La devuelve ordenada por prioridad (orden ASC, id ASC) para que
    el matcher solo tenga que quedarse con la primera que case.
    """
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.condiciones_plazo import CondicionPlazo
    from sqlalchemy.exc import OperationalError, ProgrammingError

    try:
        return (
            CatalogoPlazo.query
            .options(
                joinedload(CatalogoPlazo.condiciones).joinedload(CondicionPlazo.variable)
            )
            .filter_by(tipo_elemento=tipo_elemento, activo=True)
            .order_by(CatalogoPlazo.orden.asc(), CatalogoPlazo.id.asc())
            .all()
        )
    except (OperationalError, ProgrammingError) as exc:
        log.warning('plazos: tabla catalogo_plazos no disponible (%s) — devolviendo SIN_PLAZO', exc)
        return []


def _seleccionar_catalogo(elemento, tipo_elemento: str, variables_dict: dict, entradas=None):
    """
    Devuelve la primera entrada activa de catalogo_plazos aplicable al elemento.

    Desde #785 la identificación es estructural: se casa el camino SFTT real del
    elemento contra el patrón `camino` de cada entrada (comodín 'ANY', mismo
    matcher que el motor). Antes se filtraba por `tipo_elemento_codigo`, que no
    distinguía dos puntos distintos del árbol con el mismo literal, y la
    ascendencia se reconstruía con condiciones sobre variables — FK disfrazada.

    Las condiciones que quedan expresan supuesto legal real (tensión, tipo de
    procedimiento previo), no posición, y se siguen evaluando con AND implícito.

    Algoritmo:
      1. Carga las entradas del nivel (o reutiliza las que le pasen: el recorrido
         de causas de suspensión mide muchas tareas y no debe repetir la query).
      2. Descarta las entradas cuyo camino no casa con el del elemento, y las que
         declaran un `tipo_documento` que el elemento no tiene vinculado (#788).
      3. De las que casan: sin condiciones → válida inmediata; con condiciones →
         AND implícito. Devuelve la primera que pasa.

    Por qué `tipo_documento` filtra aquí y no solo al resolver la fecha: si una
    candidata se elige y luego su campo_fecha no resuelve, la función NO prueba la
    siguiente — el llamador devuelve SIN_PLAZO. Las dos esperas de un ANUNCIO_*
    comparten camino, así que sin este predicado la de menor orden ganaría para
    ambas y la otra se quedaría muda.
    """
    from app.services.operadores import camino_casa

    camino_real = compilar_camino(elemento, tipo_elemento)
    if camino_real is None:
        return None

    if entradas is None:
        entradas = _cargar_entradas(tipo_elemento)

    candidatas = [
        e for e in entradas
        if camino_casa(e.camino or '', camino_real)
        and _tipo_documento_presente(elemento, e.campo_fecha or {})
    ]

    for entrada in candidatas:
        if not entrada.condiciones:
            return entrada
        if _evaluar_condiciones_plazo(entrada.condiciones, variables_dict):
            return entrada

    if candidatas:
        log.debug(
            'plazos: ninguna entrada de catalogo_plazos satisface condiciones '
            'para %s — se devuelve SIN_PLAZO',
            camino_real,
        )
    return None


def _get_tipo_elemento_codigo(elemento, tipo_elemento: str) -> Optional[str]:
    rel_nombre = _TIPO_REL_CAMPO.get(tipo_elemento)
    attr_nombre = _TIPO_CODIGO_ATTR.get(tipo_elemento, 'codigo')
    if not rel_nombre:
        return None
    tipo_rel = getattr(elemento, rel_nombre, None)
    return getattr(tipo_rel, attr_nombre, None) if tipo_rel else None


# ---------------------------------------------------------------------------
# Utilidades internas — documentos que portan las fechas
# ---------------------------------------------------------------------------

def _resolver_campo_fecha(elemento, campo_fecha: dict) -> Optional[date]:
    """Resuelve un señalador JSON → Documento.fecha_administrativa.

    Vocabulario cerrado desde #788 — dos ramas, una por portador de fecha:

      {'fk': 'documento_solicitud_id'}                       → Solicitud, por FK directa
      {'fk': 'documento_cierre_id'}                          → ídem, ancla de cierre (#778)
      {'rol': 'CONSUMIDO'|'PRODUCIDO'[, 'tipo_documento']}   → Tarea, por vínculo (ADR-010)

    No es extensible: no hay un tercer portador de fecha al que apuntar. Lo que
    había antes —el parche que trepaba de la fase a su solicitud y la indirección
    `via_tarea_tipo` que bajaba de un trámite a su tarea— era la huella de filas
    declaradas en niveles que no llegan a ningún documento; con la fila en su
    nivel, ambas sobran.

    Lo usan los dos señaladores de la entrada, el del disparo (`campo_fecha`) y el
    del cumplimiento (`campo_fecha_cumplimiento`): el vocabulario es el mismo
    porque el problema es el mismo — localizar un documento desde el elemento.
    """
    if not campo_fecha:
        return None

    rol = campo_fecha.get('rol')

    if rol:
        doc = _documento_por_rol(elemento, rol, campo_fecha.get('tipo_documento'))
    else:
        fk_col = campo_fecha.get('fk', '')
        rel_name = fk_col[:-3] if fk_col.endswith('_id') else fk_col
        doc = getattr(elemento, rel_name, None) if rel_name else None

    return _fecha_doc_admin(doc)


def _resolver_cumplimiento(elemento, entrada) -> Optional[date]:
    """Fecha del documento que acredita el cumplimiento, o None.

    Sin `campo_fecha_cumplimiento` declarado el plazo nunca alcanza CUMPLIDO y se
    comporta como antes de #778: solo puede estar corriendo o vencido. Es opcional
    por un caso real, no por prudencia — en TABLON_AYUNTAMIENTOS el disparo y el
    único candidato a cierre son el mismo documento (#416), y ahí VENCIDO se lee
    como «la exposición se completó», que es lo que el tramitador necesita ver.
    """
    return _resolver_campo_fecha(elemento, entrada.campo_fecha_cumplimiento or {})


def _documento_por_rol(tarea, rol: str, tipo_documento: Optional[str] = None):
    """Documento vinculado a la tarea por rol, opcionalmente filtrado por tipo.

    `tipo_documento` desempata cuando dos tareas del mismo tipo conviven en un
    trámite y el camino no las distingue — las dos esperas de un ANUNCIO_*, donde
    la que cuenta los 30 días de exposición es la que consume el
    ANUNCIO_PUBLICADO. Es opcional a propósito: la entrada del ESPERAR_PLAZO de
    CONSULTA_SEPARATA está declarada polimórfica en `tramites_tareas_documentos`
    porque el justificante depende del canal (BANDEJA / NOTIFICA / POSTAL / SIR),
    y ahí no se puede nombrar un tipo ni hace falta — esa espera es única en su
    trámite. Para el rol PRODUCIDO tampoco hace falta nunca: el vínculo de salida
    es único por tarea.
    """
    if rol == 'PRODUCIDO':
        producido = getattr(tarea, 'documento_producido', None)
        candidatos = [producido] if producido is not None else []
    else:
        candidatos = list(getattr(tarea, 'documentos_consumidos', None) or [])

    if tipo_documento:
        candidatos = [d for d in candidatos if _codigo_tipo_doc(d) == tipo_documento]

    return candidatos[0] if candidatos else None


def _codigo_tipo_doc(doc) -> Optional[str]:
    """Código semántico del documento (tipos_documentos.codigo), o None."""
    tipo = getattr(doc, 'tipo_doc', None)
    return getattr(tipo, 'codigo', None) if tipo else None


def _tipo_documento_presente(elemento, campo_fecha: dict) -> bool:
    """Predicado de candidatura: la fila que declara un tipo exige ese vínculo.

    Sin `tipo_documento` declarado la fila es candidata siempre (comportamiento
    anterior a #788).
    """
    tipo_documento = campo_fecha.get('tipo_documento')
    if not tipo_documento:
        return True
    rol = campo_fecha.get('rol') or 'CONSUMIDO'
    return _documento_por_rol(elemento, rol, tipo_documento) is not None


def _fecha_doc_admin(doc) -> Optional[date]:
    return getattr(doc, 'fecha_administrativa', None) if doc else None


def _primer_consumido(tarea):
    """Primer documento consumido por la tarea (rol CONSUMIDO), o None.

    Las tareas con un único documento de entrada (ANALIZAR, ESPERAR_PLAZO en
    los patrones de plazo) lo exponen aquí de forma determinista por orden de
    vínculo. Ver ADR-010.
    """
    docs = getattr(tarea, 'documentos_consumidos', None) or []
    return docs[0] if docs else None


# ---------------------------------------------------------------------------
# Utilidades internas — BD
# ---------------------------------------------------------------------------

def _hoy() -> date:
    """Fecha "hoy" para el motor de plazos.

    Delega en `reloj_simulado.hoy()`, que es donde vive el candado por DEBUG
    desde #824 — el motor de plazos ya no es su único consumidor. Se conserva
    el nombre porque lo importan `generador_cert` y los tests.
    """
    from app.services.reloj_simulado import hoy
    return hoy()


def _obtener_inhabiles_bd(fecha_ini: date, fecha_fin: date) -> frozenset:
    """Carga fechas inhábiles del calendario BD en el rango dado."""
    from app.models.dias_inhabiles import DiaInhabil
    registros = DiaInhabil.query.filter(
        DiaInhabil.fecha >= fecha_ini,
        DiaInhabil.fecha <= fecha_fin,
    ).all()
    return frozenset(r.fecha for r in registros)
