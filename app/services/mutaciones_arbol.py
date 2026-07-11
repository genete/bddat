"""
mutaciones_arbol.py — Servicio de mutaciones ESFTT para el árbol (ADR-016, S3b-0).

Funciones puras de dominio (sin request/jsonify) para Crear / Editar / Borrar
los cuatro niveles del árbol (solicitud, fase, trámite, tarea).

Extraídas literalmente de app/routes/api_bc.py (camino B, #500):
- api_bc delega aquí y mantiene su contrato HTTP intacto.
- Los endpoints JSON del árbol también llaman a estas funciones.

Nota: `resultado` en tareas NOTIFICAR es una @property computada desde Notificacion
y no es editable por este servicio — ver hallazgos S3b-0.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.documentos_tarea import DocumentoTarea
from app.models.tramites_organismos import TramiteOrganismo
from app.services.assembler import build_sujeto
from app.services import bitacora as bitacora_svc
from app.services.motor_reglas import EvaluacionResult, PERMITIDO
from app.services.motor_modo_global import evaluar_con_modo_global as _evaluar
from app.services.invariantes_esftt import _check_cierre_fase

log = logging.getLogger(__name__)

# Espejo de api_bc — mantener sincronizados hasta unificar (deuda conocida)
_CODIGOS_TRASLADO = frozenset({'CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR'})
_FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS = frozenset({'RESOLUCION', 'AAU_AAUS_INTEGRADA'})


@dataclass
class ResultadoMutacion:
    """Retorno unificado de todas las funciones de mutación."""
    ok: bool
    ids: list[int] = field(default_factory=list)
    bloqueo: Optional[EvaluacionResult] = None
    advertencia: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _advertencia_dict(res_eval: EvaluacionResult) -> Optional[dict]:
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {
            'motivo': res_eval.motivo,
            'norma_compilada': res_eval.norma_compilada,
            'url_norma': res_eval.url_norma,
        }
    return None


# ---------------------------------------------------------------------------
# Hook #458 (movido desde api_bc; test_458 actualizado para importar de aquí)
# ---------------------------------------------------------------------------

def _hook_458_analizar_separata(tarea, id_producido):
    """Hook #458: al producir diagnóstico en CONSULTA_SEPARATA pasa el organismo a en_tramitacion."""
    if (id_producido is not None
            and tarea.tipo_tarea.codigo == 'ANALIZAR'
            and tarea.tramite.tipo_tramite.codigo == 'CONSULTA_SEPARATA'):
        vinculo = TramiteOrganismo.query.filter_by(tramite_id=tarea.tramite_id).first()
        if vinculo:
            vinculo.organismo_expediente.estado = 'en_tramitacion'


# ===========================================================================
# CREAR
# ===========================================================================

def crear_solicitud(expediente, tipos: list[TipoSolicitud], entidad_id: int,
                    *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    """Crea una o varias solicitudes (multi-tipo). Valida motor para todos antes de persistir."""
    exp_id = expediente.id

    if not entidad_id:
        return ResultadoMutacion(ok=False, error='El expediente no tiene titular asignado.')

    # Fase 1: evaluar motor para todos los tipos; si alguno bloquea, rechazar todo
    if justificacion is None:
        for tipo in tipos:
            sol_stub = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                                 tipo_solicitud_id=tipo.id)
            sol_stub.tipo_solicitud = tipo  # stub transiente — assembler compila sin flush
            res_eval = _evaluar('CREAR', expediente, objeto=sol_stub)
            if not res_eval.permitido:
                return ResultadoMutacion(ok=False, bloqueo=res_eval)

    # Fase 2: persistir
    creadas = []
    try:
        for tipo in tipos:
            sol = Solicitud(expediente_id=exp_id, entidad_id=entidad_id,
                            tipo_solicitud_id=tipo.id)
            db.session.add(sol)
            db.session.flush()
            if justificacion:
                sujeto = build_sujeto(expediente, sol)
                bitacora_svc.registrar(
                    current_user.id, 'CREAR', 'solicitudes', sol.id,
                    detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
                )
            creadas.append(sol)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))

    return ResultadoMutacion(ok=True, ids=[s.id for s in creadas])


def crear_fase(solicitud, tipo_fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'solicitud': solicitud, 'tipo_fase': tipo_fase})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    fase = Fase(solicitud_id=solicitud.id, tipo_fase_id=tipo_fase.id)
    db.session.add(fase)
    db.session.flush()

    if tipo_fase.codigo in _FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS:
        from app.services.cert_fin_ip_consultas import crear_cert_fin_ip_consultas
        crear_cert_fin_ip_consultas(expediente, solicitud)

    if justificacion:
        sujeto = build_sujeto(expediente, {'solicitud': solicitud, 'tipo_fase': tipo_fase})
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'fases', fase.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[fase.id], advertencia=_advertencia_dict(res_eval))


def crear_tramite(fase, tipo_tramite, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    if tipo_tramite.codigo in _CODIGOS_TRASLADO:
        return ResultadoMutacion(
            ok=False,
            error='Los trámites de traslado se crean desde la acción específica de organismo',
        )

    expediente = fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'fase': fase, 'tipo_tramite': tipo_tramite})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    tramite = Tramite(fase_id=fase.id, tipo_tramite_id=tipo_tramite.id)
    db.session.add(tramite)
    db.session.flush()

    if justificacion:
        sujeto = build_sujeto(expediente, {'fase': fase, 'tipo_tramite': tipo_tramite})
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tramites', tramite.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tramite.id], advertencia=_advertencia_dict(res_eval))


