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

    Localización del trámite anterior delegada en
    `invariantes_esftt.diagnostico_tramite_anterior` (#717): mismo criterio
    que usa la derivación del vínculo CONSUMIDO — no se puede duplicar sin
    arriesgar divergencia entre "qué defectos se muestran" y "qué diagnóstico
    se marca consumido".

    Campos adicionales aportados (#679): los defectos del diagnóstico
    anterior, separados por origen — el escrito de requerimiento distingue
    los tres ejes de ADR-033 (documental/técnico/libre) en apartados propios,
    no un listado único. Los defectos ya vienen filtrados a "activos en el
    momento de producir" (un requerimiento libre resuelto no llega a entrar
    en Diagnostico.defectos, ver consolidar_defectos) — nada que filtrar aquí.
    - defectos_documentales  list[str]  Defectos de origen 'documental'
    - defectos_tecnicos      list[str]  Defectos de origen 'tecnico'
    - defectos_libres        list[str]  Defectos de origen 'requerimiento'
    """

    TOKENS = [
        {'campo': 'defectos_documentales', 'descripcion': 'Defectos documentales del diagnóstico anterior', 'tipo': 'lista'},
        {'campo': 'defectos_tecnicos', 'descripcion': 'Defectos técnicos del diagnóstico anterior', 'tipo': 'lista'},
        {'campo': 'defectos_libres', 'descripcion': 'Otros defectos (requerimientos libres) del diagnóstico anterior', 'tipo': 'lista'},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea or not self._tarea.tramite:
            return {}

        from app.services.invariantes_esftt import diagnostico_tramite_anterior

        diagnostico = diagnostico_tramite_anterior(self._tarea.tramite)
        if diagnostico is None:
            return {}

        defectos = diagnostico.as_contexto_cb()['diagnostico_defectos']

        def _textos(origen):
            return [d.get('texto', '') for d in defectos if d.get('origen') == origen]

        return {
            'defectos_documentales': _textos('documental'),
            'defectos_tecnicos': _textos('tecnico'),
            'defectos_libres': _textos('requerimiento'),
        }
