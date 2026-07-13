"""
detalle_nodo.py — Detalle read-only de un nodo del árbol para el inspector (ADR-016 §5/§16).

El árbol (/arbol) lleva solo decoradores; el detalle fino del nodo seleccionado se
pide bajo demanda a /api/expedientes/<id>/nodo/<tipo>/<nodo_id> (§16, detalle lazy).
Este servicio construye ese payload por nivel.

Contrato del payload (acordado en implementación de #500, cierra deuda §15
«Contenido específico del inspector»):

    {
      "nodo": {"tipo": str, "id": int},
      "campos": [{"etiqueta": str, "valor": str}, ...],   # adaptativo por nivel
      "documentos": [{"id","rol","nombre","tipo_doc","fecha","enlace","externo",
                      "puede_abrir_carpeta"}, ...],
      "plazo": {"estado","fecha_limite","dias_restantes"} | null,  # solo ESPERAR_PLAZO
      "referencia": str,                                  # cadena de ancestros (§8)
    }

La cabecera (tipo + nombre + estado + semáforo) y los `agregados` los toma el front
del nodo ya cargado en el árbol (store); aquí solo va lo que el árbol NO trae.

Defensivo ante catálogo no disponible (REGLAS_DESARROLLO §Servicios con catálogo):
captura OperationalError / ProgrammingError y degrada. ValueError si el nodo no
pertenece al expediente (la ruta lo traduce a 404).
"""
from __future__ import annotations

import logging
from typing import Optional

from flask import url_for
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.services.arbol_expediente import plazo_tarea

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def detalle_de_nodo(expediente, tipo_nodo: str, nodo_id: int) -> dict:
    """
    Detalle read-only del nodo (tipo_nodo, nodo_id) del expediente.

    Lanza ValueError si el nodo no existe o no pertenece al expediente.
    Degrada a un payload mínimo si el catálogo no está disponible.
    """
    try:
        if tipo_nodo == 'expediente':
            return _detalle_expediente(expediente, nodo_id)
        if tipo_nodo == 'solicitud':
            return _detalle_solicitud(expediente, nodo_id)
        if tipo_nodo == 'fase':
            return _detalle_fase(expediente, nodo_id)
        if tipo_nodo == 'tramite':
            return _detalle_tramite(expediente, nodo_id)
        if tipo_nodo == 'tarea':
            return _detalle_tarea(expediente, nodo_id)
    except (OperationalError, ProgrammingError) as exc:
        log.warning('detalle_nodo: catálogo no disponible — %s', exc)
        return {'nodo': {'tipo': tipo_nodo, 'id': nodo_id},
                'campos': [], 'documentos': [], 'plazo': None, 'referencia': ''}

    raise ValueError(f'Tipo de nodo desconocido: {tipo_nodo!r}')


# ---------------------------------------------------------------------------
# Helpers de presentación
# ---------------------------------------------------------------------------

