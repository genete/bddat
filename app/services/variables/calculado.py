"""
Variables de tipo 'calculado' — computan estado del expediente a partir de consultas
o propiedades de los modelos. No se persisten; se recalculan en cada invocación.
"""
from __future__ import annotations

import logging

from app.services.variables import variable
from app.services.invariantes_esftt import RESULTADO_FASE_FAVORABLE_CODIGOS

log = logging.getLogger(__name__)


@variable('fase_ip_finalizada')
def _(ctx) -> bool:
    """
    True si la solicitud en contexto tiene al menos una fase INFORMACION_PUBLICA
    finalizada (documento_resultado_id IS NOT NULL).

    Devuelve False si no hay solicitud en contexto, si la fase no existe o
    existe pero no está finalizada.
    """
    solicitud = ctx.solicitud
    if solicitud is None:
        return False
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
    True si el ÚLTIMO ANALIZAR de la cadena de subsanación de alguna fase
    (ANALISIS_DOCUMENTAL o REQUERIMIENTO_SUBSANACION, el de mayor `Tarea.id`
    con Diagnostico dentro de esa fase) tiene resultado 'desfavorable'.

    Bloquea CREAR ANALISIS_SOLICITUD/COMUNICACION_INICIO_ADMISION: si el
    último análisis sigue desfavorable el técnico debe emitir un nuevo
    requerimiento, no comunicar el inicio/admisión.

    Corrección #776: la versión original (#455) solo miraba
    ANALISIS_DOCUMENTAL, así que un ANALISIS_DOCUMENTAL desfavorable
    bloqueaba para siempre aunque la subsanación posterior fuera favorable
    — precisamente el caso normal (con requerimiento) que
    COMUNICACION_INICIO_ADMISION necesita alcanzar.

    Mismo criterio de "último de la cadena" que
    invariantes_esftt.ultima_tarea_cadena_subsanacion / diagnostico_tramite_anterior
    (orden por Tarea.id, TRAMITES_CADENA_SUBSANACION). Replicado aquí en
    navegación pura sobre el árbol ya cargado —sin consulta a BD— porque esta
    variable se computa desde ExpedienteContext, no desde una fase suelta; si
    ese criterio cambia, actualizar los tres sitios.

    Fuente: tabla diagnosticos (implementada en #392).
    ANALISIS_DOCUMENTAL nunca emite resultado 'condicionado'.
    """
    from app.services.invariantes_esftt import TRAMITES_CADENA_SUBSANACION

    solicitud = ctx.solicitud
    if solicitud is None:
        return False
    for fase in solicitud.fases:
        candidatas = []
        for tramite in fase.tramites:
            if not (tramite.tipo_tramite
                    and tramite.tipo_tramite.codigo in TRAMITES_CADENA_SUBSANACION):
                continue
            for tarea in tramite.tareas:
                if not (tarea.tipo_tarea and tarea.tipo_tarea.codigo == 'ANALIZAR'):
                    continue
                doc = tarea.documento_producido
                if doc and doc.diagnostico:
                    candidatas.append(tarea)
        if not candidatas:
            continue
        ultima = max(candidatas, key=lambda t: t.id)
        if ultima.documento_producido.diagnostico.resultado == 'desfavorable':
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


@variable('tasa_impagada')
def _(ctx) -> bool:
    """
    True si el requisito documental de la tasa (RequisitoDocumental cuyo
    TipoDocumento tiene codigo='JUSTIFICANTE_PAGO_TASA') no está cubierto
    en documentos_requisito para la solicitud en contexto (#582, art. 45.1
    Ley 10/2021).

    Ese TipoDocumento/RequisitoDocumental lo puebla #408. Mientras el
    catálogo no lo tenga, degrada a False (no bloquea) y loguea warning —
    mismo criterio que app/services/requisitos.py::evaluar_requisitos (#347).
    """
    from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
    from app.models.tipos_documentos import TipoDocumento

    solicitud = ctx.solicitud
    if solicitud is None:
        return False

    requisitos_tasa = (
        RequisitoDocumental.query
        .join(TipoDocumento)
        .filter(TipoDocumento.codigo == 'JUSTIFICANTE_PAGO_TASA',
                RequisitoDocumental.activo.is_(True))
        .all()
    )
    if not requisitos_tasa:
        log.warning(
            'tasa_impagada: no existe RequisitoDocumental activo con '
            "tipo_documento.codigo='JUSTIFICANTE_PAGO_TASA' — catálogo aún no poblado (#408)"
        )
        return False

    ids_requisito = {r.id for r in requisitos_tasa}
    cubiertos = {
        dr.requisito_id
        for dr in DocumentoRequisito.query.filter_by(solicitud_id=solicitud.id).all()
        if dr.requisito_id in ids_requisito
    }
    return len(cubiertos) < len(ids_requisito)


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


# ---------------------------------------------------------------------------
# Variables compatibilidad de tipos de solicitud (#410)
# ---------------------------------------------------------------------------

@variable('tipo_expediente')
def _(ctx) -> str | None:
    """
    Tipo de expediente como string: 'Distribucion', 'Transporte', 'Renovable', 'Convencional'.

    Devuelve el valor del campo TipoExpediente.tipo del expediente en contexto,
    o None si no está definido. Se usa en condiciones de requisitos documentales
    y en condiciones del motor que dependen del tipo de instalación.

    Nota: los valores son los de la tabla tipos_expedientes.tipo — no cambiar
    sin actualizar las condiciones_requisito que los referencian.
    """
    tipo_exp = ctx.expediente.tipo_expediente if ctx.expediente else None
    if tipo_exp is None:
        return None
    return tipo_exp.tipo


@variable('es_expediente_produccion')
def _(ctx) -> bool:
    """
    True si el tipo de expediente es de producción (Renovable o Convencional).

    Los registros RAIPEE y la autorización de explotación provisional (AE_PROVISIONAL)
    solo aplican a instalaciones de generación. En distribución, transporte y demás
    tipos carecen de base legal y se bloquean al crear la solicitud.
    """
    tipo_exp = ctx.expediente.tipo_expediente
    if tipo_exp is None:
        return False
    return tipo_exp.tipo in ('Renovable', 'Convencional')


@variable('tiene_aac_resuelta_favorable')
def _(ctx) -> bool:
    """
    True si existe en el expediente una solicitud con tipo AAC cuya fase
    finalizadora está cerrada con resultado favorable.

    Prerequisito para AE_PROVISIONAL y AE_DEFINITIVA: la explotación requiere
    que la construcción haya sido autorizada favorablemente. Crear una AE sin
    AAC resuelta constituiría una infracción administrativa (RD 1955/2000).

    Patrón idéntico a tiene_solicitud_aap_favorable pero evaluando AAC.
    La solicitud en contexto (la AE que se intenta crear) se excluye del recorrido.
    """
    solicitud_actual = ctx.solicitud
    for sol in ctx.expediente.solicitudes:
        if sol is solicitud_actual:
            continue
        if not sol.contiene_tipo('AAC'):
            continue
        for fase in sol.fases:
            if (fase.tipo_fase
                    and fase.tipo_fase.es_finalizadora
                    and fase.finalizada
                    and fase.resultado_fase
                    and fase.resultado_fase.codigo in RESULTADO_FASE_FAVORABLE_CODIGOS):
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

    Implementación — el plazo se evalúa sobre la tarea ESPERAR_PLAZO del trámite,
    no sobre el trámite (#788): el nivel TRAMITE no porta fecha administrativa y
    dejó de existir en catalogo_plazos. Bajar hasta ella es navegación del árbol
    (`Tramite.tarea_espera`), no una entrada del servicio de plazos (#778). La
    llamada sigue pasando variables={} para evitar recursión (#475); el seed #463
    no define condiciones en la entrada de CONSULTA_TRASLADO_TITULAR, así que da
    el mismo resultado que el contexto completo. Si en el futuro se añaden
    condiciones a ese plazo, revisarlo.
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
        espera = vinculo.tramite.tarea_espera if vinculo.tramite else None
        if espera is None:
            continue
        if plazos.obtener_estado_plazo_tarea(espera, variables={}).estado == 'VENCIDO':
            return True
    return False


# ---------------------------------------------------------------------------
# Variables activos de red (#591)
# ---------------------------------------------------------------------------

@variable('aplica_rd223_2008')
def _(ctx) -> bool:
    """
    True si el expediente en contexto tiene algún activo vinculado con
    envolvente lógica (linea/circuito) — aplica RD 223/2008 (líneas).

    Un expediente puede tener a la vez aplica_rd223_2008 y aplica_rd337_2014
    (p. ej. una línea que llega a una subestación nueva).
    """
    expediente = ctx.expediente
    if expediente is None:
        return False
    for vinculo in expediente.activos_expediente:
        envolvente = vinculo.activo.envolvente
        if envolvente and envolvente.es_logica:
            return True
    return False


@variable('aplica_rd337_2014')
def _(ctx) -> bool:
    """
    True si el expediente en contexto tiene algún activo vinculado con
    envolvente física (CT/subestación/posición...) — aplica RD 337/2014
    (instalaciones). Ver aplica_rd223_2008.
    """
    expediente = ctx.expediente
    if expediente is None:
        return False
    for vinculo in expediente.activos_expediente:
        envolvente = vinculo.activo.envolvente
        if envolvente and envolvente.es_fisica:
            return True
    return False
