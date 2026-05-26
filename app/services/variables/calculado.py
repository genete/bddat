"""
Variables de tipo 'calculado' — computan estado del expediente a partir de consultas
o propiedades de los modelos. No se persisten; se recalculan en cada invocación.
"""
from __future__ import annotations

from app.services.variables import variable
from app.services.invariantes_esftt import RESULTADO_FASE_FAVORABLE_CODIGOS


@variable('fase_ip_finalizada')
def _(ctx) -> bool:
    """
    True si existe al menos una fase de tipo INFORMACION_PUBLICA finalizada
    (con documento_resultado_id) en cualquier solicitud del expediente.

    Devuelve False si la fase no existe o existe pero no está finalizada.
    """
    for solicitud in ctx.expediente.solicitudes:
        for fase in solicitud.fases:
            if (fase.tipo_fase
                    and fase.tipo_fase.codigo == 'INFORMACION_PUBLICA'
                    and fase.finalizada):
                return True
    return False


@variable('tramite_publicar_existe')
def _(ctx) -> bool:
    """
    True si, dentro de la solicitud en contexto, la fase RESOLUCION tiene
    algún trámite de tipo PUBLICACION.

    Devuelve False si no hay solicitud en contexto, si no existe la fase
    RESOLUCION o si no tiene trámite PUBLICACION.
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    for fase in solicitud.fases:
        if fase.tipo_fase and fase.tipo_fase.codigo == 'RESOLUCION':
            for tramite in fase.tramites:
                if tramite.tipo_tramite and tramite.tipo_tramite.codigo == 'PUBLICACION':
                    return True
    return False


@variable('existe_fase_finalizadora_cerrada')
def _(ctx) -> bool:
    """True si la solicitud en contexto tiene al menos una fase finalizadora cerrada."""
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    for fase in solicitud.fases:
        if fase.tipo_fase and fase.tipo_fase.es_finalizadora and fase.finalizada:
            return True
    return False


@variable('tiene_solicitud_aap_favorable')
def _(ctx) -> bool:
    """
    True si existe en el expediente una solicitud con tipo AAP (distinta de la actual)
    cuya fase finalizadora está finalizada con resultado FAVORABLE o FAVORABLE_CONDICIONADO.

    Condición del art. 131.1 párr. 2 RD 1955/2000: reduce el plazo de consultas
    en AAC de 30 a 15 días naturales cuando concurre junto con es_solicitud_aac_pura.
    """
    solicitud_actual = ctx.solicitud
    if solicitud_actual is None:
        return False
    for sol in ctx.expediente.solicitudes:
        if sol is solicitud_actual:
            continue
        if not sol.contiene_tipo('AAP'):
            continue
        for fase in sol.fases:
            if (fase.tipo_fase
                    and fase.tipo_fase.es_finalizadora
                    and fase.finalizada
                    and fase.resultado_fase
                    and fase.resultado_fase.codigo in RESULTADO_FASE_FAVORABLE_CODIGOS):
                return True
    return False


@variable('tipo_sujeto_solicitado')
def _(ctx) -> str | None:
    tipo = ctx.tipo_sujeto
    return tipo.codigo if tipo else None


@variable('tipo_solicitud')
def _(ctx) -> str | None:
    """
    Siglas (literal, sin descomponer) del tipo de solicitud en contexto.

    Devuelve 'AAP', 'AAC', 'AAP+AAC', 'AAP+AAC+DUP', 'CIERRE'… exactamente como
    están en tipos_solicitudes.siglas. Las condiciones de `catalogo_plazos`
    usan operador IN con el array de combinaciones cubiertas por una misma
    cita normativa (ver seed 448_seed_plazos_resolucion).
    """
    solicitud = ctx.solicitud
    if solicitud is None or solicitud.tipo_solicitud is None:
        return None
    return solicitud.tipo_solicitud.siglas


@variable('es_solicitud_aac_pura')
def _(ctx) -> bool:
    """
    True si la solicitud en contexto contiene el tipo AAC y NO contiene AAP ni DUP.

    'Pura' significa que el promotor solicita solo la AAC, sin combinarla con AAP
    (ya obtenida en solicitud previa) ni con DUP. Condición del art. 131.1 párr. 2
    RD 1955/2000. Excluye implícitamente la solicitud de DUP y las combinadas AAP+AAC.
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    return (
        solicitud.contiene_tipo('AAC')
        and not solicitud.contiene_tipo('AAP')
        and not solicitud.contiene_tipo('DUP')
    )


# ---------------------------------------------------------------------------
# Variables ANALISIS_SOLICITUD (#455)
# ---------------------------------------------------------------------------

