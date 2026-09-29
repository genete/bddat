"""Fechas y estado de un acto de notificar, derivados de sus documentos
(#928, N1 §5; ADR-049 §B/§C).

Fuente única: `Documento.fecha_administrativa`. Sustituye a leer directamente
`notificaciones.fecha_puesta_disposicion`/`fecha_resultado` (retiradas en
928c, ADR-049 §G) o a navegar `tarea.notificacion`/`tarea.vinculos_documento` a
pelo desde el resto del código — todo consumidor nuevo llama a este servicio.

Dos reglas uniformes, sin ramificar por canal (ADR-049 §C):
  - Cumplimiento del deber de notificar: la fecha más antigua entre los
    documentos vinculados (cualquier rol) de `JUSTIFICANTES_CUMPLIMIENTO`.
  - Efectos frente al interesado: la fecha del `PRODUCIDO`, si su tipo es un
    `JUSTIFICANTE_FINAL` y el resultado da la notificación por efectuada.

Y una regla de agregado, la del plazo de resolver (#930, N2; ADR-049 §E): el
acto se cumple con el documento que acredita la notificación al solicitante, que
es el cumplimiento de la `NOTIFICAR` de fuente `SOLICITANTE` del trámite
`NOTIFICACION` de la fase que lo resuelve (#969, ADR-051 §F; en ese trámite hay
también una `NOTIFICAR` por organismo o interesado, que no lo cumplen:
`documento_cumplimiento_fase`). Vive aquí y no en el acto
(`services/actos_solicitud.py`), que solo delega: la regla existe una sola vez.
Desde #947 (N4), con el `CERT_CUMPLIMIENTO_FASE` emitido se lee de él
(`services/sellos.py`) en vez de calcularse.

Destinatario (#967, N5a-1; ADR-051 §B/§K): una `NOTIFICAR` por destinatario
(ADR-051 §A), así que la tarea sigue teniendo una sola fila y las funciones de
fechas no cambian de firma. Aquí viven la regla «notificar al solicitante»
(`destinatario_solicitante`), la copia del destinatario (`copiar_destinatario`)
y las preguntas de las que cuelga el bloqueo sin destinatario
(`tiene_justificante`, `tuvo_escape_sin_destinatario`). Qué fuentes tiene cada
trámite y a quién hay que notificar por cada una es de
`services/destinatarios_notificacion.py` (#968, N5a-2). Escribir es de
`mutaciones_arbol` (`crear_tarea`, `fijar_destinatario`,
`anadir_notificaciones_que_faltan`).

`RESULTADOS`, `RESULTADOS_EFECTUADA` y `TIPOS_JUSTIFICANTE_PREVIO` viven en
`app.models.notificaciones` (junto al CHECK de `resultado`, 928c); se
reexportan aquí para que los consumidores tengan un único import.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.models.notificaciones import (  # noqa: F401 — reexportadas
    FUENTES, RESULTADOS, RESULTADOS_EFECTUADA, TIPOS_JUSTIFICANTE_PREVIO,
)
from app.services import sellos

# Dan CUMPLIMIENTO del deber de notificar (arts. 43.3, 40.4/42.2, 44): la
# fecha más antigua entre los vinculados a la tarea, cualquier rol.
# JUSTIFICANTE_BANDEJA/SIR no están — su "no aplica" sale solo, sin `if canal`.
JUSTIFICANTES_CUMPLIMIENTO = (
    'JUSTIFICANTE_NOTIFICA_DISPOSICION',
    'JUSTIFICANTE_POSTAL_1ER',
    'JUSTIFICANTE_NOTIFICA',
    'JUSTIFICANTE_POSTAL',
    'ANUNCIO_PUBLICADO',
)

# Justificantes finales: pueden ser el PRODUCIDO de la tarea y dan EFECTOS
# frente al interesado si el resultado lo permite (art. 41.7).
JUSTIFICANTES_FINALES = (
    'JUSTIFICANTE_NOTIFICA',
    'JUSTIFICANTE_POSTAL',
    'JUSTIFICANTE_BANDEJA',
    'JUSTIFICANTE_SIR',
    'ANUNCIO_PUBLICADO',
)

# `bitacora.detalle.accion` con que `…/notificar` registra la justificación de no
# poner en sede una notificación postal (ADR-049 §C). No lleva `escape: True`: no
# se fuerza ningún bloqueo. La relatan los certificados como acto salvado (#956,
# `informe_instruccion._relato_sede`).
ACCION_JUSTIFICAR_SEDE = 'JUSTIFICAR_SEDE'

# RESULTADOS_EFECTUADA (modelo): D1 ratificada — al publicarse el edicto,
# `resultado` pasa a CORRECTA, así que el filtro de efectos es el mismo para
# el justificante y para el anuncio.

# Canal implícito de cada tipo de documento de notificación — D6 (ADR-049
# §D): RECHAZADA solo tiene sentido en NOTIFICA y POSTAL, «en BANDEJA/SIR no
# consta ningún rechazo» (la recepción misma es la notificación).
CANAL_POR_TIPO_DOC = {
    'JUSTIFICANTE_NOTIFICA_DISPOSICION': 'NOTIFICA',
    'JUSTIFICANTE_NOTIFICA': 'NOTIFICA',
    'JUSTIFICANTE_POSTAL_1ER': 'POSTAL',
    'JUSTIFICANTE_POSTAL': 'POSTAL',
    'JUSTIFICANTE_BANDEJA': 'BANDEJA',
    'JUSTIFICANTE_SIR': 'SIR',
}

_RESULTADOS_POR_CANAL = {
    'NOTIFICA': RESULTADOS,
    'POSTAL': RESULTADOS,
    'BANDEJA': ('CORRECTA',),
    'SIR': ('CORRECTA',),
}


@dataclass(frozen=True)
class FechaNotificacion:
    """Una fecha derivada, junto con el documento que la acredita — N2/N4
    necesitan el `documento_id` (el certificado de cumplimiento lo guarda)."""
    fecha: date
    documento: 'Documento'  # noqa: F821 — anotación diferida, evita el import a nivel de módulo


def _tipo_codigo(documento) -> Optional[str]:
    return documento.tipo_doc.codigo if documento.tipo_doc is not None else None


def documentos_a_notificar(tarea) -> list:
    """Documentos CONSUMIDO que no son un justificante previo — lo único que
    cuenta `_estado_notificar`/`_check_finalizar_tarea` como "hay algo que
    notificar" (#928 N1 §8): un `NOTIFICAR` con solo la puesta a disposición
    vinculada no pasa por tener documento a notificar."""
    return [
        v.documento for v in tarea.vinculos_documento
        if v.rol == 'CONSUMIDO' and _tipo_codigo(v.documento) not in TIPOS_JUSTIFICANTE_PREVIO
    ]


def justificantes_previos(tarea) -> list:
    """Justificantes previos (disposición Notifica, 1er intento postal,
    sede) vinculados como CONSUMIDO — presupuesto del justificante final."""
    return [
        v.documento for v in tarea.vinculos_documento
        if v.rol == 'CONSUMIDO' and _tipo_codigo(v.documento) in TIPOS_JUSTIFICANTE_PREVIO
    ]


def fecha_cumplimiento(tarea) -> Optional[FechaNotificacion]:
    """La fecha más antigua entre los documentos vinculados a la tarea
    (cualquier rol) de `JUSTIFICANTES_CUMPLIMIENTO` con `fecha_administrativa`
    no nula. No lee `notificaciones.resultado`: el cumplimiento del deber de
    notificar es independiente de si la notificación salió bien. Empate:
    menor `documento.id`.
    """
    candidatos = [
        v.documento for v in tarea.vinculos_documento
        if _tipo_codigo(v.documento) in JUSTIFICANTES_CUMPLIMIENTO
        and v.documento.fecha_administrativa is not None
    ]
    if not candidatos:
        return None
    documento = min(candidatos, key=lambda d: (d.fecha_administrativa, d.id))
    return FechaNotificacion(fecha=documento.fecha_administrativa, documento=documento)


def fecha_efectos(tarea) -> Optional[FechaNotificacion]:
    """La `fecha_administrativa` del `PRODUCIDO` de la tarea, si su tipo está
    en `JUSTIFICANTES_FINALES` y el resultado da la notificación por
    efectuada (`RESULTADOS_EFECTUADA`, art. 41.7). Con `INCORRECTA` o sin
    resultado no hay efectos.

    Una tarea tiene un solo `PRODUCIDO` (índice único parcial
    `uq_documento_un_productor`): el anuncio del edicto (#568) y el
    justificante final no coexisten, así que no hace falta comparar "el más
    antiguo entre los dos" aquí — eso solo tiene sentido en el cumplimiento.
    """
    notif = tarea.notificacion
    if notif is None or notif.resultado not in RESULTADOS_EFECTUADA:
        return None
    documento = tarea.documento_producido
    if documento is None or _tipo_codigo(documento) not in JUSTIFICANTES_FINALES:
        return None
    if documento.fecha_administrativa is None:
        return None
    return FechaNotificacion(fecha=documento.fecha_administrativa, documento=documento)


# ---------------------------------------------------------------------------
# La notificación al solicitante y el cumplimiento del plazo del acto (#930, N2;
# por la fuente en #969, ADR-051 §F)
# ---------------------------------------------------------------------------

# El trámite cuya NOTIFICAR de fuente SOLICITANTE es la de la resolución al
# solicitante (D2). Invariante en código, no dato: las cinco fases finalizadoras
# lo tienen con una NOTIFICAR, y un test de catálogo protege la convención — si
# una finalizadora futura la rompiera, el plazo de su acto quedaría VENCIDO sin
# explicación. El trámite solo no basta: en él hay también una NOTIFICAR por
# organismo, propietario o interesado (ADR-051 §C), que no cierran el plazo de
# resolver. Las demás NOTIFICAR de una finalizadora (REQUERIMIENTO_RBDA_DEFINITIVA,
# publicaciones) tienen su propio plazo de cursar (art. 40.2), pero tampoco.
TRAMITE_NOTIFICACION_SOLICITANTE = 'NOTIFICACION'


def _codigo(tipo) -> Optional[str]:
    return tipo.codigo if tipo is not None else None


def _es_notificar_del_solicitante(fase, tramite, tarea) -> bool:
    """Núcleo del predicado, con la ascendencia ya en la mano: quien baja por
    el árbol (`documento_cumplimiento_fase`) no tiene que volver a subir.

    La fuente vive en la ficha desde que nace la tarea y no cambia (ADR-051
    §B), así que una NOTIFICAR al solicitante cerrada con escape sin
    destinatario sigue contando."""
    notificacion = tarea.notificacion
    return (
        _codigo(tarea.tipo_tarea) == 'NOTIFICAR'
        and _codigo(tramite.tipo_tramite) == TRAMITE_NOTIFICACION_SOLICITANTE
        and fase.tipo_fase is not None and bool(fase.tipo_fase.es_finalizadora)
        and notificacion is not None and notificacion.fuente == 'SOLICITANTE'
    )


def es_notificar_del_solicitante(tarea) -> bool:
    """La `NOTIFICAR` de fuente `SOLICITANTE` del trámite `NOTIFICACION` de una
    fase finalizadora: la notificación de la resolución al solicitante (o a su
    representante, ADR-051 §K). Es el único sitio que lo dice; lo usan el
    cálculo del cumplimiento y el indicador del payload de `…/notificar` (D10).
    Describe qué notificación es, no qué plazo cierra."""
    tramite = tarea.tramite
    return _es_notificar_del_solicitante(tramite.fase, tramite, tarea)


def documento_cumplimiento_fase(fase) -> Optional['Documento']:  # noqa: F821
    """Documento que acredita la notificación al solicitante de lo que resuelve
    `fase`, o `None`.

    Con sello se lee, sin sello se calcula (ADR-049 §E/§F, #947): si la fase
    tiene emitido su `CERT_CUMPLIMIENTO_FASE`, el documento es el que el
    certificado cita, aunque después se haya vinculado a la tarea un
    justificante con fecha anterior (D4) — la vía para cambiarlo es deshacer el
    certificado. Sin certificado, `calcular_documento_cumplimiento_fase`.

    Único punto de entrada del cumplimiento del acto: el acto
    (`ActoSolicitud.documento_cumplimiento`), el plazo y las barras de #922 lo
    heredan sin cambios. `plazos.py` no sabe que existen certificados.
    """
    if fase.tipo_fase is None or not fase.tipo_fase.es_finalizadora:
        return None
    sellado = sellos.documento_cumplimiento_sellado(fase)
    if sellado is not None:
        return sellado
    return calcular_documento_cumplimiento_fase(fase)


def calcular_documento_cumplimiento_fase(fase) -> Optional['Documento']:  # noqa: F821
    """El cálculo puro, sin mirar el sello: el cumplimiento
    (`fecha_cumplimiento`) más antiguo entre las `NOTIFICAR` del solicitante de
    la fase (empate: menor `documento.id`).

    `None` si la fase no es finalizadora, si no tiene esa `NOTIFICAR` o si
    ninguna tiene un justificante de cumplimiento con fecha (BANDEJA y SIR no
    lo son). No lee `notificaciones.resultado` ni el canal: lo hereda de
    `fecha_cumplimiento`.

    Pública porque la necesita, además del plazo sin sello, quien decide qué
    documento citaría el certificado (`cert_cumplimiento_fase.revisar`) y la
    puerta cerrada de su emisión: los dos preguntan por el cálculo aunque ya
    haya un sello.
    """
    if fase.tipo_fase is None or not fase.tipo_fase.es_finalizadora:
        return None
    candidatos = [
        cumplimiento
        for tramite in fase.tramites
        for tarea in tramite.tareas
        if _es_notificar_del_solicitante(fase, tramite, tarea)
        and (cumplimiento := fecha_cumplimiento(tarea)) is not None
    ]
    if not candidatos:
        return None
    return min(candidatos, key=lambda c: (c.fecha, c.documento.id)).documento


def estado_sede(tarea) -> Optional[str]:
    """Estado de la obligación paralela de sede electrónica (art. 42.1):

    - `None` si no aplica: sin fila `Notificacion`, o `canal != 'POSTAL'`.
    - `'PUESTA'` si hay un `JUSTIFICANTE_SEDE` vinculado con fecha.
    - `'JUSTIFICADA'` si `notificacion.sede_justificacion` tiene texto.
    - `'PENDIENTE'` en el resto de casos.
    """
    notif = tarea.notificacion
    if notif is None or notif.canal != 'POSTAL':
        return None
    for v in tarea.vinculos_documento:
        doc = v.documento
        if _tipo_codigo(doc) == 'JUSTIFICANTE_SEDE' and doc.fecha_administrativa is not None:
            return 'PUESTA'
    if notif.sede_justificacion:
        return 'JUSTIFICADA'
    return 'PENDIENTE'


def notificacion_efectuada(tarea) -> bool:
    """`tarea.ejecutada` (hay `PRODUCIDO`) y el resultado registrado da la
    notificación por efectuada. Sustituye a las comparaciones con
    `'CORRECTA'` repetidas a mano en `Tramite.finalizado` y
    `_check_crear_esperar_plazo` (#928 N1 §7)."""
    if not tarea.ejecutada:
        return False
    notif = tarea.notificacion
    return notif is not None and notif.resultado in RESULTADOS_EFECTUADA


def canal_de_tipo(codigo: str) -> Optional[str]:
    """Canal implícito de un tipo de documento de notificación, o `None` si
    el tipo no tiene canal propio (`JUSTIFICANTE_SEDE` no es una notificación;
    `ANUNCIO_PUBLICADO` es el edicto de #568, su canal es cosa suya — D15)."""
    return CANAL_POR_TIPO_DOC.get(codigo)


def fecha_sugerida(tipo_doc_codigo: Optional[str], parseo) -> Optional[date]:
    """Fecha administrativa que el pool propone al subir un justificante de
    Notifica ya parseado (#928 §10). Cada tipo lleva la fecha de SU hito — el
    defecto de ADR-049 §G era proponer la puesta a disposición para el
    justificante final:

    - `JUSTIFICANTE_NOTIFICA_DISPOSICION` → la puesta a disposición (art. 43.3).
    - `JUSTIFICANTE_NOTIFICA` → la lectura, única fecha de desenlace que lee el
      parser hoy (`None` en rechazada/caducada hasta el parser completo).
    - cualquier otro tipo, o parseo no reconocido → `None`.

    El parser completo futuro solo toca este lado: el frontend se limita a
    poner el valor que recibe.
    """
    if parseo is None or not parseo.reconocido:
        return None
    if tipo_doc_codigo == 'JUSTIFICANTE_NOTIFICA_DISPOSICION':
        instante = parseo.fecha_puesta_disposicion
    elif tipo_doc_codigo == 'JUSTIFICANTE_NOTIFICA':
        instante = parseo.fecha_lectura
    else:
        return None
    return instante.date() if instante is not None else None


def resultados_validos(canal: str) -> tuple:
    """Resultados admisibles para `canal` (D6: `RECHAZADA` solo en `NOTIFICA`
    y `POSTAL` — en `BANDEJA`/`SIR` «no consta ningún rechazo», ADR-049 §D)."""
    return _RESULTADOS_POR_CANAL.get(canal, RESULTADOS)


# ---------------------------------------------------------------------------
# Destinatario de la NOTIFICAR (#967, N5a-1 — ADR-051 §B, §C, §K)
# ---------------------------------------------------------------------------

# Qué dirección de la entidad se copia según la fuente (ADR-051 §B: «cada
# fuente lleva un rol»). Los roles de propietarios e interesados llegan con
# #431/#432; hasta entonces toman la de titular, como el solicitante.
_ROL_DIRECCION_POR_FUENTE = {
    'SOLICITANTE': 'titular',
    'ORGANISMO_DEL_TRAMITE': 'consultado',
    'ORGANISMOS_CONSULTADOS': 'consultado',
    'ORGANO_AMBIENTAL': 'consultado',
    'MINISTERIO': 'consultado',
    'ORGANO_SUPERIOR': 'consultado',
    'BOLETIN': 'publicador',
    'AYUNTAMIENTO': 'publicador',
    'PROPIETARIOS_DUP': 'titular',
    'INTERESADOS_RECONOCIDOS': 'titular',
}

# `bitacora.detalle.accion` del escape «vincular sin destinatario» (ADR-051
# §B), con `escape: True` sobre la tarea. Tras él la tarea queda sin
# destinatario para siempre.
ACCION_SIN_DESTINATARIO = 'NOTIFICAR_SIN_DESTINATARIO'

# `bitacora.detalle.accion` al fijar o refrescar el destinatario.
ACCION_FIJAR_DESTINATARIO = 'FIJAR_DESTINATARIO'

# Documentos cuya sola presencia en la tarea congela el destinatario: todo
# justificante, previo o final, incluida la sede (ADR-051 §D: «desde el primer
# justificante, la fila queda fija»).
_TIPOS_JUSTIFICANTE = (set(CANAL_POR_TIPO_DOC) | set(JUSTIFICANTES_CUMPLIMIENTO)
                       | set(TIPOS_JUSTIFICANTE_PREVIO))


@dataclass(frozen=True)
class Destinatario:
    """A quién se envía, en nombre de quién y desde qué dirección se copia.
    `direccion` es una `DireccionNotificacion`, o `None` si la entidad no tiene
    una del rol y se copia su dirección principal."""
    entidad: 'Entidad'  # noqa: F821
    en_nombre_de: Optional['Entidad']  # noqa: F821
    direccion: Optional['DireccionNotificacion']  # noqa: F821


def direccion_de_rol(entidad_id: int, fuente: str):
    """La dirección de notificación activa de la entidad para el rol de la
    fuente (la más reciente), o `None` → se usará su dirección principal."""
    from app.models.direccion_notificacion import DireccionNotificacion
    rol = _ROL_DIRECCION_POR_FUENTE.get(fuente, 'titular')
    return DireccionNotificacion.obtener_direccion_notificacion(
        entidad_id,
        es_titular=rol == 'titular',
        es_consultado=rol == 'consultado',
        es_publicador=rol == 'publicador',
    )


def destinatario_solicitante(solicitud) -> Optional[Destinatario]:
    """«Notificar al solicitante» (ADR-051 §K), la regla única: con
    representante en la solicitud, al representante en nombre del solicitante;
    sin él, al solicitante (`solicitudes.entidad_id`). La dirección, la de rol
    TITULAR de quien recibe, o su principal si no tiene."""
    solicitante = solicitud.entidad
    if solicitante is None:
        return None
    representante = solicitud.representante
    receptor = representante or solicitante
    return Destinatario(
        entidad=receptor,
        en_nombre_de=solicitante if representante is not None else None,
        direccion=direccion_de_rol(receptor.id, 'SOLICITANTE'),
    )


def copiar_destinatario(notif, destino: Destinatario, *, ahora) -> None:
    """Copia el destinatario en la fila (ADR-051 §B): entidad, representación
    (con nombre y NIF del representado), nombre, NIF, dirección postal y canales
    electrónicos. Es el único sitio que escribe esas columnas. La copia es lo que
    vale; `direccion_origen_id` queda solo como referencia. No valida ni
    comprueba si está congelada: eso es de `mutaciones_arbol.fijar_destinatario`."""
    entidad, src = destino.entidad, destino.direccion
    postal = src if src is not None else entidad
    mun = getattr(postal, 'municipio', None)
    representado = destino.en_nombre_de
    notif.entidad_id = entidad.id
    notif.en_nombre_de_entidad_id = representado.id if representado else None
    # Foto fija del representado (#968): la necesita el envío (Notifica lleva
    # al interesado y a su representante, cada uno con su NIF).
    notif.dest_en_nombre_de_nombre = representado.nombre_completo if representado else None
    notif.dest_en_nombre_de_nif = representado.nif if representado else None
    notif.direccion_origen_id = src.id if src is not None else None
    notif.dest_nombre = entidad.nombre_completo
    notif.dest_nif = (src.nif if src is not None and src.nif else None) or entidad.nif
    if postal.direccion_fallback:
        notif.dest_direccion = postal.direccion_fallback
        notif.dest_codigo_postal = None
        notif.dest_municipio = None
        notif.dest_provincia = None
    else:
        notif.dest_direccion = postal.direccion
        notif.dest_codigo_postal = postal.codigo_postal
        notif.dest_municipio = mun.nombre if mun else None
        notif.dest_provincia = mun.provincia if mun else None
    notif.dest_email = (src.email if src is not None and src.email else None) or entidad.email
    notif.dest_dir3 = src.codigo_dir3 if src is not None else None
    notif.dest_sir = src.codigo_sir if src is not None else None
    notif.destinatario_fijado_en = ahora


def tiene_justificante(tarea) -> bool:
    """Hay algún justificante vinculado a la tarea, previo o final, o un
    resultado registrado: desde entonces el destinatario queda fijo (ADR-051
    §D) — ya se envió algo a alguien."""
    notif = tarea.notificacion
    if notif is not None and notif.registrada:
        return True
    return any(_tipo_codigo(v.documento) in _TIPOS_JUSTIFICANTE for v in tarea.vinculos_documento)


def tuvo_escape_sin_destinatario(tarea) -> bool:
    """La tarea avanzó sin destinatario por escape justificado (ADR-051 §B):
    queda así para siempre. La constancia es la bitácora, como en los demás
    escapes (`escape: True` sobre `tareas`)."""
    if tarea.id is None:
        return False
    from app.models.bitacora import Bitacora
    entradas = Bitacora.query.filter_by(tabla='tareas', registro_id=tarea.id).all()
    return any((e.detalle or {}).get('accion') == ACCION_SIN_DESTINATARIO for e in entradas)


def falta_destinatario(tarea) -> bool:
    """La `NOTIFICAR` no puede avanzar: no tiene destinatario ni lo salvó un
    escape (ADR-051 §B). Una tarea que no es `NOTIFICAR` nunca."""
    if _codigo(tarea.tipo_tarea) != 'NOTIFICAR':
        return False
    notif = tarea.notificacion
    if notif is not None and notif.tiene_destinatario:
        return False
    return not tuvo_escape_sin_destinatario(tarea)
