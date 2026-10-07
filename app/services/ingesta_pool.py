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

Aquí viven también las dos reglas de la URL externa (ADR-050 §C y §M), para que valgan igual
vengan por la ruta que vengan: solo `http(s)://` entra como URL externa, y la `url` de un
documento solo se rectifica si es de URL externa, dejando la anterior en la bitácora.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import BinaryIO, Optional, Sequence

from app.models.documentos import Documento
from app.services import bitacora as bitacora_svc
from app.services.almacenamiento.contenido import EntradaSubida, subir
from app.services.reformados import exigir_fecha_administrativa

_ESQUEMAS_URL_EXTERNA = ('http://', 'https://')


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


def _es_url_externa(url) -> bool:
    return (url or '').startswith(_ESQUEMAS_URL_EXTERNA)


def exigir_url_externa(url: str) -> str:
    """Devuelve la URL sin espacios si es `http://` o `https://`; si no, lanza `ValueError`.

    Es lo único que entra al pool como «URL externa». Rechaza una ruta local, un `bddat://`
    escrito a mano (los crean solo sus servicios: certificados y diagnósticos), cualquier otro
    esquema (`ftp://`, `javascript:`) y el esquema en mayúsculas (`HTTPS://`), como el modelo.
    El mensaje es para el usuario; la ruta lo devuelve en un 422.
    """
    url = (url or '').strip()
    if not _es_url_externa(url):
        raise ValueError('Solo se admiten enlaces que empiecen por http:// o https://.')
    return url


def comprobar_rectificacion_url(documento: Documento, url_nueva: str) -> str:
    """Comprueba que se puede cambiar la `url` de `documento` por `url_nueva` y devuelve la
    nueva sin espacios. No cambia nada. Lanza `ValueError` con el mensaje para el usuario.

    Solo se rectifica la `url` de un documento **de URL externa** (la suya empieza por
    `http(s)://`) y por otra URL externa. La de un fichero propio, de un `bddat://` o de una
    ruta local no se cambia nunca: para el fichero, cambiar la `url` perdería el rastro de lo
    que contenía (ADR-050 §M); los `bddat://` los fijan sus servicios.
    """
    if not _es_url_externa(documento.url):
        raise ValueError('Solo se puede rectificar la URL de un documento de URL externa; '
                         'la de un fichero o de un registro interno no se cambia.')
    return exigir_url_externa(url_nueva)


def rectificar_url_externa(documento: Documento, url_nueva: str, usuario_id: int) -> bool:
    """Cambia la `url` de un documento de URL externa y anota la anterior en la bitácora.

    Devuelve `False` y no hace nada si `url_nueva` es la que ya tiene. Si no, comprueba que la
    rectificación vale (`comprobar_rectificacion_url`), asigna y anota quién, cuándo y de qué
    URL venía (`ALTERAR` sobre `documentos`, columna `url`). Quien llama no asigna
    `documento.url`, así que ninguna rectificación se salta la bitácora; la anotación y el
    cambio van en la misma transacción.

    No hace commit: lo decide quien llama. Lanza `ValueError` si la rectificación no vale.
    """
    url_nueva = (url_nueva or '').strip()
    if url_nueva == documento.url:
        return False
    url_nueva = comprobar_rectificacion_url(documento, url_nueva)
    anterior = documento.url
    documento.url = url_nueva
    bitacora_svc.registrar(
        usuario_id, 'ALTERAR', 'documentos', documento.id, columna='url',
        detalle={'url_anterior': anterior, 'url_nueva': url_nueva},
    )
    return True
