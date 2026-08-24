"""
Servicio de nombres de documentos generados (#698).

RESPONSABILIDAD:
    Calcula el texto que aporta el trámite de una tarea ELABORAR al nombre
    sugerido del documento que genera (componer_nombre_documento, en
    generador_escritos.py).

    La fuente principal del texto sigue siendo tipos_tramites.nombre_en_plantilla
    — dato de catálogo, editable por el supervisor en tablas_maestras (#171),
    igual que siempre. Este servicio es solo el HELPER que combina ese dato
    con lo que un campo de texto no puede expresar por sí solo:

    - AJUSTE: el texto de catálogo se usa tal cual y el servicio le añade
      algo calculado (numeración de vuelta repetida). El dato sigue siendo
      la fuente; el servicio solo lo completa.
    - SUSTITUCIÓN: el texto de catálogo no basta porque hay más de un
      resultado posible y la diferencia no es de wording sino de qué acto
      administrativo es el documento (p.ej. Admisión a Trámite vs. Oficio
      Inicio según tipo de expediente — carácter jurídico distinto, no una
      preferencia estética). Estos pocos casos viven en código a propósito:
      no son datos que un supervisor deba poder cambiar sin más.

REGISTRO POR (fase, trámite), NO SOLO POR TRÁMITE:
    Hay códigos de tipo_tramite reutilizados como vocabulario en más de una
    fase (fases_tramites, ADR-037/#725) — p.ej. ELABORACION aparece en
    RESOLUCION y en RECONOCIMIENTO_INTERESADO. tipos_tramites tiene una fila
    por código, no por (fase, código) — así que el dato de catálogo de un
    trámite compartido es el MISMO en las dos fases. Para RESOLUCION.ELABORACION
    (única implementada en esta pasada) no es un problema porque
    RECONOCIMIENTO_INTERESADO.ELABORACION no está implementado todavía; el
    día que se aborde (issue de seguimiento #809) hay que decidir ahí cómo
    desambiguar (sustitución de código específica por fase, o mover el dato
    a fases_tramites si el patrón se repite). Registrar las excepciones
    (ajustes y sustituciones) por el par completo, nunca solo por el código
    de trámite, evita que una entrada nueva colisione con otra fase sin que
    nadie lo note.

FALLBACK:
    tipos_tramites.nombre_en_plantilla vacío y sin ajuste/sustitución
    registrados → código crudo del trámite (tramite.tipo_tramite.codigo).
    Nunca bloquea, nunca produce un marcador sin sentido tipo "ANY" —
    decisión de Carlos, 2026-08-24: el nombre del fichero no implica nada
    administrativamente ni presupone su contenido, es solo ayuda semántica
    para cuando el documento circula fuera de BDDAT (la trazabilidad real va
    por el código embebido BDDAT-<tarea_id>-<letra>, #182 — el nombre es
    irrelevante para BDDAT).

ALCANCE POBLADO (#698, primera pasada):
    - ANALISIS_SOLICITUD.REQUERIMIENTO_SUBSANACION (ajuste: numeración de vuelta)
    - ANALISIS_SOLICITUD.COMUNICACION_INICIO_ADMISION (sustitución: condicional renovable)
    - RESOLUCION.ELABORACION (dato de catálogo puro, sin ajuste ni sustitución
      — se puebla nombre_en_plantilla='Resolución' vía migración, sin código)
    El resto de fases/trámites cae al fallback de código crudo mientras su
    tipos_tramites.nombre_en_plantilla siga vacío — issue de seguimiento #809
    para ir poblando el dato (y añadir ajuste/sustitución solo si el trámite
    concreto lo necesita).

USO:
    from app.services.nombres_documentos import texto_tramite
    texto = texto_tramite(tarea.tramite)
"""
from typing import Callable


def _numero_vuelta(tramite) -> int:
    """
    Posición de `tramite` entre los trámites de su misma fase con el mismo
    tipo_tramite.codigo, ordenados por id (1 = primera vuelta, 2 = segunda...).

    Mismo criterio de orden que invariantes_esftt.tramite_anterior_en_fase
    (#717) y que ya usa ContextoSubsanacion — no se inventa un segundo
    criterio de "qué vino antes" que pudiera divergir del existente.
    """
    codigo = tramite.tipo_tramite.codigo
    hermanos = sorted(
        (t for t in tramite.fase.tramites if t.tipo_tramite and t.tipo_tramite.codigo == codigo),
        key=lambda t: t.id,
    )
    return hermanos.index(tramite) + 1


def _es_renovable(tramite) -> bool:
    """True si el expediente de `tramite` es de tipo Renovable (RD-ley 23/2020)."""
    expediente = tramite.fase.solicitud.expediente
    tipo_expediente = expediente.tipo_expediente
    return bool(tipo_expediente and tipo_expediente.tipo == 'Renovable')


def _ajuste_numero_vuelta(tramite, base: str) -> str:
    """AJUSTE: combina el texto de catálogo con la numeración de vuelta."""
    n = _numero_vuelta(tramite)
    return base if n == 1 else f'{base} {n}'


def _sustitucion_comunicacion_inicio_admision(tramite) -> str:
    """SUSTITUCIÓN: qué acto administrativo es, no una variante de wording."""
    return 'Admisión a Trámite' if _es_renovable(tramite) else 'Oficio Inicio'


# AJUSTES: combinan tipos_tramites.nombre_en_plantilla con algo calculado.
# Firma: (tramite, texto_base) -> str
_AJUSTES: dict[tuple[str, str], Callable[[object, str], str]] = {
    ('ANALISIS_SOLICITUD', 'REQUERIMIENTO_SUBSANACION'): _ajuste_numero_vuelta,
}

# SUSTITUCIONES: el dato de catálogo no interviene, el texto completo es
# código a propósito (más de un resultado posible, diferencia de fondo
# jurídico/administrativo, no de wording).
# Firma: (tramite) -> str
_SUSTITUCIONES: dict[tuple[str, str], Callable[[object], str]] = {
    ('ANALISIS_SOLICITUD', 'COMUNICACION_INICIO_ADMISION'): _sustitucion_comunicacion_inicio_admision,
}


def texto_tramite(tramite) -> str:
    """
    Texto que aporta `tramite` al nombre del documento generado por su
    tarea ELABORAR. Ver docstring del módulo para el orden de prioridad
    (sustitución > catálogo+ajuste > catálogo > fallback código crudo).
    """
    fase_codigo = tramite.fase.tipo_fase.codigo
    tramite_codigo = tramite.tipo_tramite.codigo

    sustitucion = _SUSTITUCIONES.get((fase_codigo, tramite_codigo))
    if sustitucion is not None:
        return sustitucion(tramite)

    base = tramite.tipo_tramite.nombre_en_plantilla or tramite_codigo

    ajuste = _AJUSTES.get((fase_codigo, tramite_codigo))
    if ajuste is not None:
        return ajuste(tramite, base)

    return base
