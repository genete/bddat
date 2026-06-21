"""
seguimiento.py — Proyección por PISTAS del estado del árbol (listado de seguimiento).

Proyecta el núcleo `estado_dominio` sobre las 5 pistas (SOL/CONSULTAS/MA/IP/RES) de la
fila del listado inteligente. Las reglas de estado (hoja, contenedor, prioridad, color)
viven en `estado_dominio`; aquí solo está lo propio de esta vista:
  - el agrupamiento de fases en pistas (PISTAS),
  - el contador de elementos en el estado ganador (count) y la nota (tooltip),
  - el relabel de la pista SOL: la espera de plazo se muestra como subsanación,
  - fin_total para el color de la celda SOLICITUD.

Salida: {pista → EstadoPista(codigo, color, count, nota)}; None para pistas N/A.

La completitud se deduce de documentos (Documento.fecha_administrativa), no de campos
fecha_inicio/fecha_fin (eliminados del modelo ESFTT).

Uso:
    from app.services.seguimiento import estado_solicitud, fin_total
    estados = estado_solicitud(solicitud_id)   # → {'SOL': EstadoPista(...), 'CONSULTAS': None, ...}
    es_fin = fin_total(estados)                 # → True si todas las pistas con fases están en FIN
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import logging

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud
import app.services.estado_dominio as ed

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constantes de la proyección
# ---------------------------------------------------------------------------

# Pistas y los tipos_fases que las componen. Orden de aparición en el listado.
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


# ---------------------------------------------------------------------------
# Resultado público
# ---------------------------------------------------------------------------

@dataclass
class EstadoPista:
    """Estado proyectado para una pista de una solicitud."""
    codigo: str    # p.ej. 'PENDIENTE_ESTUDIO' (o 'PENDIENTE_SUBSANAR' en la pista SOL)
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
        EstadoPista → estado más urgente del núcleo, con contador acumulado.
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
            result[pista] = _na_o_tramitar(pista)
            continue

        if not fases:
            result[pista] = _na_o_tramitar(pista)
            continue

        if all(f.finalizada for f in fases):
            result[pista] = EstadoPista('FIN', ed.color('FIN'), count=1)
            continue

        fases_abiertas = [f for f in fases if not f.finalizada]
        acc: dict[str, int] = {}
        for f in fases_abiertas:
            _acumular(acc, _acc_fase(f))

        ganador, count = _mayor_prioridad(acc)
        codigo = _relabel(pista, ganador)
        nota = _nota_activa(fases_abiertas)
        result[pista] = EstadoPista(codigo, ed.color(ganador), count, nota)

    return result


def fin_total(estados: dict[str, Optional[EstadoPista]]) -> bool:
    """
    True si todas las pistas con fases están en FIN.
    Determina el color naranja de la celda SOLICITUD.
    """
    pistas_con_fases = [e for e in estados.values() if e is not None]
    return bool(pistas_con_fases) and all(e.codigo == 'FIN' for e in pistas_con_fases)


# ---------------------------------------------------------------------------
# Walk de acumulación — cuenta elementos por estado, con las reglas del núcleo
# ---------------------------------------------------------------------------

def _acc_fase(fase) -> dict[str, int]:
    """{estado: count} de una fase no finalizada, según el núcleo."""
    if fase.planificada:                       # sin trámites aún
        return {'PENDIENTE_TRAMITAR': 1}
    if fase.pdte_cierre:                        # cierre: ESTUDIO (finalizadora) o CERRAR
        estado, _ = ed.estado_fase(fase, [])
        return {estado: 1}
    acc: dict[str, int] = {}
    for tr in fase.tramites:
        if tr.finalizado:
            continue
        _acumular(acc, _acc_tramite(tr))
    return acc


def _acc_tramite(tramite) -> dict[str, int]:
    """{estado: count} de un trámite no finalizado, según el núcleo."""
    if tramite.planificado:                    # sin tareas aún
        return {'PENDIENTE_TRAMITAR': 1}
    acc: dict[str, int] = {}
    for ta in tramite.tareas:
        estado = _estado_tarea(ta)
        acc[estado] = acc.get(estado, 0) + 1
    return acc


def _estado_tarea(tarea) -> str:
    """Estado de dominio de una tarea (hoja); resuelve el plazo si es ESPERAR_PLAZO."""
    tipo_rel = getattr(tarea, 'tipo_tarea', None)
    tipo = tipo_rel.codigo if tipo_rel else None
    plazo = _plazo_tarea(tarea) if tipo == 'ESPERAR_PLAZO' else None
    return ed.estado_tarea(tarea, plazo=plazo)


def _plazo_tarea(tarea) -> Optional[dict]:
    """Resuelve el estado de plazo (server-only) de una tarea ESPERAR_PLAZO.

    Defensivo: cualquier fallo degrada a None (el núcleo lo mapea a TRAMITAR) sin
    tumbar la fila completa.
    """
    from app.services.plazos import obtener_estado_plazo
    try:
        ep = obtener_estado_plazo(tarea, 'TAREA', variables=_variables_esperar_plazo(tarea))
        return {'estado': ep.estado}
    except Exception as exc:  # noqa: BLE001 — un plazo no debe tumbar la fila entera
        log.warning('seguimiento: plazo no disponible para tarea %s — %s', getattr(tarea, 'id', '?'), exc)
        return None


def _variables_esperar_plazo(tarea) -> dict:
    """Variables del motor para resolver el plazo (tipo_tramite).

    Público: lo reutiliza también services/certificados.py.
    """
    try:
        tt = tarea.tramite.tipo_tramite
        return {'tipo_tramite': tt.codigo} if tt else {}
    except Exception:
        log.warning('seguimiento: no se pudo acceder a tipo_tramite de tarea %s', getattr(tarea, 'id', '?'))
        return {}


# ---------------------------------------------------------------------------
# Helpers de proyección
# ---------------------------------------------------------------------------

def _relabel(pista: str, estado: str) -> str:
    """En la pista SOL la espera de plazo se muestra como subsanación (mismo gris)."""
    if pista == 'SOL' and estado == 'PENDIENTE_PLAZOS':
        return 'PENDIENTE_SUBSANAR'
    return estado


def _na_o_tramitar(pista: str) -> Optional[EstadoPista]:
    """Pista sin fases: TRAMITAR si es obligatoria, None (N/A) si no."""
    if pista in PISTAS_OBLIGATORIAS:
        return EstadoPista('PENDIENTE_TRAMITAR', 'rojo')
    return None


def _mayor_prioridad(acc: dict[str, int]) -> tuple[str, int]:
    """(estado_ganador, count) del estado de menor número de prioridad (núcleo)."""
    ganador = min(acc, key=lambda e: ed.PRIORIDAD.get(e, 99))
    return ganador, acc[ganador]


def _acumular(acc: dict[str, int], otro: dict[str, int]) -> None:
    """Suma counts por estado de `otro` dentro de `acc` (in-place)."""
    for estado, n in otro.items():
        acc[estado] = acc.get(estado, 0) + n


def _nota_activa(fases_abiertas) -> Optional[str]:
    """
    Devuelve las notas de la primera tarea no ejecutada de las fases abiertas.
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
