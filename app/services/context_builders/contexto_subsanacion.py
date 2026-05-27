class ContextoSubsanacion:
    """
    Context Builder para escritos del trámite REQUERIMIENTO_SUBSANACION.

    Enriquece el contexto base con la lista ordenada de defectos detectados
    en la tarea ANALIZAR asociada (tabla requerimientos_tarea).

    Campos adicionales aportados:
    - requerimientos    list  Lista de dicts ordenada por el campo `orden`

    Estructura de cada dict en requerimientos:
    - texto   str  Texto efectivo del requerimiento (catálogo o texto libre)
    - orden   int  Posición 1-based en el listado del escrito
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        return {
            'requerimientos': [
                {'texto': r.texto, 'orden': r.orden}
                for r in self._tarea.requerimientos
            ]
        }
