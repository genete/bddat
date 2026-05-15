class ContextoAnalisisDocumental:
    """
    Context Builder para documentos del trámite ANALISIS_DOCUMENTAL.

    Enriquece el contexto con el diagnóstico del documento producido
    por la tarea ANALIZAR del mismo trámite.

    Campos aportados:
    - diagnostico_resultado        str   'favorable', 'condicionado' o 'desfavorable'
    - diagnostico_defectos         list  Lista de defectos detectados
    - diagnostico_tiene_defectos   bool  True si hay al menos un defecto
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        tareas_por_codigo = {
            t.tipo_tarea.codigo: t
            for t in self._tarea.tramite.tareas
            if t.tipo_tarea
        }

        tarea_analizar = tareas_por_codigo.get('ANALIZAR')
        if not tarea_analizar:
            return {}

        doc = tarea_analizar.documento_producido
        if not doc:
            return {}

        if not doc.diagnostico:
            return {}

        return doc.diagnostico.as_contexto_cb()
