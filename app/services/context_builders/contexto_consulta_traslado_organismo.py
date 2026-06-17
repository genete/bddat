from app.models.tramites import Tramite
from app.models.tramites_organismos import TramiteOrganismo
from app.models.tipos_tramites import TipoTramite


class ContextoConsultaTrasladoOrganismo:
    """
    Context Builder para escritos del trámite CONSULTA_TRASLADO_ORGANISMO.

    Enriquece el contexto base con datos del organismo al que se trasladan
    los reparos del titular y las fechas del ciclo. Navega al organismo vía
    tramites_organismos (ADR-011 §1).

    Campos adicionales aportados:
    - organismo_nombre          str   Nombre oficial del organismo
    - organismo_nif             str   NIF del organismo (puede ser None)
    - organismo_plazo_legal     int   Plazo legal en días capturado al crear la separata
    - organismo_resultado       str   Estado del ciclo del organismo
    - organismo_fecha_respuesta str   Fecha del doc producido por ESPERAR_PLAZO del trámite
                                      anterior del organismo (separata o traslado previo).
                                      DD/MM/AAAA o None si no está disponible
    - titular_fecha_respuesta   str   Fecha del doc producido por ESPERAR_PLAZO del
                                      CONSULTA_TRASLADO_TITULAR más reciente del organismo.
                                      DD/MM/AAAA o None si aún no se ha recibido respuesta
    - organismo_num_iteraciones int   Número de trámites CONSULTA_TRASLADO_ORGANISMO del
                                      organismo (incluye el actual). Derivado de ADR-011 §2
    """

    TOKENS = [
        {'campo': 'organismo_nombre',          'descripcion': 'Nombre oficial del organismo'},
        {'campo': 'organismo_nif',             'descripcion': 'NIF del organismo (puede ser vacío)'},
        {'campo': 'organismo_plazo_legal',     'descripcion': 'Plazo legal en días capturado al crear la separata'},
        {'campo': 'organismo_resultado',       'descripcion': 'Estado del ciclo del organismo'},
        {'campo': 'organismo_fecha_respuesta', 'descripcion': 'Fecha de respuesta del trámite anterior del organismo (DD/MM/AAAA)'},
        {'campo': 'titular_fecha_respuesta',   'descripcion': 'Fecha de respuesta del traslado al titular más reciente (DD/MM/AAAA)'},
        {'campo': 'organismo_num_iteraciones', 'descripcion': 'Número de traslados al organismo (incluye el actual)'},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        vinculo = (TramiteOrganismo.query
                   .filter_by(tramite_id=self._tarea.tramite_id)
                   .first())
        org_exp = vinculo.organismo_expediente if vinculo else None

        if not org_exp:
            return {}

        ctx = org_exp.as_contexto_cb()

        # Respuesta del organismo: ESPERAR_PLAZO del trámite anterior del organismo
        # (CONSULTA_SEPARATA o CONSULTA_TRASLADO_ORGANISMO previo, excluyendo el actual)
        tramite_ant = (TramiteOrganismo.query
                       .join(Tramite, TramiteOrganismo.tramite_id == Tramite.id)
                       .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
                       .filter(TramiteOrganismo.organismo_expediente_id == org_exp.id)
                       .filter(TipoTramite.codigo.in_(
                           ['CONSULTA_SEPARATA', 'CONSULTA_TRASLADO_ORGANISMO']
                       ))
                       .filter(TramiteOrganismo.tramite_id != self._tarea.tramite_id)
                       .order_by(TramiteOrganismo.id.desc())
                       .first())
        doc_org = _doc_esperar_plazo(tramite_ant)
        ctx['organismo_fecha_respuesta'] = _formato_fecha(doc_org)

        # Respuesta del titular: ESPERAR_PLAZO del CONSULTA_TRASLADO_TITULAR más reciente
        traslado_tit = (TramiteOrganismo.query
                        .join(Tramite, TramiteOrganismo.tramite_id == Tramite.id)
                        .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
                        .filter(TramiteOrganismo.organismo_expediente_id == org_exp.id)
                        .filter(TipoTramite.codigo == 'CONSULTA_TRASLADO_TITULAR')
                        .order_by(TramiteOrganismo.id.desc())
                        .first())
        doc_tit = _doc_esperar_plazo(traslado_tit)
        ctx['titular_fecha_respuesta'] = _formato_fecha(doc_tit)

        # Número de iteraciones: COUNT de CONSULTA_TRASLADO_ORGANISMO del organismo
        ctx['organismo_num_iteraciones'] = (
            TramiteOrganismo.query
            .join(Tramite, TramiteOrganismo.tramite_id == Tramite.id)
            .join(TipoTramite, Tramite.tipo_tramite_id == TipoTramite.id)
            .filter(TramiteOrganismo.organismo_expediente_id == org_exp.id)
            .filter(TipoTramite.codigo == 'CONSULTA_TRASLADO_ORGANISMO')
            .count()
        )

        return ctx


def _doc_esperar_plazo(vinculo_tramite):
    """Devuelve el doc producido por la tarea ESPERAR_PLAZO del trámite vinculado, o None."""
    if not vinculo_tramite:
        return None
    tareas = {
        t.tipo_tarea.codigo: t
        for t in vinculo_tramite.tramite.tareas
        if t.tipo_tarea
    }
    tarea_esp = tareas.get('ESPERAR_PLAZO')
    return tarea_esp.documento_producido if tarea_esp else None


def _formato_fecha(doc):
    """Formatea fecha_administrativa de un documento como DD/MM/AAAA, o None."""
    if doc and doc.fecha_administrativa:
        return doc.fecha_administrativa.strftime('%d/%m/%Y')
    return None
