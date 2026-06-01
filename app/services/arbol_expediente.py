"""
arbol_expediente.py — Serialización del árbol completo de un expediente.

Construye el JSON anidado de dominio que consume la isla React de la vista de
árbol (ADR-016 §16): expediente → solicitudes → fases → trámites → tareas, con
los decoradores por nodo (§2), el estado deducido (semántico, sin color) y los
agregadores de subárbol que afloran al colapsar (§11).

Decisiones de contrato (ADR-016 §16):
- Estado SEMÁNTICO, nunca color. El front mapea estado→color en el tematizado xyflow.
- El plazo de tareas ESPERAR_PLAZO se resuelve aquí (obtener_estado_plazo) porque su
  cómputo depende del calendario hábil / suspensiones / catalogo_plazos, server-only.
- Agregadores por nodo no-hoja: contadores del subárbol completo. El front muestra el
  badge solo cuando el nodo está colapsado (agregado total y fijo, sin recálculo).

Defensivo ante catálogo no disponible (REGLAS_DESARROLLO §Servicios con catálogo):
captura OperationalError / ProgrammingError y degrada sin propagar.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import joinedload, selectinload

from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos_tarea import DocumentoTarea
from app.models.documentos import Documento
from app.services import estado_semaforo as sem

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Agregadores (ADR-016 §11) — v1: plazos + notificar. "pendientes_firma" → deuda §15.
# ---------------------------------------------------------------------------

def _agregados_vacios() -> dict:
    return {
        'plazos_vencidos': 0,
        'plazos_proximos': 0,
        'plazos_en_plazo': 0,
        'pendientes_notificar': 0,
    }


def _sumar_agregados(acc: dict, otro: dict) -> None:
    for clave, valor in otro.items():
        acc[clave] = acc.get(clave, 0) + valor


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def construir_arbol(expediente_id: int) -> Optional[dict]:
    """
    Devuelve el árbol completo serializado de un expediente, o None si no existe.

    Forma: ADR-016 §16. selectinload para colecciones (evita el producto cartesiano
    de joinedload anidado) + joinedload para escalares → sin N+1.
    """
    try:
        expediente = (
            Expediente.query
            .options(
                joinedload(Expediente.titular),
                joinedload(Expediente.responsable),
                joinedload(Expediente.tipo_expediente),
            )
            .get(expediente_id)
        )
    except (OperationalError, ProgrammingError) as exc:
        log.warning('arbol_expediente: BD no disponible para expediente %s — %s', expediente_id, exc)
        return None

    if expediente is None:
        return None

    try:
        solicitudes = (
            Solicitud.query
            .filter_by(expediente_id=expediente_id)
            .options(
                joinedload(Solicitud.tipo_solicitud),
                joinedload(Solicitud.documento_solicitud),
                selectinload(Solicitud.fases).joinedload(Fase.tipo_fase),
                selectinload(Solicitud.fases).joinedload(Fase.resultado_fase),
                selectinload(Solicitud.fases)
                .selectinload(Fase.tramites).joinedload(Tramite.tipo_tramite),
                selectinload(Solicitud.fases)
                .selectinload(Fase.tramites)
                .selectinload(Tramite.tareas).joinedload(Tarea.tipo_tarea),
                # Documento + tipo_doc (detectar BORRADOR_FIRMA en ELABORAR, §3).
                selectinload(Solicitud.fases)
                .selectinload(Fase.tramites)
                .selectinload(Tramite.tareas)
                .selectinload(Tarea.vinculos_documento)
                .joinedload(DocumentoTarea.documento)
                .joinedload(Documento.tipo_doc),
                # Documento + notificacion (resultado/intento de NOTIFICAR, §3).
                selectinload(Solicitud.fases)
                .selectinload(Fase.tramites)
                .selectinload(Tramite.tareas)
                .selectinload(Tarea.vinculos_documento)
                .joinedload(DocumentoTarea.documento)
                .joinedload(Documento.notificacion),
            )
            .order_by(Solicitud.id)
            .all()
        )
    except (OperationalError, ProgrammingError) as exc:
        log.warning('arbol_expediente: error cargando jerarquía de expediente %s — %s', expediente_id, exc)
        solicitudes = []

    exp_data = _serializar_expediente(expediente)
    sols_data = [_serializar_solicitud(s) for s in solicitudes]

    # Semáforo del expediente: agregado de la mayor prioridad de sus solicitudes (§4/§5).
    est_exp, propio_exp = sem.estado_expediente(
        expediente, [s['semaforo']['estado'] for s in sols_data]
    )
    exp_data['semaforo'] = _semaforo(est_exp, propio_exp)

    return {'expediente': exp_data, 'solicitudes': sols_data}


def _semaforo(estado: str, propio: bool) -> dict:
    """Bloque semáforo del contrato: estado + nombre de color (§2) + flag de relleno."""
    return {'estado': estado, 'color': sem.color(estado), 'propio': propio}


# ---------------------------------------------------------------------------
# Serializadores por nivel (anidados; los agregadores fluyen de abajo arriba)
# ---------------------------------------------------------------------------

def _serializar_expediente(exp) -> dict:
    return {
        'tipo': 'expediente',
        'id': exp.id,
        'codigo': f'AT-{exp.numero_at}',
        'titular': exp.titular.nombre_completo if exp.titular else None,
        'responsable': exp.responsable.siglas if exp.responsable else None,
        'tipo_expediente': exp.tipo_expediente.tipo if exp.tipo_expediente else None,
    }


def _serializar_solicitud(sol) -> dict:
    agg = _agregados_vacios()
    fases_data = []
    for fase in sorted(sol.fases, key=lambda f: f.id):
        fd = _serializar_fase(fase)
        fases_data.append(fd)
        _sumar_agregados(agg, fd['agregados'])

    est, propio = sem.estado_solicitud(sol, [f['semaforo']['estado'] for f in fases_data])

    # Documentos (§8): la solicitud consume el documento de solicitud presentado;
    # no produce documento → producido marcado N/A (-) para el front.
    doc_sol = sol.documento_solicitud
    ts = sol.tipo_solicitud
    return {
        'tipo': 'solicitud',
        'id': sol.id,
        'siglas': ts.siglas if ts else None,
        'descripcion': ts.descripcion if ts else None,
        'estado': sol.estado,
        'fecha_presentacion': (
            doc_sol.fecha_administrativa.isoformat()
            if doc_sol and doc_sol.fecha_administrativa
            else None
        ),
        'doc_consumido': {'presente': doc_sol is not None, 'count': 1 if doc_sol else 0},
        'doc_producido': {'presente': False, 'count': 0, 'na': True},
        'semaforo': _semaforo(est, propio),
        'agregados': agg,
        'fases': fases_data,
    }


def _serializar_fase(fase) -> dict:
    agg = _agregados_vacios()
    tramites_data = []
    for tr in sorted(fase.tramites, key=lambda t: t.id):
        td = _serializar_tramite(tr)
        tramites_data.append(td)
        _sumar_agregados(agg, td['agregados'])

    est, propio = sem.estado_fase(fase, [t['semaforo']['estado'] for t in tramites_data])

    tf = fase.tipo_fase
    return {
        'tipo': 'fase',
        'id': fase.id,
        'tipo_codigo': tf.codigo if tf else None,
        'nombre': tf.nombre if tf else None,
        'abrev': tf.abrev if tf else None,
        'estado': fase.estado,
        'resultado': fase.resultado_fase.codigo if (fase.finalizada and fase.resultado_fase) else None,
        'semaforo': _semaforo(est, propio),
        'agregados': agg,
        'tramites': tramites_data,
    }


def _serializar_tramite(tr) -> dict:
    agg = _agregados_vacios()
    tareas_data = []
    for ta in sorted(tr.tareas, key=lambda t: t.id):
        nodo, nodo_agg = _serializar_tarea(ta, tr)
        tareas_data.append(nodo)
        _sumar_agregados(agg, nodo_agg)

    est, propio = sem.estado_tramite(tr, [t['semaforo']['estado'] for t in tareas_data])

    tt = tr.tipo_tramite
    return {
        'tipo': 'tramite',
        'id': tr.id,
        'tipo_codigo': tt.codigo if tt else None,
        'nombre': tt.nombre if tt else None,
        'abrev': tt.abrev if tt else None,
        'estado': tr.estado,
        'semaforo': _semaforo(est, propio),
        'agregados': agg,
        'tareas': tareas_data,
    }


def _serializar_tarea(tarea, tramite) -> tuple[dict, dict]:
    """
    Devuelve (nodo, agregados_de_esta_tarea).

    La tarea es hoja: no lleva bloque 'agregados' propio, pero aporta sus átomos
    (plazos, pendientes_notificar) al agregado de sus ancestros.
    """
    tt = tarea.tipo_tarea
    codigo = tt.codigo if tt else None

    consumidos = tarea.documentos_consumidos
    producido = tarea.documento_producido

    nodo = {
        'tipo': 'tarea',
        'id': tarea.id,
        'tipo_codigo': codigo,
        'nombre': tt.nombre if tt else None,
        'abrev': tt.abrev if tt else None,
        'estado': tarea.estado,
        'doc_consumido': {'presente': bool(consumidos), 'count': len(consumidos)},
        'doc_producido': {'presente': producido is not None, 'count': 1 if producido is not None else 0},
        'plazo': None,       # solo ESPERAR_PLAZO
        'resultado': None,   # solo NOTIFICAR
    }

    agg = _agregados_vacios()

    if codigo == 'ESPERAR_PLAZO':
        plazo = plazo_tarea(tarea, tramite)
        nodo['plazo'] = plazo
        # El agregado solo cuenta plazos accionables (tarea aún no ejecutada).
        if plazo and not tarea.ejecutada:
            estado = plazo['estado']
            if estado == 'VENCIDO':
                agg['plazos_vencidos'] += 1
            elif estado == 'PROXIMO_VENCER':
                agg['plazos_proximos'] += 1
            elif estado == 'EN_PLAZO':
                agg['plazos_en_plazo'] += 1

    elif codigo == 'NOTIFICAR':
        nodo['resultado'] = tarea.resultado
        if not tarea.ejecutada:
            agg['pendientes_notificar'] += 1

    # Semáforo de la tarea (§3). Hoja → siempre rellena (propio=True). El plazo ya
    # está resuelto en nodo['plazo'] para ESPERAR_PLAZO; estado_tarea no lo recalcula.
    estado_sem = sem.estado_tarea(tarea, plazo=nodo['plazo'])
    nodo['semaforo'] = _semaforo(estado_sem, True)

    return nodo, agg


def plazo_tarea(tarea, tramite) -> Optional[dict]:
    """
    Resuelve el estado de plazo de una tarea ESPERAR_PLAZO (server-only).
    Defensivo: cualquier fallo degrada a None sin romper el árbol completo.

    Público: lo reutiliza también services/detalle_nodo.py (inspector lazy, S3a).
    """
    try:
        from app.services.plazos import obtener_estado_plazo
        variables = {}
        tt = tramite.tipo_tramite if tramite else None
        if tt:
            variables['tipo_tramite'] = tt.codigo
        ep = obtener_estado_plazo(tarea, 'TAREA', variables=variables)
        return {
            'estado': ep.estado,
            'fecha_limite': ep.fecha_limite.isoformat() if ep.fecha_limite else None,
            'dias_restantes': ep.dias_restantes,
        }
    except Exception as exc:  # noqa: BLE001 — un plazo no debe tumbar el árbol entero
        log.warning('arbol_expediente: plazo no disponible para tarea %s — %s', getattr(tarea, 'id', '?'), exc)
        return None
