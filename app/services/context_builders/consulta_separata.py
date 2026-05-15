from app.models.organismos_expediente import OrganismoExpediente


class ContextoConsultaSeparata:
    """
    Context Builder para escritos del trámite CONSULTA_SEPARATA.

    Enriquece el contexto base con datos del organismo consultado y las
    fechas del ciclo de consulta. Requiere que el trámite tenga un registro
    en organismos_expediente (campo tramite_id enlazado).

    Campos adicionales aportados:
    - organismo_nombre       str   Nombre oficial del organismo
    - organismo_nif          str   NIF del organismo (puede ser None)
    - organismo_plazo_legal  int   Plazo legal en días (30 o 15 según tipo expediente)
    - organismo_resultado    str   Estado del ciclo: pendiente, conformidad, condicionado…
    - organismo_fecha_envio  str   Fecha de la notificación enviada (DD/MM/AAAA o None)
    - organismo_fecha_respuesta str Fecha del documento de respuesta recibido (DD/MM/AAAA o None)
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        org_exp = (OrganismoExpediente.query
                   .filter_by(tramite_id=self._tarea.tramite_id)
                   .first())

        if not org_exp:
            return {}

        ctx = org_exp.as_contexto_cb()

        # Fechas desde las tareas del trámite (pueden no existir aún)
        tareas_por_codigo = {
            t.tipo_tarea.codigo: t
            for t in self._tarea.tramite.tareas
            if t.tipo_tarea
        }

        tarea_notif = tareas_por_codigo.get('NOTIFICAR')
        tarea_anal = tareas_por_codigo.get('ANALIZAR')

        doc_envio = tarea_notif.documento_producido if tarea_notif else None
        doc_respuesta = tarea_anal.documento_usado if tarea_anal else None

        ctx['organismo_fecha_envio'] = (
            doc_envio.fecha_administrativa.strftime('%d/%m/%Y')
            if doc_envio and doc_envio.fecha_administrativa else None
        )
        ctx['organismo_fecha_respuesta'] = (
            doc_respuesta.fecha_administrativa.strftime('%d/%m/%Y')
            if doc_respuesta and doc_respuesta.fecha_administrativa else None
        )

        return ctx
