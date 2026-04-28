"""
Invariantes estructurales del árbol ESFTT.

Checks de negocio hardcoded que el motor agnóstico no puede evaluar porque
requieren consultas al dominio BDDAT. Se invocan desde las rutas Flask ANTES
de llamar a motor_reglas.evaluar().

En el futuro estas variables pasarán como variables del dict al ContextAssembler
(tiene_hijos_abiertos, doc_producido_presente, etc.) y estos checks desaparecerán.
Por ahora viven aquí para mantener el motor agnóstico sin romper el comportamiento.
"""
from __future__ import annotations

from typing import Optional

from app import db
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.solicitudes import Solicitud
from app.services.motor_reglas import EvaluacionResult

_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALISIS', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}


def _bloquear(mensaje: str) -> EvaluacionResult:
    return EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada=mensaje, url_norma=''
    )


def check_invariante(accion: str, sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    """
    Verifica los invariantes estructurales para (accion, sujeto, entidad_id).

    Devuelve EvaluacionResult(BLOQUEAR) si se viola un invariante, None si todo OK.
    Solo cubre los casos hardcoded — si no hay regla para la combinación devuelve None.
    """
    if accion == 'BORRAR':
        return _check_borrar(sujeto, entidad_id)
    if accion == 'FINALIZAR':
        return _check_finalizar(sujeto, entidad_id)
    return None


# ---------------------------------------------------------------------------
# Borrar
# ---------------------------------------------------------------------------

def _check_borrar(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    if sujeto == 'TAREA':
        tarea = Tarea.query.get(entidad_id)
        if tarea and (tarea.documento_producido_id is not None or tarea.documento_usado_id is not None):
            return _bloquear('No se puede eliminar una tarea que ya tiene documentos asignados.')

    elif sujeto == 'TRAMITE':
        tiene_tareas = db.session.query(Tarea).filter(
            Tarea.tramite_id == entidad_id
        ).first()
        if tiene_tareas:
            return _bloquear('No se puede eliminar un trámite que ya tiene tareas.')

    elif sujeto == 'FASE':
        tiene_tramites = db.session.query(Tramite).filter(
            Tramite.fase_id == entidad_id
        ).first()
        if tiene_tramites:
            return _bloquear('No se puede eliminar una fase que ya tiene trámites.')

    elif sujeto == 'SOLICITUD':
        tiene_fases = db.session.query(Fase).filter(
            Fase.solicitud_id == entidad_id
        ).first()
        if tiene_fases:
            return _bloquear('No se puede eliminar una solicitud con fases creadas.')

    return None


# ---------------------------------------------------------------------------
# Finalizar
# ---------------------------------------------------------------------------

def _check_finalizar(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    if sujeto == 'SOLICITUD':
        # Bloqueado si alguna fase no tiene documento de resultado
        fase_sin_resultado = db.session.query(Fase).filter(
            Fase.solicitud_id == entidad_id,
            Fase.documento_resultado_id.is_(None)
        ).first()
        if fase_sin_resultado:
            return _bloquear('Hay fases sin resultado formalizado. Asocie el documento de resultado a cada fase antes de cerrar la solicitud.')

    elif sujeto == 'FASE':
        return _check_finalizar_fase(entidad_id)

    elif sujeto == 'TRAMITE':
        return _check_finalizar_tramite(entidad_id)

    elif sujeto == 'TAREA':
        return _check_finalizar_tarea(entidad_id)

    return None


def _check_finalizar_fase(fase_id: int) -> Optional[EvaluacionResult]:
    from app.models.tipos_tareas import TipoTarea
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.resultados_documentos import ResultadoDocumento
    from app.models.tipos_resultado_documentos import TipoResultadoDocumento
    tarea_incompleta = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo.in_(_TIPOS_REQUIEREN_DOC_PRODUCIDO),
            Tarea.documento_producido_id.is_(None)
        )
        .first()
    )
    if tarea_incompleta:
        return _bloquear('Hay tareas sin documento producido en esta fase. Finalice todas las tareas antes de cerrar la fase.')

    incorporar_incompleta = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .outerjoin(DocumentoTarea, DocumentoTarea.tarea_id == Tarea.id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo == 'INCORPORAR',
            DocumentoTarea.id.is_(None)
        )
        .first()
    )
    if incorporar_incompleta:
        return _bloquear('Hay tareas INCORPORAR sin documentos vinculados. Añada al menos un documento antes de cerrar la fase.')

    # Tarea NOTIFICAR con resultado INCORRECTA bloquea el cierre de la fase (#296)
    notificar_incorrecta = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(ResultadoDocumento, ResultadoDocumento.documento_id == Tarea.documento_producido_id)
        .join(TipoResultadoDocumento, TipoResultadoDocumento.id == ResultadoDocumento.tipo_resultado_documento_id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo == 'NOTIFICAR',
            TipoResultadoDocumento.efecto_tarea == 'INCORRECTA',
        )
        .first()
    )
    if notificar_incorrecta:
        return _bloquear('Hay notificaciones caducadas o fallidas en esta fase. Subsane el resultado antes de cerrar la fase.')

    return None


