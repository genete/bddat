"""Módulo único de sellos (ADR-049 §F, #947 — N4).

Un certificado emitido **sella** lo que constata: desde ese momento se lee de él,
no se calcula, y lo que cita no se toca («con sello se lee, sin sello se
calcula»). Aquí vive la respuesta a las dos preguntas que el resto del sistema
le hace a un sello:

- **«¿Me usa algún certificado?»** — `certificado_que_cita`, `motivo_sellado`,
  `motivo_vinculo_sellado`. El CRUD de documentos (pool, `editar_tarea`) pregunta
  aquí antes de dejar cambiar la fecha, el tipo o el fichero de un documento,
  desvincularlo o borrarlo. Un `documento_id` dentro de `certificados.datos`
  (JSONB) no es clave foránea: nadie más que este módulo lo protege.
- **«¿Qué dice el sello?»** — `documento_cumplimiento_sellado`, la lectura que
  `notificaciones.documento_cumplimiento_fase` antepone al cálculo.

Una función por tipo de certificado y un solo punto de comprobación, sin motor
declarativo genérico (§F). Nace con un único tipo, `CERT_CUMPLIMIENTO_FASE`; el
sello de `CERT_FIN_INSTRUCCION` (#838) sigue en `invariantes_esftt` hasta que se
mude aquí (N7/N9).

SER CERTIFICADO NO DEPENDE DE LA URL (#947, D2)
===============================================
Son dos preguntas distintas que hasta ahora respondía el mismo campo:

1. **¿Dónde está el papel?** `Documento.url`. Hoy `bddat://certificados/N`, que
   quiere decir «no hay papel, se pinta»; el día que el certificado pase a PDF,
   la ruta del fichero.
2. **¿Qué sella?** La fila de `certificados` (unida por `documento_id`), que no
   cambia al pasar a PDF.

Todo código que necesite saber si un documento es un certificado pregunta por su
fila (`doc.certificado`), **nunca** por el esquema de la url. Así el paso a PDF
solo cambia dónde está el papel.

Dependencias: solo modelos. `services.notificaciones` importa este módulo; este
no importa aquel, para no cerrar un ciclo.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento

log = logging.getLogger(__name__)

CERT_CUMPLIMIENTO_FASE = 'CERT_CUMPLIMIENTO_FASE'


# ---------------------------------------------------------------------------
# ¿Qué dice el sello? — lectura
# ---------------------------------------------------------------------------

def certificado_cumplimiento(fase) -> Optional[Certificado]:
    """El `CERT_CUMPLIMIENTO_FASE` emitido de `fase`, o `None`.

    En memoria sobre `fase.certificados_cumplimiento`, que el árbol carga con
    `opciones_solicitud()`: leer el sello no cuesta una sentencia por fase. El
    índice único `(fase_id, tipo)` (#932) garantiza que hay como mucho uno.
    """
    return next(
        (c for c in fase.certificados_cumplimiento if c.tipo == CERT_CUMPLIMIENTO_FASE),
        None,
    )


def documento_citado(certificado) -> Optional[Documento]:
    """El documento que cita un `CERT_CUMPLIMIENTO_FASE`.

    `datos` guarda `{"documento_id": N}` y nada más: ni su fecha (una sola
    fuente, §F) ni su tipo, tarea o actos, que se derivan del documento y de la
    fase — y no pueden cambiar mientras el sello exista.

    `db.session.get` mira antes el mapa de identidad: con el árbol cargado, el
    documento citado ya está en él (cuelga de la `NOTIFICAR` de la fase) y no
    se emite ninguna sentencia. Si no lo está, lo trae de la BD.
    """
    documento_id = (certificado.datos or {}).get('documento_id')
    if documento_id is None:
        log.warning('sellos: el certificado %s no cita ningún documento', certificado.id)
        return None
    documento = db.session.get(Documento, documento_id)
    if documento is None:
        # No debería ocurrir: el borrado del documento citado lo niega el pool y
        # su desvinculación, `editar_tarea`. Si ocurre, el llamador vuelve al
        # cálculo, que es lo más cercano a la verdad que queda.
        log.warning('sellos: el certificado %s cita el documento %s, que no existe',
                    certificado.id, documento_id)
    return documento


def documento_cumplimiento_sellado(fase) -> Optional[Documento]:
    """El documento que el `CERT_CUMPLIMIENTO_FASE` de `fase` fija como
    acreditación de la notificación al titular, o `None` si no hay sello."""
    certificado = certificado_cumplimiento(fase)
    return documento_citado(certificado) if certificado is not None else None


# ---------------------------------------------------------------------------
# ¿Me usa algún certificado? — protección
# ---------------------------------------------------------------------------

def es_certificado_emitido(documento) -> bool:
    """`documento` es él mismo un certificado emitido: tiene fila en
    `certificados`. Por la fila, nunca por la url (D2)."""
    return documento is not None and documento.certificado is not None


def certificado_que_cita(documento) -> Optional[Certificado]:
    """El certificado emitido que cita `documento`, o `None`.

    Hoy solo cita documentos el `CERT_CUMPLIMIENTO_FASE` (`datos.documento_id`).
    `CERT_PLAZO_CUMPLIDO` guarda un `documento_inicio_id` que tampoco es FK, pero
    protegerlo es de N7/N8.
    """
    if documento is None or documento.id is None:
        return None
    return (
        Certificado.query
        .filter(
            Certificado.tipo == CERT_CUMPLIMIENTO_FASE,
            Certificado.datos['documento_id'].as_integer() == documento.id,
        )
        .first()
    )


def motivo_sellado(documento) -> Optional[str]:
    """Por qué no se puede tocar `documento` y cuál es la salida, o `None` si
    ningún sello lo alcanza. Mensaje único para el pool y para `editar_tarea`.

    Dos casos: el documento lo **cita** un certificado (su fecha es la que
    cuenta), o **es** un certificado emitido. Como los bloqueos del sello de la
    instrucción, el mensaje nombra la salida en vez de prohibir a secas.
    """
    certificado = certificado_que_cita(documento)
    if certificado is not None:
        return (
            f'Este documento acredita la notificación al titular de la fase '
            f'«{_nombre_fase(certificado.fase)}», y así lo hace constar su certificado '
            f'de cumplimiento, emitido el {_fecha_emision(certificado)}: no puede '
            f'cambiarse su fecha, su tipo ni su fichero, ni desvincularse de la tarea, '
            f'ni borrarse. Si no es el documento correcto, deshaga el certificado de '
            f'cumplimiento desde el inspector de la fase y vuelva a emitirlo.'
        )

    propio = documento.certificado if documento is not None else None
    if propio is None:
        return None
    if propio.tipo == CERT_CUMPLIMIENTO_FASE:
        return (
            f'Este documento es el certificado de cumplimiento de la fase '
            f'«{_nombre_fase(propio.fase)}»: no se edita ni se borra desde el pool. '
            f'Para retirarlo, deshágalo desde el inspector de la fase.'
        )
    nombre = documento.tipo_doc.nombre if documento.tipo_doc else propio.tipo
    return (
        f'Este documento es un certificado emitido por el sistema ({nombre}): '
        f'no se edita ni se borra desde el pool.'
    )


def motivo_vinculo_sellado(tarea, documento) -> Optional[str]:
    """Por qué no se puede soltar (desvincular o cambiar de rol) el vínculo de
    `documento` con `tarea`, o `None`.

    Se protege el vínculo con la tarea de la fase sellada (ADR-049 §F: «el
    documento citado, su vínculo con la tarea»), no los que el mismo documento
    pueda tener con tareas de otras fases: esos no sostienen el sello.

    El resto de la `NOTIFICAR` sigue editable (D4): en POSTAL y NOTIFICA el
    justificante final llega después de emitir, a la misma tarea.
    """
    certificado = certificado_que_cita(documento)
    if certificado is None or tarea.tramite.fase_id != certificado.fase_id:
        return None
    return motivo_sellado(documento)


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def momento_emision(certificado) -> Optional[datetime]:
    """`generado_en` en la hora local del servidor.

    La columna es `DateTime` sin zona y el ORM la rellena con `utcnow()`. Se
    convierte con `astimezone()` sin argumento —la zona del sistema— porque en
    Windows no hay `tzdata` y `zoneinfo` no resolvería «Europe/Madrid».
    """
    if certificado.generado_en is None:
        return None
    return certificado.generado_en.replace(tzinfo=timezone.utc).astimezone()


def _fecha_emision(certificado) -> str:
    momento = momento_emision(certificado)
    return momento.strftime('%d/%m/%Y') if momento else '—'


def _nombre_fase(fase) -> str:
    if fase is None:
        return '—'
    tf = fase.tipo_fase
    return (tf.nombre or tf.codigo) if tf else f'#{fase.id}'
