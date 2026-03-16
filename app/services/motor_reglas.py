"""
Motor de reglas — Evaluador de acciones sobre entidades ESFTT.

Principio rector: todo está PERMITIDO excepto lo expresamente prohibido.
Flujo de evaluación:
  1. Construir contexto jerárquico (sube hasta Expediente/Proyecto)
  2. Ejecutar checks estructurales hardcoded (invariantes de negocio)
  3. Consultar reglas en BD y evaluar condiciones configurables
  4. BLOQUEAR tiene prioridad sobre ADVERTIR

Uso:
    from app.services.motor_reglas import evaluar

    # Crear una fase (tipo_fase_id=8) dentro de la solicitud 23
    res = evaluar('CREAR', 'FASE', tipo_id=8, padre_id=23)

    # Iniciar la fase 45
    res = evaluar('INICIAR', 'FASE', entidad_id=45)

    # Borrar la tarea 12
    res = evaluar('BORRAR', 'TAREA', entidad_id=12)

    if not res.permitido:
        return jsonify({'ok': False, 'error': res.mensaje, 'norma': res.norma}), 422
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app import db
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.motor_reglas import ReglaMotor, CondicionRegla


# ---------------------------------------------------------------------------
# Resultado público
# ---------------------------------------------------------------------------

@dataclass
class EvaluacionResult:
    permitido: bool
    nivel: str     # 'BLOQUEAR' | 'ADVERTIR' | ''
    mensaje: str
    norma: str


# Resultado singleton para "todo ok"
PERMITIDO = EvaluacionResult(permitido=True, nivel='', mensaje='', norma='')


# ---------------------------------------------------------------------------
# Contexto jerárquico (privado)
# ---------------------------------------------------------------------------

@dataclass
class _Contexto:
    """Snapshot del árbol ESFTT necesario para evaluar una regla."""
    entidad: str
    tarea:      Optional[Tarea]      = field(default=None)
    tramite:    Optional[Tramite]    = field(default=None)
    fase:       Optional[Fase]       = field(default=None)
    solicitud:  Optional[Solicitud]  = field(default=None)
    expediente: Optional[Expediente] = field(default=None)
    proyecto:   Optional[object]     = field(default=None)  # Proyecto


def _construir_contexto(evento: str, entidad: str,
                        entidad_id: Optional[int],
                        padre_id: Optional[int]) -> _Contexto:
    """
    Sube el árbol jerárquico desde el objeto indicado hasta Expediente/Proyecto.

    Para CREAR, padre_id es el ID del contenedor (solicitud, fase o tramite).
    Para INICIAR/FINALIZAR/BORRAR, entidad_id es el ID del objeto en cuestión.
    """
    ctx = _Contexto(entidad=entidad)

    if evento == 'CREAR':
        _ctx_crear(entidad, padre_id, ctx)
    else:
        _ctx_operar(entidad, entidad_id, ctx)

    return ctx


def _ctx_crear(entidad: str, padre_id: Optional[int], ctx: _Contexto) -> None:
    """Construye contexto para evento CREAR (padre_id = contenedor)."""
    if entidad == 'SOLICITUD':
        # padre_id = expediente_id
        if padre_id:
            ctx.expediente = Expediente.query.get(padre_id)
            if ctx.expediente:
                ctx.proyecto = ctx.expediente.proyecto

    elif entidad == 'FASE':
        # padre_id = solicitud_id
        if padre_id:
            ctx.solicitud = Solicitud.query.get(padre_id)
            if ctx.solicitud:
                ctx.expediente = ctx.solicitud.expediente
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'TRAMITE':
        # padre_id = fase_id
        if padre_id:
            ctx.fase = Fase.query.get(padre_id)
            if ctx.fase:
                ctx.solicitud = ctx.fase.solicitud
                ctx.expediente = ctx.solicitud.expediente if ctx.solicitud else None
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'TAREA':
        # padre_id = tramite_id
        if padre_id:
            ctx.tramite = Tramite.query.get(padre_id)
            if ctx.tramite:
                ctx.fase = ctx.tramite.fase
                ctx.solicitud = ctx.fase.solicitud if ctx.fase else None
                ctx.expediente = ctx.solicitud.expediente if ctx.solicitud else None
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None


def _ctx_operar(entidad: str, entidad_id: Optional[int], ctx: _Contexto) -> None:
    """Construye contexto para INICIAR/FINALIZAR/BORRAR."""
    if entidad == 'TAREA':
        if entidad_id:
            ctx.tarea = Tarea.query.get(entidad_id)
            if ctx.tarea:
                ctx.tramite = ctx.tarea.tramite
                ctx.fase = ctx.tramite.fase if ctx.tramite else None
                ctx.solicitud = ctx.fase.solicitud if ctx.fase else None
                ctx.expediente = ctx.solicitud.expediente if ctx.solicitud else None
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'TRAMITE':
        if entidad_id:
            ctx.tramite = Tramite.query.get(entidad_id)
            if ctx.tramite:
                ctx.fase = ctx.tramite.fase
                ctx.solicitud = ctx.fase.solicitud if ctx.fase else None
                ctx.expediente = ctx.solicitud.expediente if ctx.solicitud else None
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'FASE':
        if entidad_id:
            ctx.fase = Fase.query.get(entidad_id)
            if ctx.fase:
                ctx.solicitud = ctx.fase.solicitud
                ctx.expediente = ctx.solicitud.expediente if ctx.solicitud else None
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'SOLICITUD':
        if entidad_id:
            ctx.solicitud = Solicitud.query.get(entidad_id)
            if ctx.solicitud:
                ctx.expediente = ctx.solicitud.expediente
                ctx.proyecto = ctx.expediente.proyecto if ctx.expediente else None

    elif entidad == 'EXPEDIENTE':
        if entidad_id:
            ctx.expediente = Expediente.query.get(entidad_id)
            if ctx.expediente:
                ctx.proyecto = ctx.expediente.proyecto


# ---------------------------------------------------------------------------
# Checks estructurales hardcoded
# ---------------------------------------------------------------------------

def _checks_hardcoded(evento: str, entidad: str,
                      ctx: _Contexto) -> Optional[EvaluacionResult]:
    """
    Invariantes de negocio no configurables en BD.
    Retorna EvaluacionResult(BLOQUEAR) si se viola una regla, None si todo OK.
    """
    if evento == 'BORRAR':
        return _check_borrar(entidad, ctx)
    elif evento == 'FINALIZAR':
        return _check_finalizar(entidad, ctx)
    return None


def _check_borrar(entidad: str, ctx: _Contexto) -> Optional[EvaluacionResult]:
    if entidad in ('FASE', 'TRAMITE', 'TAREA'):
        obj = {'FASE': ctx.fase, 'TRAMITE': ctx.tramite, 'TAREA': ctx.tarea}[entidad]
        if obj and obj.fecha_inicio is not None:
            return EvaluacionResult(
                permitido=False,
                nivel='BLOQUEAR',
                mensaje='No se puede eliminar una entidad ya iniciada.',
                norma=''
            )

    elif entidad == 'SOLICITUD':
        if ctx.solicitud:
            tiene_fase_iniciada = db.session.query(Fase).filter(
                Fase.solicitud_id == ctx.solicitud.id,
                Fase.fecha_inicio.isnot(None)
            ).first()
            if tiene_fase_iniciada:
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    mensaje='No se puede eliminar una solicitud con fases ya iniciadas.',
                    norma=''
                )
    return None


def _check_finalizar(entidad: str, ctx: _Contexto) -> Optional[EvaluacionResult]:
    if entidad == 'SOLICITUD':
        if ctx.solicitud:
            fase_abierta = db.session.query(Fase).filter(
                Fase.solicitud_id == ctx.solicitud.id,
                Fase.fecha_fin.is_(None)
            ).first()
            if fase_abierta:
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    mensaje='Hay fases sin cerrar. Finalice todas las fases antes de cerrar la solicitud.',
                    norma=''
                )

    elif entidad == 'FASE':
        if ctx.fase:
            tramite_abierto = db.session.query(Tramite).filter(
                Tramite.fase_id == ctx.fase.id,
                Tramite.fecha_fin.is_(None)
            ).first()
            if tramite_abierto:
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    mensaje='Hay trámites sin cerrar. Finalice todos los trámites antes de cerrar la fase.',
                    norma=''
                )

    elif entidad == 'TRAMITE':
        if ctx.tramite:
            tarea_abierta = db.session.query(Tarea).filter(
                Tarea.tramite_id == ctx.tramite.id,
                Tarea.fecha_fin.is_(None)
            ).first()
            if tarea_abierta:
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    mensaje='Hay tareas sin ejecutar. Finalice todas las tareas antes de cerrar el trámite.',
                    norma=''
                )

    elif entidad == 'TAREA':
        return _check_finalizar_tarea(ctx)

    return None


# Tipos de tarea que requieren documento producido al finalizar
_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'INCORPORAR', 'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}

# Tipos de tarea que requieren documento de entrada al finalizar
_TIPOS_REQUIEREN_DOC_USADO = {'ANALISIS', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}


def _check_finalizar_tarea(ctx: _Contexto) -> Optional[EvaluacionResult]:
    tarea = ctx.tarea
    if not tarea or not tarea.tipo_tarea:
        return None

    codigo = tarea.tipo_tarea.codigo

    if codigo in _TIPOS_REQUIEREN_DOC_PRODUCIDO and tarea.documento_producido_id is None:
        return EvaluacionResult(
            permitido=False,
            nivel='BLOQUEAR',
            mensaje='Falta el documento producido. Asócielo antes de finalizar la tarea.',
            norma=''
        )

    if codigo in _TIPOS_REQUIEREN_DOC_USADO and tarea.documento_usado_id is None:
        return EvaluacionResult(
            permitido=False,
            nivel='BLOQUEAR',
            mensaje='Falta el documento de entrada. Asócielo antes de finalizar la tarea.',
            norma=''
        )

    return None


# ---------------------------------------------------------------------------
# Evaluadores de criterio
# ---------------------------------------------------------------------------

def _evaluar_criterio(tipo_criterio: str, parametros: dict,
                      ctx: _Contexto, params: dict) -> bool:
    """
    Despacha al evaluador específico según el tipo_criterio.
    Devuelve True si la condición se cumple.
    """
    evaluadores = {
        'EXISTE_FASE_CERRADA':      _criterio_existe_fase_cerrada,
        'EXISTE_FASE_CON_RESULTADO': _criterio_existe_fase_con_resultado,
        'VARIABLE_EXPEDIENTE':      _criterio_variable_expediente,
        'VARIABLE_PROYECTO':        _criterio_variable_proyecto,
        'TIPO_FASE_PADRE_ES':       _criterio_tipo_fase_padre_es,
        'EXISTE_TAREA_TIPO':        _criterio_existe_tarea_tipo,
        'EXISTE_TRAMITE_TIPO':      _criterio_existe_tramite_tipo,
        'ESTADO_SOLICITUD':         _criterio_estado_solicitud,
        'EXISTE_TIPO_SOLICITUD':    _criterio_existe_tipo_solicitud,
        # Stubs — requieren modelo Documento (pendiente)
        'EXISTE_DOCUMENTO_TIPO':    lambda p, c, ps: False,
        'EXISTE_DOC_ORGANISMO':     lambda p, c, ps: False,
    }
    fn = evaluadores.get(tipo_criterio)
    if fn is None:
        # Criterio desconocido: por seguridad, se considera no cumplido
        return False
    return fn(parametros, ctx, params)


def _criterio_existe_fase_cerrada(p: dict, ctx: _Contexto, params: dict) -> bool:
    """¿Existe una fase cerrada del tipo indicado en la solicitud?"""
    if not ctx.solicitud:
        return False
    tipo_fase_codigo = p.get('tipo_fase_codigo')
    q = db.session.query(Fase).join(TipoFase, Fase.tipo_fase_id == TipoFase.id).filter(
        Fase.solicitud_id == ctx.solicitud.id,
        Fase.fecha_fin.isnot(None)
    )
    if tipo_fase_codigo:
        q = q.filter(TipoFase.codigo == tipo_fase_codigo)
    return q.first() is not None


def _criterio_existe_fase_con_resultado(p: dict, ctx: _Contexto, params: dict) -> bool:
    """¿Existe una fase del tipo indicado con alguno de los resultados especificados?"""
    if not ctx.solicitud:
        return False
    from app.models.tipos_resultados_fases import TipoResultadoFase
    tipo_fase_codigo  = p.get('tipo_fase_codigo')
    resultado_codigos = p.get('resultado_codigos', [])
    q = (db.session.query(Fase)
         .join(TipoFase, Fase.tipo_fase_id == TipoFase.id)
         .join(TipoResultadoFase, Fase.resultado_fase_id == TipoResultadoFase.id)
         .filter(Fase.solicitud_id == ctx.solicitud.id))
    if tipo_fase_codigo:
        q = q.filter(TipoFase.codigo == tipo_fase_codigo)
    if resultado_codigos:
        q = q.filter(TipoResultadoFase.codigo.in_(resultado_codigos))
    return q.first() is not None


def _navegar_dot(obj, ruta: str):
    """Navega una ruta dot-notation ('campo.subcampo') sobre un objeto."""
    for parte in ruta.split('.'):
        if obj is None:
            return None
        obj = getattr(obj, parte, None)
    return obj


_OPERADORES = {
    'EQ':      lambda v, ref: v == ref,
    'NEQ':     lambda v, ref: v != ref,
    'IN':      lambda v, ref: v in (ref if isinstance(ref, list) else [ref]),
    'NOT_IN':  lambda v, ref: v not in (ref if isinstance(ref, list) else [ref]),
    'IS_NULL': lambda v, _: v is None,
    'NOT_NULL': lambda v, _: v is not None,
}


def _criterio_variable_expediente(p: dict, ctx: _Contexto, params: dict) -> bool:
    if not ctx.expediente:
        return False
    valor = _navegar_dot(ctx.expediente, p['campo'])
    op_fn = _OPERADORES.get(p.get('operador', 'EQ'))
    return op_fn(valor, p.get('valor')) if op_fn else False


def _criterio_variable_proyecto(p: dict, ctx: _Contexto, params: dict) -> bool:
    if not ctx.proyecto:
        return False
    valor = _navegar_dot(ctx.proyecto, p['campo'])
    op_fn = _OPERADORES.get(p.get('operador', 'EQ'))
    return op_fn(valor, p.get('valor')) if op_fn else False


def _criterio_tipo_fase_padre_es(p: dict, ctx: _Contexto, params: dict) -> bool:
    if not ctx.fase or not ctx.fase.tipo_fase:
        return False
    return ctx.fase.tipo_fase.codigo == p.get('tipo_fase_codigo')


def _criterio_existe_tarea_tipo(p: dict, ctx: _Contexto, params: dict) -> bool:
    """¿Existe una tarea del tipo indicado en el trámite actual?"""
    if not ctx.tramite:
        return False
    codigo = p.get('tipo_tarea_codigo')
    cerrada = p.get('cerrada', False)
    requiere_doc_producido = p.get('requiere_doc_producido', False)

    q = (db.session.query(Tarea)
         .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
         .filter(Tarea.tramite_id == ctx.tramite.id))
    if codigo:
        q = q.filter(TipoTarea.codigo == codigo)
    if cerrada:
        q = q.filter(Tarea.fecha_fin.isnot(None))
    if requiere_doc_producido:
        q = q.filter(Tarea.documento_producido_id.isnot(None))
    return q.first() is not None


def _criterio_existe_tramite_tipo(p: dict, ctx: _Contexto, params: dict) -> bool:
    """¿Existe un trámite del tipo indicado en la fase actual?"""
    if not ctx.fase:
        return False
    codigo = p.get('tipo_tramite_codigo')
    cerrado = p.get('cerrado', False)
    requiere_doc_producido = p.get('requiere_doc_producido', False)

    q = (db.session.query(Tramite)
         .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
         .filter(Tramite.fase_id == ctx.fase.id))
    if codigo:
        q = q.filter(TipoTramite.codigo == codigo)
    if cerrado:
        q = q.filter(Tramite.fecha_fin.isnot(None))
    if requiere_doc_producido:
        # Existe al menos una tarea en ese trámite con documento producido
        q = q.filter(
            db.session.query(Tarea)
            .filter(Tarea.tramite_id == Tramite.id,
                    Tarea.documento_producido_id.isnot(None))
            .exists()
        )
    return q.first() is not None


def _criterio_estado_solicitud(p: dict, ctx: _Contexto, params: dict) -> bool:
    if not ctx.solicitud:
        return False
    return ctx.solicitud.estado == p.get('estado')


def _criterio_existe_tipo_solicitud(p: dict, ctx: _Contexto, params: dict) -> bool:
    """Comparación exacta de siglas. La inteligencia está en la regla, no en el motor."""
    if not ctx.solicitud or not ctx.solicitud.tipo_solicitud:
        return False
    siglas = p.get('tipo_solicitud_codigo')
    return ctx.solicitud.tipo_solicitud.siglas == siglas


# ---------------------------------------------------------------------------
# Evaluación de condiciones de una regla
# ---------------------------------------------------------------------------

def _evaluar_regla(regla: ReglaMotor, ctx: _Contexto, params: dict) -> bool:
    """
    Evalúa todas las condiciones de una regla.
    Sin condiciones → regla siempre dispara (True).
    Combina condiciones izq→dcha usando operador_siguiente[i].
    """
    condiciones = sorted(regla.condiciones, key=lambda c: c.orden)
    if not condiciones:
        return True

    resultados = []
    for cond in condiciones:
        val = _evaluar_criterio(cond.tipo_criterio, cond.parametros or {}, ctx, params)
        if cond.negacion:
            val = not val
        resultados.append((val, cond.operador_siguiente))

    # Combinar usando el operador_siguiente de cada condición con la siguiente
    acumulado = resultados[0][0]
    for i in range(1, len(resultados)):
        operador = resultados[i - 1][1]  # operador entre i-1 e i
        siguiente = resultados[i][0]
        if operador == 'OR':
            acumulado = acumulado or siguiente
        else:  # AND (por defecto)
            acumulado = acumulado and siguiente

    return acumulado


# ---------------------------------------------------------------------------
# Función pública principal
# ---------------------------------------------------------------------------

def evaluar(
    evento:     str,
    entidad:    str,
    tipo_id:    Optional[int] = None,
    entidad_id: Optional[int] = None,
    padre_id:   Optional[int] = None,
    params:     Optional[dict] = None
) -> EvaluacionResult:
    """
    Evalúa si un evento sobre una entidad está permitido.

    Args:
        evento:     'CREAR' | 'INICIAR' | 'FINALIZAR' | 'BORRAR'
        entidad:    'SOLICITUD' | 'FASE' | 'TRAMITE' | 'TAREA' | 'EXPEDIENTE'
        tipo_id:    ID en la tabla tipos_* correspondiente. Para CREAR, es obligatorio.
                    Para INICIAR/FINALIZAR/BORRAR se deduce del objeto si no se pasa.
        entidad_id: ID del objeto existente (INICIAR/FINALIZAR/BORRAR).
        padre_id:   ID del contenedor (CREAR).
        params:     Parámetros adicionales para evaluadores (ej: organismo_id).

    Returns:
        EvaluacionResult con permitido=True o False.
    """
    if params is None:
        params = {}

    # --- Construir contexto ---
    ctx = _construir_contexto(evento, entidad, entidad_id, padre_id)

    # --- Para INICIAR/FINALIZAR/BORRAR, deducir tipo_id si no se pasó ---
    if tipo_id is None and evento != 'CREAR':
        tipo_id = _deducir_tipo_id(entidad, ctx)

    # --- Checks estructurales hardcoded ---
    bloqueo = _checks_hardcoded(evento, entidad, ctx)
    if bloqueo:
        return bloqueo

    # --- Consultar reglas en BD ---
    q = ReglaMotor.query.filter_by(evento=evento, entidad=entidad, activa=True)
    if tipo_id is not None:
        # Reglas específicas del tipo O genéricas (tipo_id NULL)
        q = q.filter(
            db.or_(ReglaMotor.tipo_id == tipo_id, ReglaMotor.tipo_id.is_(None))
        )
    else:
        # Sin tipo_id conocido: solo reglas genéricas
        q = q.filter(ReglaMotor.tipo_id.is_(None))

    reglas = q.all()

    # --- Evaluar reglas: primero BLOQUEAR, luego ADVERTIR ---
    resultado_advertir = None

    for regla in reglas:
        if _evaluar_regla(regla, ctx, params):
            if regla.accion == 'BLOQUEAR':
                return EvaluacionResult(
                    permitido=False,
                    nivel='BLOQUEAR',
                    mensaje=regla.mensaje,
                    norma=regla.norma or ''
                )
            elif regla.accion == 'ADVERTIR' and resultado_advertir is None:
                # Guardamos la primera advertencia; seguimos buscando BLOQUEARs
                resultado_advertir = EvaluacionResult(
                    permitido=True,
                    nivel='ADVERTIR',
                    mensaje=regla.mensaje,
                    norma=regla.norma or ''
                )

    if resultado_advertir:
        return resultado_advertir

    return PERMITIDO


def _deducir_tipo_id(entidad: str, ctx: _Contexto) -> Optional[int]:
    """Obtiene el tipo_id del objeto en contexto."""
    if entidad == 'TAREA'    and ctx.tarea:
        return ctx.tarea.tipo_tarea_id
    if entidad == 'TRAMITE'  and ctx.tramite:
        return ctx.tramite.tipo_tramite_id
    if entidad == 'FASE'     and ctx.fase:
        return ctx.fase.tipo_fase_id
    if entidad == 'SOLICITUD' and ctx.solicitud:
        return ctx.solicitud.tipo_solicitud_id
    return None
