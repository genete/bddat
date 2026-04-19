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
    if sujeto in ('FASE', 'TRAMITE', 'TAREA'):
        obj = _cargar(sujeto, entidad_id)
        if obj and obj.fecha_inicio is not None:
            return _bloquear('No se puede eliminar una entidad ya iniciada.')

    elif sujeto == 'SOLICITUD':
        tiene_fase_iniciada = db.session.query(Fase).filter(
            Fase.solicitud_id == entidad_id,
            Fase.fecha_inicio.isnot(None)
        ).first()
        if tiene_fase_iniciada:
            return _bloquear('No se puede eliminar una solicitud con fases ya iniciadas.')

    return None


# ---------------------------------------------------------------------------
# Finalizar
# ---------------------------------------------------------------------------

def _check_finalizar(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    if sujeto == 'SOLICITUD':
        fase_abierta = db.session.query(Fase).filter(
            Fase.solicitud_id == entidad_id,
            Fase.fecha_fin.is_(None)
        ).first()
        if fase_abierta:
            return _bloquear('Hay fases sin cerrar. Finalice todas las fases antes de cerrar la solicitud.')

    elif sujeto == 'FASE':
        tramite_abierto = db.session.query(Tramite).filter(
            Tramite.fase_id == entidad_id,
            Tramite.fecha_fin.is_(None)
        ).first()
        if tramite_abierto:
            return _bloquear('Hay trámites sin cerrar. Finalice todos los trámites antes de cerrar la fase.')

    elif sujeto == 'TRAMITE':
        tarea_abierta = db.session.query(Tarea).filter(
            Tarea.tramite_id == entidad_id,
            Tarea.fecha_fin.is_(None)
        ).first()
        if tarea_abierta:
            return _bloquear('Hay tareas sin ejecutar. Finalice todas las tareas antes de cerrar el trámite.')

    elif sujeto == 'TAREA':
        return _check_finalizar_tarea(entidad_id)

    return None


_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'INCORPORAR', 'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALISIS', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}


def _check_finalizar_tarea(tarea_id: int) -> Optional[EvaluacionResult]:
    tarea = Tarea.query.get(tarea_id)
    if not tarea or not tarea.tipo_tarea:
        return None

    codigo = tarea.tipo_tarea.codigo

    if codigo in _TIPOS_REQUIEREN_DOC_PRODUCIDO and tarea.documento_producido_id is None:
        return _bloquear('Falta el documento producido. Asócielo antes de finalizar la tarea.')

    if codigo in _TIPOS_REQUIEREN_DOC_USADO and tarea.documento_usado_id is None:
        return _bloquear('Falta el documento de entrada. Asócielo antes de finalizar la tarea.')

    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cargar(sujeto: str, entidad_id: int):
    modelos = {'FASE': Fase, 'TRAMITE': Tramite, 'TAREA': Tarea}
    modelo = modelos.get(sujeto)
    return modelo.query.get(entidad_id) if modelo else None
