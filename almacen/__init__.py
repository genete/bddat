"""Almacén de contenidos en disco, direccionado por SHA-256.

Librería independiente: solo usa la biblioteca estándar de Python y no sabe nada
de quien la usa (ni expedientes, ni documentos, ni nombres de fichero). Guarda
bytes y devuelve una referencia (`ref`) para volver a encontrarlos. Escrita como
si fuera de terceros (ADR-050 §B de BDDAT): su API es la que habla el adaptador de
BDDAT; con otro almacén, BDDAT escribe otro adaptador para la API de ese.

API
===

    almacen = AlmacenDisco('/ruta/raiz')

    escribir(flujo, comprobacion=None) -> ref
        Guarda el contenido de `flujo` (objeto con `.read(n)`, leído a trozos,
        nunca entero en memoria). `comprobacion` es opcional:
        `Comprobacion(algoritmo, valor)`; el almacén calcula ese algoritmo sobre
        lo que recibe y, si no coincide, no guarda nada y lanza
        `ComprobacionFallida`. Algoritmos admitidos: `comprobaciones_admitidas()`.

    leer(ref) -> flujo binario abierto (el llamador lo cierra)
    existe(ref) -> bool
    borrar(ref) -> None
    listar() -> iterador de ref
    comprobaciones_admitidas() -> frozenset de nombres de algoritmo

Respuestas que no son el resultado, como excepciones:

    NoExiste       la ref no está en el almacén (leer, borrar).
    NoDisponible   el almacén no contesta o no está montado (cualquier
                   operación). No dice nada del contenido: reintentar más tarde.
    ComprobacionFallida   escribir: lo recibido no coincide con la comprobación.
    RefInvalida    la ref no tiene la forma que da este almacén.

`NoExiste` y `NoDisponible` no significan lo mismo y no se confunden: el primero
es un fallo de integridad; el segundo, que el almacén no está en ese momento.

Cómo guarda
===========

    <raiz>/ALMACEN.txt            marca de raíz (ver «La marca» abajo)
    <raiz>/sha256/3a/f1/3af1…e07b  un fichero por contenido, sin extensión
    <raiz>/.tmp/                  escrituras en curso

La `ref` de este almacén es el SHA-256 del contenido en hexadecimal (64
caracteres). Quien la use no debe suponer nada de su forma: otro almacén daría
otra cosa.

Un contenido ya escrito no se modifica nunca, con una excepción: si se vuelve a
escribir un contenido cuyo fichero está dañado, el nuevo lo sustituye (es la
forma de repararlo subiendo otra vez el original).

La marca
========

`inicializar(raiz)` crea la raíz con su marca `ALMACEN.txt`. Las operaciones
exigen que la marca esté: si falta, responden `NoDisponible` en vez de crear
carpetas. Así, con el almacén en una carpeta de red sin montar, no se escribe en
silencio en el disco local que queda debajo, ni se toma un almacén desconectado
por un almacén vacío.
"""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
from typing import BinaryIO, Iterator, NamedTuple

__all__ = [
    'AlmacenDisco', 'Comprobacion', 'inicializar',
    'ErrorAlmacen', 'NoExiste', 'NoDisponible', 'ComprobacionFallida', 'RefInvalida',
]

MARCA = 'ALMACEN.txt'
_TEXTO_MARCA = (
    'Almacen de contenidos. No modificar, mover ni borrar nada a mano:\n'
    'cada fichero se identifica por su contenido y lo referencia una base de datos.\n'
)
_ALGORITMO = 'sha256'
_TROZO = 1024 * 1024
_RE_REF = re.compile(r'^[0-9a-f]{64}$')


class ErrorAlmacen(Exception):
    """Base de los errores de este almacén."""


class NoExiste(ErrorAlmacen):
    """La ref no está en el almacén."""


class NoDisponible(ErrorAlmacen):
    """El almacén no contesta o no está montado. Reintentar más tarde."""


class ComprobacionFallida(ErrorAlmacen):
    """Lo recibido en `escribir` no coincide con la comprobación: no se guarda."""


class RefInvalida(ErrorAlmacen, ValueError):
    """La ref no tiene la forma que da este almacén."""


class Comprobacion(NamedTuple):
    algoritmo: str
    valor: str


def inicializar(raiz: str) -> None:
    """Crea la raíz del almacén con su marca. Idempotente."""
    for sub in ('', _ALGORITMO, '.tmp'):
        os.makedirs(os.path.join(raiz, sub), exist_ok=True)
    marca = os.path.join(raiz, MARCA)
    if not os.path.exists(marca):
        with open(marca, 'w', encoding='utf-8') as f:
            f.write(_TEXTO_MARCA)


