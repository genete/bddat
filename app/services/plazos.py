"""
Servicio de plazos administrativos — BDDAT.

Calcula el estado del plazo legal asociado a un elemento ESFTT y devuelve un
EstadoPlazo.

Arquitectura (DISEÑO_FECHAS_PLAZOS.md §4):
    ContextAssembler llama a obtener_estado_plazo() para poblar las variables
    'estado_plazo' y 'efecto_plazo' que el motor agnóstico evalúa con operadores
    estándar (EQ/IN/etc.). El motor no conoce este servicio.

Dos niveles, no cuatro (#788):
    Solo la Solicitud y la Tarea portan fecha administrativa —la primera por
    `documento_solicitud_id`, la segunda por `documentos_tarea` (ADR-010)—, así
    que solo ellas pueden tener plazo. La Fase y el Trámite son taxonomía ESFTT,
    no figuras jurídicas: los plazos legales se enganchan a actos (presentar,
    notificar, publicar, esperar) y los actos son solicitudes y tareas. La firma
    sigue aceptando los cuatro literales —los consumidores llaman por
    duck-typing— pero FASE y TRAMITE devuelven siempre SIN_PLAZO, sin tocar BD:
    `_SEGMENTOS_CAMINO` no los conoce y el camino no se puede compilar.

Lógica real (#172, identificación reescrita en #785):
    1. Compila el camino SFTT del elemento y busca en catalogo_plazos la entrada
       cuyo patrón `camino` casa con él (comodín ANY, matcher de operadores.py).
    2. Resuelve campo_fecha JSONB → Documento.fecha_administrativa.
    3. Calcula fecha_limite con calcular_fecha_fin() (art. 30 LPACAP).
    4. Deriva estado según condiciones de §2.4 (umbral 5 días hábiles).

Identificación estructural (#785):
    El catálogo se identifica por camino, no por el literal del tipo hoja: los
    consumidores no tienen que inyectar variables que reexpongan la posición del
    elemento en el árbol. Por eso obtener_estado_plazo() da un resultado correcto
    sin `ctx` ni `variables` siempre que las entradas candidatas no tengan
    condiciones de supuesto legal — el caso de todas las de ESPERAR_PLAZO.

Suspensiones (#173, corregidas en #788):
    _obtener_suspensiones() recibe la SOLICITUD y recorre solicitud → fases →
    trámites buscando causas del art. 22 LPACAP. No usa tabla propia. El objeto
    de la suspensión lo fija el propio precepto: «el plazo máximo legal para
    resolver un procedimiento y notificar la resolución», que es el plazo de la
    solicitud y ninguno más. Por eso obtener_estado_plazo() solo la invoca en ese
    nivel — explícito, no por recorrido que salga vacío.
"""
from __future__ import annotations

import calendar
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)

UMBRAL_ALERTA = 5  # días hábiles (DISEÑO_FECHAS_PLAZOS.md §2.4)

_TIPO_ID_CAMPO = {
    'SOLICITUD': 'tipo_solicitud_id',
    'FASE':      'tipo_fase_id',
    'TRAMITE':   'tipo_tramite_id',
    'TAREA':     'tipo_tarea_id',
}

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
# Solo los dos niveles que portan fecha (#788). Los tres diccionarios de arriba
# SÍ conservan sus entradas de FASE y TRAMITE: no son niveles de fila, los usa
# compilar_camino para construir los segmentos de ascendencia del camino de 5
# segmentos de una tarea.
_SEGMENTOS_CAMINO = {'SOLICITUD': 2, 'TAREA': 5}

# ---------------------------------------------------------------------------
# Suspensiones — constantes de inferencia (art. 22 LPACAP, #173)
# ---------------------------------------------------------------------------

