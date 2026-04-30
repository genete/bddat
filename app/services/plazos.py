"""
Servicio de plazos administrativos — BDDAT.

Calcula el estado del plazo legal asociado a un elemento ESFTT
(Solicitud, Fase, Trámite, Tarea) y devuelve un EstadoPlazo.

Arquitectura (DISEÑO_FECHAS_PLAZOS.md §4):
    ContextAssembler llama a obtener_estado_plazo() para poblar las variables
    'estado_plazo' y 'efecto_plazo' que el motor agnóstico evalúa con operadores
    estándar (EQ/IN/etc.). El motor no conoce este servicio.

Lógica real (#172):
    1. Busca en catalogo_plazos el plazo aplicable al tipo de elemento.
    2. Resuelve campo_fecha JSONB → Documento.fecha_administrativa.
    3. Calcula fecha_limite con calcular_fecha_fin() (art. 30 LPACAP).
    4. Deriva estado según condiciones de §2.4 (umbral 5 días hábiles).
    Suspensiones: hook _obtener_suspensiones() → [] hasta que #173 lo implemente.
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
        elemento:      Instancia ORM del elemento evaluado
                       (Solicitud, Fase, Tramite o Tarea).
                       None o dict → SIN_PLAZO sin consultar BD.
        tipo_elemento: 'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA'
        ctx:           ExpedienteContext. Si se pasa, construye variables internamente
                       (excluyendo estado_plazo/efecto_plazo para evitar recursión).
        variables:     Dict de variables pre-construido. Tiene precedencia sobre ctx.

    Ruta legacy (ctx=None, variables=None):
        Usa CatalogoPlazo.query.filter_by(...).first() — compatible con mocks de test_172.
        La llaman las variables de plazo.py antes de la sesión 4; se elimina en sesión 6.

    Ruta nueva (ctx o variables proporcionados):
        Delega en _seleccionar_catalogo con el dict de variables para evaluar condiciones.
    """
    if elemento is None or isinstance(elemento, dict):
        return _SIN_PLAZO

    tipo_elemento_id = _get_tipo_elemento_id(elemento, tipo_elemento)
    if tipo_elemento_id is None:
        return _SIN_PLAZO

    if ctx is None and variables is None:
        # Ruta legacy: query simple, sin evaluador de condiciones.
        # Mantiene la cadena .filter_by(...).first() que mockean los tests #172 y #190
        # para que sigan verdes sin modificación.
        from app.models.catalogo_plazos import CatalogoPlazo
        catalogo = CatalogoPlazo.query.filter_by(
            tipo_elemento=tipo_elemento,
            tipo_elemento_id=tipo_elemento_id,
            activo=True,
        ).first()
    else:
        if variables is not None:
            variables_dict = variables
        else:
            from app.services.assembler import _compilar_variables
            variables_dict = _compilar_variables(
                ctx, excluir={'estado_plazo', 'efecto_plazo'}
            )
        catalogo = _seleccionar_catalogo(tipo_elemento, tipo_elemento_id, variables_dict)

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


def _seleccionar_catalogo(tipo_elemento: str, tipo_id: int, variables_dict: dict):
    """
    Devuelve la primera entrada activa de catalogo_plazos que supera sus condiciones.

    Algoritmo (IMPLEMENTACION_341.md §Sesión 4):
      1. Carga entradas activas con joinedload de condiciones+variable.
      2. Ordena por orden ASC, id ASC (menor orden = mayor prioridad).
      3. Itera: entrada sin condiciones → candidata válida inmediata.
              entrada con condiciones → evalúa con AND implícito.
      4. Devuelve la primera que pasa; si ninguna → None con warning.
    """
    from app.models.catalogo_plazos import CatalogoPlazo
    from app.models.condiciones_plazo import CondicionPlazo

    entradas = (
        CatalogoPlazo.query
        .options(
            joinedload(CatalogoPlazo.condiciones).joinedload(CondicionPlazo.variable)
        )
        .filter_by(tipo_elemento=tipo_elemento, tipo_elemento_id=tipo_id, activo=True)
        .order_by(CatalogoPlazo.orden.asc(), CatalogoPlazo.id.asc())
        .all()
    )

    for entrada in entradas:
        if not entrada.condiciones:
            return entrada
        if _evaluar_condiciones_plazo(entrada.condiciones, variables_dict):
            return entrada

    if entradas:
        log.warning(
            'plazos: ninguna entrada de catalogo_plazos satisface condiciones '
            'para %s/%s — se devuelve SIN_PLAZO',
            tipo_elemento, tipo_id,
        )
    return None


def _get_tipo_elemento_id(elemento, tipo_elemento: str) -> Optional[int]:
    campo = _TIPO_ID_CAMPO.get(tipo_elemento)
    return getattr(elemento, campo, None) if campo else None


def _resolver_campo_fecha(elemento, tipo_elemento: str, campo_fecha: dict) -> Optional[date]:
    """Resuelve campo_fecha JSONB → Documento.fecha_administrativa.

    Navega el ORM según el JSON configurado en catalogo_plazos:
      {'fk': 'documento_resultado_id'}             → elemento.documento_resultado
      {'via_tarea_tipo': 'T', 'fk': 'doc_id'}     → tarea hija tipo T → rel
    Para FASE con 'documento_solicitud_id': navega vía fase.solicitud.
    """
    fk_col = campo_fecha.get('fk', '')
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


def _obtener_suspensiones(elemento) -> list:
    """Hook de suspensiones — stub hasta #173."""
    return []


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
