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
    para alcanzar el plazo máximo de la solicitud y su documento de origen,
    datos que no son propios del trámite sino de la solicitud completa.

    Cubre el art. 21.4 LPACAP: el escrito informa del plazo máximo para
    resolver y notificar, del efecto del silencio administrativo, y de la
    fecha en que la solicitud fue recibida.

    Campos aportados:
    - plazo_maximo_resolucion  int   Valor del plazo máximo de la solicitud
    - unidad_plazo             str   Unidad legible ('meses', 'días hábiles'…)
    - norma_plazo              str   Cita de la entrada de catálogo aplicada
    - efecto_silencio          str   Nombre legible del efecto del vencimiento
    - fecha_recepcion_solicitud str  Fecha del documento de solicitud (DD/MM/AAAA)

    Degradación por catálogo ausente (#347, REGLAS_DESARROLLO.md): si no hay
    entrada de `catalogo_plazos` aplicable a esta solicitud, o si falta el
    documento de solicitud, los campos correspondientes llegan a None con
    `log.warning` — nunca se propaga excepción ni se impide generar el escrito.
    """

    TOKENS = [
        {'campo': 'plazo_maximo_resolucion', 'descripcion': 'Plazo máximo para resolver y notificar (número)'},
        {'campo': 'unidad_plazo', 'descripcion': "Unidad del plazo máximo ('meses', 'días hábiles'…)"},
        {'campo': 'norma_plazo', 'descripcion': 'Cita de la norma que fija el plazo máximo'},
        {'campo': 'efecto_silencio', 'descripcion': 'Nombre legible del efecto del silencio administrativo'},
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
        from app.services.plazos import obtener_estado_plazo_solicitud

        estado = obtener_estado_plazo_solicitud(solicitud)
        if estado.estado == 'SIN_PLAZO':
            log.warning(
                'ContextoComunicacionInicioAdmision: sin entrada de catalogo_plazos '
                'aplicable a la solicitud %s — contexto de plazo degradado',
                solicitud.id,
            )
            return {
                'plazo_maximo_resolucion': None,
                'unidad_plazo': None,
                'norma_plazo': None,
                'efecto_silencio': None,
            }

        return {
            'plazo_maximo_resolucion': estado.plazo_valor,
            'unidad_plazo': _UNIDADES_LEGIBLES.get(estado.plazo_unidad, estado.plazo_unidad),
            'norma_plazo': estado.norma_origen,
            'efecto_silencio': estado.efecto_nombre,
        }

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
