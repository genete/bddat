"""
ContextAssembler — ensambla sujeto calificado y dict de variables para el motor.

Conoce BDDAT a fondo. El motor NO.

Uso en rutas Flask:
    from app.services.assembler import build
    from app.services.motor_reglas import evaluar

    # Para FINALIZAR un objeto existente (Fase, Tramite...):
    sujeto, variables = build(expediente, objeto=fase)
    resultado = evaluar('FINALIZAR', sujeto, variables)

    # Para CREAR (objeto aún no existe):
    sujeto, variables = build(expediente, objeto={'solicitud': sol, 'tipo_fase': tipo_fase})
    resultado = evaluar('CREAR', sujeto, variables)

Ver docs/DISEÑO_CONTEXT_ASSEMBLER.md para diseño completo.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Contexto de evaluación
# ---------------------------------------------------------------------------

class ExpedienteContext:
    """
    Contexto inmutable de evaluación que las funciones de variable reciben.

    objeto puede ser:
      - Una instancia existente: Solicitud, Fase, Tramite, Tarea
      - Un dict para CREAR:
          {'solicitud': s, 'tipo_fase': tf}          → crear Fase
          {'fase': f, 'tipo_tramite': tt}             → crear Tramite
      - None: solo el expediente en contexto
    """

    def __init__(self, expediente: Any, objeto: Any = None) -> None:
        self.expediente = expediente
        self._objeto    = objeto

    # --- Helpers derivados --------------------------------------------------

    @property
    def solicitud(self) -> Optional[Any]:
        """Solicitud en contexto, derivada del objeto actuado.

        Duck-typing por atributos (no por nombre de clase) para soportar mocks:
          Solicitud → tiene 'fases', NO tiene 'solicitud'
          Fase      → tiene 'solicitud' y 'tramites'
          Tramite   → tiene 'fase', NO tiene 'tramites'
          Tarea     → tiene 'tramite'
        """
        obj = self._objeto
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get('solicitud')
        if hasattr(obj, 'fases') and not hasattr(obj, 'solicitud'):
            return obj                        # es Solicitud
        if hasattr(obj, 'solicitud') and hasattr(obj, 'tramites'):
            return obj.solicitud              # es Fase
        if hasattr(obj, 'fase') and not hasattr(obj, 'tramites'):
            return obj.fase.solicitud         # es Tramite
        if hasattr(obj, 'tramite'):
            return obj.tramite.fase.solicitud # es Tarea
        return None

    @property
    def fase(self) -> Optional[Any]:
        """Fase en contexto (solo para objetos existentes Fase/Tramite/Tarea)."""
        obj = self._objeto
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get('fase')
        if hasattr(obj, 'solicitud') and hasattr(obj, 'tramites'):
            return obj                        # es Fase
        if hasattr(obj, 'fase') and not hasattr(obj, 'tramites'):
            return obj.fase                   # es Tramite
        if hasattr(obj, 'tramite'):
            return obj.tramite.fase           # es Tarea
        return None

    @property
    def tramite(self) -> Optional[Any]:
        """Trámite en contexto (solo para objetos existentes Tramite/Tarea)."""
        obj = self._objeto
        if obj is None:
            return None
        if isinstance(obj, dict):
            return None
        if hasattr(obj, 'fase') and not hasattr(obj, 'tramites'):
            return obj                        # es Tramite
        if hasattr(obj, 'tramite'):
            return obj.tramite                # es Tarea
        return None


# ---------------------------------------------------------------------------
# Compilación del sujeto calificado
# ---------------------------------------------------------------------------

def _compilar_sujeto(ctx: ExpedienteContext, siglas_override: str = None) -> str:
    """
    Produce el sujeto calificado ESFTT completo a partir del contexto.

    Recorre la jerarquía de exterior (E) a interior (hasta el nivel del objeto).
    Nunca produce ANY — eso es un comodín de las reglas, no de la realidad.

    siglas_override: si se pasa, sustituye las siglas del tipo de solicitud.
    Usado por evaluar_multi para iterar sobre tipos simples de combinados.

    Ejemplos:
        Fase en solicitud AAP+AAC, override='AAP':
            → 'Distribucion/AAP/RESOLUCION'
        Fase en solicitud AAP+AAC, override='AAC':
            → 'Distribucion/AAC/RESOLUCION'
    """
    tipo_exp = ctx.expediente.tipo_expediente
    segmentos = [tipo_exp.tipo if tipo_exp else 'DESCONOCIDO']

    sol = ctx.solicitud
    if sol and sol.tipo_solicitud:
        segmentos.append(siglas_override if siglas_override is not None else sol.tipo_solicitud.siglas)

    # Fase: existente (via ctx.fase) o prevista (via dict 'tipo_fase')
    fase = ctx.fase
    obj  = ctx._objeto
    if fase and fase.tipo_fase:
        segmentos.append(fase.tipo_fase.codigo)
    elif isinstance(obj, dict) and 'tipo_fase' in obj:
        tf = obj['tipo_fase']
        if tf:
            segmentos.append(tf.codigo)

    # Trámite: existente (via ctx.tramite) o previsto (via dict 'tipo_tramite')
    tramite = ctx.tramite
    if tramite and tramite.tipo_tramite:
        segmentos.append(tramite.tipo_tramite.codigo)
    elif isinstance(obj, dict) and 'tipo_tramite' in obj:
        tt = obj['tipo_tramite']
        if tt:
            segmentos.append(tt.codigo)

    return '/'.join(segmentos)


# ---------------------------------------------------------------------------
# Compilación del dict de variables
# ---------------------------------------------------------------------------

def _compilar_variables(ctx: ExpedienteContext) -> dict:
    """
    Evalúa todas las variables activas en catalogo_variables invocando el registry.

    Las variables inactivas (activa=False) se omiten del dict.
    Las que fallan o no tienen función devuelven None con warning en log.
    """
    from app.models.motor_reglas import CatalogoVariable
    from app.services.variables import _REGISTRY  # importación tardía: evita circular

    variables_activas = CatalogoVariable.query.filter_by(activa=True).all()
    resultado = {}
    for var in variables_activas:
        fn = _REGISTRY.get(var.nombre)
        if fn is None:
            log.warning('assembler: variable activa sin función en registry: %s', var.nombre)
            resultado[var.nombre] = None
            continue
        try:
            resultado[var.nombre] = fn(ctx)
        except Exception as exc:
            log.warning('assembler: error calculando variable %s: %s', var.nombre, exc)
            resultado[var.nombre] = None
    return resultado


# ---------------------------------------------------------------------------
# Función pública
# ---------------------------------------------------------------------------

def build(expediente: Any, objeto: Any = None) -> tuple[str, dict]:
    """
    Ensambla sujeto calificado y dict de variables para el motor agnóstico.

    Args:
        expediente: Instancia de Expediente con relaciones accesibles.
        objeto:     Objeto sobre el que se actúa. Puede ser:
                    - Instancia existente: Solicitud, Fase, Tramite, Tarea
                    - Dict para CREAR: {'solicitud': s, 'tipo_fase': tf}
                    - None si no aplica

    Returns:
        (sujeto, variables): sujeto calificado tipo 'Distribucion/AAP/RESOLUCION'
        y dict plano de variables para el motor.

    Nota: para solicitudes con tipos combinados (AAP+AAC) este método devuelve
    el sujeto con las siglas completas. Usar evaluar_multi para evaluar por
    tipo simple automáticamente.
    """
    ctx = ExpedienteContext(expediente, objeto)
    sujeto    = _compilar_sujeto(ctx)
    variables = _compilar_variables(ctx)
    return sujeto, variables


def evaluar_multi(accion: str, expediente: Any, objeto: Any = None):
    """
    Evalúa una acción para todos los tipos simples de la solicitud en contexto.

    Para solicitudes con tipo combinado (ej. AAP+AAC) evalúa el motor una vez
    por cada tipo simple. Devuelve el primer resultado BLOQUEAR encontrado,
    o el último resultado (PERMITIDO) si ninguno bloquea.

    Args:
        accion:     Acción a evaluar ('CREAR', 'INICIAR', 'FINALIZAR', 'BORRAR').
        expediente: Instancia de Expediente.
        objeto:     Objeto actuado (misma semántica que build()).

    Returns:
        EvaluacionResult del motor.
    """
    from app.services.motor_reglas import evaluar

    ctx = ExpedienteContext(expediente, objeto)
    variables = _compilar_variables(ctx)
    sol = ctx.solicitud

    tipos = sol.tipos_simples if (sol and sol.tipo_solicitud) else [None]

    ultimo = None
    for tipo in tipos:
        sujeto = _compilar_sujeto(ctx, siglas_override=tipo)
        ultimo = evaluar(accion, sujeto, variables)
        if not ultimo.permitido:
            return ultimo
    return ultimo