# Trámites que inician una suspensión del plazo de la solicitud.
#
# Lista cerrada, como la del art. 22. No están —y no deben estar— la información
# pública ni los traslados al peticionario (arts. 126 / 127.3): son instrucción
# ordinaria, corren DENTRO del plazo y lo consumen. Son justo los que lo aprietan.
_TRAMITES_SUSPENSION = frozenset({
    'REQUERIMIENTO_SUBSANACION',   # art. 22.1.a — subsanación al interesado
    'SOLICITUD_INFORME',           # art. 22.1.d — informe preceptivo a organismo
    'CONSULTA_SEPARATA',           # art. 22.1.d — separata a organismo en consultas
    'SOLICITUD_COMPATIBILIDAD',    # art. 22.1.d — EIA preceptiva a Medio Ambiente
})

# Para trámites sin ANALIZAR propio, el trámite hermano que cierra la suspensión
_TRAMITES_CIERRE = {
    'SOLICITUD_INFORME': frozenset({
        'RECEPCION_INFORME', 'RECEPCION_INFORME_VINCULANTE',
    }),
    'SOLICITUD_COMPATIBILIDAD': frozenset({
        'RECEPCION_DICTAMEN', 'RECEPCION_FIGURA',
    }),
}


@dataclass
class EstadoPlazo:
    estado: str                    # 'SIN_PLAZO' | 'EN_PLAZO' | 'PROXIMO_VENCER' | 'VENCIDO'
    efecto: str                    # 'NINGUNO' | 'SILENCIO_ESTIMATORIO' | 'RESPONSABILIDAD_DISCIPLINARIA'
                                   # | 'SILENCIO_DESESTIMATORIO' | 'CADUCIDAD_PROCEDIMIENTO'
                                   # | 'PERDIDA_TRAMITE' | 'APERTURA_RECURSO'
                                   # | 'PRESCRIPCION_CONDICIONADO' | 'CONFORMIDAD_PRESUNTA'
                                   # | 'SIN_EFECTO_AUTOMATICO'
    fecha_limite: Optional[date]   # None si SIN_PLAZO
    dias_restantes: Optional[int]  # None si SIN_PLAZO; negativo si VENCIDO


_SIN_PLAZO = EstadoPlazo(
    estado='SIN_PLAZO',
    efecto='NINGUNO',
    fecha_limite=None,
    dias_restantes=None,
)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def obtener_estado_plazo(
    elemento,
    tipo_elemento: str,
    ctx=None,
    variables=None,
) -> EstadoPlazo:
    """
    Devuelve el estado del plazo legal asociado a un elemento ESFTT.

    Args:
        elemento:      Instancia ORM del elemento evaluado.
                       None o dict → SIN_PLAZO sin consultar BD.
        tipo_elemento: 'SOLICITUD' | 'TAREA' son los niveles con plazo posible.
                       'FASE' y 'TRAMITE' se aceptan y devuelven SIN_PLAZO (#788):
                       los consumidores despachan por duck-typing y no les toca
                       saber qué niveles portan fecha.
        ctx:           ExpedienteContext. Construye variables internamente
                       (excluyendo estado_plazo/efecto_plazo para evitar recursión).
        variables:     Dict de variables pre-construido. Tiene precedencia sobre ctx.
                       Sin ctx ni variables → dict vacío (solo entradas sin condiciones).
    """
    if elemento is None or isinstance(elemento, dict):
        return _SIN_PLAZO

    if _get_tipo_elemento_codigo(elemento, tipo_elemento) is None:
        return _SIN_PLAZO

    if variables is not None:
        variables_dict = variables
    elif ctx is not None:
        from app.services.assembler import _compilar_variables
        variables_dict = _compilar_variables(
            ctx, excluir={'estado_plazo', 'efecto_plazo'}
        )
    else:
        variables_dict = {}

    catalogo = _seleccionar_catalogo(elemento, tipo_elemento, variables_dict)

    if catalogo is None:
        return _SIN_PLAZO

    fecha_acto = _resolver_campo_fecha(elemento, catalogo.campo_fecha or {})
    if fecha_acto is None:
        return _SIN_PLAZO

    hoy = _hoy()
    margen_dias = max(catalogo.plazo_valor * 60, 400)
    inhabiles = _obtener_inhabiles_bd(fecha_acto, hoy + timedelta(days=margen_dias))

    # Art. 22 LPACAP suspende «el plazo máximo legal para resolver un
    # procedimiento y notificar la resolución» — el de la solicitud, y solo ese.
    # Los plazos de nivel TAREA son de un tercero (organismo, DGPEM), del
    # interesado (art. 68.1) o períodos que han de transcurrir: nada que
    # suspender (#788).
    suspensiones = _obtener_suspensiones(elemento) if tipo_elemento == 'SOLICITUD' else []
    fecha_limite = _aplicar_suspensiones(
        calcular_fecha_fin(fecha_acto, catalogo.plazo_valor, catalogo.plazo_unidad, inhabiles),
        suspensiones,
        inhabiles,
    )

    efecto = catalogo.efecto_plazo.codigo if catalogo.efecto_plazo else 'SIN_EFECTO_AUTOMATICO'

    if hoy > fecha_limite:
        dias = -_dias_habiles_entre(fecha_limite + timedelta(days=1), hoy, inhabiles)
        return EstadoPlazo(estado='VENCIDO', efecto=efecto,
                           fecha_limite=fecha_limite, dias_restantes=dias)

    dias = _dias_habiles_entre(hoy, fecha_limite, inhabiles)
    if dias <= UMBRAL_ALERTA:
        return EstadoPlazo(estado='PROXIMO_VENCER', efecto=efecto,
                           fecha_limite=fecha_limite, dias_restantes=dias)

    return EstadoPlazo(estado='EN_PLAZO', efecto=efecto,
                       fecha_limite=fecha_limite, dias_restantes=dias)


