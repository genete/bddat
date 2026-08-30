"""
Invariantes estructurales del árbol ESFTT.

Checks de negocio hardcoded que el motor agnóstico no puede evaluar porque
requieren consultas al dominio BDDAT. Se invocan desde las rutas Flask ANTES
de llamar a motor_reglas.evaluar().

No son candidatos a pasar a reglas_motor (ADR-037): no hay norma que citar —son
integridad estructural del árbol (hoja-a-hoja, #722) o decisiones de workflow ya
fijadas (sellado, ADR-036; completitud de cierre, #723)— y varias ramas son a
propósito no forzables, semántica que una fila de reglas_motor (pensada para
contenido citable, editable por el supervisor) no expresa bien. Viven aquí de
forma permanente, no como paso intermedio hacia el motor.
"""
from __future__ import annotations

from typing import Optional

from app import db
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.solicitudes import Solicitud
from app.models.organismos_expediente import OrganismoExpediente
from app.models.tramites_organismos import TramiteOrganismo
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


def es_documento_critico(doc) -> bool:
    """True si `doc` es evidencia de un acto ya comunicado hacia fuera (#738):
    los 9 tipos `JUSTIFICANTE_*` del catálogo (4 de notificación + 5 de
    publicación BOE/BOP/BOJA/PRENSA/PORTAL, `TIPOS_DOCUMENTOS_CATALOGO.md`),
    detectados por prefijo — no hace falta mantener una lista, cualquier
    justificante nuevo del catálogo ya sigue esa convención de nombre.

    Perder el vínculo estructural que hoy los protege (`DocumentoTarea`,
    `Notificacion`) no debe pasar en silencio, aunque no se bloquee.
    """
    return bool(doc.tipo_doc and doc.tipo_doc.codigo.startswith('JUSTIFICANTE_'))


def _documentos_criticos_huerfanos(expediente_id: int) -> list:
    """Documentos `JUSTIFICANTE_*` del pool del expediente sin ningún vínculo
    `DocumentoTarea` (ni PRODUCIDO ni CONSUMIDO) — #738 punto 4: la señal de
    que un justificante pudo subirse y no llegar nunca a vincularse a la tarea
    que lo produjo (o haber perdido ese vínculo, ver punto 1).
    """
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento

    return (
        db.session.query(Documento)
        .join(TipoDocumento, Documento.tipo_doc_id == TipoDocumento.id)
        .filter(
            Documento.expediente_id == expediente_id,
            TipoDocumento.codigo.like('JUSTIFICANTE_%'),
            ~Documento.vinculos_tarea.any(),
        )
        .all()
    )


def advertir_documentos_criticos_huerfanos(expediente_id: int) -> Optional[dict]:
    """Advertencia no bloqueante (#738 punto 4, ADVERTIR) para el cierre de
    fase: hay documentos `JUSTIFICANTE_*` en el pool del expediente sin
    vincular a ninguna tarea.

    No bloquea: el pool es del expediente completo, no de la fase que se
    cierra, así que el documento suelto puede pertenecer legítimamente a otro
    trámite o fase — bloquear el cierre por él sería una señal ambigua sobre
    qué corregir. Mismo canal de advertencia no bloqueante que los hooks
    #657/#717 de `editar_tarea`.
    """
    huerfanos = _documentos_criticos_huerfanos(expediente_id)
    if not huerfanos:
        return None
    nombres = ', '.join(str(d) for d in huerfanos)
    return {
        'motivo': (
            f'Hay documento(s) justificante en el pool sin vincular a ninguna tarea: '
            f'{nombres}. Revise si deben asociarse antes de continuar.'
        ),
    }


def _bloquear(mensaje: str, *, puede_escapar: bool = False) -> EvaluacionResult:
    # CONVENIO de mensajería de bloqueos (invariantes vs motor):
    # el mensaje humano del invariante va en `norma_compilada` (no hay norma
    # compilada que mostrar) y `motivo` queda ''. El motor, en cambio, rellena
    # `motivo`. Por eso TODO consumidor que muestre un bloqueo debe leer
    # `motivo or norma_compilada` (ver api_expedientes._bloqueo_422).
    # No basta con leer solo `motivo`.
    #
    # `puede_escapar` (#723): la mayoría de invariantes son puerta cerrada
    # (default False — precondición estructural o evidencia irreversible, ver
    # docstrings de cada check). Los pocos forzables lo pasan explícito.
    return EvaluacionResult(
        permitido=False, nivel='BLOQUEAR',
        variables_trigger={}, norma_compilada=mensaje, url_norma='',
        puede_escapar=puede_escapar,
    )


