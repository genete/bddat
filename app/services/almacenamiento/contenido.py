"""Módulo de contenido (ADR-050 §B): las operaciones sobre el contenido de un documento.

Con el adaptador, lo único de BDDAT que lee o escribe `ficheros` y `fichero_ref`. El
resto trabaja con `documentos.id` y pide el contenido por aquí:

- `subir`: el flujo de §B (validar todo, hash a trozos, reutilizar o escribir, la fila
  de `ficheros` en su propia transacción, los documentos todo o nada).
- `leer`: el contenido entero con su formato, comprobando el hash.
- `tiene_contenido_propio`: si el documento guarda su contenido en el almacén (y no es un enlace
  externo ni un documento virtual).
- `documentos_con_contenido`: qué documentos de un expediente ya tienen un contenido, por su
  SHA-256 (el aviso antes de subir, N077).
- `comprobar_para_vincular`: un contenido ausente o corrupto no sostiene ningún acto.
- `servir_descarga`: la respuesta HTTP con las cabeceras de §E.
- `cambiar_contenido`: el documento se conserva (mismo `id`, mismos vínculos) y apunta a otro
  contenido; el cambio queda en la bitácora con el hash anterior y el nuevo (§C).
- `sustituir_con_motivo`: «subí el fichero equivocado» (§F). Motivo obligatorio; solo lo
  bloquea un sello —un certificado o una fase cerrada—, siempre con salida; el nombre pasa a
  ser el del fichero nuevo. Pasa por `cambiar_contenido`, así que nada cambia de contenido
  sin bitácora.
- `copiar_documento`: un documento nuevo sobre el mismo contenido que otro, sin enviar nada
  al almacén (la copia del anuncio edictal, #568).

«Aportar desde otro expediente» (§H) está diferido por decisión de Carlos (2026-10-08): cuando
llegue, será otro uso de `copiar_documento` con su listado.

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
import re
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
from app.services import bitacora as bitacora_svc
from app.services import sellos
from app.services.almacenamiento.adaptador import (
    AlmacenNoDisponible, ContenidoNoExiste, ErrorAlmacenamiento, obtener_adaptador,
)
from app.services.almacenamiento.formatos import (
    FormatoNoAdmitido, es_visible_en_navegador, validar_fichero,
)
from app.services.almacenamiento.nombres import sanear_nombre

_TROZO = 1024 * 1024
_T = Fichero.__table__

# Cuántas huellas admite una consulta del aviso antes de subir (una subida son pocos ficheros).
_MAX_HUELLAS_POR_CONSULTA = 200
_RE_SHA256 = re.compile(r'[0-9a-f]{64}')

# Lo que fija el módulo al subir: quien llama no lo pasa (si pudiera, saltaría el saneado
# del nombre o la comprobación del contenido).
_CAMPOS_DEL_MODULO = frozenset({'url', 'nombre_fichero', 'fichero_ref', 'fecha_modificacion_fichero'})

# Por qué vía cambia el contenido de un documento (§C): la regeneración de un escrito y la
# sustitución con motivo; la edición (fase 5) se añade con su interfaz.
VIA_REGENERACION = 'REGENERACION'
VIA_SUSTITUCION = 'SUSTITUCION'


class ContenidoNoUtilizable(ErrorAlmacenamiento):
    """El contenido del documento está ausente o dañado, y no se puede usar. El mensaje
    es para el usuario: qué pasa y que avise al administrador."""


class SustitucionBloqueada(ValueError):
    """Un sello impide sustituir el contenido del documento. El mensaje es para el usuario
    y nombra la salida (deshacer el certificado, reabrir la fase)."""


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


def cambiar_contenido(documento: Documento, flujo: BinaryIO, *, via: str, usuario_id: int,
                      motivo: str | None = None, nombre_nuevo: str | None = None) -> bool:
    """Da al documento otro contenido, conservando el documento (§C): mismo `id` y mismos
    vínculos; solo cambia el contenido al que apunta, y el nombre solo si se da `nombre_nuevo`.

    Devuelve `False` y no hace nada si el contenido nuevo es el que ya tiene (mismo SHA-256).
    Si no, lo valida con el nombre del documento (o con `nombre_nuevo`, si se da; como
    `subir`), lo guarda (si ese contenido ya estaba en el almacén se reutiliza su fila y no se
    envía nada), apunta el documento a él y **anota en la bitácora** el hash anterior y el
    nuevo, quién y la `via`. Quien llama no escribe `fichero_ref`, así que ningún cambio de
    contenido se salta la bitácora.

    `motivo` y `nombre_nuevo` son de la sustitución (§F). `motivo` va a la bitácora tal cual;
    `nombre_nuevo` entra saneado (§C) y la bitácora guarda el nombre anterior y el nuevo.
    Solo se anotan si se dan: el detalle de una regeneración no cambia.

    El contenido anterior no se toca: otros documentos pueden compartirlo. Cuando ya no lo
    referencie nada, la limpieza (fase 7) lo recoge pasados los días de la papelera, y la
    bitácora dice cuál era. Se compara con la fila de `ficheros`, sin leer el contenido
    anterior: funciona aunque esté ausente o dañado.

    No hace commit: el cambio del documento y la entrada de bitácora van en la sesión de
    quien llama y se confirman juntos. Si ese commit falla, el contenido nuevo queda en el
    almacén sin referencias y el documento sigue con el anterior.

    Lanza `FormatoNoAdmitido`, `ValueError` (el documento no tiene contenido propio) o
    `AlmacenNoDisponible`.
    """
    if documento.fichero_ref is None:
        raise ValueError(_mensaje_sin_contenido_propio(documento))
    anterior = _fila_por_ref(documento.fichero_ref)
    if anterior is None:
        raise ErrorAlmacenamiento(f'Falta la fila de ficheros de {documento.fichero_ref}')

    nombre = nombre_nuevo if nombre_nuevo is not None else documento.nombre_visible()
    try:
        formato = validar_fichero(nombre, flujo)
    except FormatoNoAdmitido as exc:
        raise FormatoNoAdmitido(f'«{nombre}»: {exc}') from exc
    sha256, tamano = _calcular_sha256(flujo)
    if sha256 == anterior.contenido_sha256:
        return False

    fila = _guardar_contenido(flujo, formato, sha256, tamano)
    detalle = {'via': via, 'sha256_anterior': anterior.contenido_sha256, 'sha256_nuevo': sha256}
    if motivo is not None:
        detalle['motivo'] = motivo
    if nombre_nuevo is not None:
        detalle['nombre_anterior'] = documento.nombre_fichero
        documento.nombre_fichero = sanear_nombre(nombre_nuevo)
        detalle['nombre_nuevo'] = documento.nombre_fichero
    documento.fichero_ref = fila.ref
    documento.fecha_modificacion_fichero = datetime.now(timezone.utc)
    bitacora_svc.registrar(
        usuario_id, 'ALTERAR', 'documentos', documento.id, columna='fichero_ref', detalle=detalle,
    )
    return True


def sustituir_con_motivo(documento: Documento, flujo: BinaryIO, nombre_fichero: str,
                         motivo: str, *, usuario_id: int) -> None:
    """«Subí el fichero equivocado» (ADR-050 §F): cambia el contenido de `documento` por
    `flujo`, con motivo obligatorio y dejando rastro. El documento se conserva (mismo `id`,
    datos y vínculos) y su nombre pasa a ser el de `nombre_fichero`, saneado.

    **Solo lo bloquea un sello, y siempre con salida**: un certificado que cita el documento o
    que es el documento (`sellos.motivo_sellado`: se deshace el certificado) o una fase cerrada
    (`sellos.motivo_fase_cerrada`, ADR-036: se reabre la fase). Lo notificado no se bloquea por
    estarlo: la notificación consta como efectuada en cuanto se vincula el justificante, y un
    justificante equivocado se descubre justo entonces. Hasta el sellado se puede rectificar.

    La bitácora (`ALTERAR` sobre `documentos`, columna `fichero_ref`, vía `SUSTITUCION`) guarda
    el motivo, los hashes anterior y nuevo y los nombres anterior y nuevo. El contenido anterior
    no se toca; lo recoge la limpieza (fase 7) cuando nadie lo referencie.

    No hace commit: el cambio y la bitácora van en la sesión de quien llama. Si ese commit
    falla, el contenido nuevo queda en el almacén sin referencias.

    Lanza `ValueError` (con mensaje para el usuario) si falta el motivo, si el documento no
    tiene fichero propio (un enlace `http(s)://` se rectifica cambiando su URL; un `bddat://` lo
    fijan sus servicios) o si el fichero tiene el mismo contenido que el actual;
    `SustitucionBloqueada` (un `ValueError`) si lo impide un sello; `FormatoNoAdmitido` si el
    fichero no es de un formato admitido o no coincide con su extensión (§E); y
    `AlmacenNoDisponible` si el almacén no contesta.
    """
    motivo = (motivo or '').strip()
    if not motivo:
        raise ValueError('Indica el motivo de la sustitución.')
    if documento.fichero_ref is None:
        raise ValueError(_mensaje_sin_contenido_propio(documento))
    bloqueo = sellos.motivo_sellado(documento) or sellos.motivo_fase_cerrada(documento)
    if bloqueo is not None:
        raise SustitucionBloqueada(bloqueo)
    if not cambiar_contenido(documento, flujo, via=VIA_SUSTITUCION, usuario_id=usuario_id,
                             motivo=motivo, nombre_nuevo=nombre_fichero):
        raise ValueError('El fichero elegido tiene el mismo contenido que el actual: '
                         'no hay nada que sustituir.')


def copiar_documento(origen: Documento, **datos) -> Documento:
    """Un documento nuevo con el mismo contenido que `origen`, sin enviar nada al almacén.

    Hace falta cuando un mismo contenido tiene que figurar en más de un documento (un
    documento tiene un solo productor, así que cada tarea que lo produce necesita el suyo).
    La copia apunta a la misma fila de `ficheros` y lleva el mismo nombre y la misma fecha
    de fichero que el origen; si el origen es un enlace `http(s)://`, lleva la misma `url`.

    `datos` son los del documento nuevo (`expediente_id`, `tipo_doc_id`,
    `fecha_administrativa`, `asunto`…) y no pueden llevar `url`, `nombre_fichero`,
    `fichero_ref` ni `fecha_modificacion_fichero`: los toma este módulo del origen, así
    que ninguna copia sale sin su contenido.

    El documento **no se añade a la sesión**: quien llama lo añade, como con `subir`. Que el
    contenido se pueda usar lo comprueba `comprobar_para_vincular` al vincular la copia.

    Lanza `ValueError` si `datos` trae un campo del módulo, o si el origen no tiene nada que
    copiar: ni contenido propio ni enlace `http(s)://` (un documento `bddat://`, una ruta
    local sin migrar o un documento vacío).
    """
    propios = _CAMPOS_DEL_MODULO & set(datos)
    if propios:
        raise ValueError(f'datos no puede llevar {sorted(propios)}: los toma el módulo del origen')
    if origen.fichero_ref is not None:
        return Documento(
            **datos, nombre_fichero=origen.nombre_fichero, fichero_ref=origen.fichero_ref,
            fecha_modificacion_fichero=origen.fecha_modificacion_fichero,
        )
    if (origen.url or '').startswith(('http://', 'https://')):
        return Documento(**datos, url=origen.url, nombre_fichero=origen.nombre_fichero)
    raise ValueError(
        f'El documento {origen.id} no tiene nada que copiar: ni contenido propio en el '
        f'almacén ni un enlace http(s)://')


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


def tiene_contenido_propio(documento: Documento) -> bool:
    """El documento guarda su contenido en el almacén, a diferencia de un enlace externo
    (`http(s)://`) o un documento virtual (`bddat://`), que no tienen nada que leer ni servir.

    Es la pregunta que se le hace al módulo en vez de mirar `fichero_ref` desde fuera: la `ref`
    solo la ve el subsistema de almacenamiento (ADR-050 §B)."""
    return documento.fichero_ref is not None


def documentos_con_contenido(expediente_id: int, sha256s: Sequence[str]) -> dict[str, list[Documento]]:
    """Los documentos del expediente que ya tienen alguno de estos contenidos, por SHA-256
    (en minúsculas), los más recientes primero. Solo salen los hashes que coinciden.

    Contesta al aviso antes de subir (ADR-050 §H, N077): el navegador calcula la huella de cada
    fichero que el usuario elige y pregunta si el expediente ya lo tiene. Mira **solo ese
    expediente**: «ya está en otro expediente» espera a «Aportar desde otro expediente».
    No hace nada con los documentos; no devuelve ninguna `ref`.

    Un contenido ausente o dañado no cuenta: volver a subir el original lo repara (§G), y
    decir «ya está» lo dejaría sin subir. La huella del navegador solo sirve para avisar:
    nunca es el `contenido_sha256` de un documento nuevo, que calcula el servidor al subir.

    Lanza `ValueError` (mensaje para el usuario) si `sha256s` no es una lista de a lo sumo
    200 huellas de 64 caracteres hexadecimales.
    """
    if not isinstance(sha256s, (list, tuple)):
        raise ValueError('Se esperaba una lista de huellas SHA-256.')
    if len(sha256s) > _MAX_HUELLAS_POR_CONSULTA:
        raise ValueError(f'Demasiadas huellas: el máximo es {_MAX_HUELLAS_POR_CONSULTA}.')
    huellas = set()
    for huella in sha256s:
        if not isinstance(huella, str) or not _RE_SHA256.fullmatch(huella.lower()):
            raise ValueError('Cada huella debe ser un SHA-256 de 64 caracteres hexadecimales.')
        huellas.add(huella.lower())
    if not huellas:
        return {}

    filas = (
        db.session.query(Documento, Fichero.contenido_sha256)
        .join(Fichero, Documento.fichero_ref == Fichero.ref)
        .filter(Documento.expediente_id == expediente_id,
                Fichero.contenido_sha256.in_(huellas),
                Fichero.estado == OK)
        .order_by(Documento.id.desc())
        .all()
    )
    encontrados: dict[str, list[Documento]] = {}
    for documento, huella in filas:
        encontrados.setdefault(huella, []).append(documento)
    return encontrados


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

def _guardar_contenido(flujo: BinaryIO, formato: str, sha256: str | None = None, tamano: int | None = None):
    """Pasos 2-5 de §B para un fichero: la fila de `ficheros` con su contenido en el almacén.

    `sha256` y `tamano` se pasan si quien llama ya los calculó, para no leer dos veces un
    fichero grande."""
    if sha256 is None:
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
        raise ValueError(_mensaje_sin_contenido_propio(documento))
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


def _mensaje_sin_contenido_propio(documento: Documento) -> str:
    """Para el usuario (llega en un 422, p. ej. al regenerar sobre un «borrador» que es
    un enlace): sin nombres de columnas."""
    return (f'«{documento.nombre_visible()}» no tiene fichero propio en BDDAT: es un '
            f'enlace externo o un registro interno.')


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
