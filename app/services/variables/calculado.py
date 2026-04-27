"""
Variables de tipo 'calculado' — computan estado del expediente a partir de consultas
o propiedades de los modelos. No se persisten; se recalculan en cada invocación.
"""
from __future__ import annotations

from app.services.variables import variable


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
