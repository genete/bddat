"""API REST para generación de escritos administrativos (#167 Fase 5).

ENDPOINTS:
    1. GET  /api/escritos/plantillas?tarea_id=X — Plantillas ESFTT compatibles
    2. GET  /api/escritos/preview?plantilla_id=X&tarea_id=Y — Preview del contexto
    3. POST /api/escritos/generar — Genera el escrito (.docx o .odt) y lo registra en pool
"""

import logging
import os
from datetime import date

import jinja2
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from app import db
from app.models.plantillas import Plantilla
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.services.codigo_seguimiento import componer_codigo
from app.services.escritos import ContextoBaseExpediente
from app.services.generador_escritos import (
    generar_escrito,
    componer_nombre_documento,
    guardar_documento,
    tipo_contenido_documento,
)
from app.services.regeneracion_escritos import evaluar_regeneracion, ejecutar_regeneracion
from app.services.rutas_esftt import ruta_destino_esftt_fichero
from app.utils.permisos import puede_editar_expediente

logger = logging.getLogger(__name__)

api_escritos_bp = Blueprint('api_escritos', __name__, url_prefix='/api/escritos')


# ------------------------------------------------------------------
# Helpers internos
# ------------------------------------------------------------------

def _obtener_tarea_y_expediente(tarea_id):
    """Obtiene tarea, sube por la cadena ESFTT y devuelve (tarea, expediente) o None."""
    tarea = Tarea.query.get(tarea_id)
    if not tarea:
        return None, None
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None
    return tarea, expediente


def _ids_esftt(tarea):
    """Extrae los IDs ESFTT de la cadena tarea → tramite → fase → solicitud → expediente."""
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None

    return {
        'te_id': expediente.tipo_expediente_id if expediente else None,
        'ts_id': solicitud.tipo_solicitud_id if solicitud else None,
        'tf_id': fase.tipo_fase_id if fase else None,
        'tt_id': tramite.tipo_tramite_id if tramite else None,
    }


def _especificidad(plantilla):
    """Cuenta campos ESFTT no-NULL (0-4) para ordenar por especificidad."""
    return sum(1 for f in [
        plantilla.tipo_expediente_id,
        plantilla.tipo_solicitud_id,
        plantilla.tipo_fase_id,
        plantilla.tipo_tramite_id,
    ] if f is not None)


# ------------------------------------------------------------------
# GET /api/escritos/plantillas?tarea_id=X
# ------------------------------------------------------------------

@api_escritos_bp.route('/plantillas')
@login_required
def listar_plantillas():
    """Devuelve plantillas activas compatibles con el contexto ESFTT de la tarea."""
    tarea_id = request.args.get('tarea_id', type=int)
    if not tarea_id:
        return jsonify(ok=False, error='Parámetro tarea_id requerido'), 400

    tarea, expediente = _obtener_tarea_y_expediente(tarea_id)
    if not tarea or not expediente:
        return jsonify(ok=False, error='Tarea no encontrada'), 404

    ids = _ids_esftt(tarea)

    # Query NULL-comodín: NULL en plantilla = aplica a cualquier valor
    plantillas = Plantilla.query.filter(
        Plantilla.activo == True,
        db.or_(Plantilla.tipo_expediente_id == None, Plantilla.tipo_expediente_id == ids['te_id']),
        db.or_(Plantilla.tipo_solicitud_id == None, Plantilla.tipo_solicitud_id == ids['ts_id']),
        db.or_(Plantilla.tipo_fase_id == None, Plantilla.tipo_fase_id == ids['tf_id']),
        db.or_(Plantilla.tipo_tramite_id == None, Plantilla.tipo_tramite_id == ids['tt_id']),
    ).all()

    resultado = [{
        'id': p.id,
        'nombre': p.nombre,
        'variante': p.variante,
        'descripcion': p.descripcion,
        'especificidad': _especificidad(p),
    } for p in plantillas]

    # Ordenar: más específicas primero
    resultado.sort(key=lambda x: x['especificidad'], reverse=True)

    return jsonify(ok=True, plantillas=resultado)


