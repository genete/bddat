class ContextoAnalisisAlegaciones:
    """
    Context Builder para documentos del trámite ANALISIS_ALEGACIONES.

    Agrega los datos de todos los trámites RECEPCION_ALEGACION de la misma
    solicitud que tengan alegante registrado. Navega via tarea → tramite →
    fase → solicitud para acotar el alcance a la solicitud correcta.

    Campos aportados en el contexto raíz:
    - num_alegaciones          int   Total de alegaciones registradas
    - alegaciones              list  Un dict por alegante (ver estructura abajo)
    - resumen_clasificacion    dict  Conteo por tipo_interesado

    Estructura de cada dict en alegaciones:
    - alegante_nombre              str   Nombre (entidad si entidad_id, campo local si no)
    - alegante_nif                 str   NIF (ídem; puede ser None)
    - alegante_tipo_interesado     str   particular | administracion | asociacion | empresa
    - alegacion_asunto             str   asunto del doc ALEGACION_IP (puede ser None)
    - alegacion_fecha              str   fecha_administrativa de ALEGACION_IP (DD/MM/AAAA o None)
    - respuesta_titular_recibida   bool  True si ESPERAR_PLAZO tiene documento_producido
    - respuesta_titular_asunto     str   asunto de RESPUESTA_TITULAR_ALEGACION (puede ser None)
    - respuesta_titular_fecha      str   fecha_administrativa de RESPUESTA_TITULAR_ALEGACION (DD/MM/AAAA o None)
    """

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        if not self._tarea:
            return {}

        solicitud = self._tarea.tramite.fase.solicitud

        tramites_recepcion = [
            t
            for fase in solicitud.fases
            for t in fase.tramites
            if t.tipo_tramite
            and t.tipo_tramite.codigo == 'RECEPCION_ALEGACION'
            and t.alegante
        ]

        alegaciones = [self._datos_alegacion(t) for t in tramites_recepcion]

        resumen = {}
        for a in alegaciones:
            tipo = a['alegante_tipo_interesado']
            resumen[tipo] = resumen.get(tipo, 0) + 1

        return {
            'num_alegaciones': len(alegaciones),
            'alegaciones': alegaciones,
            'resumen_clasificacion': resumen,
        }

    def _datos_alegacion(self, tramite) -> dict:
        tareas = {t.tipo_tarea.codigo: t for t in tramite.tareas if t.tipo_tarea}

        tarea_analizar = tareas.get('ANALIZAR')
        _consumidos = tarea_analizar.documentos_consumidos if tarea_analizar else []
        doc_alegacion = _consumidos[0] if _consumidos else None

        tarea_esperar = tareas.get('ESPERAR_PLAZO')
        doc_respuesta = tarea_esperar.documento_producido if tarea_esperar else None

        ctx = tramite.alegante.as_contexto_cb()
        ctx.update({
            'alegacion_asunto': doc_alegacion.asunto if doc_alegacion else None,
            'alegacion_fecha': (
                doc_alegacion.fecha_administrativa.strftime('%d/%m/%Y')
                if doc_alegacion and doc_alegacion.fecha_administrativa else None
            ),
            'respuesta_titular_recibida': doc_respuesta is not None,
            'respuesta_titular_asunto': doc_respuesta.asunto if doc_respuesta else None,
            'respuesta_titular_fecha': (
                doc_respuesta.fecha_administrativa.strftime('%d/%m/%Y')
                if doc_respuesta and doc_respuesta.fecha_administrativa else None
            ),
        })
        return ctx
