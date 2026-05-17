"""
seguimiento.py — Deducción de estado de pistas para el listado inteligente.

Implementa el algoritmo de ANALISIS_LISTADO_INTELIGENTE.md §5.
Recorre el árbol Solicitud → Fases → Trámites → Tareas de abajo arriba
y devuelve el estado más urgente de cada pista.

La completitud se deduce de documentos (Documento.fecha_administrativa),
no de campos fecha_inicio/fecha_fin (eliminados del modelo ESFTT).

Uso:
    from app.services.seguimiento import estado_solicitud, fin_total

    estados = estado_solicitud(solicitud_id)
    # → {'SOL': EstadoPista(codigo='PENDIENTE_ESTUDIO', color='rojo', count=1), ...}
    # → None para pistas N/A (sin fases de ese tipo en la solicitud)

    es_fin = fin_total(estados)
    # → True si todas las pistas con fases están en FIN
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import logging

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Pistas y los tipos_fases que las componen.
# Orden de aparición en el listado.
PISTAS: dict[str, list[str]] = {
    'SOL':      ['ANALISIS_SOLICITUD'],
    'CONSULTAS': ['CONSULTAS', 'CONSULTA_MINISTERIO'],
    'MA':       ['COMPATIBILIDAD_AMBIENTAL', 'FIGURA_AMBIENTAL_EXTERNA', 'AAU_AAUS_INTEGRADA'],
    'IP':       ['INFORMACION_PUBLICA'],
    'RES':      ['RESOLUCION'],
}

# Pistas que deben existir en toda solicitud EN_TRAMITE.
# Si no hay fases de estos tipos → PENDIENTE_TRAMITAR (alguien debe crearlas).
# El resto de pistas devuelven None (N/A) cuando no tienen fases.
PISTAS_OBLIGATORIAS = {'SOL'}

# Color canónico de cada estado (§4.1)
COLOR: dict[str, str] = {
    'PENDIENTE_TRAMITAR':  'rojo',
    'PENDIENTE_ESTUDIO':   'rojo',
    'PENDIENTE_ELABORAR':  'amarillo',
    'PENDIENTE_NOTIFICAR': 'azul',
    'PENDIENTE_SUBSANAR':  'gris',
    'PENDIENTE_PLAZOS':    'gris',
    'PENDIENTE_CERRAR':    'naranja',
    'FIN':                 'verde',
}

# Prioridad numérica por §4.2 (1 = más urgente, 10 = menos urgente)
PRIORIDAD: dict[str, int] = {
    'PENDIENTE_TRAMITAR':  1,
    'PENDIENTE_ESTUDIO':   2,
    'PENDIENTE_ELABORAR':  3,
    'PENDIENTE_CERRAR':    4,
    'PENDIENTE_NOTIFICAR': 5,
    'PENDIENTE_SUBSANAR':  6,
    'PENDIENTE_PLAZOS':    7,
    'FIN':                 8,
}


# ---------------------------------------------------------------------------
# Resultado público
# ---------------------------------------------------------------------------

@dataclass
class EstadoPista:
    """Estado deducido para una pista de una solicitud."""
    codigo: str    # p.ej. 'PENDIENTE_ESTUDIO'
    color: str     # p.ej. 'rojo'
    count: int = 1 # elementos en el estado de mayor prioridad (para contador visible)
    nota: Optional[str] = None  # notas de la tarea activa (para tooltip en seguimiento)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def estado_solicitud(solicitud_id: int) -> dict[str, Optional[EstadoPista]]:
    """
    Deduce el estado de cada pista para una solicitud.

    Returns:
        Dict con claves SOL, CONSULTAS, MA, IP, RES.
        None  → pista N/A (sin fases de ese tipo).
        EstadoPista → estado más urgente, con contador acumulado desde los niveles inferiores.
        PENDIENTE_TRAMITAR en todas las pistas obligatorias si la BD no está disponible.
    """
    try:
        sol = Solicitud.query.get(solicitud_id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('seguimiento: BD no disponible para solicitud %s — %s', solicitud_id, exc)
        return {p: EstadoPista('PENDIENTE_TRAMITAR', 'rojo') for p in PISTAS_OBLIGATORIAS}

    if sol is None:
        raise ValueError(f'Solicitud {solicitud_id} no encontrada')

    result: dict[str, Optional[EstadoPista]] = {}

    for pista, tipos_fases in PISTAS.items():
        try:
            fases = [f for f in sol.fases if f.tipo_fase.codigo in tipos_fases]
        except (AttributeError, OperationalError, ProgrammingError) as exc:
            log.warning('seguimiento: error accediendo a fases de pista %s — %s', pista, exc)
            if pista in PISTAS_OBLIGATORIAS:
                result[pista] = EstadoPista('PENDIENTE_TRAMITAR', 'rojo')
            else:
                result[pista] = None
            continue

        if not fases:
            if pista in PISTAS_OBLIGATORIAS:
                result[pista] = EstadoPista('PENDIENTE_TRAMITAR', 'rojo')
            else:
                result[pista] = None
            continue

        if all(f.finalizada for f in fases):
            result[pista] = EstadoPista('FIN', 'verde', count=1)
            continue

        fases_abiertas = [f for f in fases if not f.finalizada]
        acc = _acumular([_estado_fase(f, pista) for f in fases_abiertas])
        ganador, count = _mayor_prioridad(acc)
        nota = _nota_activa(fases_abiertas)
        result[pista] = EstadoPista(ganador, COLOR[ganador], count, nota)

    return result


def fin_total(estados: dict[str, Optional[EstadoPista]]) -> bool:
    """
    True si todas las pistas con fases están en FIN.
    Determina el color naranja de la celda SOLICITUD.
    """
    pistas_con_fases = [e for e in estados.values() if e is not None]
    return bool(pistas_con_fases) and all(e.codigo == 'FIN' for e in pistas_con_fases)


# ---------------------------------------------------------------------------
# Algoritmo §5 — deducción jerárquica
# ---------------------------------------------------------------------------

def _estado_fase(fase, pista: str) -> tuple[str, int]:
    """Estado de una fase no finalizada (documento_resultado_id IS NULL)."""
    if fase.planificada:  # sin trámites aún
        return ('PENDIENTE_TRAMITAR', 1)

    tramites = sorted(fase.tramites, key=lambda t: t.id)
    tramites_activos = [t for t in tramites if not t.finalizado]

    if not tramites_activos:
        # Todos los trámites completados — esperando que el técnico formalice el resultado de fase
        if fase.resultado_fase_id is None:
            return ('PENDIENTE_ESTUDIO', 1)
        return ('PENDIENTE_CERRAR', 1)

    acc = _acumular([_estado_tramite(t, pista) for t in tramites_activos])
    return _mayor_prioridad(acc)


def _estado_tramite(tramite, pista: str) -> tuple[str, int]:
    """Estado de un trámite no finalizado."""
    if tramite.planificado:  # sin tareas aún
        return ('PENDIENTE_TRAMITAR', 1)

    tareas = list(tramite.tareas)
    tareas_pendientes = [t for t in tareas if not t.ejecutada]

    if not tareas_pendientes:
        # Todas las tareas completadas — trámite pendiente de cerrar (transitorio)
        return ('PENDIENTE_CERRAR', 1)

    acc = _acumular([_estado_tarea(t, pista) for t in tareas_pendientes])
    return _mayor_prioridad(acc)


def _estado_tarea(tarea, pista: str) -> tuple[str, int]:
    """Estado de una tarea no ejecutada. §4.4"""
    if tarea.planificada:  # sin documentos asignados aún
        return ('PENDIENTE_TRAMITAR', 1)

    tipo_rel = getattr(tarea, 'tipo_tarea', None)
    if tipo_rel is None:
        log.warning('seguimiento: tarea %s sin tipo_tarea — tratando como PENDIENTE_TRAMITAR', getattr(tarea, 'id', '?'))
        return ('PENDIENTE_TRAMITAR', 1)
    tipo = tipo_rel.codigo

    if tipo == 'ANALIZAR':
        if not tarea.documentos_consumidos:
            return ('PENDIENTE_TRAMITAR', 1)   # sin doc de entrada: hay que tramitar
        if not tarea.ejecutada:
            return ('PENDIENTE_ESTUDIO', 1)    # doc recibido, hay que estudiar y redactar informe
        return ('PENDIENTE_CERRAR', 1)         # entrada y salida presentes

    if tipo == 'ELABORAR':
        # Entrada opcional → no hay estado "en espera de documento de entrada"
        if tarea.ejecutada:
            return ('PENDIENTE_CERRAR', 1)
        return ('PENDIENTE_ELABORAR', 1)

    if tipo == 'NOTIFICAR':
        if not tarea.documentos_consumidos:
            return ('PENDIENTE_TRAMITAR', 1)   # falta doc firmado
        if not tarea.ejecutada:
            return ('PENDIENTE_NOTIFICAR', 1)  # doc firmado, falta justificante
        return ('PENDIENTE_CERRAR', 1)

    if tipo == 'ESPERAR_PLAZO':
        return (_estado_esperar_plazo(tarea, pista), 1)

    return ('PENDIENTE_TRAMITAR', 1)  # tipo desconocido — seguro por defecto


def _estado_esperar_plazo(tarea, pista: str) -> str:
    """
    ESPERAR_PLAZO: §4.4 — consulta catalogo_plazos en lugar de parsear Tarea.notas.
    Sin entrada configurada → PENDIENTE_TRAMITAR (tarea sin configurar).
    Con entrada pero sin documento consumido aún → estado_espera (esperando inicio de cómputo).
    Plazo vencido → PENDIENTE_ESTUDIO.
    """
    from app.services.plazos import obtener_estado_plazo, tiene_plazo_configurado

    variables = _variables_esperar_plazo(tarea)

    if not tiene_plazo_configurado('TAREA', 'ESPERAR_PLAZO', variables):
        return 'PENDIENTE_TRAMITAR'

    estado_espera = 'PENDIENTE_SUBSANAR' if pista == 'SOL' else 'PENDIENTE_PLAZOS'

    ep = obtener_estado_plazo(tarea, 'TAREA', variables=variables)

    if ep.estado == 'VENCIDO':
        return 'PENDIENTE_ESTUDIO'
    return estado_espera   # SIN_PLAZO (sin doc), EN_PLAZO, PROXIMO_VENCER


def _variables_esperar_plazo(tarea) -> dict:
    try:
        tt = tarea.tramite.tipo_tramite
        return {'tipo_tramite': tt.codigo} if tt else {}
    except Exception:
        log.warning('seguimiento: no se pudo acceder a tipo_tramite de tarea %s', getattr(tarea, 'id', '?'))
        return {}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _nota_activa(fases_abiertas) -> Optional[str]:
    """
    Devuelve las notas de la primera tarea no ejecutada encontrada en las fases abiertas.
    Se usa para poblar el tooltip en el listado de seguimiento.
    """
    for fase in fases_abiertas:
        for tramite in sorted(fase.tramites, key=lambda t: t.id):
            if tramite.finalizado:
                continue
            for tarea in tramite.tareas:
                if not tarea.ejecutada and tarea.notas:
                    return tarea.notas
    return None


def _acumular(resultados: list[tuple[str, int]]) -> dict[str, int]:
    """Suma counts por estado interno a través de los niveles del árbol."""
    acc: dict[str, int] = {}
    for estado, n in resultados:
        acc[estado] = acc.get(estado, 0) + n
    return acc


def _mayor_prioridad(acumulado: dict[str, int]) -> tuple[str, int]:
    """(estado_ganador, count) del estado de menor número en §4.2 (más urgente)."""
    ganador = min(acumulado, key=lambda e: PRIORIDAD[e])
    return ganador, acumulado[ganador]