# ------------------------------------------------------------------
# GET /api/escritos/preview?plantilla_id=X&tarea_id=Y
# ------------------------------------------------------------------

@api_escritos_bp.route('/preview')
@login_required
def preview():
    """Devuelve campos del contexto base, nombre propuesto y ruta destino."""
    plantilla_id = request.args.get('plantilla_id', type=int)
    tarea_id = request.args.get('tarea_id', type=int)
    if not plantilla_id or not tarea_id:
        return jsonify(ok=False, error='Parámetros plantilla_id y tarea_id requeridos'), 400

    plantilla = Plantilla.query.get(plantilla_id)
    if not plantilla:
        return jsonify(ok=False, error='Plantilla no encontrada'), 404

    tarea, expediente = _obtener_tarea_y_expediente(tarea_id)
    if not tarea or not expediente:
        return jsonify(ok=False, error='Tarea no encontrada'), 404

    # Contexto base (campos para preview)
    ctx = ContextoBaseExpediente(expediente).get_contexto()

    # Nombre propuesto y ruta destino (ESFTT definitiva, #730 — ya no un
    # intermedio en AT-N raíz que había que mover después)
    nombre = componer_nombre_documento(tarea, plantilla)
    try:
        ruta = ruta_destino_esftt_fichero(tarea, nombre)
    except RuntimeError as e:
        return jsonify(ok=False, error=str(e)), 503

    return jsonify(ok=True, campos=ctx, nombre_propuesto=nombre, ruta_destino=ruta)


# ------------------------------------------------------------------
# POST /api/escritos/generar (+ /generar/confirmar) — #730
# ------------------------------------------------------------------

class _ErrorGenerar(Exception):
    """Error de validación/generación con su respuesta HTTP ya decidida.
    Común a /generar y /generar/confirmar para no duplicar las 6 comprobaciones."""
    def __init__(self, mensaje, status):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def _preparar_generacion(data):
    """Valida la petición y genera los bytes del escrito.

    Returns:
        (tarea, expediente, plantilla, nombre_fichero, doc_bytes, fs_base)

    Raises:
        _ErrorGenerar — con la respuesta de error lista para devolver.
    """
    plantilla_id = data.get('plantilla_id')
    tarea_id = data.get('tarea_id')
    nombre_fichero = (data.get('nombre_fichero') or '').strip()

    if not plantilla_id or not tarea_id:
        raise _ErrorGenerar('plantilla_id y tarea_id requeridos', 400)

    plantilla = Plantilla.query.get(plantilla_id)
    if not plantilla:
        raise _ErrorGenerar('Plantilla no encontrada', 404)

    tarea, expediente = _obtener_tarea_y_expediente(tarea_id)
    if not tarea or not expediente:
        raise _ErrorGenerar('Tarea no encontrada', 404)

    if not puede_editar_expediente(expediente):
        raise _ErrorGenerar('Sin permisos de edición sobre este expediente', 403)

    fs_base = current_app.config.get('FILESYSTEM_BASE', '')
    if not fs_base:
        raise _ErrorGenerar('FILESYSTEM_BASE no configurado en el servidor', 503)

    if not nombre_fichero:
        nombre_fichero = componer_nombre_documento(tarea, plantilla)

    # Código de seguimiento (#182) se compone siempre; el motor .docx lo
    # ignora con un warning porque ningún canal de metadatos OOXML sobrevive
    # al pipeline (ADR-035).
    codigo_seguimiento = componer_codigo(tarea.id)
    try:
        doc_bytes = generar_escrito(plantilla, expediente, db.session, tarea=tarea,
                                    codigo_seguimiento=codigo_seguimiento)
    except FileNotFoundError as e:
        raise _ErrorGenerar(f'Plantilla no encontrada: {e}', 404)
    except jinja2.TemplateSyntaxError as e:
        raise _ErrorGenerar(f'Error de sintaxis en plantilla: {e.message} (línea {e.lineno})', 422)
    except jinja2.UndefinedError as e:
        raise _ErrorGenerar(f'Variable no definida en plantilla: {e.message}', 422)
    except (RuntimeError, ValueError) as e:
        raise _ErrorGenerar(str(e), 500)

    return tarea, expediente, plantilla, nombre_fichero, doc_bytes, fs_base