def _check_finalizar_tramite(tramite_id: int) -> Optional[EvaluacionResult]:
    from app.models.tipos_tareas import TipoTarea
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.resultados_documentos import ResultadoDocumento
    from app.models.tipos_resultado_documentos import TipoResultadoDocumento
    tarea_incompleta = (
        db.session.query(Tarea)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .filter(
            Tarea.tramite_id == tramite_id,
            TipoTarea.codigo.in_(_TIPOS_REQUIEREN_DOC_PRODUCIDO),
            Tarea.documento_producido_id.is_(None)
        )
        .first()
    )
    if tarea_incompleta:
        return _bloquear('Hay tareas sin ejecutar. Finalice todas las tareas antes de cerrar el trámite.')

    incorporar_incompleta = (
        db.session.query(Tarea)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .outerjoin(DocumentoTarea, DocumentoTarea.tarea_id == Tarea.id)
        .filter(
            Tarea.tramite_id == tramite_id,
            TipoTarea.codigo == 'INCORPORAR',
            DocumentoTarea.id.is_(None)
        )
        .first()
    )
    if incorporar_incompleta:
        return _bloquear('Hay tareas INCORPORAR sin documentos vinculados. Añada al menos un documento antes de cerrar el trámite.')

    # Tarea NOTIFICAR con resultado INCORRECTA bloquea el cierre del trámite (#296)
    notificar_incorrecta = (
        db.session.query(Tarea)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(ResultadoDocumento, ResultadoDocumento.documento_id == Tarea.documento_producido_id)
        .join(TipoResultadoDocumento, TipoResultadoDocumento.id == ResultadoDocumento.tipo_resultado_documento_id)
        .filter(
            Tarea.tramite_id == tramite_id,
            TipoTarea.codigo == 'NOTIFICAR',
            TipoResultadoDocumento.efecto_tarea == 'INCORRECTA',
        )
        .first()
    )
    if notificar_incorrecta:
        return _bloquear('Hay notificaciones caducadas o fallidas en este trámite. Subsane el resultado antes de cerrarlo.')

    return None


def _check_finalizar_tarea(tarea_id: int) -> Optional[EvaluacionResult]:
    tarea = Tarea.query.get(tarea_id)
    if not tarea or not tarea.tipo_tarea:
        return None

    codigo = tarea.tipo_tarea.codigo

    if codigo == 'INCORPORAR':
        if not tarea.documentos_tarea:
            return _bloquear('Falta vincular al menos un documento. Añádalo antes de finalizar la tarea.')
        return None

    if codigo in _TIPOS_REQUIEREN_DOC_PRODUCIDO and tarea.documento_producido_id is None:
        return _bloquear('Falta el documento producido. Asócielo antes de finalizar la tarea.')

    if codigo in _TIPOS_REQUIEREN_DOC_USADO and tarea.documento_usado_id is None:
        return _bloquear('Falta el documento de entrada. Asócielo antes de finalizar la tarea.')

    return None
