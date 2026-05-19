from datetime import timedelta

from app.models.organismos_expediente import OrganismoExpediente


class ContextoNotificacionOrganismo:
    """
    Context Builder para escritos del trámite CONSULTA_TRASLADO_ORGANISMO.

    Enriquece el contexto base con datos del organismo consultado, la fecha
    de su última respuesta y la fecha límite calculada para la siguiente.

    Campos adicionales aportados:
    - organismo_nombre          str   Nombre oficial del organismo
    - organismo_nif             str   NIF del organismo (puede ser None)
    - organismo_plazo_legal     int   Plazo legal en días (30 o 15)
    - organismo_resultado       str   Estado actual del ciclo del organismo
    - organismo_fecha_respuesta str   Fecha de la respuesta recibida (DD/MM/AAAA o None)
    - organismo_fecha_limite    str   Fecha límite = respuesta + plazo_legal días (DD/MM/AAAA o None)
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

        tareas_por_codigo = {
            t.tipo_tarea.codigo: t
            for t in self._tarea.tramite.tareas
            if t.tipo_tarea
        }

        tarea_anal = tareas_por_codigo.get('ANALIZAR')
        consumidos = tarea_anal.documentos_consumidos if tarea_anal else []
        doc_respuesta = consumidos[0] if consumidos else None

        fecha_respuesta = (
            doc_respuesta.fecha_administrativa
            if doc_respuesta and doc_respuesta.fecha_administrativa else None
        )

        ctx['organismo_fecha_respuesta'] = (
            fecha_respuesta.strftime('%d/%m/%Y') if fecha_respuesta else None
        )

        plazo = org_exp.plazo_legal_dias
        ctx['organismo_fecha_limite'] = (
            (fecha_respuesta + timedelta(days=plazo)).strftime('%d/%m/%Y')
            if fecha_respuesta and plazo else None
        )

        return ctx