def _asunto_escrito(plantilla):
    asunto = plantilla.nombre
    if plantilla.variante:
        asunto += f' — {plantilla.variante}'
    return asunto


def _uri_explorador(ruta_abs):
    return 'file:///' + os.path.dirname(ruta_abs).replace('\\', '/')


def _respuesta_generado(documento, caso):
    ruta_abs = documento.ruta_absoluta()
    return jsonify(
        ok=True,
        caso=caso,
        nombre_fichero=os.path.basename(ruta_abs),
        ruta=ruta_abs,
        doc_id=documento.id,
        uri_explorador=_uri_explorador(ruta_abs),
    )


def _generar_producido(tarea, expediente, plantilla, doc_bytes, nombre_fichero, ruta):
    """Circuito PRODUCIDO histórico (#167 B6), sin tocar su lógica de
    identidad — fuera de alcance de #730 (reasignar un documento PRODUCIDO ya
    firmado es un problema propio, ligado a automatizar firma+asignación sin
    intervención del usuario; tendrá su propio issue). Solo cambia de dónde
    sale `ruta` (ESFTT definitiva en vez del intermedio en AT-N raíz)."""
    from app.models.documentos_tarea import DocumentoTarea
    from app.services.mutaciones_arbol import _hook_717_elaborar_consumido_diagnostico

    fs_base = current_app.config.get('FILESYSTEM_BASE', '')
    guardar_documento(doc_bytes, ruta)
    ruta_relativa = os.path.relpath(ruta, fs_base).replace(os.sep, '/')

    doc_existente = Documento.query.filter_by(
        expediente_id=expediente.id, url=ruta_relativa,
    ).first()

    if doc_existente:
        doc = doc_existente
        doc.tipo_doc_id = plantilla.tipo_documento_id
    else:
        doc = Documento(
            expediente_id=expediente.id,
            url=ruta_relativa,
            tipo_doc_id=plantilla.tipo_documento_id,
            tipo_contenido=tipo_contenido_documento(nombre_fichero),
            fecha_administrativa=None,
            prioridad=0,
            asunto=_asunto_escrito(plantilla),
        )
        db.session.add(doc)

    db.session.flush()
    doc_id = doc.id

    existente = next((v for v in tarea.vinculos_documento if v.rol == 'PRODUCIDO'), None)
    id_producido_previo = existente.documento_id if existente else None
    if existente:
        existente.documento_id = doc_id
    else:
        tarea.vinculos_documento.append(DocumentoTarea(documento_id=doc_id, rol='PRODUCIDO'))

    if doc_id != id_producido_previo:
        db.session.flush()
        _hook_717_elaborar_consumido_diagnostico(tarea, doc_id)

    db.session.commit()
    return jsonify(ok=True, nombre_fichero=nombre_fichero, ruta=ruta, doc_id=doc_id,
                   uri_explorador=_uri_explorador(ruta))


