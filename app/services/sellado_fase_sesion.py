"""
Hook de sesión SQLAlchemy — red de cierre del sellado de fase cerrada
(#720, ADR-036 §6, capa 3).

Intercepta cualquier escritura en Tramite/Tarea/DocumentoTarea/Notificacion/
OrganismoExpediente en el momento del flush, venga de donde venga: ruta HTTP, servicio de dominio,
script de consola o un futuro job de integración externa (p. ej. un
auto-vinculador de justificantes de notificación) que no pase por ninguna de
las otras dos capas (`_resolver_nodo`, `check_invariante('MUTAR', ...)`). Es
la única capa que no depende de que el código que muta conozca el invariante.

No hay ninguna excepción registrada para el propio ciclo cierre/reapertura:
`mutaciones_arbol.editar_fase`/`reabrir_fase` solo escriben la fila `fases`,
nunca las cinco tablas vigiladas aquí — con el diseño actual no hay riesgo de
autobloqueo. Si en el futuro alguna de esas dos funciones empieza a tocar
Tramite/Tarea/DocumentoTarea/Notificacion/OrganismoExpediente en la misma
transacción, revisar este hook antes de tocar nada más.
"""
from __future__ import annotations

import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos_tarea import DocumentoTarea
from app.models.notificaciones import Notificacion
from app.models.organismos_expediente import OrganismoExpediente

log = logging.getLogger(__name__)

_MODELOS_VIGILADOS = (Tramite, Tarea, DocumentoTarea, Notificacion, OrganismoExpediente)


class SelladoFaseVioladoError(Exception):
    """Un flush intentó escribir en el interior de una fase cerrada sin pasar
    por ninguna de las otras dos capas del sellado (#720, ADR-036). El flujo
    normal (rutas HTTP, `mutaciones_arbol.py`, `diagnosticos.py`) nunca debería
    disparar esto — si llega aquí, algún código está mutando el árbol por
    fuera de esos caminos."""


def _fase_de_instancia(obj):
    """Fase ancestro de una instancia vigilada, o None si no se puede resolver
    (objeto a medio construir, FK aún sin asignar).

    Resuelve por query explícita sobre el FK (`Modelo.query.get(id)`), no vía
    la relación ORM (`obj.tramite`, `obj.tarea`): para un objeto recién creado
    y solo `session.add()`-eado (estado "pending", el caso típico de un
    asignador automático que hace `DocumentoTarea(tarea_id=..., ...)` directo)
    la relación lazy no resuelve — SQLAlchemy no la sincroniza hasta el propio
    flush — mientras que una query por PK funciona en cualquier estado.
    """
    try:
        if isinstance(obj, (Tramite, OrganismoExpediente)):
            return Fase.query.get(obj.fase_id) if obj.fase_id else None
        if isinstance(obj, Tarea):
            tramite = Tramite.query.get(obj.tramite_id) if obj.tramite_id else None
            return Fase.query.get(tramite.fase_id) if tramite else None
        if isinstance(obj, (DocumentoTarea, Notificacion)):
            tarea = Tarea.query.get(obj.tarea_id) if obj.tarea_id else None
            if tarea is None:
                return None
            tramite = Tramite.query.get(tarea.tramite_id) if tarea.tramite_id else None
            return Fase.query.get(tramite.fase_id) if tramite else None
    except Exception:
        # FK no resoluble en este punto del flush — no es este hook quien debe
        # fallar por eso; lo hará la propia constraint NOT NULL al insertar.
        return None
    return None


@event.listens_for(Session, 'before_flush')
def _bloquear_mutacion_bajo_fase_cerrada(session, flush_context, instances):
    candidatos = [
        obj for obj in list(session.new) + list(session.dirty) + list(session.deleted)
        if isinstance(obj, _MODELOS_VIGILADOS)
    ]
    if not candidatos:
        return

    with session.no_autoflush:
        for obj in candidatos:
            fase = _fase_de_instancia(obj)
            if fase is not None and fase.finalizada:
                log.error(
                    'Sellado de fase violado en flush: %s bajo fase %s cerrada, sin '
                    'pasar por check_invariante ni _resolver_nodo (#720)',
                    obj, fase.id,
                )
                raise SelladoFaseVioladoError(
                    f'La fase {fase.id} está cerrada; {type(obj).__name__} no puede '
                    f'mutarse en su interior sin reabrirla antes.'
                )
