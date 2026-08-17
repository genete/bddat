"""
Servicio de plazos administrativos — BDDAT.

Calcula el estado del plazo legal asociado a un elemento ESFTT
(Solicitud, Fase, Trámite, Tarea) y devuelve un EstadoPlazo.

Arquitectura (DISEÑO_FECHAS_PLAZOS.md §4):
    ContextAssembler llama a obtener_estado_plazo() para poblar las variables
    'estado_plazo' y 'efecto_plazo' que el motor agnóstico evalúa con operadores
    estándar (EQ/IN/etc.). El motor no conoce este servicio.

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

Suspensiones (#173):
    _obtener_suspensiones() infiere intervalos de art. 22 LPACAP desde el árbol
    documental de los trámites de la Fase/Trámite evaluado. No usa tabla propia.
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
_SEGMENTOS_CAMINO = {'SOLICITUD': 2, 'FASE': 3, 'TRAMITE': 4, 'TAREA': 5}

# ---------------------------------------------------------------------------
# Suspensiones — constantes de inferencia (art. 22 LPACAP, #173)
# ---------------------------------------------------------------------------

# Trámites que inician una suspensión del plazo del elemento evaluado
_TRAMITES_SUSPENSION = frozenset({
    'REQUERIMIENTO_SUBSANACION',   # art. 22.1.a — subsanación al interesado
    'SOLICITUD_INFORME',           # art. 22.1.b — informe preceptivo a organismo
    'CONSULTA_SEPARATA',           # art. 22.1.b — separata a organismo en consultas
    'SOLICITUD_COMPATIBILIDAD',    # art. 22.1.c — EIA preceptiva a Medio Ambiente
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
        tipo_elemento: 'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA'
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

    fecha_acto = _resolver_campo_fecha(elemento, tipo_elemento, catalogo.campo_fecha or {})
    if fecha_acto is None:
        return _SIN_PLAZO

    hoy = _hoy()
    margen_dias = max(catalogo.plazo_valor * 60, 400)
    inhabiles = _obtener_inhabiles_bd(fecha_acto, hoy + timedelta(days=margen_dias))

    suspensiones = _obtener_suspensiones(elemento)
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

        TAREA  → 'Distribucion/AAP/ANALISIS_SOLICITUD/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO'
        FASE   → 'Distribucion/AAP/RESOLUCION'

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
      3. Descarta las entradas cuyo camino no casa con el del elemento.
      4. De las que casan: sin condiciones → válida inmediata; con condiciones →
         AND implícito. Devuelve la primera que pasa.
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

    candidatas = [e for e in entradas if camino_casa(e.camino or '', camino_real)]

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


def _resolver_campo_fecha(elemento, tipo_elemento: str, campo_fecha: dict) -> Optional[date]:
    """Resuelve campo_fecha JSONB → Documento.fecha_administrativa.

    Navega el ORM según el JSON configurado en catalogo_plazos:
      {'fk': 'documento_resultado_id'}              → elemento.documento_resultado
      {'via_tarea_tipo': 'T', 'rol': 'CONSUMIDO'}   → tarea hija tipo T → documento por rol
      {'rol': 'CONSUMIDO'}                          → el propio elemento (Tarea) → documento por rol
    Para FASE con 'documento_solicitud_id': navega vía fase.solicitud.
    """
    fk_col = campo_fecha.get('fk', '')
    rol = campo_fecha.get('rol')
    via_tarea_tipo = campo_fecha.get('via_tarea_tipo')

    obj = elemento

    if via_tarea_tipo:
        tareas = getattr(obj, 'tareas', None) or []
        obj = next(
            (t for t in tareas
             if getattr(getattr(t, 'tipo_tarea', None), 'codigo', None) == via_tarea_tipo),
            None,
        )
        if obj is None:
            return None

    if rol:
        # obj es una Tarea — el documento se obtiene por rol del vínculo (ADR-010)
        if rol == 'PRODUCIDO':
            doc = getattr(obj, 'documento_producido', None)
        else:
            doc = _primer_consumido(obj)
    else:
        rel_name = fk_col[:-3] if fk_col.endswith('_id') else fk_col
        doc = getattr(obj, rel_name, None)
        if doc is None and tipo_elemento == 'FASE' and not via_tarea_tipo:
            solicitud = getattr(obj, 'solicitud', None)
            doc = getattr(solicitud, rel_name, None) if solicitud else None

    if doc is None:
        return None
    return getattr(doc, 'fecha_administrativa', None)


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


def _fecha_cierre_suspension(tramite_trigger, todos_tramites: list) -> Optional[date]:
    """
    Fecha de fin de la suspensión iniciada por tramite_trigger.

    Orden de búsqueda:
    1. Primer documento consumido de ANALIZAR del propio trámite (REQUERIMIENTO_SUBSANACION, CONSULTA_SEPARATA).
    2. Documento producido de ESPERAR_PLAZO del propio trámite (ADR-004 para SOLICITUD_INFORME).
    3. Primer documento consumido de ANALIZAR del primer trámite hermano receptor (RECEPCION_INFORME, etc.)
       con id > tramite_trigger.id.
    """
    analizar = _tarea_de_tipo(tramite_trigger, 'ANALIZAR')
    if analizar:
        f = _fecha_doc_admin(_primer_consumido(analizar))
        if f:
            return f

    esperar = _tarea_de_tipo(tramite_trigger, 'ESPERAR_PLAZO')
    if esperar:
        f = _fecha_doc_admin(getattr(esperar, 'documento_producido', None))
        if f:
            return f

    cierre_tipos = _TRAMITES_CIERRE.get(_codigo_tramite(tramite_trigger), frozenset())
    if cierre_tipos:
        for hermano in sorted(todos_tramites, key=lambda x: x.id):
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


def _obtener_suspensiones(elemento) -> list:
    """
    Deriva los intervalos de suspensión (art. 22 LPACAP) del elemento ESFTT
    consultando el árbol documental de sus trámites. No usa tabla propia.

    Retorna list de dict {'fecha_inicio': date, 'fecha_fin': date}.
    Suspensión sin cierre detectado → fecha_fin = hoy (suspensión activa).
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError
    try:
        tramites_attr = getattr(elemento, 'tramites', None)
        if tramites_attr is not None:
            todos_tramites = list(tramites_attr)
        else:
            # Elemento es un Trámite → usa tramites de su Fase para búsqueda de hermanos
            fase = getattr(elemento, 'fase', None)
            if fase:
                todos_tramites = list(getattr(fase, 'tramites', []) or [])
            else:
                todos_tramites = [elemento] if hasattr(elemento, 'tipo_tramite') else []
    except (OperationalError, ProgrammingError) as exc:
        log.warning('plazos: error cargando trámites para suspensiones (%s)', exc)
        return []

    suspensiones = []
    for tramite in todos_tramites:
        if _codigo_tramite(tramite) not in _TRAMITES_SUSPENSION:
            continue
        notificar = _tarea_de_tipo(tramite, 'NOTIFICAR')
        if not notificar:
            continue
        fecha_inicio = _fecha_doc_admin(getattr(notificar, 'documento_producido', None))
        if not fecha_inicio:
            continue
        fecha_fin = _fecha_cierre_suspension(tramite, todos_tramites) or _hoy()
        suspensiones.append({'fecha_inicio': fecha_inicio, 'fecha_fin': fecha_fin})

    return suspensiones


def _aplicar_suspensiones(fecha_limite: date, suspensiones: list, inhabiles: frozenset) -> date:
    """Suma los días de suspensión al plazo (art. 22 LPACAP). Stub hasta #173."""
    if not suspensiones:
        return fecha_limite
    dias_suspension = sum(
        _dias_habiles_entre(s['fecha_inicio'], s['fecha_fin'], inhabiles)
        for s in suspensiones
    )
    cursor = fecha_limite
    dias = 0
    while dias < dias_suspension:
        cursor += timedelta(days=1)
        if _es_habil(cursor, inhabiles):
            dias += 1
    return cursor