@api_escritos_bp.route('/generar', methods=['POST'])
@login_required
def generar():
    """Genera el escrito.

    - registrar_pool=False: comportamiento histórico, solo disco, sin BD.
    - asignar_doc_producido=True: circuito PRODUCIDO, ver _generar_producido.
    - Caso real (CONSUMIDO, #608 — único caller: ElaborarEditor.jsx): pasa por
      la matriz de #730. Si hace falta decisión del usuario (colisión de
      nombre o sustitución de contenido) no escribe nada y devuelve el caso
      para que el frontend pida confirmación vía /generar/confirmar.
    """
    data = request.get_json(silent=True) or {}
    registrar_pool = data.get('registrar_pool', True)
    asignar_doc_producido = data.get('asignar_doc_producido', True)

    try:
        tarea, expediente, plantilla, nombre_fichero, doc_bytes, fs_base = _preparar_generacion(data)
    except _ErrorGenerar as e:
        return jsonify(ok=False, error=e.mensaje), e.status

    ruta = ruta_destino_esftt_fichero(tarea, nombre_fichero)

    if not registrar_pool:
        guardar_documento(doc_bytes, ruta)
        return jsonify(ok=True, nombre_fichero=os.path.basename(ruta), ruta=ruta,
                       doc_id=None, uri_explorador=_uri_explorador(ruta))

    if asignar_doc_producido:
        return _generar_producido(tarea, expediente, plantilla, doc_bytes, nombre_fichero, ruta)

    evaluacion = evaluar_regeneracion(
        tarea=tarea, rol='CONSUMIDO', tipo_doc_id=plantilla.tipo_documento_id,
        doc_bytes=doc_bytes, nombre_fichero=nombre_fichero, ruta_destino_abs=ruta,
    )

    if evaluacion.requiere_confirmacion:
        return jsonify(
            ok=True,
            requiere_confirmacion=True,
            caso=evaluacion.caso,
            nombre_fichero=nombre_fichero,
            documento_existente_id=(
                evaluacion.documento_existente.id if evaluacion.documento_existente else None
            ),
            colision_nombre=evaluacion.colision_nombre,
        )

    documento = ejecutar_regeneracion(
        tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=doc_bytes,
        nombre_fichero=nombre_fichero, ruta_destino_abs=ruta, fs_base=fs_base,
        rol='CONSUMIDO', asunto=_asunto_escrito(plantilla), evaluacion=evaluacion,
    )
    db.session.commit()
    return _respuesta_generado(documento, evaluacion.caso)


@api_escritos_bp.route('/generar/confirmar', methods=['POST'])
@login_required
def generar_confirmar():
    """Segundo paso de la regeneración (#730): ejecuta la decisión que el
    usuario tomó en el popup correspondiente al caso devuelto por /generar.

    Regenera el documento en vez de guardar bytes entre peticiones — el motor
    es determinista (misma plantilla + mismos datos → mismos bytes), y es más
    simple que mantener un estado de sesión intermedio.

    decision: 'continuar' (casos 6/7, sin colisión) | 'cancelar' |
              'renombrar_nuevo' | 'renombrar_existente' (casos 2/5/8).
    """
    data = request.get_json(silent=True) or {}
    decision = data.get('decision')

    if decision == 'cancelar':
        return jsonify(ok=True, cancelado=True)

    try:
        tarea, expediente, plantilla, nombre_fichero, doc_bytes, fs_base = _preparar_generacion(data)
    except _ErrorGenerar as e:
        return jsonify(ok=False, error=e.mensaje), e.status

    ruta = ruta_destino_esftt_fichero(tarea, nombre_fichero)
    evaluacion = evaluar_regeneracion(
        tarea=tarea, rol='CONSUMIDO', tipo_doc_id=plantilla.tipo_documento_id,
        doc_bytes=doc_bytes, nombre_fichero=nombre_fichero, ruta_destino_abs=ruta,
    )

    decision_colision = decision if decision in ('renombrar_nuevo', 'renombrar_existente') else None
    if evaluacion.colision_nombre and decision_colision is None:
        return jsonify(ok=False, error='Falta indicar cómo resolver la colisión de nombre'), 400

    documento = ejecutar_regeneracion(
        tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=doc_bytes,
        nombre_fichero=nombre_fichero, ruta_destino_abs=ruta, fs_base=fs_base,
        rol='CONSUMIDO', asunto=_asunto_escrito(plantilla), evaluacion=evaluacion,
        decision_colision=decision_colision,
    )
    db.session.commit()
    return _respuesta_generado(documento, evaluacion.caso)
