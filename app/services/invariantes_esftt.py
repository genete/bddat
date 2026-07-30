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

_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'ANALIZAR', 'ELABORAR', 'NOTIFICAR'}
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALIZAR', 'NOTIFICAR'}

# Trámites cuyos ANALIZAR encadenan diagnósticos: cada vuelta de subsanación revisa lo
# mismo que la anterior y la supera (#711). Fuera de esta lista los diagnósticos de una
# fase son paralelos —un CONSULTA_SEPARATA por organismo— y ninguno supera a otro.
# Capa "casos especiales (código)" del catálogo; si algún día aparecen más cadenas,
# el sitio natural sería un flag en `tipos_tramites`, no alargar esta lista.
#
# Público desde #714: la vigencia de un diagnóstico dentro de la cadena la consultan dos
# reglas simétricas —el cierre de fase (aquí) y la reversión (services/diagnosticos.py)—
# y deben leer el mismo criterio para no divergir.
TRAMITES_CADENA_SUBSANACION = frozenset({'ANALISIS_DOCUMENTAL', 'REQUERIMIENTO_SUBSANACION'})

# Códigos de resultado de fase finalizadora que se consideran resolución favorable.
# Usado por tiene_solicitud_aap_favorable (art. 131.1 párr. 2 RD 1955/2000).
RESULTADO_FASE_FAVORABLE_CODIGOS = frozenset({'FAVORABLE', 'FAVORABLE_CONDICIONADO'})


def _bloquear(mensaje: str) -> EvaluacionResult:
    # CONVENIO de mensajería de bloqueos (invariantes vs motor):
    # el mensaje humano del invariante va en `norma_compilada` (no hay norma
    # compilada que mostrar) y `motivo` queda ''. El motor, en cambio, rellena
    # `motivo`. Por eso TODO consumidor que muestre un bloqueo debe leer
    # `motivo or norma_compilada` (ver api_expedientes._bloqueo_422 y
    # api_bc._res_error). No basta con leer solo `motivo`.
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
        if tarea and tarea.vinculos_documento:
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
    from app.models.notificaciones import Notificacion

    # Una tarea está completa si tiene un vínculo PRODUCIDO en documentos_tarea (ADR-010)
    _tiene_producido = (
        db.session.query(DocumentoTarea.id)
        .filter(DocumentoTarea.tarea_id == Tarea.id,
                DocumentoTarea.rol == 'PRODUCIDO')
        .exists()
    )
    tarea_incompleta = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo.in_(_TIPOS_REQUIEREN_DOC_PRODUCIDO),
            ~_tiene_producido
        )
        .first()
    )
    if tarea_incompleta:
        return _bloquear('Hay tareas sin documento producido en esta fase. Finalice todas las tareas antes de cerrar la fase.')

    # Tarea NOTIFICAR con resultado INCORRECTA bloquea el cierre de la fase (#418).
    # Join directo por tarea_id (ADR-034) — Notificacion ya no cuelga del documento.
    notificar_incorrecta = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(Notificacion, Notificacion.tarea_id == Tarea.id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo == 'NOTIFICAR',
            Notificacion.resultado == 'INCORRECTA',
        )
        .first()
    )
    if notificar_incorrecta:
        return _bloquear('Hay notificaciones caducadas o fallidas en esta fase. Subsane el resultado antes de cerrar la fase.')

    return None


def _check_finalizar_tramite(tramite_id: int) -> Optional[EvaluacionResult]:
    from app.models.tipos_tareas import TipoTarea
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.notificaciones import Notificacion

    _tiene_producido = (
        db.session.query(DocumentoTarea.id)
        .filter(DocumentoTarea.tarea_id == Tarea.id,
                DocumentoTarea.rol == 'PRODUCIDO')
        .exists()
    )
    tarea_incompleta = (
        db.session.query(Tarea)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .filter(
            Tarea.tramite_id == tramite_id,
            TipoTarea.codigo.in_(_TIPOS_REQUIEREN_DOC_PRODUCIDO),
            ~_tiene_producido
        )
        .first()
    )
    if tarea_incompleta:
        return _bloquear('Hay tareas sin ejecutar. Finalice todas las tareas antes de cerrar el trámite.')

    # Tarea NOTIFICAR con resultado INCORRECTA bloquea el cierre del trámite (#418).
    # Join directo por tarea_id (ADR-034) — Notificacion ya no cuelga del documento.
    notificar_incorrecta = (
        db.session.query(Tarea)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(Notificacion, Notificacion.tarea_id == Tarea.id)
        .filter(
            Tarea.tramite_id == tramite_id,
            TipoTarea.codigo == 'NOTIFICAR',
            Notificacion.resultado == 'INCORRECTA',
        )
        .first()
    )
    if notificar_incorrecta:
        return _bloquear('Hay notificaciones caducadas o fallidas en este trámite. Subsane el resultado antes de cerrarlo.')

    return None