class AlmacenDisco:
    """Almacén en una carpeta (local o de red), un fichero por contenido."""

    def __init__(self, raiz: str):
        if not raiz:
            raise ValueError('AlmacenDisco necesita una raíz')
        self.raiz = os.path.abspath(raiz)
        self._dir_tmp = os.path.join(self.raiz, '.tmp')

    # -- API ------------------------------------------------------------------

    def comprobaciones_admitidas(self) -> frozenset:
        return frozenset({_ALGORITMO})

    def escribir(self, flujo: BinaryIO, comprobacion: Comprobacion | None = None) -> str:
        if comprobacion is not None and comprobacion.algoritmo not in self.comprobaciones_admitidas():
            raise ValueError(f'Comprobación no admitida: {comprobacion.algoritmo!r}')
        self._exigir_marca()

        try:
            fd, temporal = tempfile.mkstemp(dir=self._dir_tmp)
        except OSError as exc:
            raise NoDisponible(f'No se puede escribir en el almacén: {exc}') from exc

        try:
            hasher = hashlib.sha256()
            with os.fdopen(fd, 'wb') as f:
                # Un error al leer `flujo` es del origen y sube tal cual; uno al
                # escribir es del almacén y se traduce a NoDisponible.
                for trozo in _trozos(flujo):
                    hasher.update(trozo)
                    _en_almacen(f.write, trozo)
                _en_almacen(f.flush)
                _en_almacen(os.fsync, f.fileno())
            ref = hasher.hexdigest()

            if comprobacion is not None and comprobacion.valor.lower() != ref:
                raise ComprobacionFallida(
                    f'El contenido recibido no coincide con su comprobación '
                    f'({comprobacion.algoritmo}): esperado {comprobacion.valor}, recibido {ref}')

            destino = self._ruta(ref)
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                # Si ya está y está sano, se reutiliza; si está dañado, el nuevo
                # lo repara. Solo se llega aquí con el contenido ya en el almacén
                # en dos casos raros (dos escrituras a la vez, o una reparación),
                # así que releerlo para comprobarlo no cuesta en el uso normal.
                if os.path.exists(destino) and _sha256_fichero(destino) == ref:
                    os.remove(temporal)
                else:
                    _reemplazar(temporal, destino, ref)
            except OSError as exc:
                raise NoDisponible(f'No se puede guardar {ref}: {exc}') from exc
            return ref
        except BaseException:
            _borrar_si_existe(temporal)
            raise

    def leer(self, ref: str) -> BinaryIO:
        ruta = self._ruta(ref)
        self._exigir_marca()
        try:
            return open(ruta, 'rb')
        except FileNotFoundError as exc:
            raise NoExiste(ref) from exc
        except OSError as exc:
            raise NoDisponible(f'No se puede leer {ref}: {exc}') from exc

    def existe(self, ref: str) -> bool:
        ruta = self._ruta(ref)
        self._exigir_marca()
        # os.path.isfile no sirve: devuelve False ante cualquier error, y un
        # almacén desconectado se confundiría con un contenido que no está.
        try:
            os.stat(ruta)
        except FileNotFoundError:
            return False
        except OSError as exc:
            raise NoDisponible(f'No se puede consultar {ref}: {exc}') from exc
        return True

    def borrar(self, ref: str) -> None:
        ruta = self._ruta(ref)
        self._exigir_marca()
        try:
            os.remove(ruta)
        except FileNotFoundError as exc:
            raise NoExiste(ref) from exc
        except OSError as exc:
            raise NoDisponible(f'No se puede borrar {ref}: {exc}') from exc

    def listar(self) -> Iterator[str]:
        self._exigir_marca()
        base = os.path.join(self.raiz, _ALGORITMO)
        try:
            for nivel1 in _subcarpetas(base):
                for nivel2 in _subcarpetas(nivel1):
                    with os.scandir(nivel2) as entradas:
                        for e in entradas:
                            if e.is_file() and _RE_REF.match(e.name):
                                yield e.name
        except OSError as exc:
            raise NoDisponible(f'No se puede listar el almacén: {exc}') from exc

    # -- interno --------------------------------------------------------------

    def _ruta(self, ref: str) -> str:
        # La forma exacta se exige antes de tocar el disco: una ref es un dato
        # que llega de fuera, y con '..' o separadores saldría de la raíz.
        if not isinstance(ref, str) or not _RE_REF.match(ref):
            raise RefInvalida(f'Ref con forma no válida: {ref!r}')
        return os.path.join(self.raiz, _ALGORITMO, ref[:2], ref[2:4], ref)

    def _exigir_marca(self) -> None:
        try:
            os.stat(os.path.join(self.raiz, MARCA))
        except OSError as exc:
            raise NoDisponible(
                f'Almacén no disponible en {self.raiz}: falta {MARCA} '
                f'(¿carpeta sin montar o sin inicializar?)') from exc


def _trozos(flujo: BinaryIO) -> Iterator[bytes]:
    while True:
        trozo = flujo.read(_TROZO)
        if not trozo:
            return
        yield trozo


def _en_almacen(operacion, *args):
    """Ejecuta una operación sobre el disco del almacén; su fallo es NoDisponible."""
    try:
        return operacion(*args)
    except OSError as exc:
        raise NoDisponible(f'Fallo al escribir en el almacén: {exc}') from exc


def _sha256_fichero(ruta: str) -> str:
    hasher = hashlib.sha256()
    with open(ruta, 'rb') as f:
        for trozo in iter(lambda: f.read(_TROZO), b''):
            hasher.update(trozo)
    return hasher.hexdigest()


def _reemplazar(temporal: str, destino: str, ref: str) -> None:
    """Renombrado atómico del temporal a su sitio definitivo.

    En Windows, renombrar sobre un fichero que otro proceso tiene abierto falla.
    Si en ese momento el destino ya tiene el contenido correcto (otra escritura
    simultánea del mismo contenido ganó la carrera), el resultado es el buscado.
    """
    try:
        os.replace(temporal, destino)
    except OSError:
        if os.path.exists(destino) and _sha256_fichero(destino) == ref:
            os.remove(temporal)
            return
        raise


def _borrar_si_existe(ruta: str) -> None:
    try:
        os.remove(ruta)
    except FileNotFoundError:
        pass
    except OSError:
        # Un temporal que no se pudo borrar no compromete nada: está en .tmp/,
        # fuera de lo que se lista o se lee.
        pass


def _subcarpetas(ruta: str) -> Iterator[str]:
    try:
        with os.scandir(ruta) as entradas:
            nombres = [e.path for e in entradas if e.is_dir()]
    except FileNotFoundError:
        return
    yield from sorted(nombres)
