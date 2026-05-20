from app.models.resolucion import Resolucion


class ContextoResolucion:
    """
    Context Builder para escritos del trámite ELABORACION (fase RESOLUCION).

    Enriquece el contexto base con el sentido del acto (desde Fase.resultado_fase)
    y los cuatro bloques redaccionales de la tabla resoluciones.

    Campos adicionales aportados:
    - sentido_acto_codigo       str   Código del resultado: FAVORABLE, DESFAVORABLE…
    - sentido_acto_nombre       str   Nombre legible del resultado de fase
    - resolucion_antecedentes   str   Antecedentes del expediente (None si no redactado)
    - resolucion_fundamentos    str   Fundamentos jurídicos (None si no redactado)
    - resolucion_resuelve       str   Expresión verbal del sentido (None si no redactado)
    - resolucion_condicionado   str   Condicionado técnico (None si no redactado)
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

        resultado = fase.resultado_fase
        if not resultado:
            return {}

        ctx = {
            'sentido_acto_codigo': resultado.codigo,
            'sentido_acto_nombre': resultado.nombre,
        }

        resolucion = fase.resolucion
        if resolucion:
            ctx.update(resolucion.as_contexto_cb())
        else:
            ctx.update({
                'resolucion_antecedentes': None,
                'resolucion_fundamentos':  None,
                'resolucion_resuelve':     None,
                'resolucion_condicionado': None,
            })

        return ctx