@variable('tramite_analisis_con_deficiencias')
def _(ctx) -> bool:
    """
    True si algún trámite ANALISIS_DOCUMENTAL de la solicitud en contexto
    tiene un Diagnostico con resultado = 'desfavorable'.

    Bloquea CREAR ANALISIS_SOLICITUD/COMUNICACION_INICIO: si hay defectos
    pendientes el técnico debe emitir un requerimiento, no comunicar el inicio.

    Fuente: tabla diagnosticos (implementada en #392).
    ANALISIS_DOCUMENTAL nunca emite resultado 'condicionado'.
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    for fase in solicitud.fases:
        for tramite in fase.tramites:
            if (tramite.tipo_tramite
                    and tramite.tipo_tramite.codigo == 'ANALISIS_DOCUMENTAL'):
                for tarea in tramite.tareas:
                    if (tarea.tipo_tarea
                            and tarea.tipo_tarea.codigo == 'ANALIZAR'):
                        doc = tarea.documento_producido
                        if (doc
                                and doc.diagnostico
                                and doc.diagnostico.resultado == 'desfavorable'):
                            return True
    return False


@variable('tramite_requerimiento_sin_respuesta')
def _(ctx) -> bool:
    """
    True si algún trámite REQUERIMIENTO_SUBSANACION de la solicitud en contexto
    tiene la tarea ESPERAR_PLAZO sin documento producido (titular no ha respondido).

    Bloquea CREAR fase RESOLUCION. Las fases intermedias (p.ej. CONSULTAS) pueden
    avanzar si los defectos no las afectan.

    La vinculación documental usa la propiedad tarea.ejecutada (rol PRODUCIDO
    en documentos_tarea — ADR-010).
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    for fase in solicitud.fases:
        for tramite in fase.tramites:
            if (tramite.tipo_tramite
                    and tramite.tipo_tramite.codigo == 'REQUERIMIENTO_SUBSANACION'):
                for tarea in tramite.tareas:
                    if (tarea.tipo_tarea
                            and tarea.tipo_tarea.codigo == 'ESPERAR_PLAZO'):
                        if not tarea.ejecutada:
                            return True
    return False


# ---------------------------------------------------------------------------
# Variables CONSULTAS (#460)
# ---------------------------------------------------------------------------

_ESTADOS_TERMINALES_CONSULTAS = frozenset({
    'cerrado_favorable', 'cerrado_con_condicionados', 'audiencia_previa', 'exonerado'
})


@variable('organismos_todos_terminados')
def _(ctx) -> bool:
    """
    True si todos los organismos del expediente han alcanzado un estado terminal.
    Precondición del cierre de fase CONSULTAS (ver #470).
    """
    organismos = ctx.expediente.organismos
    if not organismos:
        return True
    return all(org.estado in _ESTADOS_TERMINALES_CONSULTAS for org in organismos)


@variable('organismo_supera_iteraciones')
def _(ctx) -> bool:
    """
    True si algún organismo acumula ≥ 1 CONSULTA_TRASLADO_ORGANISMO en tramites_organismos,
    lo que indica que se va a crear una segunda iteración.

    Devuelve False mientras #471 (vincular tramites TRASLADO a tramites_organismos)
    no esté implementado, ya que la tabla no tendrá entradas para TRASLADOs.

    Evaluar al CREAR CONSULTA_TRASLADO_ORGANISMO (motor: ADVERTIR).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    from app.models.tramites import Tramite as _Tramite
    from app.models.tipos_tramites import TipoTramite
    from app import db

    for org in ctx.expediente.organismos:
        count = (
            db.session.query(TramiteOrganismo)
            .join(_Tramite, TramiteOrganismo.tramite_id == _Tramite.id)
            .join(TipoTramite, _Tramite.tipo_tramite_id == TipoTramite.id)
            .filter(
                TramiteOrganismo.organismo_expediente_id == org.id,
                TipoTramite.codigo == 'CONSULTA_TRASLADO_ORGANISMO',
            )
            .count()
        )
        if count >= 1:
            return True
    return False


@variable('traslado_organismo_titular_vencido')
def _(ctx) -> bool:
    """
    True si algún organismo en en_tramitacion tiene su CONSULTA_TRASLADO_TITULAR
    más reciente con plazo VENCIDO.

    Permite al motor emitir una alerta diferenciada cuando el titular no ha
    respondido al traslado dentro del plazo legal (15 días hábiles, art. 127.3 /
    131.3 RD 1955/2000). El efecto es SIN_EFECTO_AUTOMATICO: el sistema no puede
    inferir la acción correcta sin leer el resultado del trámite de organismo
    precedente (ADR-011 §5).

    Implementación — variables={} para evitar recursión: el seed #463 no define
    condiciones en la entrada de CONSULTA_TRASLADO_TITULAR, por lo que pasar un
    dict vacío produce el mismo resultado que el contexto completo. Si en el futuro
    se añaden condiciones a ese plazo, revisar esta llamada (#475).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    from app.models.tramites import Tramite as _Tramite
    from app.models.tipos_tramites import TipoTramite
    from app.services import plazos
    from app import db

    for org in ctx.expediente.organismos:
        if org.estado != 'en_tramitacion':
            continue
        vinculo = (
            db.session.query(TramiteOrganismo)
            .join(_Tramite, TramiteOrganismo.tramite_id == _Tramite.id)
            .join(TipoTramite, _Tramite.tipo_tramite_id == TipoTramite.id)
            .filter(
                TramiteOrganismo.organismo_expediente_id == org.id,
                TipoTramite.codigo == 'CONSULTA_TRASLADO_TITULAR',
            )
            .order_by(TramiteOrganismo.tramite_id.desc())
            .first()
        )
        if vinculo is None:
            continue
        ep = plazos.obtener_estado_plazo(vinculo.tramite, 'TRAMITE', variables={})
        if ep.estado == 'VENCIDO':
            return True
    return False
