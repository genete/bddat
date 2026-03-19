"""API REST para generación de escritos administrativos (#167 Fase 5).

ENDPOINTS:
    1. GET  /api/escritos/plantillas?tarea_id=X — Plantillas ESFTT compatibles
    2. GET  /api/escritos/preview?plantilla_id=X&tarea_id=Y — Preview del contexto
    3. POST /api/escritos/generar — Genera el .docx y lo registra en pool
"""

import logging
from datetime import date

import jinja2
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from app import db
from app.models.plantillas import Plantilla
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.services.escritos import ContextoBaseExpediente
from app.services.generador_escritos import (
    generar_escrito,
    componer_nombre_documento,
    ruta_destino_documento,
    guardar_docx,
)
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

    # Nombre propuesto y ruta destino
    nombre = componer_nombre_documento(tarea, plantilla)
    try:
        ruta = ruta_destino_documento(expediente, nombre)
    except RuntimeError as e:
        return jsonify(ok=False, error=str(e)), 503

    return jsonify(ok=True, campos=ctx, nombre_propuesto=nombre, ruta_destino=ruta)


# ------------------------------------------------------------------
# POST /api/escritos/generar
# ------------------------------------------------------------------

@api_escritos_bp.route('/generar', methods=['POST'])
@login_required
def generar():
    """Genera el .docx, lo guarda en disco y opcionalmente lo registra en el pool."""
    data = request.get_json(silent=True) or {}
    plantilla_id = data.get('plantilla_id')
    tarea_id = data.get('tarea_id')
    nombre_fichero = data.get('nombre_fichero', '').strip()
    registrar_pool = data.get('registrar_pool', True)
    asignar_doc_producido = data.get('asignar_doc_producido', True)

    if not plantilla_id or not tarea_id:
        return jsonify(ok=False, error='plantilla_id y tarea_id requeridos'), 400

    plantilla = Plantilla.query.get(plantilla_id)
    if not plantilla:
        return jsonify(ok=False, error='Plantilla no encontrada'), 404

    tarea, expediente = _obtener_tarea_y_expediente(tarea_id)
    if not tarea or not expediente:
        return jsonify(ok=False, error='Tarea no encontrada'), 404

    # Verificar acceso edición
    if not puede_editar_expediente(expediente):
        return jsonify(ok=False, error='Sin permisos de edición sobre este expediente'), 403

    # FILESYSTEM_BASE obligatorio
    fs_base = current_app.config.get('FILESYSTEM_BASE', '')
    if not fs_base:
        return jsonify(ok=False, error='FILESYSTEM_BASE no configurado en el servidor'), 503

    # Nombre y ruta
    if not nombre_fichero:
        nombre_fichero = componer_nombre_documento(tarea, plantilla)
    ruta = ruta_destino_documento(expediente, nombre_fichero)

    # B8: Si tarea.fecha_inicio es None → establecer fecha de hoy
    if tarea.fecha_inicio is None:
        tarea.fecha_inicio = date.today()

    # Generar .docx
    try:
        docx_bytes = generar_escrito(plantilla, expediente, db.session)
    except FileNotFoundError as e:
        return jsonify(ok=False, error=f'Plantilla .docx no encontrada: {e}'), 404
    except jinja2.TemplateSyntaxError as e:
        return jsonify(ok=False, error=f'Error de sintaxis en plantilla: {e.message} (línea {e.lineno})'), 422
    except jinja2.UndefinedError as e:
        return jsonify(ok=False, error=f'Variable no definida en plantilla: {e.message}'), 422
    except RuntimeError as e:
        return jsonify(ok=False, error=str(e)), 500

    # Guardar a disco
    guardar_docx(docx_bytes, ruta)

    doc_id = None

    if registrar_pool:
        # B6: Buscar doc existente por URL (regeneración) o crear nuevo
        doc_existente = Documento.query.filter_by(
            expediente_id=expediente.id,
            url=ruta,
        ).first()

        if doc_existente:
            doc = doc_existente
            # Actualizar metadatos si cambian
            doc.tipo_doc_id = plantilla.tipo_documento_id
        else:
            # Composición del asunto: nombre plantilla + variante
            asunto = plantilla.nombre
            if plantilla.variante:
                asunto += f' — {plantilla.variante}'

            doc = Documento(
                expediente_id=expediente.id,
                url=ruta,
                tipo_doc_id=plantilla.tipo_documento_id,
                tipo_contenido='application/docx',
                fecha_administrativa=None,
                prioridad=0,
                asunto=asunto,
            )
            db.session.add(doc)

        db.session.flush()  # Para obtener doc.id si es nuevo
        doc_id = doc.id

        if asignar_doc_producido:
            tarea.documento_producido_id = doc_id

    db.session.commit()

    # URI para abrir carpeta en explorador (file:/// con barras normalizadas)
    import os
    carpeta = os.path.dirname(ruta)
    uri_explorador = 'file:///' + carpeta.replace('\\', '/')

    return jsonify(
        ok=True,
        nombre_fichero=nombre_fichero,
        ruta=ruta,
        doc_id=doc_id,
        uri_explorador=uri_explorador,
    )
