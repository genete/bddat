"""Entrada de un fichero al pool del expediente (ADR-032 §1/§4).

Extraído de `pool_subir_documento` (#428) sin cambiar una coma de lo que hacía:
calcular el MD5, resolver el nombre único, escribir el fichero y crear el
`Documento`. Lo que se gana es que deje de ser cuerpo de una ruta HTTP, porque el
alta de expediente necesita exactamente esto —el documento de solicitud entra al
pool como cualquier otro— y no puede llamar a un endpoint desde dentro de su
propia transacción.

**No hace commit, a propósito.** El `Documento` queda añadido a la sesión y es el
llamador quien decide cuándo cerrar: la ruta del pool commitea el lote entero, y
el alta de expediente lo hace junto con el expediente, el proyecto y la solicitud,
que es lo que permite que el fallo de cualquiera de los cuatro deshaga los otros
tres.

Lo que NO entra aquí es todo lo que solo tiene sentido hablando HTTP: el permiso,
el 503 si el servidor de ficheros no responde, el parseo del JSON de metadatos y
la traducción de un error a código de estado. Eso se queda en la ruta.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from flask import current_app

from app import db
from app.models.documentos import Documento
from app.services.rutas_esftt import ruta_pool_documento, nombre_pool_unico


@dataclass(frozen=True)
class ResultadoIngesta:
    """Lo que hizo falta escribir, además del documento.

    `ruta_absoluta` y `fichero_escrito` existen por el alta de expediente: si su
    transacción revienta, el rollback devuelve el `numero_at` al contador pero no
    borra el fichero, y el siguiente expediente heredaría la carpeta con el
    documento del intento fallido. Para limpiarlo hay que saber qué se escribió y
    si se escribió — un duplicado exacto no se reescribe, y borrarlo se llevaría
    por delante el fichero de otro documento que sí lo usa.
    """
    documento: Documento
    ruta_absoluta: str
    fichero_escrito: bool


def ingestar_en_pool(
    expediente,
    contenido: bytes,
    nombre_original: str,
    *,
    tipo_doc_id: int,
    fecha_administrativa: Optional[date] = None,
    asunto: Optional[str] = None,
    prioridad: bool = False,
) -> ResultadoIngesta:
    """Copia `contenido` al pool del expediente y crea su `Documento` (sin commit).

    El punto de entrada es siempre el mismo, venga el fichero del disco local del
    usuario o de una carpeta del servidor: `AT-N/pool/<prefijo-hash>_<nombre>`.

    Duplicado exacto (mismo MD5 ya presente en el pool): no se reescribe el
    fichero, pero sí se crea el `Documento` — quien lo sube lo ha pedido
    explícitamente (ADR-032 §4, sin bloquear ni avisar).

    La fecha administrativa la valida el propio modelo (#824): si es futura,
    construir el `Documento` lanza `ValueError`. Se deja subir hasta el llamador
    en vez de traducirla aquí, porque cada puerta la cuenta a su manera —la ruta
    del pool devuelve un 500 con el mensaje, el formulario de alta lo repinta
    junto al campo—.
    """
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio = ruta_pool_documento(expediente)

    hash_md5 = hashlib.md5(contenido).hexdigest()
    nombre, ya_existe = nombre_pool_unico(hash_md5, nombre_original, directorio)
    destino = os.path.join(directorio, nombre)

    if not ya_existe:
        with open(destino, 'wb') as f:
            f.write(contenido)

    ruta_relativa = os.path.relpath(destino, base).replace(os.sep, '/')

    documento = Documento(
        expediente_id=expediente.id,
        url=ruta_relativa,
        hash_md5=hash_md5,
        tipo_doc_id=tipo_doc_id,
        fecha_administrativa=fecha_administrativa,
        asunto=asunto,
        prioridad=1 if prioridad else 0,
    )
    db.session.add(documento)

    return ResultadoIngesta(
        documento=documento,
        ruta_absoluta=destino,
        fichero_escrito=not ya_existe,
    )
