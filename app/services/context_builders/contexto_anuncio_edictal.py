from app.services import notificaciones as notif_svc
from app.services.invariantes_esftt import TRAMITE_EDICTAL


def _identificacion(notif):
    """Cómo se identifica a un afectado en un anuncio del art. 44 LPACAP: su documento
    completo; si no tiene, su nombre y apellidos. Nunca los dos (DA 7.ª LOPDGDD).
    `None` si no hay ni uno ni otro."""
    documento = (notif.dest_nif or '').strip()
    return documento or (notif.dest_nombre or '').strip() or None


class ContextoAnuncioEdictal:
    """
    Context Builder para el anuncio del trámite NOTIFICACION_EDICTAL (#1037, ADR-052 §A y §G).

    Se ancla en el ELABORAR del propio trámite edictal (auto-trámite) y aporta a quiénes se
    notifica por el anuncio: las NOTIFICAR que el edicto recogió al crearse, marcadas antes por
    el usuario.

    Campos adicionales aportados:
    - interesados_edicto   list[str]  Cómo se identifica a cada interesado en el anuncio

    **Qué se publica (DA 7.ª LOPDGDD, Ley Orgánica 3/2018).** En la notificación por anuncios del
    art. 44 LPACAP se identifica al afectado exclusivamente por el número completo de su documento
    (DNI, NIE, pasaporte o equivalente); si no tiene, solo por nombre y apellidos; y en ningún caso
    el nombre junto al documento completo. Por eso el contexto no aporta nombre y NIF por separado:
    cada elemento de `interesados_edicto` es ya lo publicable, y una plantilla no puede imprimir los
    dos juntos aunque quiera. Tampoco se aporta la dirección, que no se publica.

    Se lee de la copia congelada del destinatario en cada notificación (`dest_*`), no de la ficha
    de hoy. `dest_en_nombre_de_*` (el representado) solo se rellena para el solicitante con
    representante (ADR-051 §K), que no admite edicto (`FUENTES_QUE_ADMITEN_EDICTO`): si algún día
    lo admite, habrá que decidir a quién identifica el anuncio.

    Falla con aviso, no devuelve una lista vacía: un anuncio sin interesados, o con uno que no se
    puede identificar, es un defecto jurídico que nadie vería al generarlo.
    """

    TOKENS = [
        {'campo': 'interesados_edicto',
         'descripcion': 'Interesados a quienes se notifica por el anuncio, cada uno ya identificado '
                        'como exige la DA 7.ª LOPDGDD: su documento completo o, si no tiene, su '
                        'nombre (nunca los dos)',
         'tipo': 'lista'},
    ]

    def __init__(self, expediente, db_session, tarea=None):
        self._expediente = expediente
        self._db = db_session
        self._tarea = tarea

    def get_contexto(self) -> dict:
        tarea = self._tarea
        if (tarea is None or tarea.tramite is None
                or tarea.tramite.tipo_tramite.codigo != TRAMITE_EDICTAL):
            raise ValueError(
                f'El anuncio edictal solo se redacta desde el ELABORAR de un trámite {TRAMITE_EDICTAL}.')

        recogidas = notif_svc.recogidas_por_edicto(tarea.tramite)
        if not recogidas:
            raise ValueError(
                'Este edicto no ha recogido ninguna notificación: marca antes, en el trámite de '
                'notificación de la fase, las que van por edicto.')

        sin_identificar = []
        identificaciones = []
        for ta in recogidas:
            identificacion = _identificacion(ta.notificacion)
            if identificacion is None:
                sin_identificar.append(f'#{ta.id}')
            else:
                identificaciones.append(identificacion)
        if sin_identificar:
            raise ValueError(
                'No se puede redactar el anuncio: no se puede identificar al interesado de las '
                'notificaciones de las tareas ' + ', '.join(sin_identificar)
                + ' (sin destinatario). Fija antes a quién se notifica.')

        # Sin repetir: el mismo interesado en dos notificaciones sale una vez.
        return {'interesados_edicto': list(dict.fromkeys(identificaciones))}
