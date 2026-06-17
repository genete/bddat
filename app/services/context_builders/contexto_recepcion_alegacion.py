class ContextoRecepcionAlegacion:
    """
    Context Builder para documentos del trámite RECEPCION_ALEGACION.

    Enriquece el contexto con los datos del alegante registrado en el trámite.

    Campos aportados:
    - alegante_nombre          str   Nombre completo del alegante
    - alegante_nif             str   NIF del alegante (puede ser None)
    - alegante_tipo_interesado str   'particular', 'administracion', 'asociacion' o 'empresa'
    """

    TOKENS = [
        {'campo': 'alegante_nombre',          'descripcion': 'Nombre completo del alegante'},
        {'campo': 'alegante_nif',             'descripcion': 'NIF del alegante (puede ser vacío)'},
        {'campo': 'alegante_tipo_interesado', 'descripcion': 'particular, administracion, asociacion o empresa'},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        alegante = self._tarea.tramite.alegante
        if not alegante:
            return {}

        return alegante.as_contexto_cb()
