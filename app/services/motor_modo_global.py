"""
Modo global de operación del motor (#323, unificado en #479).

Overlay de política sobre evaluar_multi(): antes cada caller (api_bc.py —retirado
en #577—, mutaciones_arbol.py, tipos_creables.py) tenía su propia copia de
_aplicar_modo_global — este módulo es la única fuente.

BLOQUEAR (default)  — comportamiento normal: BLOQUEAR bloquea, ADVERTIR advierte.
SOLO_ADVERTIR        — los BLOQUEAR se convierten en ADVERTIR; nunca bloquea.
INACTIVO             — el motor no evalúa; todo permitido.

El modo global NO afecta a las llamadas internas de assembler.py que usan el
evaluador para calcular estados ESFTT (auditar/auditar_multi) — solo a los
callers que deciden si CREAR/BORRAR se permite.
"""
from __future__ import annotations

from app.models.configuracion_sistema import ConfiguracionSistema
from app.services.assembler import evaluar_multi
from app.services.motor_reglas import EvaluacionResult, PERMITIDO

CLAVE_MODO = 'motor.modo_operacion'


def aplicar_modo_global(res_eval: EvaluacionResult) -> EvaluacionResult:
    """Ajusta el resultado del motor según el modo global configurado en BD."""
    modo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    if modo == 'INACTIVO':
        return PERMITIDO
    if modo == 'SOLO_ADVERTIR' and res_eval.nivel == 'BLOQUEAR':
        return EvaluacionResult(
            permitido=True, nivel='ADVERTIR',
            variables_trigger=res_eval.variables_trigger,
            norma_compilada=res_eval.norma_compilada,
            url_norma=res_eval.url_norma,
            motivo=res_eval.motivo,
        )
    return res_eval


def evaluar_con_modo_global(accion: str, expediente, *, objeto) -> EvaluacionResult:
    """evaluar_multi(accion, ...) + modo global. Punto único de entrada para callers BDDAT."""
    return aplicar_modo_global(evaluar_multi(accion, expediente, objeto=objeto))
