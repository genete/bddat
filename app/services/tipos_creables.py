"""
tipos_creables.py — Tipos de hijo creables bajo un nodo del árbol (ADR-016 §16, §8).

Fuente ÚNICA para la despensa de tipos del inspector y el submenú "Crear hijo" del
menú contextual. Para cada tipo candidato consulta el motor (evaluar_multi + modo
global) y devuelve permitido / no-permitido con su norma + motivo, de modo que el
front pueda pintar los permitidos en la despensa y los no-permitidos atenuados con
tooltip al activar "Mostrar todos…".

Niveles (padre → hijo):
  expediente → solicitud   candidatos: todos los TipoSolicitud (stub transiente, como api_bc)
  solicitud  → fase        candidatos: todos los TipoFase
  fase       → tramite     candidatos: todos los TipoTramite (los de traslado, no creables aquí)
  tramite    → tarea        candidatos: patrón FTT tramites_tareas; el motor solo veta global
                            (el sujeto ESFTT no tiene segmento de tarea → no discrimina por tipo)

Defensivo ante catálogo no disponible (REGLAS_DESARROLLO §Servicios con catálogo).
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.models.tramites_tareas import TramiteTarea
from app.models.configuracion_sistema import ConfiguracionSistema
from app.services.assembler import evaluar_multi
from app.services.motor_reglas import EvaluacionResult, PERMITIDO

log = logging.getLogger(__name__)

# Trámites que NO se crean por la vía genérica (se crean desde la acción de organismo).
# Espejo de api_bc._CODIGOS_TRASLADO — mantener sincronizado.
_CODIGOS_TRASLADO = frozenset({'CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR'})


# ---------------------------------------------------------------------------
# Modo global del motor
# DEUDA: duplica api_bc._aplicar_modo_global. Unificar en un helper del motor
# (BDDAT-aware, p.ej. assembler) cuando se toque api_bc — no hacerlo ahora para
# no arriesgar el flujo de creación en producción.
# ---------------------------------------------------------------------------

def _aplicar_modo_global(res: EvaluacionResult) -> EvaluacionResult:
    modo = ConfiguracionSistema.get('motor.modo_operacion', 'BLOQUEAR')
    if modo == 'INACTIVO':
        return PERMITIDO
    if modo == 'SOLO_ADVERTIR' and res.nivel == 'BLOQUEAR':
        return EvaluacionResult(
            permitido=True, nivel='ADVERTIR',
            variables_trigger=res.variables_trigger,
            norma_compilada=res.norma_compilada,
            url_norma=res.url_norma,
            motivo=res.motivo,
        )
    return res


def _evaluar_creacion(expediente, objeto) -> EvaluacionResult:
    """evaluar_multi('CREAR', …) + modo global. Defensivo: error → no-permitido."""
    try:
        return _aplicar_modo_global(evaluar_multi('CREAR', expediente, objeto=objeto))
    except Exception as exc:  # noqa: BLE001 — un candidato no debe tumbar la despensa
        log.warning('tipos_creables: fallo evaluando creación %s: %s', objeto, exc)
        return EvaluacionResult(
            permitido=False, nivel='BLOQUEAR', variables_trigger={},
            norma_compilada='', url_norma='', motivo='No se pudo evaluar (ver logs)',
        )


def _item(tipo_id, codigo, nombre, res: EvaluacionResult) -> dict:
    """Empaqueta un candidato con el veredicto del motor."""
    item = {'tipo_id': tipo_id, 'codigo': codigo, 'nombre': nombre, 'permitido': res.permitido}
    if not res.permitido:
        item['motivo'] = res.motivo
        item['norma'] = res.norma_compilada
        item['url_norma'] = res.url_norma
    elif res.nivel == 'ADVERTIR':
        item['advertencia'] = {'motivo': res.motivo, 'norma': res.norma_compilada, 'url_norma': res.url_norma}
    return item


def _item_estructural(tipo_id, codigo, nombre, permitido, motivo='') -> dict:
    """Candidato cuyo permitido/no viene de la estructura FTT, no del motor (tareas no-patrón)."""
    item = {'tipo_id': tipo_id, 'codigo': codigo, 'nombre': nombre, 'permitido': permitido}
    if not permitido:
        item['motivo'] = motivo
        item['norma'] = ''
        item['url_norma'] = ''
    return item


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def tipos_creables_de_nodo(expediente, tipo_nodo: str, nodo_id: int) -> dict:
    """
    Devuelve los tipos de hijo creables bajo el nodo (tipo_nodo, nodo_id) del expediente.

    Forma: {'nodo': {'tipo','id'}, 'tipo_hijo': str, 'tipos': [item, …]}
    Cada item: {tipo_id, codigo, nombre, permitido} (+ motivo/norma/url_norma si no permitido).

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
        return {'nodo': {'tipo': tipo_nodo, 'id': nodo_id}, 'tipo_hijo': None, 'tipos': []}

    raise ValueError(f"Tipo de nodo sin hijos-tipo creables: {tipo_nodo!r}")


