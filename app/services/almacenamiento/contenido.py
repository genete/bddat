"""Módulo de contenido (ADR-050 §B): las operaciones sobre el contenido de un documento.

Con el adaptador, lo único de BDDAT que lee o escribe `ficheros` y `fichero_ref`. El
resto trabaja con `documentos.id` y pide el contenido por aquí:

- `subir`: el flujo de §B (validar todo, hash a trozos, reutilizar o escribir, la fila
  de `ficheros` en su propia transacción, los documentos todo o nada).
- `leer`: el contenido entero con su formato, comprobando el hash.
- `comprobar_para_vincular`: un contenido ausente o corrupto no sostiene ningún acto.
- `servir_descarga`: la respuesta HTTP con las cabeceras de §E.

Sustituir con motivo y aportar desde otro expediente llegan en el PR 6, con su interfaz.

**Dos conexiones.** La fila de `ficheros` se escribe **en una conexión propia**, no en la
sesión de la petición: con la sesión, el commit de la fila arrastraría lo que el
llamador tenga pendiente (en el alta de expediente, el expediente a medio crear). Lo
mismo vale para marcar un contenido `AUSENTE` o `CORRUPTO`: es un hecho del almacén, que
no se deshace porque la petición falle después. Consecuencia: en los tests esas filas
escapan al SAVEPOINT de `app_ctx`, y la fixture `almacen_tmp` las borra al terminar.

**No distingue lo que no es suyo.** Que el almacén no conteste (`AlmacenNoDisponible`)
no es un fallo del documento y no marca nada: con el almacén desmontado, marcar los
contenidos como ausentes los daría por perdidos a todos.
"""
from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import BinaryIO, Sequence
from urllib.parse import quote

from flask import Response, stream_with_context
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import db
from app.models.documentos import Documento
from app.models.ficheros import AUSENTE, CORRUPTO, OK, Fichero
from app.services.almacenamiento.adaptador import (
    AlmacenNoDisponible, ContenidoNoExiste, ErrorAlmacenamiento, obtener_adaptador,
)
from app.services.almacenamiento.formatos import (
    FormatoNoAdmitido, es_visible_en_navegador, validar_fichero,
)
from app.services.almacenamiento.nombres import sanear_nombre

_TROZO = 1024 * 1024
_T = Fichero.__table__

# Lo que fija el módulo al subir: quien llama no lo pasa (si pudiera, saltaría el saneado
# del nombre o la comprobación del contenido).
_CAMPOS_DEL_MODULO = frozenset({'url', 'nombre_fichero', 'fichero_ref', 'fecha_modificacion_fichero'})


class ContenidoNoUtilizable(ErrorAlmacenamiento):
    """El contenido del documento está ausente o dañado, y no se puede usar. El mensaje
    es para el usuario: qué pasa y que avise al administrador."""


@dataclass(frozen=True)
class EntradaSubida:
    """Un fichero de una subida y los datos del documento que se crea con él."""
    flujo: BinaryIO                 # binario y con seek: el temporal en que el servidor web deja la subida
    nombre_original: str            # el que llega del navegador; entra saneado (ADR-050 §C)
    datos_documento: dict = field(default_factory=dict)   # expediente_id, tipo_doc_id, fecha_administrativa…


@dataclass(frozen=True)
class ContenidoLeido:
    datos: bytes
    formato: str                    # el de su fila de `ficheros`, no el de la extensión
    nombre_fichero: str


