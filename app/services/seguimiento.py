"""
seguimiento.py — Deducción de estado de pistas para el listado inteligente.

Implementa el algoritmo de ANALISIS_LISTADO_INTELIGENTE.md §5.
Recorre el árbol Solicitud → Fases → Trámites → Tareas de abajo arriba
y devuelve el estado más urgente de cada pista.

Uso:
    from app.services.seguimiento import estado_solicitud, fin_total

    estados = estado_solicitud(solicitud_id)
    # → {'SOL': EstadoPista(codigo='PENDIENTE_ESTUDIO', color='rojo', count=1), ...}
    # → None para pistas N/A (sin fases de ese tipo en la solicitud)

    es_fin = fin_total(estados)
    # → True si todas las pistas con fases están en FIN
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from app.models.solicitudes import Solicitud


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
    'PENDIENTE_REDACTAR':  'rojo',
    'PENDIENTE_FIRMA':     'amarillo',
    'PENDIENTE_NOTIFICAR': 'azul',
    'PENDIENTE_PUBLICAR':  'azul',
    'PENDIENTE_SUBSANAR':  'gris',
    'PENDIENTE_PLAZOS':    'gris',
    'PENDIENTE_CERRAR':    'naranja',
    'FIN':                 'verde',
}

# Prioridad de urgencia: mayor número = más urgente (§5)
URGENCIA: dict[str, int] = {
    'rojo':     6,
    'amarillo': 5,
    'azul':     4,
    'naranja':  3,
    'gris':     2,
    'verde':    1,
}


# ---------------------------------------------------------------------------
# Resultado público
# ---------------------------------------------------------------------------

@dataclass
class EstadoPista:
    """Estado deducido para una pista de una solicitud."""
    codigo: str    # p.ej. 'PENDIENTE_ESTUDIO'
    color: str     # p.ej. 'rojo'
    count: int = 1 # fases en el nivel de urgencia máximo (para mostrar contador)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def estado_solicitud(solicitud_id: int) -> dict[str, Optional[EstadoPista]]:
    """
    Deduce el estado de cada pista para una solicitud.

    Returns:
        Dict con claves SOL, CONSULTAS, MA, IP, RES.
        None  → pista N/A (sin fases de ese tipo).
        EstadoPista → estado más urgente de las fases abiertas, con contador.
    """
    sol = Solicitud.query.get(solicitud_id)
    if sol is None:
        raise ValueError(f'Solicitud {solicitud_id} no encontrada')

    result: dict[str, Optional[EstadoPista]] = {}

    for pista, tipos_fases in PISTAS.items():
        fases = [f for f in sol.fases if f.tipo_fase.codigo in tipos_fases]

        if not fases:
            if pista in PISTAS_OBLIGATORIAS:
                result[pista] = EstadoPista('PENDIENTE_TRAMITAR', 'rojo')
            else:
                result[pista] = None
            continue

        if all(f.fecha_fin is not None for f in fases):
            result[pista] = EstadoPista('FIN', 'verde', count=len(fases))
            continue

        fases_abiertas = [f for f in fases if f.fecha_fin is None]
        estados = [_estado_fase(f, pista) for f in fases_abiertas]
        result[pista] = _agregar(estados)

    return result


def fin_total(estados: dict[str, Optional[EstadoPista]]) -> bool:
    """
    True si todas las pistas con fases están en FIN.
    Columna FIN del listado.
    """
    pistas_con_fases = [e for e in estados.values() if e is not None]
    return bool(pistas_con_fases) and all(e.codigo == 'FIN' for e in pistas_con_fases)


# ---------------------------------------------------------------------------
# Algoritmo §5 — deducción jerárquica
# ---------------------------------------------------------------------------

def _estado_fase(fase, pista: str) -> str:
    """Estado de una fase abierta (fecha_fin IS NULL). §5 paso 4."""
    if fase.fecha_inicio is None:
        return 'PENDIENTE_TRAMITAR'                          # §5.4a

    tramites = sorted(fase.tramites, key=lambda t: t.id)

    if not tramites:
        return 'PENDIENTE_TRAMITAR'                          # §5.4b

    tramites_abiertos = [t for t in tramites if t.fecha_fin is None]

    if not tramites_abiertos:
        # Todos los trámites cerrados — depende del resultado de fase
        if fase.resultado_fase_id is None:
            return 'PENDIENTE_ESTUDIO'
        return 'PENDIENTE_CERRAR'

    estados = [_estado_tramite(t, pista) for t in tramites_abiertos]
    return _mas_urgente(estados)


def _estado_tramite(tramite, pista: str) -> str:
    """Estado de un trámite abierto (fecha_fin IS NULL). §5.4c"""
    tareas = sorted(tramite.tareas, key=lambda t: t.id)

    if tramite.fecha_inicio is None:
        # Trámite no iniciado — excepción si la primera tarea es REDACTAR
        if tareas and tareas[0].tipo_tarea.codigo == 'REDACTAR':
            return 'PENDIENTE_REDACTAR'
        return 'PENDIENTE_TRAMITAR'

    if not tareas:
        return 'PENDIENTE_TRAMITAR'

    activas     = [t for t in tareas if t.fecha_inicio is not None and t.fecha_fin is None]
    planificadas = [t for t in tareas if t.fecha_inicio is None]

    if not activas:
        return 'PENDIENTE_TRAMITAR' if planificadas else 'PENDIENTE_CERRAR'

    estados = [_estado_tarea(t, pista) for t in activas]
    return _mas_urgente(estados)


def _estado_tarea(tarea, pista: str) -> str:
    """Estado de una tarea activa (fecha_inicio NOT NULL, fecha_fin IS NULL). §4.4"""
    tipo = tarea.tipo_tarea.codigo

    if tipo == 'ANALIZAR':
        if tarea.documento_usado_id is None or tarea.documento_producido_id is None:
            return 'PENDIENTE_ESTUDIO'
        return 'PENDIENTE_CERRAR'

    if tipo == 'REDACTAR':
        return 'PENDIENTE_CERRAR' if tarea.documento_producido_id else 'PENDIENTE_REDACTAR'

    if tipo == 'FIRMAR':
        if tarea.documento_usado_id is None:
            return 'PENDIENTE_TRAMITAR'
        return 'PENDIENTE_CERRAR' if tarea.documento_producido_id else 'PENDIENTE_FIRMA'

    if tipo == 'NOTIFICAR':
        if tarea.documento_usado_id is None:
            return 'PENDIENTE_TRAMITAR'
        return 'PENDIENTE_CERRAR' if tarea.documento_producido_id else 'PENDIENTE_NOTIFICAR'

    if tipo == 'PUBLICAR':
        if tarea.documento_usado_id is None:
            return 'PENDIENTE_TRAMITAR'
        return 'PENDIENTE_CERRAR' if tarea.documento_producido_id else 'PENDIENTE_PUBLICAR'

    if tipo == 'ESPERAR_PLAZO':
        return _estado_esperar_plazo(tarea, pista)

    if tipo == 'INCORPORAR':
        return 'PENDIENTE_CERRAR' if tarea.documento_producido_id else 'PENDIENTE_ESTUDIO'

    return 'PENDIENTE_TRAMITAR'


def _estado_esperar_plazo(tarea, pista: str) -> str:
    """
    ESPERAR_PLAZO: gris si el plazo está activo o es indefinido,
    PENDIENTE_ESTUDIO si el plazo ha vencido. §4.4
    Lee PLAZO_DIAS del campo notas.
    """
    estado_espera = 'PENDIENTE_SUBSANAR' if pista == 'SOL' else 'PENDIENTE_PLAZOS'
    plazo = _parse_plazo_dias(tarea.notas)

    if plazo == 0:
        return estado_espera  # espera indefinida

    if tarea.fecha_inicio:
        vencimiento = tarea.fecha_inicio + timedelta(days=plazo)
        if vencimiento < date.today():
            return 'PENDIENTE_ESTUDIO'

    return estado_espera


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_plazo_dias(notas: Optional[str]) -> int:
    """Extrae PLAZO_DIAS=N de notas. Devuelve 0 si no encontrado."""
    if not notas:
        return 0
    m = re.search(r'PLAZO_DIAS=(\d+)', notas)
    return int(m.group(1)) if m else 0


def _mas_urgente(estados: list[str]) -> str:
    """El estado de mayor urgencia de la lista."""
    return max(estados, key=lambda e: URGENCIA[COLOR[e]])


def _agregar(estados: list[str]) -> EstadoPista:
    """EstadoPista con el estado más urgente y cuántas fases lo comparten."""
    mejor = _mas_urgente(estados)
    urgencia_max = URGENCIA[COLOR[mejor]]
    count = sum(1 for e in estados if URGENCIA[COLOR[e]] == urgencia_max)
    return EstadoPista(mejor, COLOR[mejor], count)
