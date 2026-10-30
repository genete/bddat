"""
Las filas de la tarjeta «Notificaciones por edicto» de un trámite (#1037, ADR-052 §A y §G).

Una sola lista, formateada aquí para las dos puertas que la necesitan: el detalle de lectura
(`detalle_nodo`) y el esquema editable (`esquema_editable`). Lo que se ofrece y lo que se acepta
no pueden discrepar (contrato de selector de #1038, regla 4): ofrece
`notificaciones.candidatas_a_edicto` y acepta `mutaciones_arbol.editar_tramite`, con las mismas
funciones de `notificaciones`.

Cada fila lleva datos, no presentación: el front las agrupa (las que han fallado y las marcadas
arriba; plegadas, las que siguen en curso y las ya notificadas) con `intentos_fallidos`,
`cerrada` y `marcada`.
"""
from typing import Optional

from app.services import notificaciones as notif_svc
from app.services.estado_dominio import estado_tarea, motivo


def _texto(notif) -> str:
    """Cómo se nombra al destinatario en la fila: nombre y NIF, o que aún no tiene."""
    if not notif.dest_nombre:
        return 'Sin destinatario'
    return f'{notif.dest_nombre} ({notif.dest_nif})' if notif.dest_nif else notif.dest_nombre


def fila(ta) -> dict:
    """La fila de una notificación: la usan la tarjeta de marcas y la de las recogidas."""
    notif = ta.notificacion
    estado = estado_tarea(ta)
    return {
        'valor': ta.id,
        'texto': _texto(notif),
        # No puede avanzar hasta fijar a quién se notifica (ADR-051 §B): aplicar el anuncio
        # se negaría a cerrarla.
        'sin_destinatario': notif_svc.falta_destinatario(ta),
        'estado': estado,
        'motivo': motivo(estado),
        'intentos_fallidos': notif_svc.intentos_fallidos(ta),
        'cerrada': ta.ejecutada,
        'marcada': notif.va_por_edicto,
        'recogida': notif.tramite_edictal_id is not None,
        # Por qué no se puede cambiar la casilla hoy, o None. La de una marcada es la de
        # quitarla; la de una sin marcar, la de ponerla.
        'bloqueo': (notif_svc.motivo_no_desmarcable(ta) if notif.va_por_edicto
                    else notif_svc.motivo_no_marcable(ta)),
    }


def fichas(tramite) -> Optional[dict]:
    """`{'filas', 'marcadas', 'aviso'}` del trámite, o `None` si no tiene ninguna `NOTIFICAR`
    cuya fuente admita edicto (entonces ni la tarjeta ni el campo del esquema existen).

    - `filas`: las candidatas, por id, cerradas o no.
    - `marcadas`: los ids marcados, de cualquier fuente: es el valor del campo.
    - `aviso`: si hay marcas sobre notificaciones que ya no son candidatas (la lista de
      fuentes cambió); se conservan hasta que alguien las quite (contrato de selector,
      regla 2: un valor guardado que ya no es opción no se oculta)."""
    candidatas = notif_svc.candidatas_a_edicto(tramite)
    if not candidatas:
        return None
    marcadas = notif_svc.marcadas_para_edicto(tramite)
    ids_candidatas = {ta.id for ta in candidatas}
    sobrantes = [ta.id for ta in marcadas if ta.id not in ids_candidatas]
    aviso = None
    if sobrantes:
        aviso = ('Hay notificaciones marcadas para edicto cuyo destinatario ya no lo admite '
                 '(tarea ' + ', '.join(f'#{i}' for i in sobrantes) + '). Se conservan hasta '
                 'que alguien las quite.')
    return {
        'filas': [fila(ta) for ta in candidatas],
        'marcadas': [ta.id for ta in marcadas],
        'aviso': aviso,
    }