def obtener_estado_plazo_espera(tramite) -> EstadoPlazo:
    """Estado del plazo de espera de un trámite, evaluado en su tarea ESPERAR_PLAZO.

    El plazo que un consumidor llama «el plazo del trámite» —los 15 días del
    traslado al titular, los 30 de la separata— es en realidad el de su tarea de
    espera: es ahí donde está el documento que fija la fecha de inicio, y desde
    #788 es ahí donde está también la fila del catálogo.

    Vive aquí y no duplicado en cada consumidor para que «bajar del trámite a su
    tarea» sea una decisión de este servicio, no un detalle repetido fuera.
    """
    if tramite is None:
        return _SIN_PLAZO
    espera = _tarea_de_tipo(tramite, 'ESPERAR_PLAZO')
    if espera is None:
        return _SIN_PLAZO
    # variables={} evita recursión en _compilar_variables (#475): las entradas de
    # ESPERAR_PLAZO con condiciones son las de CONSULTA_SEPARATA, y su fallback
    # sin condiciones da el mismo resultado que el contexto completo.
    return obtener_estado_plazo(espera, 'TAREA', variables={})


# ---------------------------------------------------------------------------
# Cómputo de plazos — funciones puras (testables sin BD)
# ---------------------------------------------------------------------------

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
# Utilidades internas
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


def _evaluar_condiciones_plazo(condiciones, variables: dict) -> bool:
    """
    Evalúa lista de condiciones con AND implícito.

    Sin condiciones → siempre True.
    Variable ausente en dict → False con warning (decisión F de IMPLEMENTACION_341.md).
    Usa _OPERADORES de operadores.py (S1) — no depende de motor_reglas.
    """
    from app.services.operadores import _OPERADORES

    for cond in sorted(condiciones, key=lambda c: c.orden):
        nombre = cond.variable.nombre
        if nombre not in variables:
            log.warning('plazos: variable ausente en dict de condiciones: %s', nombre)
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


