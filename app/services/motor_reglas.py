"""
Motor de reglas agnóstico.

No conoce el dominio BDDAT. No importa modelos de negocio. No hace queries propias.
Recibe el sujeto calificado compilado por el ContextAssembler y un dict de variables,
y evalúa las reglas configuradas en BD.

Principio rector: todo PERMITIDO excepto lo expresamente prohibido.

SUJETO CALIFICADO:
    El assembler produce siempre un sujeto concreto con la cadena ESFTT completa:
        'Distribucion/AAP/RESOLUCION'
    Las reglas en BD usan 'ANY' como comodín posicional:
        'ANY/AAP/RESOLUCION'  →  casa con cualquier tipo de expediente

DOS BARRIDOS:
    1. Se evalúan las reglas activas que casan con (accion, sujeto).
    2. Por cada regla que dispara se comprueban sus excepciones activas.
       Si alguna excepción casa → esa prohibición queda neutralizada.
    3. Cualquier prohibición no neutralizada → BLOQUEAR.

Los checks estructurales de negocio (entidad ya iniciada, hijos sin cerrar, etc.)
viven en app/services/invariantes_esftt.py — son BDDAT-aware y se invocan antes
de llamar a este motor.

Uso:
    from app.services.motor_reglas import evaluar

    variables = {}  # TODO paso 5: variables = build(expediente_id)
    resultado = evaluar('CREAR', 'Distribucion/AAP/RESOLUCION', variables)
    if not resultado.permitido:
        return jsonify({'ok': False, 'error': resultado.norma_compilada,
                        'norma': resultado.url_norma}), 422
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import joinedload

from app import db
from app.models.motor_reglas import (
    ReglaMotor, CondicionRegla,
    ExcepcionMotor, CondicionExcepcion,
)

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
    motivo:            str = ''  # descripción editorial de la regla; '' si no configurada


PERMITIDO = EvaluacionResult(
    permitido=True, nivel='',
    variables_trigger={}, norma_compilada='', url_norma='', motivo=''
)


# ---------------------------------------------------------------------------
# Matching posicional del sujeto
# ---------------------------------------------------------------------------

def _sujeto_casa(patron: str, sujeto_real: str) -> bool:
    """
    Compara segmento a segmento separando por '/'.
    'ANY' en el patrón casa con cualquier valor real en esa posición.
    Distinto número de segmentos → no casa.
    """
    partes_patron = patron.split('/')
    partes_real   = sujeto_real.split('/')
    if len(partes_patron) != len(partes_real):
        return False
    return all(
        p == 'ANY' or p == r
        for p, r in zip(partes_patron, partes_real)
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


def _evaluar_condiciones(condiciones, variables: dict) -> tuple[bool, dict]:
    """
    Evalúa una lista de condiciones con AND implícito.
    Devuelve (disparadas, variables_trigger).
    Sin condiciones → siempre dispara.
    """
    if not condiciones:
        return True, {}

    trigger = {}
    for cond in sorted(condiciones, key=lambda c: c.orden):
        nombre = cond.variable.nombre
        if nombre not in variables:
            log.warning('motor_reglas: variable ausente en dict: %s', nombre)
            return False, {}
        op_fn = _OPERADORES.get(cond.operador)
        if op_fn is None:
            log.warning('motor_reglas: operador desconocido: %s', cond.operador)
            return False, {}
        try:
            if not bool(op_fn(variables[nombre], cond.valor)):
                return False, {}
        except Exception as exc:
            log.warning('motor_reglas: error evaluando %s %s %r: %s',
                        nombre, cond.operador, cond.valor, exc)
            return False, {}
        trigger[nombre] = variables[nombre]

    return True, trigger


def _norma_ref(regla_o_exc) -> tuple[str, str]:
    """Devuelve (norma_compilada, url_norma) para una regla o excepción."""
    if not regla_o_exc.norma:
        return '', ''
    art = regla_o_exc.articulo or ''
    apt = f'.{regla_o_exc.apartado}' if regla_o_exc.apartado else ''
    ref = f'Art. {art}{apt} — {regla_o_exc.norma.titulo}' if art else regla_o_exc.norma.titulo
    return ref, regla_o_exc.norma.url_eli or ''


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def evaluar(
    accion:    str,
    sujeto:    str,
    variables: dict,
) -> EvaluacionResult:
    """
    Evalúa si una acción sobre un sujeto calificado está permitida.

    Args:
        accion:    'CREAR' | 'INICIAR' | 'FINALIZAR' | 'BORRAR'
        sujeto:    Sujeto calificado compilado por el ContextAssembler.
                   Ejemplo: 'Distribucion/AAP/RESOLUCION'
        variables: Dict plano compilado por el ContextAssembler.

    Returns:
        EvaluacionResult. Lanza excepción ante error interno — nunca devuelve
        PERMITIDO silenciosamente ante un fallo.
    """
    # Carga todas las reglas activas para esta acción con sus condiciones y excepciones
    reglas_candidatas = ReglaMotor.query.options(
        joinedload(ReglaMotor.condiciones).joinedload(CondicionRegla.variable),
        joinedload(ReglaMotor.excepciones).joinedload(ExcepcionMotor.condiciones)
            .joinedload(CondicionExcepcion.variable),
        joinedload(ReglaMotor.excepciones).joinedload(ExcepcionMotor.norma),
        joinedload(ReglaMotor.norma),
    ).filter_by(accion=accion, activa=True).all()

    # Primer filtro: matching posicional del sujeto
    reglas = [r for r in reglas_candidatas if _sujeto_casa(r.sujeto, sujeto)]

    resultado_advertir = None

    for regla in sorted(reglas, key=lambda r: r.prioridad):
        # Barrido 1: ¿dispara la prohibición?
        disparada, trigger = _evaluar_condiciones(regla.condiciones, variables)
        if not disparada:
            continue

        if regla.efecto == 'BLOQUEAR':
            # Barrido 2: ¿alguna excepción activa neutraliza esta prohibición?
            excepciones_activas = [e for e in regla.excepciones if e.activa]
            for exc in excepciones_activas:
                exc_dispara, _ = _evaluar_condiciones(exc.condiciones, variables)
                if exc_dispara:
                    break  # excepción casa → prohibición neutralizada
            else:
                # Ninguna excepción neutralizó → BLOQUEAR
                norma_ref, url_norma = _norma_ref(regla)
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    variables_trigger=trigger,
                    norma_compilada=norma_ref,
                    url_norma=url_norma,
                    motivo=regla.descripcion or '',
                )

        elif regla.efecto == 'ADVERTIR' and resultado_advertir is None:
            norma_ref, url_norma = _norma_ref(regla)
            resultado_advertir = EvaluacionResult(
                permitido=True,
                nivel='ADVERTIR',
                variables_trigger=trigger,
                norma_compilada=norma_ref,
                url_norma=url_norma,
                motivo=regla.descripcion or '',
            )

    return resultado_advertir or PERMITIDO
