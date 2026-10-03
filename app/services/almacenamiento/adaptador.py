"""Adaptador del almacén de contenidos (ADR-050 §B).

Traduce lo que BDDAT necesita a la API del almacén que toque. Hoy, la librería
`almacen/` (ficheros en disco, el SHA-256 por nombre); con otro almacén se escribe otro
adaptador y el resto de BDDAT no cambia. **Es el único módulo de `app/` que importa la
librería**: lo vigila `tests/test_1007_subsistema_almacenamiento.py`. Por eso las
respuestas del almacén que el resto del subsistema tiene que distinguir salen de aquí
como excepciones propias de BDDAT.

Tiempo límite y semáforo (§B, «Una subida no debe agotar los workers»):

- Cada petición al almacén corre en un hilo y se espera con tiempo límite; si se agota,
  la respuesta es `AlmacenNoDisponible`. Con un almacén en disco **se puede dejar de
  esperar, no cancelar**: el hilo sigue en el sistema de ficheros hasta que éste
  conteste.
- El hilo colgado **conserva su plaza del semáforo** hasta entonces. Con el almacén
  colgado las plazas se agotan, y las peticiones siguientes fallan **al momento** con
  «inténtalo en unos minutos» en vez de acumular hilos (y workers esperando). Por lo
  mismo, pedir plaza no espera: una racha de subidas grandes no deja sin workers al
  resto de la aplicación, y a la que sobra se le dice que reintente.
- El tiempo límite de `leer` cubre abrir el contenido; los trozos que se leen después
  no se cronometran uno a uno.
- Una escritura que dimos por fallida y termina después deja un contenido en el almacén
  sin fila en `ficheros`: el hueco de §B, que recoge la conciliación de la limpieza
  (fase 7).
"""
from __future__ import annotations

import threading
from typing import BinaryIO

import almacen as _libreria
from flask import current_app

# Valores de despliegue, no se configuran desde la aplicación (§K); las claves de
# configuración existen para los tests.
TIEMPO_LIMITE_DEFECTO = 30          # segundos por petición
TRANSFERENCIAS_SIMULTANEAS_DEFECTO = 4


class ErrorAlmacenamiento(Exception):
    """Base de los errores del subsistema de almacenamiento."""


class AlmacenNoDisponible(ErrorAlmacenamiento):
    """El almacén no contesta, está desmontado o está saturado. No dice nada del
    contenido: reintentar en unos minutos. No es un fallo del documento."""


class ContenidoNoExiste(ErrorAlmacenamiento):
    """El almacén contesta y no tiene ese contenido: un fallo de integridad."""


class ComprobacionFallida(ErrorAlmacenamiento):
    """Lo que recibió el almacén no coincide con el hash que se le dio: no se guardó."""


class RefInvalida(ErrorAlmacenamiento, ValueError):
    """La `ref` no tiene la forma que da este almacén: un dato de BD mal."""


class AdaptadorAlmacen:
    """Habla con un almacén con la API de `almacen/` (`escribir`, `leer`, `existe`)."""

    def __init__(self, almacen, *, tiempo_limite: float, simultaneas: int):
        self._almacen = almacen
        self._tiempo_limite = tiempo_limite
        self._plazas = threading.BoundedSemaphore(simultaneas)

    def escribir(self, flujo: BinaryIO, contenido_sha256: str) -> str:
        """Guarda el contenido y devuelve su `ref`.

        Con el almacén de hoy la comprobación es SHA-256 y reutiliza el
        `contenido_sha256` que BDDAT ya calculó; con otro, la que admita, y si no admite
        ninguna, sin comprobación.
        """
        comprobacion = None
        if 'sha256' in self._almacen.comprobaciones_admitidas():
            comprobacion = _libreria.Comprobacion('sha256', contenido_sha256)
        return self._ejecutar(self._almacen.escribir, flujo, comprobacion)

    def leer(self, ref: str) -> BinaryIO:
        """El contenido como flujo binario abierto; lo cierra quien lo pide."""
        return self._ejecutar(self._almacen.leer, ref)

    def existe(self, ref: str) -> bool:
        return self._ejecutar(self._almacen.existe, ref)

    def _ejecutar(self, operacion, *args):
        if not self._plazas.acquire(blocking=False):
            raise AlmacenNoDisponible(
                'El almacén está atendiendo demasiadas transferencias a la vez '
                'o no responde: inténtalo en unos minutos.')
        resultado = {}
        abandonado = threading.Event()

        def trabajo():
            try:
                resultado['valor'] = operacion(*args)
            except BaseException as exc:   # se re-lanza en quien espera
                resultado['error'] = exc
            else:
                # Si ya nadie espera, un flujo abierto no tiene dueño: se cierra.
                if abandonado.is_set() and hasattr(resultado['valor'], 'close'):
                    resultado['valor'].close()
            finally:
                self._plazas.release()

        hilo = threading.Thread(target=trabajo, daemon=True, name='almacen')
        hilo.start()
        hilo.join(self._tiempo_limite)
        if hilo.is_alive():
            abandonado.set()
            raise AlmacenNoDisponible(
                'El almacén no responde: inténtalo en unos minutos.')
        if 'error' in resultado:
            error = resultado['error']
            traducido = _traducir(error)
            if traducido is error:
                raise error
            raise traducido from error
        return resultado['valor']


def _traducir(exc: BaseException) -> BaseException:
    """Las respuestas de la librería, como excepciones de BDDAT; lo demás, tal cual."""
    if isinstance(exc, _libreria.NoDisponible):
        return AlmacenNoDisponible(f'El almacén no está disponible: {exc}')
    if isinstance(exc, _libreria.NoExiste):
        return ContenidoNoExiste(str(exc))
    if isinstance(exc, _libreria.ComprobacionFallida):
        return ComprobacionFallida(str(exc))
    if isinstance(exc, _libreria.RefInvalida):
        return RefInvalida(str(exc))
    if isinstance(exc, _libreria.ErrorAlmacen):
        return ErrorAlmacenamiento(str(exc))
    return exc


_ADAPTADORES: dict = {}
_CERROJO = threading.Lock()


def obtener_adaptador() -> AdaptadorAlmacen:
    """El adaptador del almacén configurado (`ALMACEN_BASE`), uno por proceso.

    El semáforo tiene que ser compartido por todas las peticiones del proceso, así que
    el adaptador se guarda aquí; se distingue por raíz y límites para que un test que
    redirige el almacén a un temporal tenga el suyo.
    """
    raiz = current_app.config.get('ALMACEN_BASE', '')
    if not raiz:
        raise RuntimeError('ALMACEN_BASE no está configurado')
    tiempo = current_app.config.get('ALMACEN_TIEMPO_LIMITE', TIEMPO_LIMITE_DEFECTO)
    plazas = current_app.config.get(
        'ALMACEN_TRANSFERENCIAS_SIMULTANEAS', TRANSFERENCIAS_SIMULTANEAS_DEFECTO)
    clave = (raiz, tiempo, plazas)
    with _CERROJO:
        if clave not in _ADAPTADORES:
            _ADAPTADORES[clave] = AdaptadorAlmacen(
                _libreria.AlmacenDisco(raiz), tiempo_limite=tiempo, simultaneas=plazas)
        return _ADAPTADORES[clave]
