class ContextoSubsanacion:
    """
    Context Builder para escritos del trámite REQUERIMIENTO_SUBSANACION.

    Enriquece el contexto con los defectos del Diagnostico producido por la
    tarea ANALIZAR del trámite ANTERIOR dentro de la misma fase — el trámite
    inmediatamente anterior por id a self._tarea.tramite (ANÁLISIS_DOCUMENTAL
    en la primera vuelta; un REQUERIMIENTO_SUBSANACIÓN previo en vueltas
    posteriores, ver DISEÑO_ANALISIS_SOLICITUD.md §3).

    Corrige #406 (leía `tarea.requerimientos` directamente): esa tabla es solo
    el borrador de trabajo del shuttle (#440), no el documento de salida — el
    escrito debe ver los tres orígenes (documental #495, técnico #581,
    requerimientos #440) ya consolidados en el Diagnostico, no solo el
    shuttle. Ver [[project_diseno_tarea_analizar_442]] y ADR-025 §4
    (reclasificado de Auto-trámite a Solicitud/fase-scoped).

    Campos adicionales aportados:
    - requerimientos    list  Defectos del diagnóstico anterior, ordenados
    """

    TOKENS = [
        {'campo': 'requerimientos', 'descripcion': 'Defectos del diagnóstico anterior', 'tipo': 'tabla', 'columnas': [
            {'campo': 'texto', 'descripcion': 'Texto del defecto'},
            {'campo': 'orden', 'descripcion': 'Posición en el listado'},
        ]},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea or not self._tarea.tramite:
            return {}

        fase = self._tarea.tramite.fase
        tramites_previos = sorted(
            (t for t in fase.tramites if t.id < self._tarea.tramite.id),
            key=lambda t: t.id,
        )
        if not tramites_previos:
            return {}
        tramite_anterior = tramites_previos[-1]

        tarea_analizar = next(
            (t for t in tramite_anterior.tareas if t.tipo_tarea and t.tipo_tarea.codigo == 'ANALIZAR'),
            None,
        )
        if tarea_analizar is None:
            return {}

        doc = tarea_analizar.documento_producido
        if doc is None or doc.diagnostico is None:
            return {}

        defectos = doc.diagnostico.as_contexto_cb()['diagnostico_defectos']
        return {
            'requerimientos': [
                {'texto': d.get('texto', ''), 'orden': i}
                for i, d in enumerate(defectos, start=1)
            ],
        }