def ultima_tarea_cadena_subsanacion(fase_id: int) -> Optional[int]:
    """`Tarea.id` del último ANALIZAR con diagnóstico de la cadena de subsanación, o None.

    "Último" por `id`: no hay ninguna columna de fecha en `diagnosticos`, `tramites`
    ni `tareas`. Mismo criterio de orden que ya usa `ContextoSubsanacion` para
    localizar el trámite anterior.

    Público desde #714 — ver nota en `TRAMITES_CADENA_SUBSANACION`.
    """
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico

    return (
        db.session.query(db.func.max(Tarea.id))
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .join(DocumentoTarea, db.and_(
            DocumentoTarea.tarea_id == Tarea.id,
            DocumentoTarea.rol == 'PRODUCIDO',
        ))
        .join(Diagnostico, Diagnostico.documento_id == DocumentoTarea.documento_id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo == 'ANALIZAR',
            TipoTramite.codigo.in_(TRAMITES_CADENA_SUBSANACION),
        )
        .scalar()
    )


def _check_cierre_fase(fase_id: int, codigo_resultado: str) -> Optional[EvaluacionResult]:
    """Bloquea el cierre de la fase si hay diagnóstico desfavorable vigente sin consumir
    y el resultado no es DESFAVORABLE (#419, corregido en #711).

    Un diagnóstico se considera consumido cuando su documento aparece como CONSUMIDO
    en cualquier otra tarea de la fase.

    **Vigencia (#711).** Dentro de la cadena de subsanación solo cuenta el ÚLTIMO
    diagnóstico: cada vuelta revisa lo mismo que la anterior y la supera, así que un
    desfavorable corregido en la vuelta siguiente ya no debe bloquear (nada crea un
    vínculo CONSUMIDO sobre él, ver #717). Fuera de la cadena la regla original queda
    intacta: los diagnósticos de una fase CONSULTAS son paralelos —uno por organismo,
    `CONSULTA_SEPARATA` es 1:1 con `organismos_expediente`— y ninguno supera a otro,
    de modo que cualquier desfavorable sin consumir sigue bloqueando.
    """
    if codigo_resultado == 'DESFAVORABLE':
        return None

    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico

    DT_cons      = db.aliased(DocumentoTarea)
    Tarea_cons   = db.aliased(Tarea)
    Tramite_cons = db.aliased(Tramite)

    # Subquery: el documento producido está siendo consumido por alguna tarea de la fase
    _consumido = (
        db.session.query(DT_cons.id)
        .join(Tarea_cons, DT_cons.tarea_id == Tarea_cons.id)
        .join(Tramite_cons, Tarea_cons.tramite_id == Tramite_cons.id)
        .filter(
            Tramite_cons.fase_id == fase_id,
            DT_cons.documento_id == DocumentoTarea.documento_id,
            DT_cons.rol == 'CONSUMIDO',
        )
        .exists()
    )

    ultima_cadena_id = ultima_tarea_cadena_subsanacion(fase_id)

    diagnostico_bloqueante = (
        db.session.query(Tarea)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .join(DocumentoTarea, db.and_(
            DocumentoTarea.tarea_id == Tarea.id,
            DocumentoTarea.rol == 'PRODUCIDO',
        ))
        .join(Diagnostico, Diagnostico.documento_id == DocumentoTarea.documento_id)
        .filter(
            Tramite.fase_id == fase_id,
            TipoTarea.codigo == 'ANALIZAR',
            Diagnostico.resultado == 'desfavorable',
            ~_consumido,
            # Fuera de la cadena bloquea siempre; dentro, solo el último de la cadena.
            # Con la cadena vacía, `Tarea.id == None` compila a IS NULL: no casa ninguna
            # fila y queda solo la rama de "fuera de la cadena", que es lo correcto.
            db.or_(
                TipoTramite.codigo.notin_(TRAMITES_CADENA_SUBSANACION),
                Tarea.id == ultima_cadena_id,
            ),
        )
        .first()
    )

    if diagnostico_bloqueante:
        return _bloquear(
            'Hay un diagnóstico desfavorable sin consumir en esta fase. '
            'No es posible cerrarla con un resultado no desfavorable.'
        )
    return None


def _check_finalizar_tarea(tarea_id: int) -> Optional[EvaluacionResult]:
    tarea = Tarea.query.get(tarea_id)
    if not tarea or not tarea.tipo_tarea:
        return None

    codigo = tarea.tipo_tarea.codigo

    if codigo in _TIPOS_REQUIEREN_DOC_PRODUCIDO and not tarea.ejecutada:
        return _bloquear('Falta el documento producido. Asócielo antes de finalizar la tarea.')

    if codigo in _TIPOS_REQUIEREN_DOC_USADO and not tarea.documentos_consumidos:
        return _bloquear('Falta el documento de entrada. Asócielo antes de finalizar la tarea.')

    return None
