from app.models.informacion_publica import InformacionPublica


class ContextoInformacionPublica:
    """
    Context Builder para escritos de la tarea REDACTAR_ANUNCIO
    en la fase INFORMACION_PUBLICA.

    Campos adicionales aportados:
    - ip_antecedentes       str   Narración de la necesidad del anuncio (None si no redactado)
    - ip_fundamentos        str   Base normativa del trámite de IP (None si no redactado)
    - ip_exposicion_publica str   Bloque de exposición pública y plazo (None si no redactado)
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        fase = self._tarea.tramite.fase
        if not fase:
            return {}

        ip = fase.informacion_publica
        if ip:
            return ip.as_contexto_cb()

        return {
            'ip_antecedentes':       None,
            'ip_fundamentos':        None,
            'ip_exposicion_publica': None,
        }
