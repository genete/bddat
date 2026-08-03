"""
Vocabulario ESFTT — categoría C de bloqueo (ADR-037).

Bloqueos estructurales escapables sin cita normativa: pertenencia y orden
contra las tablas de vocabulario (tramites_tareas, fases_tramites). No es
reglas_motor (no hay norma que citar) ni invariante de estado (no depende del
momento, depende del tipo). Comparte tubería con invariantes_esftt.py
(EvaluacionResult, puede_escapar=True, misma bitácora que un escape de motor)
pero es una familia propia — ver ADR-037 §C.

Convención de mensajería (igual que invariantes_esftt._bloquear): el mensaje
humano va en `norma_compilada`, `motivo` queda ''. Leer siempre
`motivo or norma_compilada` al mostrar un bloqueo.
"""
from __future__ import annotations

from typing import Optional

from app.models.tramites_tareas import TramiteTarea
from app.services.motor_reglas import EvaluacionResult


def _bloquear(mensaje: str) -> EvaluacionResult:
    return EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada=mensaje, url_norma='',
        puede_escapar=True,
    )


def check_orden_tarea(tramite, tipo_tarea) -> Optional[EvaluacionResult]:
    """Orden canónico de tareas dentro de un trámite (#719, absorbido en ADR-037 §C).

    "Todo permitido mientras no esté expresamente prohibido": se invita a crear
    la tarea que toca según tramites_tareas.orden; saltarse el orden bloquea,
    pero es forzable con justificación (misma bitácora que un escape de motor).

    Trámite sin patrón (tramites_tareas vacío para su tipo) → sin fricción,
    ninguna tarea es "la que toca" porque no hay patrón que seguir.
    Patrón ya agotado (más tareas creadas que pasos del patrón) → sin fricción
    adicional, no hay siguiente paso definido contra el que comparar.

    "La que toca" se calcula por conteo: la N-ésima tarea creada (por id, mismo
    criterio de orden que ya usa diagnostico_tramite_anterior) debe casar con
    el N-ésimo paso del patrón. Heurística deliberadamente simple — el propio
    mecanismo es una invitación escapable, no una máquina de estados estricta.
    """
    patron = (
        TramiteTarea.query
        .filter_by(tipo_tramite_id=tramite.tipo_tramite_id)
        .order_by(TramiteTarea.orden)
        .all()
    )
    if not patron:
        return None

    ya_creadas = len(tramite.tareas)
    if ya_creadas >= len(patron):
        return None

    paso_esperado = patron[ya_creadas]
    if tipo_tarea.id == paso_esperado.tipo_tarea_id:
        return None

    return _bloquear(
        f'Según el patrón de este trámite, ahora tocaría crear una tarea '
        f'{paso_esperado.tipo_tarea.codigo}. Puede forzar esta otra si tiene '
        f'una razón para saltarse el orden canónico.'
    )
