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
acto se cumple con el documento que acredita la notificación al titular, que
es el cumplimiento de la `NOTIFICAR` del trámite `NOTIFICACION` de la fase que
lo resuelve (`documento_cumplimiento_fase`). Vive aquí y no en el acto
(`services/actos_solicitud.py`), que solo delega: la regla existe una sola vez.
Desde #947 (N4), con el `CERT_CUMPLIMIENTO_FASE` emitido se lee de él
(`services/sellos.py`) en vez de calcularse.

Hueco para N5 (`Tarea.notificacion` → lista, un destinatario por fila): la
firma de cada función admitirá un `destinatario` opcional cuando llegue —
cambia este servicio, no sus llamadores.

`RESULTADOS`, `RESULTADOS_EFECTUADA` y `TIPOS_JUSTIFICANTE_PREVIO` viven en
`app.models.notificaciones` (junto al CHECK de `resultado`, 928c); se
reexportan aquí para que los consumidores tengan un único import.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.models.notificaciones import (  # noqa: F401 — reexportadas
    RESULTADOS, RESULTADOS_EFECTUADA, TIPOS_JUSTIFICANTE_PREVIO,
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
# La notificación al titular y el cumplimiento del plazo del acto (#930, N2)
# ---------------------------------------------------------------------------

# El trámite cuya NOTIFICAR es la de la resolución al titular (D2). Invariante
# en código, no dato: las cinco fases finalizadoras lo tienen con una
# NOTIFICAR, y un test de catálogo protege la convención — si una finalizadora
# futura la rompiera, el plazo de su acto quedaría VENCIDO sin explicación.
# Las demás NOTIFICAR de una finalizadora (NOTIFICACION_ORGANISMOS,
# NOTIFICACION_INTERESADOS, REQUERIMIENTO_RBDA_DEFINITIVA, publicaciones) tienen
# su propio plazo de cursar (art. 40.2), pero no cierran el de resolver.
TRAMITE_NOTIFICACION_TITULAR = 'NOTIFICACION'


def _codigo(tipo) -> Optional[str]:
    return tipo.codigo if tipo is not None else None


def _es_notificar_del_titular(fase, tramite, tarea) -> bool:
    """Núcleo del predicado, con la ascendencia ya en la mano: quien baja por
    el árbol (`documento_cumplimiento_fase`) no tiene que volver a subir."""
    return (
        _codigo(tarea.tipo_tarea) == 'NOTIFICAR'
        and _codigo(tramite.tipo_tramite) == TRAMITE_NOTIFICACION_TITULAR
        and fase.tipo_fase is not None and bool(fase.tipo_fase.es_finalizadora)
    )


def es_notificar_del_titular(tarea) -> bool:
    """La `NOTIFICAR` del trámite `NOTIFICACION` de una fase finalizadora: la
    notificación de la resolución al titular. Es el único sitio que lo dice;
    lo usan el cálculo del cumplimiento y el indicador del payload de
    `…/notificar` (D10). Describe qué notificación es, no qué plazo cierra."""
    tramite = tarea.tramite
    return _es_notificar_del_titular(tramite.fase, tramite, tarea)


def documento_cumplimiento_fase(fase) -> Optional['Documento']:  # noqa: F821
    """Documento que acredita la notificación al titular de lo que resuelve
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
    (`fecha_cumplimiento`) más antiguo entre las `NOTIFICAR` del titular de la
    fase (empate: menor `documento.id`).

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
        if _es_notificar_del_titular(fase, tramite, tarea)
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
