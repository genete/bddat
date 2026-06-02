"""
esquema_editable.py — Esquema de campos editables de un nodo del árbol (ADR-016, S3b-0).

Devuelve el contrato genérico que el inspector usa para pintar el formulario editor:
    {
      "nodo": {"tipo": str, "id": int},
      "campos": [{"campo", "etiqueta", "control", "valor", "opciones"?}, ...]
    }

`control` ∈ {text, textarea, select}.
`campo` mapea 1:1 a la clave que espera el PATCH editar de ese nivel.

Defensivo ante catálogo no disponible: degrada a campos:[] (igual que detalle_nodo).
ValueError si el nodo no pertenece al expediente (la ruta lo traduce a 404).
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_resultados_fases import TipoResultadoFase

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def esquema_de_nodo(expediente, tipo_nodo: str, nodo_id: int) -> dict:
    """
    Esquema editable del nodo (tipo_nodo, nodo_id) del expediente.

    Lanza ValueError si el nodo no existe o no pertenece al expediente.
    Degrada a campos:[] si el catálogo no está disponible.
    """
    try:
        if tipo_nodo == 'expediente':
            return _esquema_expediente(expediente, nodo_id)
        if tipo_nodo == 'solicitud':
            return _esquema_solicitud(expediente, nodo_id)
        if tipo_nodo == 'fase':
            return _esquema_fase(expediente, nodo_id)
        if tipo_nodo == 'tramite':
            return _esquema_tramite(expediente, nodo_id)
        if tipo_nodo == 'tarea':
            return _esquema_tarea(expediente, nodo_id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('esquema_editable: catálogo no disponible — %s', exc)
        return {'nodo': {'tipo': tipo_nodo, 'id': nodo_id}, 'campos': []}

    raise ValueError(f'Tipo de nodo desconocido: {tipo_nodo!r}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nombre_doc(doc) -> str:
    """Nombre legible: último segmento de la URL, o 'Documento <id>'."""
    filename = (doc.url or '').replace('\\', '/').rsplit('/', 1)[-1]
    filename = filename.split('?')[0].split('#')[0]
    return filename or f'Documento {doc.id}'


def _pool_docs(expediente) -> list[dict]:
    """Pool completo de documentos del expediente como opciones de select."""
    docs = Documento.query.filter_by(expediente_id=expediente.id).all()
    return [{'valor': d.id, 'texto': _nombre_doc(d)} for d in docs]


def _campo_textarea(campo: str, etiqueta: str, valor) -> dict:
    return {'campo': campo, 'etiqueta': etiqueta, 'control': 'textarea',
            'valor': valor}


def _campo_select(campo: str, etiqueta: str, valor,
                  opciones: list[dict]) -> dict:
    return {'campo': campo, 'etiqueta': etiqueta, 'control': 'select',
            'valor': valor, 'opciones': opciones}


# ---------------------------------------------------------------------------
# Serializadores por nivel
# ---------------------------------------------------------------------------

def _esquema_expediente(exp, exp_id: int) -> dict:
    if exp_id != exp.id:
        raise ValueError('El nodo expediente no coincide con el expediente de la ruta')
    # No editable en v1
    return {'nodo': {'tipo': 'expediente', 'id': exp.id}, 'campos': []}


def _esquema_solicitud(exp, sol_id: int) -> dict:
    sol = Solicitud.query.get(sol_id)
    if sol is None or sol.expediente_id != exp.id:
        raise ValueError(f'Solicitud {sol_id} no encontrada en el expediente {exp.id}')

    return {
        'nodo': {'tipo': 'solicitud', 'id': sol.id},
        'campos': [
            _campo_textarea('observaciones', 'Observaciones', sol.observaciones),
        ],
    }


def _esquema_fase(exp, fase_id: int) -> dict:
    fase = Fase.query.get(fase_id)
    if fase is None or fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Fase {fase_id} no encontrada en el expediente {exp.id}')

    opciones_resultado = [
        {'valor': t.id, 'texto': t.nombre}
        for t in TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
    ]
    opciones_doc = _pool_docs(exp)

    return {
        'nodo': {'tipo': 'fase', 'id': fase.id},
        'campos': [
            _campo_select('resultado_fase_id', 'Resultado',
                          fase.resultado_fase_id, opciones_resultado),
            _campo_select('documento_resultado_id', 'Documento resultado',
                          fase.documento_resultado_id, opciones_doc),
            _campo_textarea('observaciones', 'Observaciones', fase.observaciones),
        ],
    }


def _esquema_tramite(exp, tramite_id: int) -> dict:
    tr = Tramite.query.get(tramite_id)
    if tr is None or tr.fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Trámite {tramite_id} no encontrado en el expediente {exp.id}')

    return {
        'nodo': {'tipo': 'tramite', 'id': tr.id},
        'campos': [
            _campo_textarea('observaciones', 'Observaciones', tr.observaciones),
        ],
    }


def _esquema_tarea(exp, tarea_id: int) -> dict:
    ta = Tarea.query.get(tarea_id)
    if ta is None or ta.tramite.fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Tarea {tarea_id} no encontrada en el expediente {exp.id}')

    # `resultado` (NOTIFICAR) es @property de Notificacion — no editable aquí (hallazgos S3b-0)
    return {
        'nodo': {'tipo': 'tarea', 'id': ta.id},
        'campos': [
            _campo_textarea('notas', 'Notas', ta.notas),
        ],
    }
