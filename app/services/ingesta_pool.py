"""Entrada de ficheros al pool del expediente (ADR-032 §1/§4, ADR-050 §B).

Puerta única de «un documento que entra al pool»: la subida del pool y de la Despensa y el
alta de expediente (el documento de solicitud entra al pool como cualquier otro, y el alta no
puede llamar a un endpoint desde dentro de su propia transacción). Hace lo que es del pool y
no del contenido: la comprobación de la fecha obligatoria (#885, #928) y el armado de los
documentos. Guardar el contenido es del módulo de contenido (`contenido.subir`): validar todos
los ficheros, enviarlos al almacén y construir los `Documento`.

**No hace commit ni añade los documentos a la sesión, a propósito.** Los devuelve en el orden
de los ficheros y es el llamador quien los añade y decide cuándo cerrar: la ruta del pool
los añade de uno en uno (el corte de cada uno necesita el id del anterior ya puesto) y
commitea el lote entero; el alta de expediente lo hace junto con el expediente, el proyecto y
la solicitud, que es lo que permite que el fallo de cualquiera de los cuatro deshaga los
otros tres. Lo que el almacén ya recibió no se deshace: un contenido sin documento queda sin
referencias y lo recoge la limpieza (fase 7).

Lo que NO entra aquí es todo lo que solo tiene sentido hablando HTTP: el permiso, el 503 si
el almacén no contesta, el parseo del JSON de metadatos y la traducción de un error a código
de estado. Eso se queda en la ruta.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import BinaryIO, Optional, Sequence

from app.models.documentos import Documento
from app.services.almacenamiento.contenido import EntradaSubida, subir
from app.services.reformados import exigir_fecha_administrativa


@dataclass(frozen=True)
class FicheroAIngestar:
    """Un fichero que entra al pool y los datos de su documento.

    `flujo` es binario y con `seek` (el temporal en que el servidor web deja la subida);
    `nombre_original` es el que llega del navegador y entra saneado (ADR-050 §C).
    """
    flujo: BinaryIO
    nombre_original: str
    tipo_doc_id: int
    fecha_administrativa: Optional[date] = None
    asunto: Optional[str] = None
    prioridad: bool = False


def ingestar_en_pool(expediente, ficheros: Sequence[FicheroAIngestar]) -> list[Documento]:
    """Sube los ficheros al almacén y devuelve sus `Documento`, sin añadirlos a la sesión.

    Todo o nada: primero se comprueba la fecha obligatoria de **todos** (un DOC_PROYECTO sin
    fecha administrativa no es ingestable, #885, ADR-044 §C; desde #928 son los tipos de
    `fechas.TIPOS_FECHA_OBLIGATORIA`) y después `subir` valida todos los ficheros antes de
    enviar el primero. Así un fallo en el último no deja contenidos enviados del resto. La
    guarda de verdad es un listener del modelo, que salta en el flush —cuando el contenido ya
    está en el almacén—, por eso aquí se pregunta antes de enviar nada.

    Subir dos veces el mismo contenido no lo duplica: el almacén lo guarda una vez y cada
    subida crea su documento (ADR-032 §4: quien lo sube lo ha pedido, sin bloquear ni avisar).

    La fecha administrativa la valida el propio modelo (#824): si es futura, construir el
    `Documento` lanza `ValueError` y no se envía nada. Se deja subir hasta el llamador en vez
    de traducirla aquí, porque cada puerta la cuenta a su manera —la ruta del pool devuelve un
    error con el mensaje, el formulario de alta lo repinta junto al campo—.

    Lanza `FormatoNoAdmitido` (mensaje para el usuario), `ValueError` o `AlmacenNoDisponible`
    (reintentar en unos minutos).
    """
    for fichero in ficheros:
        exigir_fecha_administrativa(fichero.tipo_doc_id, fichero.fecha_administrativa)

    return subir([
        EntradaSubida(fichero.flujo, fichero.nombre_original, {
            'expediente_id': expediente.id,
            'tipo_doc_id': fichero.tipo_doc_id,
            'fecha_administrativa': fichero.fecha_administrativa,
            'asunto': fichero.asunto,
            'prioridad': 1 if fichero.prioridad else 0,
        })
        for fichero in ficheros
    ])
