import logging

log = logging.getLogger(__name__)

_UNIDADES_LEGIBLES = {
    'DIAS_HABILES': 'días hábiles',
    'DIAS_NATURALES': 'días naturales',
    'MESES': 'meses',
    'ANOS': 'años',
}


class ContextoComunicacionInicioAdmision:
    """
    Context Builder para escritos del trámite COMUNICACION_INICIO_ADMISION.

    Solicitud-scoped (ADR-025 §4): navega tarea → tramite → fase → solicitud
    para alcanzar los plazos máximos de la solicitud y su documento de origen,
    datos que no son propios del trámite sino de la solicitud completa.

    Cubre el art. 21.4 LPACAP: el escrito informa del plazo máximo para
    resolver y notificar, del efecto del silencio administrativo, y de la
    fecha en que la solicitud fue recibida.

    El plazo es de cada ACTO, no de la solicitud (#930, ADR-049 §E): una
    solicitud AAP+AAC+DUP pide tres autorizaciones con plazos de 3, 3 y 6
    meses, y el escrito debe informar de los tres (#931). Por eso `actos` es
    SIEMPRE una lista, también con un solo acto — contrato uniforme (D2): si
    el escrito dice una frase o enumera lo decide la plantilla con
    `{%p if actos|length == 1 %}`, no este builder.

    Campos aportados:
    - actos                     list  Un dict por acto con plazo (ver abajo)
    - fecha_recepcion_solicitud str   Fecha del documento de solicitud (DD/MM/AAAA);
                                      común a todos los actos, que arrancan el mismo día

    Estructura de cada dict en actos:
    - nombre                   str   Siglas del acto ('AAP', 'DUP'…)
    - plazo_maximo_resolucion  int   Valor del plazo máximo
    - unidad_plazo             str   Unidad legible ('meses', 'días hábiles'…)
    - norma_plazo              str   Cita de la entrada de catálogo aplicada
    - efecto_silencio          str   Nombre legible del efecto del vencimiento

    Un acto sin plazo (SIN_PLAZO: sin fila de catálogo, como INTERESADO o
    RECURSO, o sin documento de solicitud del que contar) queda fuera de la
    lista: el escrito no debe informar de un plazo que no existe.

    Degradación por catálogo ausente (#347, REGLAS_DESARROLLO.md): si ningún
    acto tiene plazo, `actos` llega vacío con `log.warning`; si falta el
    documento de solicitud, la fecha llega a None — nunca se propaga
    excepción ni se impide generar el escrito.
    """

    TOKENS = [
        {'campo': 'actos',
         'descripcion': 'Un elemento por acto con plazo de resolver. Siempre es una lista, '
                        'también con un solo acto: {%p if actos|length == 1 %} para escribir '
                        'una sola frase con {{actos[0].…}}',
         'tipo': 'tabla', 'columnas': [
             {'campo': 'nombre', 'descripcion': "Siglas del acto ('AAP', 'DUP'…)"},
             {'campo': 'plazo_maximo_resolucion', 'descripcion': 'Plazo máximo para resolver y notificar (número)'},
             {'campo': 'unidad_plazo', 'descripcion': "Unidad del plazo máximo ('meses', 'días hábiles'…)"},
             {'campo': 'norma_plazo', 'descripcion': 'Cita de la norma que fija el plazo máximo'},
             {'campo': 'efecto_silencio', 'descripcion': 'Nombre legible del efecto del silencio administrativo'},
         ]},
        {'campo': 'fecha_recepcion_solicitud', 'descripcion': 'Fecha de recepción de la solicitud (DD/MM/AAAA)'},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea or not self._tarea.tramite or not self._tarea.tramite.fase:
            return {}

        solicitud = self._tarea.tramite.fase.solicitud
        if solicitud is None:
            return {}

        ctx = {}
        ctx.update(self._contexto_plazo(solicitud))
        ctx.update(self._contexto_fecha_recepcion(solicitud))
        return ctx

    def _contexto_plazo(self, solicitud) -> dict:
        from app.services.plazos import plazos_de_la_solicitud

        actos = [
            {
                'nombre': estado.acto,
                'plazo_maximo_resolucion': estado.plazo_valor,
                'unidad_plazo': _UNIDADES_LEGIBLES.get(estado.plazo_unidad, estado.plazo_unidad),
                'norma_plazo': estado.norma_origen,
                'efecto_silencio': estado.efecto_nombre,
            }
            for estado in plazos_de_la_solicitud(solicitud)
            if estado.estado != 'SIN_PLAZO'
        ]
        if not actos:
            log.warning(
                'ContextoComunicacionInicioAdmision: ningún acto de la solicitud %s '
                'tiene plazo aplicable — contexto de plazo degradado',
                solicitud.id,
            )
        return {'actos': actos}

    def _contexto_fecha_recepcion(self, solicitud) -> dict:
        doc = solicitud.documento_solicitud
        if doc is None or doc.fecha_administrativa is None:
            log.warning(
                'ContextoComunicacionInicioAdmision: sin documento_solicitud con '
                'fecha_administrativa en la solicitud %s — fecha_recepcion_solicitud degradada',
                solicitud.id,
            )
            return {'fecha_recepcion_solicitud': None}

        return {'fecha_recepcion_solicitud': doc.fecha_administrativa.strftime('%d/%m/%Y')}
