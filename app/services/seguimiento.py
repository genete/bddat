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
from dataclasses import dataclass
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

# Prioridad numérica por §4.2 (1 = más urgente, 10 = menos urgente)
PRIORIDAD: dict[str, int] = {
    'PENDIENTE_TRAMITAR':  1,
    'PENDIENTE_ESTUDIO':   2,
    'PENDIENTE_REDACTAR':  3,
    'PENDIENTE_CERRAR':    4,
    'PENDIENTE_FIRMA':     5,
    'PENDIENTE_NOTIFICAR': 6,
    'PENDIENTE_PUBLICAR':  7,
    'PENDIENTE_SUBSANAR':  8,
    'PENDIENTE_PLAZOS':    9,
    'FIN':                 10,
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
            result[pista] = EstadoPista('FIN', 'verde', count=1)
            continue

        fases_abiertas = [f for f in fases if f.fecha_fin is None]
        acc = _acumular([_estado_fase(f, pista) for f in fases_abiertas])
        ganador, count = _mayor_prioridad(acc)
        result[pista] = EstadoPista(ganador, COLOR[ganador], count)

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
    """Estado de una fase abierta (fecha_fin IS NULL)."""
    if fase.fecha_inicio is None:
        return ('PENDIENTE_TRAMITAR', 1)

    tramites = sorted(fase.tramites, key=lambda t: t.id)

    if not tramites:
        return ('PENDIENTE_TRAMITAR', 1)

    tramites_abiertos = [t for t in tramites if t.fecha_fin is None]

    if not tramites_abiertos:
        # Todos los trámites cerrados — depende del resultado de fase
        if fase.resultado_fase_id is None:
            return ('PENDIENTE_ESTUDIO', 1)
        return ('PENDIENTE_CERRAR', 1)

    acc = _acumular([_estado_tramite(t, pista) for t in tramites_abiertos])
    return _mayor_prioridad(acc)


def _estado_tramite(tramite, pista: str) -> tuple[str, int]:
    """Estado de un trámite abierto (fecha_fin IS NULL)."""
    if tramite.fecha_inicio is None:
        return ('PENDIENTE_TRAMITAR', 1)

    tareas = list(tramite.tareas)

    if not tareas:
        return ('PENDIENTE_TRAMITAR', 1)

    tareas_abiertas = [t for t in tareas if t.fecha_fin is None]

    if not tareas_abiertas:
        # Todas las tareas completadas pero el trámite sigue abierto
        return ('PENDIENTE_CERRAR', 1)

    acc = _acumular([_estado_tarea(t, pista) for t in tareas_abiertas])
    return _mayor_prioridad(acc)


def _estado_tarea(tarea, pista: str) -> tuple[str, int]:
    """Estado de una tarea abierta (fecha_fin IS NULL). §4.4"""
    if tarea.fecha_inicio is None:
        return ('PENDIENTE_TRAMITAR', 1)  # tarea planificada, no iniciada

    tipo = tarea.tipo_tarea.codigo

    if tipo == 'ANALIZAR':
        if tarea.documento_usado_id is None:
            return ('PENDIENTE_TRAMITAR', 1)   # sin doc de entrada: hay que tramitar
        if tarea.documento_producido_id is None:
            return ('PENDIENTE_ESTUDIO', 1)    # doc recibido, hay que estudiar y redactar informe
        return ('PENDIENTE_CERRAR', 1)         # ambos documentos presentes

    if tipo == 'REDACTAR':
        if tarea.documento_producido_id is not None:
            return ('PENDIENTE_CERRAR', 1)     # borrador ya producido
        if tarea.documento_usado_id is not None:
            return ('PENDIENTE_REDACTAR', 1)   # tiene doc de entrada, falta redactar
        return ('PENDIENTE_TRAMITAR', 1)       # sin ningún doc: hay que tramitar

    if tipo == 'FIRMAR':
        if tarea.documento_usado_id is None:
            return ('PENDIENTE_TRAMITAR', 1)   # falta borrador
        if tarea.documento_producido_id is None:
            return ('PENDIENTE_FIRMA', 1)      # borrador presente, falta firmado
        return ('PENDIENTE_CERRAR', 1)

    if tipo == 'NOTIFICAR':
        if tarea.documento_usado_id is None:
            return ('PENDIENTE_TRAMITAR', 1)   # falta doc firmado
        if tarea.documento_producido_id is None:
            return ('PENDIENTE_NOTIFICAR', 1)  # doc firmado, falta justificante
        return ('PENDIENTE_CERRAR', 1)

    if tipo == 'PUBLICAR':
        if tarea.documento_usado_id is None:
            return ('PENDIENTE_TRAMITAR', 1)   # falta doc firmado
        if tarea.documento_producido_id is None:
            return ('PENDIENTE_PUBLICAR', 1)   # doc firmado, falta justificante publicación
        return ('PENDIENTE_CERRAR', 1)

    if tipo == 'ESPERAR_PLAZO':
        return (_estado_esperar_plazo(tarea, pista), 1)

    if tipo == 'INCORPORAR':
        if tarea.documento_producido_id is None:
            return ('PENDIENTE_TRAMITAR', 1)   # sin documento incorporado
        return ('PENDIENTE_CERRAR', 1)

    return ('PENDIENTE_TRAMITAR', 1)  # tipo desconocido — seguro por defecto


def _estado_esperar_plazo(tarea, pista: str) -> str:
    """
    ESPERAR_PLAZO: §4.4
    - PLAZO_DIAS no configurado (=0) → PENDIENTE_TRAMITAR
    - Plazo activo (días restantes > 0) → PENDIENTE_SUBSANAR (pista SOL) o PENDIENTE_PLAZOS (resto)
    - Plazo vencido (días restantes ≤ 0) → PENDIENTE_ESTUDIO
    """
    plazo = _parse_plazo_dias(tarea.notas)

    if plazo == 0:
        return 'PENDIENTE_TRAMITAR'  # plazo no configurado: hay que tramitar

    estado_espera = 'PENDIENTE_SUBSANAR' if pista == 'SOL' else 'PENDIENTE_PLAZOS'

    if tarea.fecha_inicio:
        vencimiento = tarea.fecha_inicio + timedelta(days=plazo)
        if vencimiento < date.today():
            return 'PENDIENTE_ESTUDIO'  # plazo vencido: hay que estudiar la respuesta

    return estado_espera


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _parse_plazo_dias(notas: Optional[str]) -> int:
    """Extrae PLAZO_DIAS=N de notas. Devuelve 0 si no encontrado."""
    if not notas:
        return 0
    m = re.search(r'PLAZO_DIAS=(\d+)', notas)
    return int(m.group(1)) if m else 0


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