def subir(entradas: Sequence[EntradaSubida]) -> list[Documento]:
    """Sube los ficheros al almacén y devuelve los `Documento` que los referencian.

    **Todo o nada** (§B): primero se validan todos los ficheros y se construyen todos los
    documentos (así saltan los validadores del modelo, como la fecha futura), y solo
    entonces se envía el primero. Si algo falla, no se devuelve ningún documento. Las
    filas de `ficheros` que ya se hubieran escrito se quedan sin referencias —las recoge
    la limpieza, fase 7— y al reintentar se reutilizan sin volver a enviar nada.

    Los documentos **no se añaden a la sesión**: quien llama los añade y hace el commit,
    como `ingestar_en_pool`. `datos_documento` no puede llevar `url`, `nombre_fichero`,
    `fichero_ref` ni `fecha_modificacion_fichero`: los pone este módulo.

    Lanza `FormatoNoAdmitido` (mensaje para el usuario), `ValueError` (los validadores
    del modelo) o `AlmacenNoDisponible` (reintentar en unos minutos).
    """
    entradas = list(entradas)
    preparadas = []
    for entrada in entradas:
        propios = _CAMPOS_DEL_MODULO & set(entrada.datos_documento)
        if propios:
            raise ValueError(f'datos_documento no puede llevar {sorted(propios)}: los pone el módulo')
        try:
            formato = validar_fichero(entrada.nombre_original, entrada.flujo)
        except FormatoNoAdmitido as exc:
            raise FormatoNoAdmitido(f'«{entrada.nombre_original}»: {exc}') from exc
        documento = Documento(
            **entrada.datos_documento,
            nombre_fichero=sanear_nombre(entrada.nombre_original),
        )
        preparadas.append((entrada, documento, formato))

    for entrada, documento, formato in preparadas:
        fila = _guardar_contenido(entrada.flujo, formato)
        documento.fichero_ref = fila.ref
        documento.fecha_modificacion_fichero = datetime.now(timezone.utc)
    return [documento for _, documento, _ in preparadas]


def leer(documento: Documento) -> ContenidoLeido:
    """El contenido entero del documento, con el hash comprobado (§G).

    Si el almacén no lo tiene o no coincide, la fila de `ficheros` queda `AUSENTE` o
    `CORRUPTO` y se lanza `ContenidoNoUtilizable`. Si el almacén no contesta, lanza
    `AlmacenNoDisponible` y no marca nada.
    """
    fila = _fila_utilizable(documento)
    flujo = _abrir(fila, documento)
    try:
        with flujo:
            datos = flujo.read()
    except OSError as exc:
        raise AlmacenNoDisponible(f'El almacén no está disponible: {exc}') from exc
    if hashlib.sha256(datos).hexdigest() != fila.contenido_sha256:
        _marcar_estado(fila.ref, CORRUPTO)
        raise ContenidoNoUtilizable(_mensaje_no_utilizable(CORRUPTO, documento))
    return ContenidoLeido(datos=datos, formato=fila.formato, nombre_fichero=documento.nombre_visible())


def comprobar_para_vincular(documento: Documento) -> None:
    """Un documento cuyo contenido no está en el almacén no se vincula (§G).

    Además del estado de la fila de `ficheros` se pregunta al almacén si el contenido
    existe, sin leerlo: el ausente se detecta cuando el documento empieza a sostener
    algo; el corrupto, en la comprobación periódica. Un documento sin contenido propio
    (`http(s)://`, `bddat://`) no tiene nada que comprobar.
    """
    if documento.fichero_ref is None:
        return
    fila = _fila_utilizable(documento)
    if not obtener_adaptador().existe(fila.ref):
        _marcar_estado(fila.ref, AUSENTE)
        raise ContenidoNoUtilizable(_mensaje_no_utilizable(AUSENTE, documento))


def servir_descarga(documento: Documento) -> Response:
    """La respuesta HTTP con el contenido del documento (ADR-050 §E, «Al servirlos»).

    PDF e imágenes se muestran en el navegador; el resto se descarga. Siempre
    `X-Content-Type-Options: nosniff` y CSP `sandbox`, y el nombre según RFC 5987. El
    contenido va a trozos y se comprueba el hash al terminar: si no coincide, queda
    `CORRUPTO` para la próxima vez (esta ya se ha servido). Hay que llamarla dentro de
    una petición.
    """
    fila = _fila_utilizable(documento)
    flujo = _abrir(fila, documento)

    def trozos():
        hasher = hashlib.sha256()
        try:
            for trozo in iter(lambda: flujo.read(_TROZO), b''):
                hasher.update(trozo)
                yield trozo
        finally:
            flujo.close()
        if hasher.hexdigest() != fila.contenido_sha256:
            _marcar_estado(fila.ref, CORRUPTO)

    disposicion = 'inline' if es_visible_en_navegador(fila.formato) else 'attachment'
    respuesta = Response(stream_with_context(trozos()), content_type=fila.formato)
    respuesta.headers['Content-Length'] = str(fila.tamano)
    respuesta.headers['Content-Disposition'] = _cabecera_disposicion(disposicion, documento.nombre_visible())
    respuesta.headers['X-Content-Type-Options'] = 'nosniff'
    respuesta.headers['Content-Security-Policy'] = 'sandbox'
    return respuesta


# --- subir: el contenido ------------------------------------------------------------

