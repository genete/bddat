"""API REST para generación de escritos administrativos (#167 Fase 5).

ENDPOINTS:
    1. GET  /api/escritos/plantillas?tarea_id=X — Plantillas ESFTT compatibles
    2. GET  /api/escritos/preview?plantilla_id=X&tarea_id=Y — Campos del contexto del escrito
    3. POST /api/escritos/generar — Genera el escrito (.odt, o .docx heredado), lo guarda en el
       almacén y lo vincula como consumido de la tarea
"""

import logging
from datetime import date

import jinja2
from flask import Blueprint, request, jsonify, url_for
from flask_login import current_user, login_required

from app import db
from app.models.plantillas import Plantilla
from app.models.tareas import Tarea
from app.services.almacenamiento.adaptador import AlmacenNoDisponible, MENSAJE_ALMACEN_NO_DISPONIBLE
from app.services.almacenamiento.contenido import ContenidoNoUtilizable
from app.services.codigo_seguimiento import componer_codigo
from app.services.escritos import ContextoBaseExpediente, solicitud_de, variables_destinatario
from app.services.generador_escritos import generar_escrito, componer_nombre_documento
from app.services.regeneracion_escritos import regenerar_escrito
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
    """Devuelve los campos del contexto base: lo que el escrito va a decir de este expediente.

    No propone un nombre de fichero: lo pone el sistema al generar (`componer_nombre_documento`,
    ADR-050 §C) y el usuario no lo elige ni lo cambia.
    """
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
    ctx = ContextoBaseExpediente(expediente, solicitud_de(tarea)).get_contexto()
    ctx.update(variables_destinatario(tarea))

    return jsonify(ok=True, campos=ctx)


# ------------------------------------------------------------------
# POST /api/escritos/generar — #730 (ADR-050: dos casos, sin segundo paso)
# ------------------------------------------------------------------