def check_invariante(accion: str, sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    """
    Verifica los invariantes estructurales para (accion, sujeto, entidad_id).

    Devuelve EvaluacionResult(BLOQUEAR) si se viola un invariante, None si todo OK.
    Solo cubre los casos hardcoded — si no hay regla para la combinación devuelve None.

    Relación con el modo global del motor (#723, checklist punto 3, decisión
    explícita): los invariantes —forzables o puerta cerrada— quedan siempre
    ajenos a `motor_modo_global.aplicar_modo_global`. Ningún caller pasa el
    resultado de esta función por ahí, y así se queda: el modo global (N018)
    es una palanca sobre el motor de reglas (modelo legal configurable), no
    sobre la estructura del árbol. Un invariante forzable sigue exigiendo su
    propia `justificacion` explícita por acto, tenga el motor el modo que
    tenga; las puertas cerradas (LPACAP) no se abren nunca, ni siquiera con
    el motor en INACTIVO.
    """
    if accion == 'BORRAR':
        return _check_borrar(sujeto, entidad_id)
    if accion == 'FINALIZAR':
        return _check_finalizar(sujeto, entidad_id)
    if accion == 'MUTAR':
        return _check_mutar(sujeto, entidad_id)
    if accion == 'REABRIR':
        return _check_reabrir(sujeto, entidad_id)
    return None


# ---------------------------------------------------------------------------
# Borrar
# ---------------------------------------------------------------------------

def _check_borrar(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    """Guardia viva del borrado del árbol (#722).

    Política hoja a hoja: cada nivel exige estar vacío para poder borrarse —
    `mutaciones_arbol.borrar_*` ya no hace cascada manual, así que la única
    forma de vaciar un trámite/fase/solicitud es borrar sus hijos uno a uno,
    y cada borrado individual pasa por su propio check. Consecuencia: una fila
    `Notificacion` (siempre colgada de una `Tarea` viva, FK NOT NULL) nunca
    puede perderse de rebote — solo se puede llegar a ella borrando
    exactamente esa tarea, que es donde se comprueba.

    Ninguna rama de este check es bypasseable con `justificacion` (a
    diferencia de las reglas del motor): "tiene hijos" es una precondición de
    orden de borrado, no una regla de negocio forzable, y la evidencia
    notificada es puerta cerrada — mismo criterio LPACAP que la reversión de
    diagnóstico (#714, `services/diagnosticos.py`).
    """
    if sujeto == 'TAREA':
        tarea = Tarea.query.get(entidad_id)
        if tarea and tarea.notificacion:
            return _bloquear(
                'No se puede eliminar una tarea con una notificación ya registrada: es la '
                'evidencia de un acto comunicado y no puede perderse.'
            )
        if tarea and tarea.vinculos_documento:
            return _bloquear('No se puede eliminar una tarea que ya tiene documentos asignados.')

    elif sujeto == 'TRAMITE':
        tiene_tareas = db.session.query(Tarea).filter(
            Tarea.tramite_id == entidad_id
        ).first()
        if tiene_tareas:
            return _bloquear('No se puede eliminar un trámite que ya tiene tareas. Bórrelas primero.')

    elif sujeto == 'FASE':
        tiene_tramites = db.session.query(Tramite).filter(
            Tramite.fase_id == entidad_id
        ).first()
        if tiene_tramites:
            return _bloquear('No se puede eliminar una fase que ya tiene trámites. Bórrelos primero.')

    elif sujeto == 'SOLICITUD':
        tiene_fases = db.session.query(Fase).filter(
            Fase.solicitud_id == entidad_id
        ).first()
        if tiene_fases:
            return _bloquear('No se puede eliminar una solicitud con fases creadas. Bórrelas primero.')

    elif sujeto == 'ORGANISMO':
        tiene_tramites = db.session.query(TramiteOrganismo).filter(
            TramiteOrganismo.organismo_expediente_id == entidad_id
        ).first()
        if tiene_tramites:
            return _bloquear(
                'No se puede eliminar un organismo que ya tiene trámites vinculados. Bórrelos primero.')

    return None


# ---------------------------------------------------------------------------
# Mutar — sellado de fase cerrada (#720, ADR-036)
# ---------------------------------------------------------------------------

def _fase_de(sujeto: str, entidad_id: int) -> Optional[Fase]:
    """Fase ancestro de un sujeto del árbol, o None si no aplica/no existe."""
    if sujeto == 'FASE':
        return Fase.query.get(entidad_id)
    if sujeto == 'TRAMITE':
        tramite = Tramite.query.get(entidad_id)
        return tramite.fase if tramite else None
    if sujeto == 'TAREA':
        tarea = Tarea.query.get(entidad_id)
        return tarea.tramite.fase if tarea and tarea.tramite else None
    if sujeto == 'ORGANISMO':
        oe = OrganismoExpediente.query.get(entidad_id)
        return oe.fase if oe else None
    return None


def _check_mutar(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    """Guardia del sellado de fase cerrada (#720, ADR-036 §6/§7).

    Bloquea cualquier mutación bajo una fase FINALIZADA (`documento_resultado_id`
    NOT NULL): crear/editar/borrar trámites y tareas, producir/revertir
    diagnósticos. El único camino de escape es `reabrir_fase` — este check
    **no admite justificación propia**, mismo criterio que `_check_borrar`
    (#722): "la fase está cerrada" no es una regla de negocio forzable caso a
    caso, es una precondición estructural.

    `editar_fase`/`reabrir_fase` no llaman a este check sobre su propia fase:
    son los dos actos que legítimamente tocan `resultado_fase_id`/
    `documento_resultado_id` (cerrar la primera vez, o reabrir).

    Sin contexto de aplicación no se aplica: en producción una mutación real
    siempre corre dentro de una request Flask con contexto activo; su ausencia
    solo se da en los tests unitarios puros de `crear_diagnostico`/
    `revertir_diagnostico` (#442/#678) que usan stubs con id inventado a
    propósito para aislar validaciones de negocio de la BD — no es a este
    check al que le corresponde forzar esa dependencia.
    """
    from flask import has_app_context
    if not has_app_context():
        return None
    fase = _fase_de(sujeto, entidad_id)
    if fase is None or not fase.finalizada:
        return None
    return _bloquear(
        'Esta fase está cerrada. Para modificar su interior, reábrala primero '
        'desde el inspector de la fase.'
    )


def _solicitud_notificada_en_fase_finalizadora(solicitud) -> bool:
    """True si existe una tarea NOTIFICAR con notificación registrada en alguna
    fase finalizadora de `solicitud` (#720, ADR-036 §4): el resultado de la
    solicitud ya se comunicó al exterior. Mismo patrón de consulta que
    `diagnosticos._hay_notificacion_posterior_en_cadena`.
    """
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tareas import TipoTarea
    from app.models.notificaciones import Notificacion

    return db.session.query(
        db.session.query(Notificacion.id)
        .join(Tarea, Notificacion.tarea_id == Tarea.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(Fase, Tramite.fase_id == Fase.id)
        .join(TipoFase, Fase.tipo_fase_id == TipoFase.id)
        .filter(
            Fase.solicitud_id == solicitud.id,
            TipoTarea.codigo == 'NOTIFICAR',
            TipoFase.es_finalizadora.is_(True),
        )
        .exists()
    ).scalar()


def _check_reabrir(sujeto: str, entidad_id: int) -> Optional[EvaluacionResult]:
    """Puerta cerrada de `reabrir_fase` (#720, ADR-036 §4): si la solicitud ya
    está resuelta (todas sus fases finalizadas) y notificada, la resolución es
    firme — no reabribible, ni con justificación. Mismo criterio LPACAP que la
    reversión de diagnóstico ya notificado (#714) y el borrado de evidencia
    notificada (#722).
    """
    if sujeto != 'FASE':
        return None
    fase = Fase.query.get(entidad_id)
    if fase is None:
        return None
    solicitud = fase.solicitud
    if not solicitud.estado.startswith('RESUELTA'):
        return None
    if _solicitud_notificada_en_fase_finalizadora(solicitud):
        return _bloquear(
            'La solicitud ya está resuelta y notificada: la resolución es firme. '
            'Ninguna de sus fases puede reabrirse; corríjalo mediante un acto '
            'administrativo expreso (revocación/anulación), fuera de este flujo.'
        )
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


def tramite_anterior_en_fase(tramite: Tramite):
    """Trámite inmediatamente anterior (por `id`) dentro de la misma fase que
    `tramite`, o None si es el primero.

    Único criterio de "qué vino antes" en la fase — extraído de
    `diagnostico_tramite_anterior` (#717) para que #776 (qué documento dispara
    el plazo de ELABORAR de COMUNICACION_INICIO_ADMISION: la solicitud si no
    hubo requerimiento, la última subsanación si lo hubo) lea el mismo
    trámite anterior sin duplicar el criterio.
    """
    fase = tramite.fase
    tramites_previos = sorted(
        (t for t in fase.tramites if t.id < tramite.id),
        key=lambda t: t.id,
    )
    return tramites_previos[-1] if tramites_previos else None


def diagnostico_tramite_anterior(tramite: Tramite):
    """Diagnóstico producido por el ANALIZAR del trámite inmediatamente anterior
    (por `id`) dentro de la misma fase que `tramite`, o None.

    Único criterio de "de qué vuelta viene esto" en la cadena de subsanación:
    lo usan `ContextoSubsanacion` (qué defectos volcar en el escrito) y #717
    (qué diagnóstico marcar CONSUMIDO al vincular el producido del ELABORAR)
    — deben leer el mismo trámite anterior o divergirían en qué diagnóstico es
    "el que este escrito volcó" (mismo motivo que `ultima_tarea_cadena_subsanacion`
    es público desde #714).

    Devuelve `Diagnostico` (no `Documento`): quien pregunta por el diagnóstico
    quiere su contenido o su documento indistintamente (`Diagnostico.documento`).
    """
    tramite_anterior = tramite_anterior_en_fase(tramite)
    if tramite_anterior is None:
        return None

    tarea_analizar = next(
        (t for t in tramite_anterior.tareas if t.tipo_tarea and t.tipo_tarea.codigo == 'ANALIZAR'),
        None,
    )
    if tarea_analizar is None:
        return None

    doc = tarea_analizar.documento_producido
    if doc is None:
        return None
    return doc.diagnostico


def documento_disparo_comunicacion_admision(tramite: Tramite):
    """Documento cuya `fecha_administrativa` dispara el plazo de ELABORAR de
    COMUNICACION_INICIO_ADMISION (art. 21.4 LPACAP), o None si aún no existe.

    Dos casos, según haya o no requerimiento de subsanación previo en la
    fase (mismo trámite anterior que `diagnostico_tramite_anterior`):
    - Sin requerimiento (trámite anterior = ANALISIS_DOCUMENTAL): el
      documento de la solicitud (`solicitud.documento_solicitud`).
    - Con requerimiento (trámite anterior = REQUERIMIENTO_SUBSANACION): el
      documento PRODUCIDO de su propia tarea ESPERAR_PLAZO — el escrito de
      subsanación que cumple el plazo del art. 68.1 LPACAP (catalogo_plazos,
      camino `ANY/ANY/ANY/REQUERIMIENTO_SUBSANACION/ESPERAR_PLAZO`), la
      fecha de entrada de la última subsanación, no la de la solicitud
      original. No se lee de los CONSUMIDO de su ANALIZAR (#825): esos los
      deriva el checklist documental (ADR-033 §1, #677) y no incluyen el
      propio escrito de subsanación —no cubre ningún requisito—, ni están
      acotados a la vuelta si #826 aún no está corregido.

    No es la fecha del Diagnostico (ADR-005/ADR-027: `fecha_administrativa
    = NULL` por diseño, no es un acto administrativo) — es la del documento
    que el diagnóstico analizó, que sí tiene efectos administrativos propios.
    """
    tramite_anterior = tramite_anterior_en_fase(tramite)
    if tramite_anterior is None:
        return tramite.fase.solicitud.documento_solicitud

    if not (tramite_anterior.tipo_tramite
            and tramite_anterior.tipo_tramite.codigo == 'REQUERIMIENTO_SUBSANACION'):
        return tramite.fase.solicitud.documento_solicitud

    tarea_esperar_plazo = next(
        (t for t in tramite_anterior.tareas if t.tipo_tarea and t.tipo_tarea.codigo == 'ESPERAR_PLAZO'),
        None,
    )
    if tarea_esperar_plazo is None:
        return None

    return tarea_esperar_plazo.documento_producido


def diagnosticos_notificados_cadena(tramite: Tramite) -> list:
    """Diagnósticos ya comunicados al titular en la cadena de subsanación hasta
    `tramite` (incluido, vía su propio NOTIFICAR), de más reciente a más antiguo (#724).

    Generaliza `diagnostico_tramite_anterior` a toda la cadena: Carlos, con
    experiencia real de tramitación, señala que dos vueltas es el caso simple —hay
    expedientes con varias (el peor recordado, cinco; a partir de ahí ya es reunión
    presencial, no un caso de sistema). Cada hueco (T_i, T_i+1) se resuelve con el
    mismo criterio que ya usa ContextoSubsanacion —T_i produce el diagnóstico, el
    NOTIFICAR de T_i+1 dice si ya se comunicó—, encadenado trámite a trámite en vez
    de limitarse a un solo salto.

    Un hueco sin notificar no corta el recorrido (seguimos mirando vueltas más
    antiguas): es best-effort, no asume que la cadena esté siempre bien formada.

    Quien consuma esto para buscar "¿ya se exigió este ítem?" debe recorrer la
    lista en orden y quedarse con la primera coincidencia — la vuelta notificada
    más reciente que lo mencione (#724, criterio acordado con Carlos).
    """
    from app.models.notificaciones import Notificacion

    fase = tramite.fase
    tramites_cadena = sorted(
        (t for t in fase.tramites
         if t.tipo_tramite and t.tipo_tramite.codigo in TRAMITES_CADENA_SUBSANACION
         and t.id <= tramite.id),
        key=lambda t: t.id,
    )

    resultado = []
    for i in range(len(tramites_cadena) - 1, 0, -1):
        t_productor = tramites_cadena[i - 1]
        t_notificador = tramites_cadena[i]

        tarea_analizar = next(
            (t for t in t_productor.tareas if t.tipo_tarea and t.tipo_tarea.codigo == 'ANALIZAR'),
            None,
        )
        if tarea_analizar is None:
            continue
        doc = tarea_analizar.documento_producido
        if doc is None or doc.diagnostico is None:
            continue

        ids_notificar = [
            t.id for t in t_notificador.tareas
            if t.tipo_tarea and t.tipo_tarea.codigo == 'NOTIFICAR'
        ]
        if not ids_notificar:
            continue
        notificado = db.session.query(
            db.session.query(Notificacion.id)
            .filter(Notificacion.tarea_id.in_(ids_notificar))
            .exists()
        ).scalar()
        if notificado:
            resultado.append(doc.diagnostico)

    return resultado


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


def documentos_consumidos_otras_tareas_cadena(tarea: Tarea) -> set:
    """Ids de documentos ya vinculados CONSUMIDO a **otra** tarea ANALIZAR de la
    misma cadena de subsanación, en la fase de `tarea` (#826).

    `sincronizar_consumido_documental` casa por solicitud (`evaluar_requisitos`),
    no por vuelta: sin este filtro, cada ANALIZAR de la cadena (ANALISIS_DOCUMENTAL,
    REQUERIMIENTO_SUBSANACION) reclamaría también lo que ya consumió una vuelta
    anterior. Acotado a la cadena a propósito — fuera de ella (CONSULTAS) los
    ANALIZAR son paralelos por organismo y varios pueden consumir legítimamente
    el mismo documento del proyecto.
    """
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.documentos_tarea import DocumentoTarea

    filas = (
        db.session.query(DocumentoTarea.documento_id)
        .join(Tarea, DocumentoTarea.tarea_id == Tarea.id)
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(TipoTarea, Tarea.tipo_tarea_id == TipoTarea.id)
        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
        .filter(
            Tramite.fase_id == tarea.tramite.fase_id,
            Tarea.id != tarea.id,
            TipoTarea.codigo == 'ANALIZAR',
            TipoTramite.codigo.in_(TRAMITES_CADENA_SUBSANACION),
            DocumentoTarea.rol == 'CONSUMIDO',
        )
        .all()
    )
    return {fila[0] for fila in filas}


def _diagnosticos_vigentes_query(fase_id: int):
    """Query de las tareas ANALIZAR de la fase cuyo diagnóstico está **vigente**,
    con el `Diagnostico` en la misma fila: `[(Tarea, Diagnostico), ...]`.

    Vigente (#711): fuera de la cadena de subsanación cuentan todos —los
    diagnósticos de una fase CONSULTAS son paralelos, uno por organismo, y
    ninguno supera a otro—; dentro de la cadena, solo el último, porque cada
    vuelta revisa lo mismo que la anterior y la supera.

    Base común de las dos ramas de `_check_cierre_fase` (#765): ambas dependen
    de qué diagnóstico "manda" y deben leerlo del mismo sitio, por el mismo
    motivo que `ultima_tarea_cadena_subsanacion` se hizo pública en #714 —lo que
    una rama dé por superado, la otra no puede darlo por vigente—. Cada rama
    añade después su propio filtro.
    """
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_tramites import TipoTramite
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.diagnosticos import Diagnostico

    ultima_cadena_id = ultima_tarea_cadena_subsanacion(fase_id)

    return (
        db.session.query(Tarea, Diagnostico)
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
            # Fuera de la cadena vale siempre; dentro, solo el último de la cadena.
            # Con la cadena vacía, `Tarea.id == None` compila a IS NULL: no casa ninguna
            # fila y queda solo la rama de "fuera de la cadena", que es lo correcto.
            db.or_(
                TipoTramite.codigo.notin_(TRAMITES_CADENA_SUBSANACION),
                Tarea.id == ultima_cadena_id,
            ),
        )
    )


def _check_cierre_desfavorable(fase_id: int) -> Optional[EvaluacionResult]:
    """Bloquea cerrar la fase con resultado DESFAVORABLE cuando ningún diagnóstico
    vigente lo respalda (#765): el caso simétrico e inverso al de #419/#711, que
    solo vigilaba el sentido "no cerrar en falso favorable".

    Criterios acordados (las tres preguntas de alcance del issue):

    - **Vigencia**: la misma noción de #711 (`_diagnosticos_vigentes_query`). Dentro
      de la cadena de subsanación manda el último diagnóstico: si la última vuelta
      salió favorable, el desfavorable de la vuelta anterior ya no respalda nada.
    - **Qué respalda**: solo un `desfavorable`. Un `condicionado` vigente es un
      "favorable con condiciones" y no sostiene por sí solo un cierre desfavorable
      —si el técnico entiende que las condiciones son incumplibles, ese es
      exactamente el juicio que debe quedar justificado y no darse por supuesto—.
    - **Consumido**: no se mira. El filtro `~consumido` de la otra rama significa
      "sin atender" y ahí sirve para no bloquear lo ya resuelto; aquí solo importa
      qué dice el veredicto documental. Caso que lo exige: se requirió subsanación
      —el desfavorable queda CONSUMIDO por el ELABORAR del requerimiento— y el
      titular no subsanó; ese desfavorable sigue siendo el último de la cadena y
      debe respaldar el cierre sin fricción.

    Sin diagnósticos vigentes no bloquea: la mayoría de fases no tienen ninguna
    tarea ANALIZAR (RESOLUCION, entre ellas — comprobado en `fases_tramites` y
    `tramites_tareas`), y no hay nada que contradecir. Esto acota el check a la
    asimetría existente de `_check_cierre_fase` y lo mantiene fuera del guardián
    general "el resultado de fase debe reflejar el diagnóstico" que la revisión de
    la fase RESOLUCION deja pendiente a propósito (ver #711 y `CONTEXTO_ACTUAL.md`).

    Forzable con justificación, por el mismo motivo que la rama de #723: cerrar la
    fase no es irreversible, y quien discrepe del diagnóstico debe poder hacerlo
    dejando escrito por qué (la justificación va a bitácora desde `editar_fase`).
    """
    resultados = [d.resultado for _, d in _diagnosticos_vigentes_query(fase_id).all()]

    if not resultados or 'desfavorable' in resultados:
        return None

    if len(resultados) == 1:
        detalle = f'el único diagnóstico vigente de esta fase es {resultados[0]}'
    else:
        detalle = (f'ninguno de los {len(resultados)} diagnósticos vigentes de esta '
                   f'fase es desfavorable')
    return _bloquear(
        f'El resultado desfavorable no está respaldado por el análisis: {detalle}. '
        'Revise el resultado de la fase, o el diagnóstico si es él el que ha quedado '
        'desfasado.',
        puede_escapar=True,
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

    Forzable con justificación (#723, caso 1): a diferencia de `_check_mutar`/
    `_check_reabrir`, cerrar la fase con este bloqueo no es un acto irreversible
    —la fase puede reabrirse después si hace falta corregirlo (y si la solicitud
    ya está resuelta y notificada, `_check_reabrir` cierra esa puerta por su
    cuenta)—, así que no hace falta distinguir causas: siempre `puede_escapar=True`.

    **Sentido inverso (#765).** Cerrar con DESFAVORABLE ya no sale sin comprobar
    nada: lo evalúa `_check_cierre_desfavorable`, que vigila el caso simétrico
    —resultado desfavorable sin ningún diagnóstico vigente que lo respalde—
    compartiendo con esta rama la noción de vigencia (`_diagnosticos_vigentes_query`).
    """
    if codigo_resultado == 'DESFAVORABLE':
        return _check_cierre_desfavorable(fase_id)

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

    # Vigencia (#711) en la query base compartida (#765); aquí solo lo propio de
    # esta rama: desfavorable y sin consumir.
    diagnostico_bloqueante = (
        _diagnosticos_vigentes_query(fase_id)
        .filter(
            Diagnostico.resultado == 'desfavorable',
            ~_consumido,
        )
        .first()
    )

    if diagnostico_bloqueante:
        return _bloquear(
            'Hay un diagnóstico desfavorable sin consumir en esta fase. '
            'No es posible cerrarla con un resultado no desfavorable.',
            puede_escapar=True,
        )
    return None


# ---------------------------------------------------------------------------
# Completitud del cierre de fase (#723, hallazgo de sesión)
# ---------------------------------------------------------------------------

def _check_completitud_cierre(fase: Fase) -> Optional[EvaluacionResult]:
    """Guardia de completitud del cierre de fase (#723): `editar_fase` no
    comprobaba nada antes de fijar `documento_resultado_id`, así que se podía
    cerrar una fase vacía o con trámites a medias sin ningún aviso.

    Reutiliza `Fase.pdte_cierre`/`Tramite.planificado` (las properties que ya
    gobiernan árbol y seguimiento) en vez de reescribir el criterio en SQL —
    evita la divergencia que arrastran `_check_finalizar_fase`/
    `_check_finalizar_tramite`, huérfanos (inventario #723, puntos 5/6, sin
    tocar aquí).

    Dos categorías, con fuerza distinta:
    - Vacío estructural (fase sin trámites, o algún trámite sin ninguna
      tarea): no hay juicio de negocio que justifique cerrar algo que nunca
      llegó a ser una fase/trámite real. Puerta cerrada — la corrección es
      borrar, no forzar (mismo criterio que la rama "tiene hijos" de
      `_check_borrar`, en espejo: aquí lo que falta son hijos, no que sobren).
    - Incompleto con contenido (trámites con tareas, pero alguna sin
      terminar): forzable con justificación, igual que `_check_cierre_fase`.
      El motivo se redacta con el mismo vocabulario que ya ve el técnico en
      árbol/seguimiento (`estado_dominio`), sin recalcular plazos reales — un
      ESPERAR_PLAZO en curso o vencido se explica igual ("falta iniciar o
      completar una tarea"); no hace falta más precisión para un bloqueo que
      además siempre admite forzarse.
    """
    if fase.pdte_cierre:
        return None

    if fase.planificada:
        return _bloquear(
            'Esta fase no tiene trámites: no hay nada que cerrar. '
            'Si no la necesita, bórrela en vez de cerrarla.'
        )

    from app.services import estado_dominio as ed

    for tramite in fase.tramites:
        if tramite.finalizado:
            continue
        nombre = tramite.tipo_tramite.nombre if tramite.tipo_tramite else f'#{tramite.id}'
        if tramite.planificado:
            return _bloquear(
                f'El trámite "{nombre}" no tiene tareas: no puede darse por completo. '
                'Si no lo necesita, bórrelo en vez de cerrar la fase.'
            )
        estados_tareas = [ed.estado_tarea(t) for t in tramite.tareas]
        estado_tr, _ = ed.estado_tramite(tramite, estados_tareas)
        return _bloquear(
            f'El trámite "{nombre}" no está completo: {ed.motivo(estado_tr)}.',
            puede_escapar=True,
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