# --- expediente → solicitud -------------------------------------------------

def _creables_solicitud(expediente, exp_id: int) -> dict:
    if exp_id != expediente.id:
        raise ValueError('El nodo expediente no coincide con el expediente de la ruta')

    tipos = []
    for tipo in TipoSolicitud.query.order_by(TipoSolicitud.siglas).all():
        # Stub transiente con tipo_solicitud precargado (igual que api_bc.crear_solicitud)
        stub = Solicitud(expediente_id=expediente.id,
                         entidad_id=expediente.titular_id,
                         tipo_solicitud_id=tipo.id)
        stub.tipo_solicitud = tipo
        res = _evaluar_creacion(expediente, stub)
        tipos.append(_item(tipo.id, tipo.siglas, tipo.descripcion, res))

    return {'nodo': {'tipo': 'expediente', 'id': expediente.id}, 'tipo_hijo': 'solicitud', 'tipos': tipos}


# --- solicitud → fase -------------------------------------------------------

def _creables_fase(expediente, sol_id: int) -> dict:
    sol = Solicitud.query.get(sol_id)
    if sol is None or sol.expediente_id != expediente.id:
        raise ValueError(f'Solicitud {sol_id} no encontrada en el expediente {expediente.id}')

    tipos = []
    for tf in TipoFase.query.order_by(TipoFase.codigo).all():
        res = _evaluar_creacion(expediente, {'solicitud': sol, 'tipo_fase': tf})
        tipos.append(_item(tf.id, tf.codigo, tf.nombre, res))

    return {'nodo': {'tipo': 'solicitud', 'id': sol_id}, 'tipo_hijo': 'fase', 'tipos': tipos}


# --- fase → tramite ---------------------------------------------------------

def _creables_tramite(expediente, fase_id: int) -> dict:
    fase = Fase.query.get(fase_id)
    if fase is None or fase.solicitud.expediente_id != expediente.id:
        raise ValueError(f'Fase {fase_id} no encontrada en el expediente {expediente.id}')

    tipos = []
    for tt in TipoTramite.query.order_by(TipoTramite.codigo).all():
        if tt.codigo in _CODIGOS_TRASLADO:
            tipos.append(_item_estructural(
                tt.id, tt.codigo, tt.nombre, permitido=False,
                motivo='Los trámites de traslado se crean desde la acción específica de organismo'))
            continue
        res = _evaluar_creacion(expediente, {'fase': fase, 'tipo_tramite': tt})
        tipos.append(_item(tt.id, tt.codigo, tt.nombre, res))

    return {'nodo': {'tipo': 'fase', 'id': fase_id}, 'tipo_hijo': 'tramite', 'tipos': tipos}


# --- tramite → tarea (patrón FTT; el motor solo veta global) ----------------

def _creables_tarea(expediente, tramite_id: int) -> dict:
    tramite = Tramite.query.get(tramite_id)
    if tramite is None or tramite.fase.solicitud.expediente_id != expediente.id:
        raise ValueError(f'Trámite {tramite_id} no encontrado en el expediente {expediente.id}')

    # Tipos de tarea del patrón FTT del tipo de trámite (los "creables" por defecto).
    patron_ids = {
        r.tipo_tarea_id
        for r in TramiteTarea.query.filter_by(tipo_tramite_id=tramite.tipo_tramite_id).all()
    }

    # Veto global del motor: el sujeto ESFTT no varía por tipo de tarea, así que una
    # sola evaluación decide si CREAR-tarea-en-este-trámite está permitido en general.
    repr_tarea = TipoTarea.query.filter(TipoTarea.id.in_(patron_ids)).first() if patron_ids else None
    if repr_tarea is None:
        repr_tarea = TipoTarea.query.first()
    veto = _evaluar_creacion(expediente, {'tramite': tramite, 'tipo_tarea': repr_tarea}) if repr_tarea else PERMITIDO

    tipos = []
    for ta in TipoTarea.query.order_by(TipoTarea.codigo).all():
        if not veto.permitido:
            # El motor veta toda creación de tarea aquí: todos no-permitidos con su norma.
            tipos.append(_item(ta.id, ta.codigo, ta.nombre, veto))
        elif ta.id in patron_ids:
            tipos.append(_item_estructural(ta.id, ta.codigo, ta.nombre, permitido=True))
        else:
            tipos.append(_item_estructural(
                ta.id, ta.codigo, ta.nombre, permitido=False,
                motivo='No forma parte del patrón de tareas de este tipo de trámite'))

    return {'nodo': {'tipo': 'tramite', 'id': tramite_id}, 'tipo_hijo': 'tarea', 'tipos': tipos}