def _seleccionar_catalogo(elemento, tipo_elemento: str, variables_dict: dict):
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
      1. Prefiltro SQL por tipo_elemento + activo (el nivel acota el juego).
      2. Ordena por orden ASC, id ASC (menor orden = mayor prioridad).
      3. Descarta las entradas cuyo camino no casa con el del elemento, y las que
         declaran un `tipo_documento` que el elemento no tiene vinculado (#788).
      4. De las que casan: sin condiciones → válida inmediata; con condiciones →
         AND implícito. Devuelve la primera que pasa.

    Por qué `tipo_documento` filtra aquí y no solo al resolver la fecha: si una
    candidata se elige y luego su campo_fecha no resuelve, la función NO prueba la
    siguiente — devuelve SIN_PLAZO. Las dos esperas de un ANUNCIO_* comparten
    camino, así que sin este predicado la de menor orden ganaría para ambas y la
    otra se quedaría muda.
    """
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.condiciones_plazo import CondicionPlazo
    from app.services.operadores import camino_casa
    from sqlalchemy.exc import OperationalError, ProgrammingError

    camino_real = compilar_camino(elemento, tipo_elemento)
    if camino_real is None:
        return None

    try:
        entradas = (
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
        return None

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
        log.warning(
            'plazos: ninguna entrada de catalogo_plazos satisface condiciones '
            'para %s — se devuelve SIN_PLAZO',
            camino_real,
        )
    return None


def _get_tipo_elemento_id(elemento, tipo_elemento: str) -> Optional[int]:
    campo = _TIPO_ID_CAMPO.get(tipo_elemento)
    return getattr(elemento, campo, None) if campo else None


def _get_tipo_elemento_codigo(elemento, tipo_elemento: str) -> Optional[str]:
    rel_nombre = _TIPO_REL_CAMPO.get(tipo_elemento)
    attr_nombre = _TIPO_CODIGO_ATTR.get(tipo_elemento, 'codigo')
    if not rel_nombre:
        return None
    tipo_rel = getattr(elemento, rel_nombre, None)
    return getattr(tipo_rel, attr_nombre, None) if tipo_rel else None


def _resolver_campo_fecha(elemento, campo_fecha: dict) -> Optional[date]:
    """Resuelve campo_fecha JSONB → Documento.fecha_administrativa.

    Vocabulario cerrado desde #788 — dos ramas, una por portador de fecha:

      {'fk': 'documento_solicitud_id'}                       → Solicitud, por FK directa
      {'rol': 'CONSUMIDO'|'PRODUCIDO'[, 'tipo_documento']}   → Tarea, por vínculo (ADR-010)

    No es extensible: no hay un tercer portador de fecha al que apuntar. Lo que
    había antes —el parche que trepaba de la fase a su solicitud y la indirección
    `via_tarea_tipo` que bajaba de un trámite a su tarea— era la huella de filas
    declaradas en niveles que no llegan a ningún documento; con la fila en su
    nivel, ambas sobran.
    """
    rol = campo_fecha.get('rol')

    if rol:
        doc = _documento_por_rol(elemento, rol, campo_fecha.get('tipo_documento'))
    else:
        fk_col = campo_fecha.get('fk', '')
        rel_name = fk_col[:-3] if fk_col.endswith('_id') else fk_col
        doc = getattr(elemento, rel_name, None) if rel_name else None

    return _fecha_doc_admin(doc)


def _documento_por_rol(tarea, rol: str, tipo_documento: Optional[str] = None):
    """Documento vinculado a la tarea por rol, opcionalmente filtrado por tipo.

    `tipo_documento` desempata cuando dos tareas del mismo tipo conviven en un
    trámite y el camino no las distingue — las dos esperas de un ANUNCIO_*, donde
    la que cuenta los 30 días de exposición es la que consume el
    ANUNCIO_PUBLICADO. Es opcional a propósito: la entrada del ESPERAR_PLAZO de
    CONSULTA_SEPARATA está declarada polimórfica en `tramites_tareas_documentos`
    porque el justificante depende del canal (BANDEJA / NOTIFICA / POSTAL / SIR),
    y ahí no se puede nombrar un tipo ni hace falta — esa espera es única en su
    trámite.
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


def _hoy() -> date:
    return date.today()


def _obtener_inhabiles_bd(fecha_ini: date, fecha_fin: date) -> frozenset:
    """Carga fechas inhábiles del calendario BD en el rango dado."""
    from app.models.dias_inhabiles import DiaInhabil
    registros = DiaInhabil.query.filter(
        DiaInhabil.fecha >= fecha_ini,
        DiaInhabil.fecha <= fecha_fin,
    ).all()
    return frozenset(r.fecha for r in registros)


def _codigo_tramite(tramite) -> str:
    tipo = getattr(tramite, 'tipo_tramite', None)
    return getattr(tipo, 'codigo', '') if tipo else ''


def _tarea_de_tipo(tramite, codigo_tarea: str):
    """Primera tarea del tipo indicado en el trámite, o None."""
    for t in getattr(tramite, 'tareas', []):
        if getattr(getattr(t, 'tipo_tarea', None), 'codigo', None) == codigo_tarea:
            return t
    return None


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


def _fecha_cierre_suspension(tramite_trigger, tramites_de_su_fase: list) -> Optional[date]:
    """
    Fecha de fin de la suspensión iniciada por tramite_trigger, o None si sigue abierta.

    1. Documento producido de su propio ESPERAR_PLAZO — la respuesta que se
       esperaba. Es el caso normal: la suspensión ES ese ESPERAR_PLAZO, y sus dos
       extremos viven ahí (el consumido abre, el producido cierra).
    2. Rescate para los trámites cuyo receptor está formalizado como trámite
       aparte (SOLICITUD_INFORME → RECEPCION_INFORME, SOLICITUD_COMPATIBILIDAD →
       RECEPCION_DICTAMEN): primer consumido del ANALIZAR del primer hermano
       receptor con id mayor. Acotado a la fase del disparador (#788) — un
       RECEPCION_INFORME de otra fase cerraría una suspensión que no le toca.
    """
    esperar = _tarea_de_tipo(tramite_trigger, 'ESPERAR_PLAZO')
    if esperar:
        f = _fecha_doc_admin(getattr(esperar, 'documento_producido', None))
        if f:
            return f

    cierre_tipos = _TRAMITES_CIERRE.get(_codigo_tramite(tramite_trigger), frozenset())
    if cierre_tipos:
        for hermano in sorted(tramites_de_su_fase, key=lambda x: x.id):
            if hermano.id <= tramite_trigger.id:
                continue
            if _codigo_tramite(hermano) not in cierre_tipos:
                continue
            a = _tarea_de_tipo(hermano, 'ANALIZAR')
            if a:
                f = _fecha_doc_admin(_primer_consumido(a))
                if f:
                    return f

    return None


def _obtener_suspensiones(solicitud) -> list:
    """
    Deriva los intervalos de suspensión (art. 22 LPACAP) del plazo de la
    solicitud, recorriendo solicitud → fases → trámites. No usa tabla propia.

    Retorna la UNIÓN de los intervalos, como lista ordenada de dicts
    {'fecha_inicio': date, 'fecha_fin': date, 'abierto': bool}, donde `abierto`
    marca el bloque que llega hasta hoy porque alguna de sus causas sigue viva.

    Por qué recibe la Solicitud (#788): el art. 22 suspende «el plazo máximo legal
    para resolver un procedimiento y notificar la resolución». El objeto de la
    suspensión lo fija el precepto, y es ese plazo — que es el de la solicitud.
    Antes la función recibía «el elemento evaluado» y buscaba a su alrededor por
    duck-typing, con dos consecuencias: la Solicitud salía siempre con lista vacía
    (no tiene `.tramites`) y un Trámite se encontraba a sí mismo entre sus
    hermanos, de modo que cada CONSULTA_SEPARATA se suspendía a sí misma y su
    fecha límite retrocedía un día hábil por cada día hábil transcurrido.

    Los dos extremos de cada intervalo salen del mismo ESPERAR_PLAZO del trámite
    suspensor: el documento CONSUMIDO (el justificante de la notificación) abre y
    el PRODUCIDO (la respuesta) cierra.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    intervalos = []
    try:
        for fase in getattr(solicitud, 'fases', None) or []:
            tramites_fase = list(getattr(fase, 'tramites', None) or [])
            for tramite in tramites_fase:
                if _codigo_tramite(tramite) not in _TRAMITES_SUSPENSION:
                    continue
                esperar = _tarea_de_tipo(tramite, 'ESPERAR_PLAZO')
                if esperar is None:
                    continue
                fecha_inicio = _fecha_doc_admin(_primer_consumido(esperar))
                if not fecha_inicio:
                    continue
                fecha_fin = _fecha_cierre_suspension(tramite, tramites_fase)
                intervalos.append({
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin or _hoy(),
                    'abierto': fecha_fin is None,
                })
    except (OperationalError, ProgrammingError) as exc:
        log.warning('plazos: error cargando trámites para suspensiones (%s)', exc)
        return []

    return _fusionar_intervalos(intervalos)


def _fusionar_intervalos(intervalos: list) -> list:
    """Une los intervalos solapados o contiguos en una sola cobertura.

    Jurídicamente el reloj se para una vez: lo que el art. 22 suspende es «el
    transcurso del plazo máximo legal para resolver», en singular. Sumar por
    separado los días de un requerimiento abierto y de las separatas que están
    fuera al mismo tiempo —situación normal— contaría dos veces los días comunes.

    Cerrados y abiertos se funden JUNTOS, en una sola pasada. En dos bolsas
    separadas el solape entre un cerrado y un abierto se duplicaría: separata
    notificada el 1-feb y contestada el 1-abr, más requerimiento notificado el
    1-mar y sin contestar, dan 2 + 2 = 4 meses por bolsas cuando la verdad es la
    unión, 1-feb → hoy.

    El bloque resultante hereda `abierto` de cualquiera de sus componentes, de
    modo que su `fecha_inicio` responde a «¿desde cuándo lleva parado el plazo de
    forma continua?» — que puede ser anterior al disparador vivo más antiguo.
    """
    if not intervalos:
        return []

    fusionados = []
    for actual in sorted(intervalos, key=lambda i: (i['fecha_inicio'], i['fecha_fin'])):
        previo = fusionados[-1] if fusionados else None
        # Contiguo cuenta como solapado: entre el día de cierre de uno y el
        # siguiente natural no hay plazo que corra.
        if previo is not None and actual['fecha_inicio'] <= previo['fecha_fin'] + timedelta(days=1):
            previo['fecha_fin'] = max(previo['fecha_fin'], actual['fecha_fin'])
            previo['abierto'] = previo['abierto'] or actual['abierto']
        else:
            fusionados.append(dict(actual))

    return fusionados


def _aplicar_suspensiones(fecha_limite: date, suspensiones: list, inhabiles: frozenset) -> date:
    """Empuja la fecha límite tantos días hábiles como duren las suspensiones.

    Cada bloque se cuenta como intervalo (A, B]: los hábiles que van del día
    SIGUIENTE al acto hasta el de cierre inclusive. La norma habla de una
    diferencia, no de un recuento inclusivo — «por el tiempo que medie entre la
    notificación… y su efectivo cumplimiento» (art. 22.1.a), «entre la petición…
    y la recepción del informe» (art. 22.1.d). Del día 1 al 10 median 9 días, no
    10. Encaja además con el art. 30.3, que arranca el cómputo el día siguiente.

    Espera la lista ya fusionada por _obtener_suspensiones: aquí se suma, y sumar
    bloques solapados contaría dos veces los días comunes.
    """
    if not suspensiones:
        return fecha_limite
    dias_suspension = sum(
        _dias_habiles_entre(s['fecha_inicio'] + timedelta(days=1), s['fecha_fin'], inhabiles)
        for s in suspensiones
    )
    cursor = fecha_limite
    dias = 0
    while dias < dias_suspension:
        cursor += timedelta(days=1)
        if _es_habil(cursor, inhabiles):
            dias += 1
    return cursor