def _guardar_contenido(flujo: BinaryIO, formato: str):
    """Pasos 2-5 de §B para un fichero: la fila de `ficheros` con su contenido en el almacén."""
    sha256, tamano = _calcular_sha256(flujo)

    fila = _fila_por_hash(sha256)
    if fila is not None and fila.estado == OK:
        return fila                       # ya está: no se envía nada

    ref = obtener_adaptador().escribir(flujo, sha256)
    if fila is not None:
        # Estaba AUSENTE o CORRUPTO: volver a subir el original lo repara (§G).
        if ref != fila.ref:
            raise ErrorAlmacenamiento(
                f'El almacén devolvió otra ref al reparar {fila.ref}: {ref}')
        _marcar_estado(fila.ref, OK)
        return _fila_por_hash(sha256)
    return _insertar_fila(ref, sha256, tamano, formato)


def _calcular_sha256(flujo: BinaryIO) -> tuple[str, int]:
    """SHA-256 y tamaño leyendo a trozos, sin cargar el fichero entero en memoria."""
    hasher = hashlib.sha256()
    tamano = 0
    flujo.seek(0)
    for trozo in iter(lambda: flujo.read(_TROZO), b''):
        hasher.update(trozo)
        tamano += len(trozo)
    flujo.seek(0)
    return hasher.hexdigest(), tamano


# --- la tabla `ficheros`, siempre en conexión propia ---------------------------------

def _fila_por_hash(sha256: str):
    with db.engine.connect() as conexion:
        return conexion.execute(select(_T).where(_T.c.contenido_sha256 == sha256)).first()


def _fila_por_ref(ref: str):
    with db.engine.connect() as conexion:
        return conexion.execute(select(_T).where(_T.c.ref == ref)).first()


def _insertar_fila(ref: str, sha256: str, tamano: int, formato: str):
    """Inserta la fila en su propia transacción; si dos subidas del mismo contenido llegan
    a la vez, la segunda se encuentra la fila de la primera (§B, paso 5)."""
    with db.engine.begin() as conexion:
        conexion.execute(
            pg_insert(_T)
            .values(ref=ref, contenido_sha256=sha256, tamano=tamano, formato=formato)
            .on_conflict_do_nothing()
        )
        return conexion.execute(select(_T).where(_T.c.contenido_sha256 == sha256)).one()


def _marcar_estado(ref: str, estado: str) -> None:
    with db.engine.begin() as conexion:
        conexion.execute(
            update(_T).where(_T.c.ref == ref).values(estado=estado, fecha_verificacion=func.now())
        )


# --- leer: comprobar antes de usar --------------------------------------------------

def _fila_utilizable(documento: Documento):
    """La fila de `ficheros` del documento, si su contenido se puede usar."""
    if documento.fichero_ref is None:
        raise ValueError('El documento no tiene contenido propio en el almacén (fichero_ref)')
    fila = _fila_por_ref(documento.fichero_ref)
    if fila is None:
        raise ErrorAlmacenamiento(f'Falta la fila de ficheros de {documento.fichero_ref}')
    if fila.estado != OK:
        raise ContenidoNoUtilizable(_mensaje_no_utilizable(fila.estado, documento))
    return fila


def _abrir(fila, documento: Documento) -> BinaryIO:
    try:
        return obtener_adaptador().leer(fila.ref)
    except ContenidoNoExiste:
        _marcar_estado(fila.ref, AUSENTE)
        raise ContenidoNoUtilizable(_mensaje_no_utilizable(AUSENTE, documento)) from None


def _mensaje_no_utilizable(estado: str, documento: Documento) -> str:
    que = 'no está en el almacén' if estado == AUSENTE else 'está dañado'
    return (f'El contenido de «{documento.nombre_visible()}» {que}. '
            f'Avisa al administrador para que lo recupere de la copia de seguridad.')


def _cabecera_disposicion(disposicion: str, nombre: str) -> str:
    """`Content-Disposition` con el nombre según RFC 6266 / RFC 5987."""
    try:
        nombre.encode('ascii')
    except UnicodeEncodeError:
        simple = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('ascii')
        return (f'{disposicion}; filename="{_escapar(simple)}"; '
                f"filename*=UTF-8''{quote(nombre, safe='')}")
    return f'{disposicion}; filename="{_escapar(nombre)}"'


def _escapar(texto: str) -> str:
    return texto.replace('\\', '\\\\').replace('"', '\\"')