def _campo(etiqueta: str, valor) -> Optional[dict]:
    """Campo {etiqueta, valor}, o None si el valor es vacío (no se pinta)."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    return {'etiqueta': etiqueta, 'valor': texto}


def _campos(*pares) -> list:
    """Compacta una lista de _campo() descartando los None."""
    return [c for c in pares if c is not None]


def _fecha(d) -> Optional[str]:
    return d.strftime('%d/%m/%Y') if d else None


def _nombre_doc(doc) -> str:
    """Nombre legible: último segmento de la URL, o 'Documento <id>'.

    bddat:// no tiene fichero real que dar nombre (el "segmento" sería solo
    el id numérico, p.ej. "16") — se usa el nombre del tipo de documento.
    """
    url = doc.url or ''
    if url.startswith('bddat://'):
        return doc.tipo_doc.nombre if doc.tipo_doc else f'Documento {doc.id}'
    filename = url.replace('\\', '/').rsplit('/', 1)[-1]
    filename = filename.split('?')[0].split('#')[0]
    return filename or f'Documento {doc.id}'


def info_apertura_documento(exp_id: int, doc) -> dict:
    """Enlace de apertura + flags de acción de un documento — no depende del rol
    (aplica igual a un documento aún no enlazado a ninguna tarea, #609)."""
    url = doc.url or ''
    externo = url.startswith(('http://', 'https://'))
    return {
        'enlace': url_for('expedientes.pool_descargar_documento', id=exp_id, doc_id=doc.id),
        'externo': externo,
        # "Abrir carpeta del documento" solo aplica a ficheros locales (§8).
        'puede_abrir_carpeta': not externo and not url.startswith('bddat://'),
    }


def _serializar_documento(exp_id: int, doc, rol: str) -> dict:
    """Documento clicable para el inspector (enlace de apertura + flags de acción)."""
    return {
        'id': doc.id,
        'rol': rol,
        'nombre': _nombre_doc(doc),
        'tipo_doc': doc.tipo_doc.nombre if doc.tipo_doc else None,
        'fecha': _fecha(doc.fecha_administrativa),
        **info_apertura_documento(exp_id, doc),
    }


# ---------------------------------------------------------------------------
# Referencia (§8): cadena de ancestros «AT-1234 · AAP · Fase … · Trámite …»
# ---------------------------------------------------------------------------

def _ref_expediente(exp) -> str:
    return f'AT-{exp.numero_at}'


def _ref_solicitud(exp, sol) -> str:
    ts = sol.tipo_solicitud
    return f'{_ref_expediente(exp)} · {ts.siglas if ts else "Solicitud"}'


def _ref_fase(exp, fase) -> str:
    tf = fase.tipo_fase
    nombre = (tf.nombre if tf else None) or 'Fase'
    return f'{_ref_solicitud(exp, fase.solicitud)} · {nombre}'


def _ref_tramite(exp, tr) -> str:
    tt = tr.tipo_tramite
    nombre = (tt.nombre if tt else None) or 'Trámite'
    return f'{_ref_fase(exp, tr.fase)} · {nombre}'


def _ref_tarea(exp, ta) -> str:
    tt = ta.tipo_tarea
    nombre = (tt.nombre if tt else None) or 'Tarea'
    return f'{_ref_tramite(exp, ta.tramite)} · {nombre}'


# ---------------------------------------------------------------------------
# Serializadores por nivel
# ---------------------------------------------------------------------------

def _detalle_expediente(exp, exp_id: int) -> dict:
    if exp_id != exp.id:
        raise ValueError('El nodo expediente no coincide con el expediente de la ruta')

    proy = exp.proyecto
    titular = exp.titular
    resp = exp.responsable
    campos = _campos(
        _campo('Tipo de expediente', exp.tipo_expediente.tipo if exp.tipo_expediente else None),
        _campo('Titular', titular.nombre_completo if titular else None),
        _campo('NIF', titular.nif if titular else None),
        _campo('Responsable', _nombre_usuario(resp)),
        _campo('Heredado', 'Sí' if exp.heredado else 'No'),
        _campo('Nº de solicitudes', len(exp.solicitudes)),
        _campo('Proyecto', proy.titulo if proy else None),
        _campo('Emplazamiento', proy.emplazamiento if proy else None),
        _campo('Finalidad', proy.finalidad if proy else None),
    )
    return {
        'nodo': {'tipo': 'expediente', 'id': exp.id},
        'campos': campos,
        'documentos': [],
        'plazo': None,
        'referencia': _ref_expediente(exp),
    }


def _detalle_solicitud(exp, sol_id: int) -> dict:
    sol = Solicitud.query.get(sol_id)
    if sol is None or sol.expediente_id != exp.id:
        raise ValueError(f'Solicitud {sol_id} no encontrada en el expediente {exp.id}')

    ts = sol.tipo_solicitud
    ent = sol.entidad
    doc_sol = sol.documento_solicitud
    campos = _campos(
        _campo('Estado', sol.estado),
        _campo('Tipo', ts.descripcion if ts else None),
        _campo('Fecha de presentación',
               _fecha(doc_sol.fecha_administrativa) if doc_sol else None),
        _campo('Solicitante', ent.nombre_completo if ent else None),
        _campo('NIF', ent.nif if ent else None),
        _campo('Nº de fases', len(sol.fases)),
        _campo('Afecta a', f'Solicitud #{sol.solicitud_afectada_id}'
               if sol.solicitud_afectada_id else None),
        _campo('Observaciones', sol.observaciones),
    )
    documentos = [_serializar_documento(exp.id, doc_sol, 'CONSUMIDO')] if doc_sol else []
    return {
        'nodo': {'tipo': 'solicitud', 'id': sol.id},
        'campos': campos,
        'documentos': documentos,
        'plazo': None,
        'referencia': _ref_solicitud(exp, sol),
    }


def _detalle_fase(exp, fase_id: int) -> dict:
    fase = Fase.query.get(fase_id)
    if fase is None or fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Fase {fase_id} no encontrada en el expediente {exp.id}')

    resultado = None
    if fase.finalizada and fase.resultado_fase:
        resultado = fase.resultado_fase.nombre or fase.resultado_fase.codigo
    campos = _campos(
        _campo('Estado', fase.estado),
        _campo('Resultado', resultado),
        _campo('Nº de trámites', len(fase.tramites)),
        _campo('Observaciones', fase.observaciones),
    )
    doc_res = fase.documento_resultado
    documentos = [_serializar_documento(exp.id, doc_res, 'PRODUCIDO')] if doc_res else []
    return {
        'nodo': {'tipo': 'fase', 'id': fase.id},
        'campos': campos,
        'documentos': documentos,
        'plazo': None,
        'referencia': _ref_fase(exp, fase),
    }


def _detalle_tramite(exp, tramite_id: int) -> dict:
    tr = Tramite.query.get(tramite_id)
    if tr is None or tr.fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Trámite {tramite_id} no encontrado en el expediente {exp.id}')

    campos = _campos(
        _campo('Estado', tr.estado),
        _campo('Nº de tareas', len(tr.tareas)),
        _campo('Observaciones', tr.observaciones),
    )
    return {
        'nodo': {'tipo': 'tramite', 'id': tr.id},
        'campos': campos,
        'documentos': [],
        'plazo': None,
        'referencia': _ref_tramite(exp, tr),
    }


def _detalle_tarea(exp, tarea_id: int) -> dict:
    ta = Tarea.query.get(tarea_id)
    if ta is None or ta.tramite.fase.solicitud.expediente_id != exp.id:
        raise ValueError(f'Tarea {tarea_id} no encontrada en el expediente {exp.id}')

    tt = ta.tipo_tarea
    codigo = tt.codigo if tt else None

    campos = _campos(
        _campo('Estado', ta.estado),
        _campo('Tipo', tt.nombre if tt else None),
        _campo('Resultado de notificación', ta.resultado if codigo == 'NOTIFICAR' else None),
        _campo('Notas', ta.notas),
    )

    documentos = []
    for doc in ta.documentos_consumidos:
        documentos.append(_serializar_documento(exp.id, doc, 'CONSUMIDO'))
    producido = ta.documento_producido
    if producido is not None:
        documentos.append(_serializar_documento(exp.id, producido, 'PRODUCIDO'))

    plazo = plazo_tarea(ta, ta.tramite) if codigo == 'ESPERAR_PLAZO' else None

    return {
        'nodo': {'tipo': 'tarea', 'id': ta.id},
        'campos': campos,
        'documentos': documentos,
        'plazo': plazo,
        'referencia': _ref_tarea(exp, ta),
    }


def _nombre_usuario(u) -> Optional[str]:
    """'SIGLAS — Nombre Apellido' del responsable, o None."""
    if u is None:
        return None
    nombre = ' '.join(filter(None, [u.nombre, getattr(u, 'apellido1', None)])).strip()
    if u.siglas and nombre:
        return f'{u.siglas} — {nombre}'
    return u.siglas or nombre or None
