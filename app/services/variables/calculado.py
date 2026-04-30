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
