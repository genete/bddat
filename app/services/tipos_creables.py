"""
tipos_creables.py — Tipos de hijo creables bajo un nodo del árbol (ADR-016 §16, §8).

Fuente ÚNICA para la despensa de tipos del inspector y el submenú "Crear hijo" del
menú contextual. Listado puramente didáctico (ADR-037 §D): nunca consulta al motor,
solo tablas de vocabulario — barato, sin las N evaluaciones por candidato que tenía
antes. El motor se consulta una única vez, en el intento real de creación
(mutaciones_arbol.py), no aquí.

Niveles (padre → hijo):
  expediente → solicitud   todos los TipoSolicitud, sin distinción canónico/resto —
                            no hay taxonomía propia en este nivel (motor decide en el
                            intento real)
  solicitud  → fase        todos los TipoFase, mismo criterio
  fase       → tramite     canónicos: fases_tramites (vocabulario, ADR-037 §B); resto:
                            catálogo menos canónicos y menos los de traslado (otra vía
                            de creación — nunca aparecen aquí, ni en "resto")
  tramite    → tarea        canónicos: patrón de tramites_tareas, con la siguiente
                            marcada (es_siguiente, #719); resto: tipos fuera del patrón

Defensivo ante catálogo no disponible (REGLAS_DESARROLLO §Servicios con catálogo).
"""
from __future__ import annotations

import logging

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.models.tramites_tareas import TramiteTarea
from app.models.fases_tramites import FaseTramite

log = logging.getLogger(__name__)


def _item(tipo_id, codigo, nombre) -> dict:
    return {'tipo_id': tipo_id, 'codigo': codigo, 'nombre': nombre}


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def tipos_creables_de_nodo(expediente, tipo_nodo: str, nodo_id: int) -> dict:
    """
    Devuelve los tipos de hijo creables bajo el nodo (tipo_nodo, nodo_id) del expediente.

    Forma: {'nodo': {'tipo','id'}, 'tipo_hijo': str, 'canonicos': [item, …], 'resto': [item, …]}
    Cada item: {tipo_id, codigo, nombre} (+ es_siguiente en trámite→tarea).

    El veredicto de permiso (¿lo bloquea el motor, una regla de vocabulario, un
    invariante?) no vive aquí — llega como respuesta al intento real de creación
    (mutaciones_arbol.py). Este listado nunca evalúa nada, solo lee catálogo.

    Lanza ValueError si el nodo no existe o no pertenece al expediente.
    """
    try:
        if tipo_nodo == 'expediente':
            return _creables_solicitud(expediente, nodo_id)
        if tipo_nodo == 'solicitud':
            return _creables_fase(expediente, nodo_id)
        if tipo_nodo == 'fase':
            return _creables_tramite(expediente, nodo_id)
        if tipo_nodo == 'tramite':
            return _creables_tarea(expediente, nodo_id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('tipos_creables: catálogo no disponible — %s', exc)
        return {'nodo': {'tipo': tipo_nodo, 'id': nodo_id}, 'tipo_hijo': None,
                'canonicos': [], 'resto': []}

    raise ValueError(f"Tipo de nodo sin hijos-tipo creables: {tipo_nodo!r}")


# --- expediente → solicitud -------------------------------------------------

def _creables_solicitud(expediente, exp_id: int) -> dict:
    if exp_id != expediente.id:
        raise ValueError('El nodo expediente no coincide con el expediente de la ruta')

    tipos = [_item(t.id, t.siglas, t.descripcion)
             for t in TipoSolicitud.query.order_by(TipoSolicitud.siglas).all()]
    return {'nodo': {'tipo': 'expediente', 'id': expediente.id}, 'tipo_hijo': 'solicitud',
            'canonicos': tipos, 'resto': []}


# --- solicitud → fase ---------------------------------------------------------

def _creables_fase(expediente, sol_id: int) -> dict:
    sol = Solicitud.query.get(sol_id)
    if sol is None or sol.expediente_id != expediente.id:
        raise ValueError(f'Solicitud {sol_id} no encontrada en el expediente {expediente.id}')

    tipos = [_item(tf.id, tf.codigo, tf.nombre)
             for tf in TipoFase.query.order_by(TipoFase.codigo).all()]
    return {'nodo': {'tipo': 'solicitud', 'id': sol_id}, 'tipo_hijo': 'fase',
            'canonicos': tipos, 'resto': []}


# --- fase → tramite (vocabulario ADR-037 §B) --------------------------------

def _creables_tramite(expediente, fase_id: int) -> dict:
    fase = Fase.query.get(fase_id)
    if fase is None or fase.solicitud.expediente_id != expediente.id:
        raise ValueError(f'Fase {fase_id} no encontrada en el expediente {expediente.id}')

    canonicos_ids = {
        ft.tipo_tramite_id
        for ft in FaseTramite.query.filter_by(tipo_fase_id=fase.tipo_fase_id).all()
    }

    canonicos, resto = [], []
    for tt in TipoTramite.query.order_by(TipoTramite.codigo).all():
        if not tt.creacion_generica:
            continue
        item = _item(tt.id, tt.codigo, tt.nombre)
        (canonicos if tt.id in canonicos_ids else resto).append(item)

    return {'nodo': {'tipo': 'fase', 'id': fase_id}, 'tipo_hijo': 'tramite',
            'canonicos': canonicos, 'resto': resto}


# --- tramite → tarea (patrón no vinculante, #719/ADR-037 §C) ----------------

def _creables_tarea(expediente, tramite_id: int) -> dict:
    tramite = Tramite.query.get(tramite_id)
    if tramite is None or tramite.fase.solicitud.expediente_id != expediente.id:
        raise ValueError(f'Trámite {tramite_id} no encontrado en el expediente {expediente.id}')

    patron = (
        TramiteTarea.query
        .filter_by(tipo_tramite_id=tramite.tipo_tramite_id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    patron_ids = {p.tipo_tarea_id for p in patron}
    ya_creadas = len(tramite.tareas)
    siguiente_id = patron[ya_creadas].tipo_tarea_id if ya_creadas < len(patron) else None

    canonicos, resto = [], []
    for ta in TipoTarea.query.order_by(TipoTarea.codigo).all():
        item = _item(ta.id, ta.codigo, ta.nombre)
        if ta.id in patron_ids:
            if ta.id == siguiente_id:
                item['es_siguiente'] = True
            canonicos.append(item)
        else:
            resto.append(item)

    return {'nodo': {'tipo': 'tramite', 'id': tramite_id}, 'tipo_hijo': 'tarea',
            'canonicos': canonicos, 'resto': resto}