class _ErrorGenerar(Exception):
    """Error de validación/generación con su respuesta HTTP ya decidida.
    `extra` va tal cual al JSON de la respuesta (p. ej. `elegir_destinatario`)."""
    def __init__(self, mensaje, status, extra=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status
        self.extra = extra or {}

    def respuesta(self):
        return jsonify(ok=False, error=self.mensaje, **self.extra), self.status


def _preparar_generacion(data):
    """Valida la petición y genera los bytes del escrito.

    El nombre del fichero lo pone el sistema (`componer_nombre_documento`): el
    cuerpo de la petición no lo lleva.

    Returns:
        (tarea, expediente, plantilla, nombre_fichero, doc_bytes)

    Raises:
        _ErrorGenerar — con la respuesta de error lista para devolver.
    """
    plantilla_id = data.get('plantilla_id')
    tarea_id = data.get('tarea_id')

    if not plantilla_id or not tarea_id:
        raise _ErrorGenerar('plantilla_id y tarea_id requeridos', 400)

    plantilla = Plantilla.query.get(plantilla_id)
    if not plantilla:
        raise _ErrorGenerar('Plantilla no encontrada', 404)

    tarea, expediente = _obtener_tarea_y_expediente(tarea_id)
    if not tarea or not expediente:
        raise _ErrorGenerar('Tarea no encontrada', 404)

    # Una NOTIFICAR no produce escritos: su producido es el justificante final,
    # y vincular aquí se saltaría el bloqueo sin destinatario y el hook de
    # NOTIFICAR, que solo pasan por `editar_tarea` (#967, ADR-051 §B).
    if tarea.tipo_tarea and tarea.tipo_tarea.codigo == 'NOTIFICAR':
        raise _ErrorGenerar('Los escritos se generan en la tarea ELABORAR, no en NOTIFICAR', 422)

    if not puede_editar_expediente(expediente):
        raise _ErrorGenerar('Sin permisos de edición sobre este expediente', 403)

    _exigir_destinatario(tarea, data.get('destinatario'))

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

    return tarea, expediente, plantilla, nombre_fichero, doc_bytes


def _exigir_destinatario(tarea, eleccion):
    """Sin destinatario no se genera el escrito (#968, ADR-051 §H).

    Solo en el ELABORAR de un trámite con un destinatario único según el
    catálogo de fuentes (los ELABORAR → NOTIFICAR); la ELABORACION de la
    resolución no lleva destinatario. Si el servicio lo resuelve, se toma sin
    preguntar. Si lo elige el usuario (boletín, ayuntamiento, ministerio,
    órgano ambiental u órgano superior), la elección puede venir en la misma
    petición —`destinatario: {entidad_id, representante_entidad_id}`— y queda
    en `tramites_destinatario`; si no viene, 422 con `elegir_destinatario`:
    la fuente, el motivo y las entidades entre las que elegir.
    """
    from app.services import destinatarios_notificacion as dest_svc
    from app.services import mutaciones_arbol as mut_svc

    if not tarea.tipo_tarea or tarea.tipo_tarea.codigo != 'ELABORAR':
        return
    tramite = tarea.tramite
    resuelto = dest_svc.destinatario_del_tramite(tramite)
    if not resuelto.aplica or resuelto.destinatario is not None:
        return
    if eleccion and resuelto.elegibles:
        res = mut_svc.registrar_destinatario_tramite(
            tramite, entidad_id=eleccion.get('entidad_id'),
            representante_entidad_id=eleccion.get('representante_entidad_id'))
        if not res.ok:
            mensaje = res.error or (
                (res.bloqueo.motivo or res.bloqueo.norma_compilada) if res.bloqueo
                else 'No se pudo guardar el destinatario')
            raise _ErrorGenerar(mensaje, 422)
        if dest_svc.destinatario_del_tramite(tramite).destinatario is not None:
            return
    raise _ErrorGenerar(
        f'No se genera el escrito sin destinatario: {resuelto.motivo}.', 422,
        extra={'elegir_destinatario': {
            'fuente': resuelto.fuente,
            'motivo': resuelto.motivo,
            'entidades': [{'id': e.id, 'nombre': e.nombre_completo, 'nif': e.nif}
                          for e in resuelto.elegibles],
        }})


def _asunto_escrito(plantilla):
    asunto = plantilla.nombre
    if plantilla.variante:
        asunto += f' — {plantilla.variante}'
    return asunto


def _respuesta_generado(res, expediente):
    documento = res.documento
    return jsonify(
        ok=True,
        resultado=res.resultado,
        doc_id=documento.id,
        nombre_fichero=documento.nombre_visible(),
        enlace=url_for('expedientes.pool_descargar_documento',
                       id=expediente.id, doc_id=documento.id),
    )


@api_escritos_bp.route('/generar', methods=['POST'])
@login_required
def generar():
    """Genera el escrito y lo vincula como CONSUMIDO de la tarea (#608 — único
    caller: ElaborarEditor.jsx), con los dos casos de #730 (ADR-050).

    Sin borrador previo, el escrito se sube al almacén y se vincula. Con
    borrador, si el contenido es el mismo no se hace nada y si es distinto se
    sustituye sin preguntar (hasta la fase 5), conservando el documento: el
    cambio queda en la bitácora. El nombre lo pone el sistema.

    Respuesta: `{ok, resultado: GENERADO | SIN_CAMBIOS | SUSTITUIDO, doc_id,
    nombre_fichero, enlace}`. Errores con mensaje para el usuario: 422 si el
    contenido no es lo que dice la extensión del borrador (p. ej. una plantilla
    que ahora genera .odt sobre un borrador .docx) o el borrador aún tiene ruta
    local; 409 si el borrador está ausente o dañado en el almacén; 503 si el
    almacén no contesta.
    """
    data = request.get_json(silent=True) or {}

    try:
        tarea, expediente, plantilla, nombre_fichero, doc_bytes = _preparar_generacion(data)
    except _ErrorGenerar as e:
        return e.respuesta()

    try:
        res = regenerar_escrito(
            tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=doc_bytes,
            nombre_fichero=nombre_fichero, asunto=_asunto_escrito(plantilla),
            usuario_id=current_user.id,
        )
        db.session.flush()   # aquí saltan los validadores del modelo, antes del commit
    except AlmacenNoDisponible:
        db.session.rollback()
        return jsonify(ok=False, error=MENSAJE_ALMACEN_NO_DISPONIBLE), 503
    except ContenidoNoUtilizable as e:
        db.session.rollback()
        return jsonify(ok=False, error=str(e)), 409
    except ValueError as e:   # FormatoNoAdmitido incluido
        db.session.rollback()
        return jsonify(ok=False, error=str(e)), 422

    db.session.commit()
    return _respuesta_generado(res, expediente)
