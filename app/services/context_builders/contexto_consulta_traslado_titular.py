from app.models.tramites_organismos import TramiteOrganismo


class ContextoConsultaTrasladoTitular:
    """
    Context Builder para escritos del trámite CONSULTA_TRASLADO_TITULAR.

    Enriquece el contexto base con datos del organismo cuya respuesta se traslada
    al titular y las fechas del ciclo. Navega al organismo vía tramites_organismos
    (ADR-011 §1).

    Campos adicionales aportados:
    - organismo_nombre         str   Nombre oficial del organismo
    - organismo_nif            str   NIF del organismo (puede ser None)
    - organismo_plazo_legal    int   Plazo legal en días capturado al crear la separata
    - organismo_resultado      str   Estado del ciclo del organismo
    - organismo_fecha_respuesta str  Fecha del doc que consume ELABORAR (respuesta del
                                     organismo: de la separata o del traslado anterior).
                                     DD/MM/AAAA o None si el doc no tiene fecha
    - titular_fecha_respuesta  str   Fecha del doc producido por ESPERAR_PLAZO del trámite
                                     (respuesta del titular). DD/MM/AAAA o None si aún
                                     no se ha recibido respuesta
    """

    TOKENS = [
        {'campo': 'organismo_nombre',          'descripcion': 'Nombre oficial del organismo'},
        {'campo': 'organismo_nif',             'descripcion': 'NIF del organismo (puede ser vacío)'},
        {'campo': 'organismo_plazo_legal',     'descripcion': 'Plazo legal en días capturado al crear la separata'},
        {'campo': 'organismo_resultado',       'descripcion': 'Estado del ciclo del organismo'},
        {'campo': 'organismo_fecha_respuesta', 'descripcion': 'Fecha de la respuesta del organismo que se traslada (DD/MM/AAAA)'},
        {'campo': 'titular_fecha_respuesta',   'descripcion': 'Fecha de la respuesta del titular (DD/MM/AAAA)'},
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

        tareas_por_codigo = {
            t.tipo_tarea.codigo: t
            for t in self._tarea.tramite.tareas
            if t.tipo_tarea
        }

        # Respuesta del organismo: primer doc consumido por ELABORAR (obligatorio en migración 346)
        tarea_elab = tareas_por_codigo.get('ELABORAR')
        _consumidos_elab = tarea_elab.documentos_consumidos if tarea_elab else []
        doc_org = _consumidos_elab[0] if _consumidos_elab else None
        ctx['organismo_fecha_respuesta'] = (
            doc_org.fecha_administrativa.strftime('%d/%m/%Y')
            if doc_org and doc_org.fecha_administrativa else None
        )

        # Respuesta del titular: doc producido por ESPERAR_PLAZO del trámite actual
        tarea_esp = tareas_por_codigo.get('ESPERAR_PLAZO')
        doc_tit = tarea_esp.documento_producido if tarea_esp else None
        ctx['titular_fecha_respuesta'] = (
            doc_tit.fecha_administrativa.strftime('%d/%m/%Y')
            if doc_tit and doc_tit.fecha_administrativa else None
        )

        return ctx
