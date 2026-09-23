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


def resultados_validos(canal: str) -> tuple:
    """Resultados admisibles para `canal` (D6: `RECHAZADA` solo en `NOTIFICA`
    y `POSTAL` — en `BANDEJA`/`SIR` «no consta ningún rechazo», ADR-049 §D)."""
    return _RESULTADOS_POR_CANAL.get(canal, RESULTADOS)
