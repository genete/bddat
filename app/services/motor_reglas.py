"""
Motor de reglas agnóstico.

No conoce el dominio BDDAT. No importa modelos de negocio. No hace queries propias.
Recibe un dict de variables compilado por el ContextAssembler y evalúa las reglas
configuradas en BD (reglas_motor + condiciones_regla).

Principio rector: todo PERMITIDO excepto lo expresamente prohibido.

Los checks estructurales de negocio (entidad ya iniciada, hijos sin cerrar, etc.)
viven en app/services/invariantes_esftt.py — son BDDAT-aware y se invocan antes
de llamar a este motor.

Uso:
    from app.services.motor_reglas import evaluar
    from app.services.invariantes_esftt import check_invariante

    bloqueo = check_invariante('FINALIZAR', 'FASE', fase.id)
    if bloqueo:
        return jsonify({'ok': False, 'error': bloqueo.norma_compilada}), 422

    variables = {}  # TODO paso 5: context_assembler.build(expediente_id)
    resultado = evaluar('FINALIZAR', 'FASE', fase.tipo_fase_id, variables)
    if not resultado.permitido:
        return jsonify({'ok': False, 'error': resultado.norma_compilada,
                        'norma': resultado.url_norma}), 422
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from app import db
from app.models.motor_reglas import ReglaMotor, CondicionRegla

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Resultado público
# ---------------------------------------------------------------------------

@dataclass
class EvaluacionResult:
    permitido:         bool
    nivel:             str   # 'BLOQUEAR' | 'ADVERTIR' | ''
    variables_trigger: dict  # subconjunto del dict que disparó la regla
    norma_compilada:   str   # referencia normativa compilada
    url_norma:         str   # URL BOE/BOJA; '' si no existe


PERMITIDO = EvaluacionResult(
    permitido=True, nivel='',
    variables_trigger={}, norma_compilada='', url_norma=''
)


# ---------------------------------------------------------------------------
# Evaluación de condiciones
# ---------------------------------------------------------------------------

_OPERADORES = {
    'EQ':          lambda v, ref: v == ref,
    'NEQ':         lambda v, ref: v != ref,
    'IN':          lambda v, ref: v in (ref if isinstance(ref, list) else [ref]),
    'NOT_IN':      lambda v, ref: v not in (ref if isinstance(ref, list) else [ref]),
    'IS_NULL':     lambda v, _: v is None,
    'NOT_NULL':    lambda v, _: v is not None,
    'GT':          lambda v, ref: v is not None and v > ref,
    'GTE':         lambda v, ref: v is not None and v >= ref,
    'LT':          lambda v, ref: v is not None and v < ref,
    'LTE':         lambda v, ref: v is not None and v <= ref,
    'BETWEEN':     lambda v, ref: v is not None and ref[0] <= v <= ref[1],
    'NOT_BETWEEN': lambda v, ref: v is not None and not (ref[0] <= v <= ref[1]),
}


def _evaluar_condicion(cond: CondicionRegla, variables: dict) -> bool:
    nombre = cond.nombre_variable
    if nombre not in variables:
        log.warning('motor_reglas: variable ausente en dict: %s', nombre)
        return False
    op_fn = _OPERADORES.get(cond.operador)
    if op_fn is None:
        log.warning('motor_reglas: operador desconocido: %s', cond.operador)
        return False
    try:
        return bool(op_fn(variables[nombre], cond.valor))
    except Exception as exc:
        log.warning('motor_reglas: error evaluando %s %s %r: %s', nombre, cond.operador, cond.valor, exc)
        return False


def _evaluar_regla(regla: ReglaMotor, variables: dict) -> tuple[bool, dict]:
    """
    Evalúa todas las condiciones con AND implícito.
    Devuelve (disparada, variables_trigger).
    Sin condiciones → regla siempre dispara.
    """
    condiciones = sorted(regla.condiciones, key=lambda c: c.orden)
    if not condiciones:
        return True, {}

    trigger = {}
    for cond in condiciones:
        if not _evaluar_condicion(cond, variables):
            return False, {}
        trigger[cond.nombre_variable] = variables.get(cond.nombre_variable)
    return True, trigger


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def evaluar(
    accion:         str,
    sujeto:         str,
    tipo_sujeto_id: Optional[int],
    variables:      dict,
) -> EvaluacionResult:
    """
    Evalúa si una acción sobre un sujeto está permitida.

    Args:
        accion:         'CREAR' | 'INICIAR' | 'FINALIZAR' | 'BORRAR'
        sujeto:         'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA' | 'EXPEDIENTE'
        tipo_sujeto_id: ID en tipos_* del sujeto. NULL = solo reglas genéricas.
        variables:      dict plano compilado por ContextAssembler.

    Returns:
        EvaluacionResult. Lanza excepción ante error interno — nunca devuelve
        PERMITIDO silenciosamente ante un fallo.
    """
    q = ReglaMotor.query.filter_by(accion=accion, sujeto=sujeto, activa=True)
    if tipo_sujeto_id is not None:
        q = q.filter(
            db.or_(ReglaMotor.tipo_sujeto_id == tipo_sujeto_id,
                   ReglaMotor.tipo_sujeto_id.is_(None))
        )
    else:
        q = q.filter(ReglaMotor.tipo_sujeto_id.is_(None))

    reglas = q.order_by(ReglaMotor.prioridad).all()

    resultado_advertir = None
    for regla in reglas:
        disparada, trigger = _evaluar_regla(regla, variables)
        if not disparada:
            continue
        if regla.efecto == 'BLOQUEAR':
            return EvaluacionResult(
                permitido=False,
                nivel='BLOQUEAR',
                variables_trigger=trigger,
                norma_compilada=regla.norma_compilada or '',
                url_norma='',
            )
        if regla.efecto == 'ADVERTIR' and resultado_advertir is None:
            resultado_advertir = EvaluacionResult(
                permitido=True,
                nivel='ADVERTIR',
                variables_trigger=trigger,
                norma_compilada=regla.norma_compilada or '',
                url_norma='',
            )

    return resultado_advertir or PERMITIDO
