"""
esquema_editable.py — Esquema de campos editables de un nodo del árbol (ADR-016, S3b-0).

Devuelve el contrato genérico que el inspector usa para pintar el formulario editor:
    {
      "nodo": {"tipo": str, "id": int},
      "campos": [{"campo", "etiqueta", "control", "valor", "opciones"?,
                  "texto_vacio"?, "aviso"?}, ...]
    }

`control` ∈ {text, textarea, select}.
`campo` mapea 1:1 a la clave que espera el PATCH editar de ese nivel.
Solo en los select: `texto_vacio` es lo que dice la opción de no elegir (por defecto
«—») y `aviso`, por qué el valor guardado ya no es una opción posible (#1038).

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
from app.models.organismos_expediente import OrganismoExpediente, VIAS_ORGANISMO, RESULTADOS_ORGANISMO
from app.models.direccion_notificacion import DireccionNotificacion
from app.services import notificaciones as notif_svc

log =logging.getLogger(__name__)


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
        if tipo_nodo == 'organismo':
            return _esquema_organismo(expediente, nodo_id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('esquema_editable: catálogo no disponible — %s', exc)
        return {'nodo': {'tipo': tipo_nodo, 'id': nodo_id}, 'campos': []}

    raise ValueError(f'Tipo de nodo desconocido: {tipo_nodo!r}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pool_docs(expediente) -> list[dict]:
    """Pool completo de documentos del expediente como opciones de select."""
    docs = Documento.query.filter_by(expediente_id=expediente.id).all()
    return [{'valor': d.id, 'texto': d.nombre_visible()} for d in docs]


def _campo_textarea(campo: str, etiqueta: str, valor) -> dict:
    return {'campo': campo, 'etiqueta': etiqueta, 'control': 'textarea',
            'valor': valor}


def _campo_select(campo: str, etiqueta: str, valor,
                  opciones: list[dict], *, texto_vacio: Optional[str] = None,
                  aviso: Optional[str] = None) -> dict:
    d = {'campo': campo, 'etiqueta': etiqueta, 'control': 'select',
         'valor': valor, 'opciones': opciones}
    if texto_vacio:
        d['texto_vacio'] = texto_vacio
    if aviso:
        d['aviso'] = aviso
    return d


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

    # Representante y sede (#1038, ADR-051 §K): se eligen de las mismas listas que ofrece
    # el alta y que acepta el guardado. Si el valor guardado ya no es una opción (se
    # revocó la autorización, se dio de baja la sede), llega tal cual con el `aviso` del
    # motivo, en vez de desaparecer: el desplegable lo enseña vacío y marcado.
    solicitante = sol.entidad
    representantes = notif_svc.representantes_posibles(solicitante) if solicitante else []
    sedes = notif_svc.sedes_posibles(solicitante) if solicitante else []
    no_vigentes = notif_svc.datos_no_vigentes(sol)

    return {
        'nodo': {'tipo': 'solicitud', 'id': sol.id},
        'campos': [
            _campo_textarea('observaciones', 'Observaciones', sol.observaciones),
            _campo_select(
                'representante_entidad_id', 'Representante', sol.representante_entidad_id,
                [{'valor': e.id, 'texto': notif_svc.texto_representante(e)} for e in representantes],
                texto_vacio=notif_svc.SIN_REPRESENTANTE,
                aviso=no_vigentes.get('representante_entidad_id')),
            _campo_select(
                'direccion_notificacion_id', 'Sede de notificación', sol.direccion_notificacion_id,
                [{'valor': d.id, 'texto': notif_svc.texto_sede(d)} for d in sedes],
                texto_vacio=notif_svc.SIN_SEDE,
                aviso=no_vigentes.get('direccion_notificacion_id')),
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
    campos = [_campo_select('resultado_fase_id', 'Resultado',
                            fase.resultado_fase_id, opciones_resultado)]
    # Las finalizadoras se cierran con su certificado de cierre, nunca eligiendo un
    # documento (#956, D6): sin el campo, el formulario no lo envía y `editar_fase`
    # conserva el que haya.
    if not (fase.tipo_fase and fase.tipo_fase.es_finalizadora):
        campos.append(_campo_select('documento_resultado_id', 'Documento resultado',
                                    fase.documento_resultado_id, _pool_docs(exp)))
    campos.append(_campo_textarea('observaciones', 'Observaciones', fase.observaciones))

    return {'nodo': {'tipo': 'fase', 'id': fase.id}, 'campos': campos}


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


def _esquema_organismo(exp, organismo_id: int) -> dict:
    oe = OrganismoExpediente.query.get(organismo_id)
    if oe is None or oe.expediente_id != exp.id:
        raise ValueError(f'Organismo {organismo_id} no encontrado en el expediente {exp.id}')

    opciones_via = [{'valor': v, 'texto': v} for v in VIAS_ORGANISMO]
    # 'exonerado' no se ofrece: lo deriva la vía (mutaciones_arbol.editar_organismo),
    # no se elige campo a campo (DISEÑO_CONSULTAS_ORGANISMOS.md §2).
    opciones_resultado = [
        {'valor': r, 'texto': r} for r in RESULTADOS_ORGANISMO if r != 'exonerado'
    ]
    direcciones = DireccionNotificacion.query.filter(
        DireccionNotificacion.entidad_id == oe.organismo_id,
        DireccionNotificacion.tipo_rol.op('&')(2) > 0,  # bit CONSULTADO
    ).all()
    opciones_direccion = [
        {'valor': d.id, 'texto': d.descripcion or d.email or f'Dirección {d.id}'}
        for d in direcciones
    ]
    opciones_doc = _pool_docs(exp)

    return {
        'nodo': {'tipo': 'organismo', 'id': oe.id},
        'campos': [
            _campo_select('via', 'Vía', oe.via, opciones_via),
            _campo_select('resultado', 'Resultado', oe.resultado, opciones_resultado),
            _campo_select('direccion_notificacion_id', 'Dirección de notificación',
                          oe.direccion_notificacion_id, opciones_direccion),
            _campo_select('documento_id', 'Documento (declaración responsable)',
                          oe.documento_id, opciones_doc),
        ],
    }