def crear_tarea(tramite, tipo_tarea, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = tramite.fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('CREAR', expediente,
                            objeto={'tramite': tramite, 'tipo_tarea': tipo_tarea})
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)
    else:
        res_eval = PERMITIDO

    tarea = Tarea(tramite_id=tramite.id, tipo_tarea_id=tipo_tarea.id)
    db.session.add(tarea)
    db.session.flush()

    if justificacion:
        sujeto = build_sujeto(expediente, tramite)
        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'tareas', tarea.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.commit()
    return ResultadoMutacion(ok=True, ids=[tarea.id], advertencia=_advertencia_dict(res_eval))


# ===========================================================================
# EDITAR
# ===========================================================================

def editar_solicitud(sol, *, observaciones: Optional[str]) -> ResultadoMutacion:
    try:
        sol.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_fase(fase, *, resultado_fase_id: Optional[int],
                documento_resultado_id: Optional[int],
                observaciones: Optional[str]) -> ResultadoMutacion:
    if documento_resultado_id and fase.documento_resultado_id is None:
        doc = Documento.query.get(documento_resultado_id)
        if not doc or doc.expediente_id != fase.solicitud.expediente_id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

        if resultado_fase_id:
            from app.models.tipos_resultados_fases import TipoResultadoFase
            tipo_res = TipoResultadoFase.query.get(resultado_fase_id)
            if tipo_res:
                res_inv = _check_cierre_fase(fase.id, tipo_res.codigo)
                if res_inv:
                    return ResultadoMutacion(ok=False, bloqueo=res_inv)

    try:
        fase.resultado_fase_id = resultado_fase_id
        fase.documento_resultado_id = documento_resultado_id
        fase.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_tramite(tr, *, observaciones: Optional[str]) -> ResultadoMutacion:
    try:
        tr.observaciones = observaciones or None
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


def editar_tarea(ta, *, documentos_consumidos_ids: list[int],
                 documento_producido_id: Optional[int],
                 notas: Optional[str]) -> ResultadoMutacion:
    """Actualiza vínculos documentales + notas de la tarea.

    `resultado` (NOTIFICAR) es una @property de Notificacion — no editable aquí.
    """
    expediente = ta.tramite.fase.solicitud.expediente

    ids_todos = list(documentos_consumidos_ids) + (
        [documento_producido_id] if documento_producido_id else [])
    for doc_id in ids_todos:
        doc = Documento.query.get(doc_id)
        if not doc or doc.expediente_id != expediente.id:
            return ResultadoMutacion(ok=False, error='Documento no válido para este expediente')

    try:
        ta.vinculos_documento.clear()
        db.session.flush()
        for doc_id in dict.fromkeys(documentos_consumidos_ids):   # sin duplicados, orden estable
            ta.vinculos_documento.append(DocumentoTarea(documento_id=doc_id, rol='CONSUMIDO'))
        if documento_producido_id:
            ta.vinculos_documento.append(
                DocumentoTarea(documento_id=documento_producido_id, rol='PRODUCIDO'))

        ta.notas = notas or None
        _hook_458_analizar_separata(ta, documento_producido_id)
        db.session.commit()
        return ResultadoMutacion(ok=True)
    except IntegrityError:
        db.session.rollback()
        return ResultadoMutacion(
            ok=False, error='Este documento ya está asignado como producido a otra tarea')
    except Exception as e:
        db.session.rollback()
        return ResultadoMutacion(ok=False, error=str(e))


# ===========================================================================
# BORRAR (cascada manual — idéntica a api_bc)
# ===========================================================================

def borrar_solicitud(sol, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = sol.expediente
    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=sol)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, sol)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'solicitudes', sol.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    fase_ids = [f.id for f in Fase.query.filter_by(solicitud_id=sol.id).all()]
    if fase_ids:
        tram_ids = [t.id for t in Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).all()]
        if tram_ids:
            Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
        Tramite.query.filter(Tramite.fase_id.in_(fase_ids)).delete()
    Fase.query.filter_by(solicitud_id=sol.id).delete()
    db.session.delete(sol)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_fase(fase, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=fase)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, fase)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'fases', fase.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    tram_ids = [t.id for t in Tramite.query.filter_by(fase_id=fase.id).all()]
    if tram_ids:
        Tarea.query.filter(Tarea.tramite_id.in_(tram_ids)).delete()
    Tramite.query.filter_by(fase_id=fase.id).delete()
    db.session.delete(fase)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tramite(tr, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = tr.fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=tr)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, tr)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'tramites', tr.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    Tarea.query.filter_by(tramite_id=tr.id).delete()
    db.session.delete(tr)
    db.session.commit()
    return ResultadoMutacion(ok=True)


def borrar_tarea(ta, *, justificacion: Optional[str] = None) -> ResultadoMutacion:
    expediente = ta.tramite.fase.solicitud.expediente
    if justificacion is None:
        res_eval = _evaluar('BORRAR', expediente, objeto=ta)
        if not res_eval.permitido:
            return ResultadoMutacion(ok=False, bloqueo=res_eval)

    if justificacion:
        sujeto = build_sujeto(expediente, ta.tramite)
        bitacora_svc.registrar(
            current_user.id, 'BORRAR', 'tareas', ta.id,
            detalle={'escape': True, 'justificacion': justificacion, 'sujeto': sujeto},
        )

    db.session.delete(ta)
    db.session.commit()
    return ResultadoMutacion(ok=True)
