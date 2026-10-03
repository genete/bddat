"""Manifiestos de los expedientes (ADR-050 §H, N009): el salvavidas para volver al papel.

Un fichero por expediente, `MANIFIESTOS_BASE/<número entre mil, tres cifras>/AT-N.json`
(`000/AT-123.json`, `004/AT-4567.json`), con lo justo para reconstruir sus carpetas sin
BDDAT: de cada documento, id, nombre, carpeta ESFTT ya calculada, `ref` y hash. Lo lee el
exportador (`exportador/`, en la raíz del repositorio), que no necesita ni la BD ni la
aplicación. No es el expediente (eso es la remisión, #573): si un día hace falta más, se
enriquece.

- Sin tarea, el documento va a `AT-N/pool`; con tarea, a la carpeta de su primera
  vinculación (`rutas_esftt.ruta_esftt_documento`).
- Los `http(s)://` figuran con su `url`, sin fichero. Los `bddat://` no figuran: sin la BD
  no hay nada que reconstruir de ellos.
- Hasta el corte (PR 4 de #1007) los documentos de ruta local no tienen `ref`: figuran sin
  ella, y el exportador los informa como «sin contenido en el almacén».

Se rehace a mano (`flask manifiestos [AT-N]`); la programación llega en la fase 2b. Solo
se reescribe si cambia: no lleva fecha de generación dentro, así que el mismo expediente
da los mismos bytes. Se escribe en un temporal y se renombra.

La carpeta lleva una marca de raíz, `MANIFIESTOS.txt`, como el almacén con `ALMACEN.txt`:
sin ella no se escribe nada, para no dejar los manifiestos en el disco local que queda
debajo de un share sin montar mientras los del share envejecen.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Iterator

from flask import current_app
from sqlalchemy import select

from app import db
from app.models.documentos import Documento
from app.models.expedientes import Expediente
from app.models.ficheros import Fichero
from app.services.rutas_esftt import ruta_esftt_documento
from exportador import FORMATO

MARCA = 'MANIFIESTOS.txt'
_TEXTO_MARCA = (
    'Manifiestos de los expedientes de BDDAT: uno por expediente, para reconstruir sus\n'
    'carpetas sin la aplicación (python -m exportador). Los escribe solo BDDAT.\n'
)
# Reintentos del renombrado ante el «acceso denegado» transitorio de Windows: dos
# escrituras del mismo manifiesto a la vez (la mano y, en la fase 2b, la programada).
_REINTENTOS_REEMPLAZO = 10
_ESPERA_REEMPLAZO = 0.02


class ManifiestosNoDisponibles(Exception):
    """La carpeta de manifiestos no está configurada, montada o inicializada."""


@dataclass(frozen=True)
class Resultado:
    expediente: str             # 'AT-123'
    reescrito: bool
    error: str | None = None


def inicializar(raiz: str) -> None:
    """Crea la carpeta de manifiestos con su marca. Idempotente."""
    os.makedirs(raiz, exist_ok=True)
    marca = os.path.join(raiz, MARCA)
    if not os.path.exists(marca):
        with open(marca, 'w', encoding='utf-8') as f:
            f.write(_TEXTO_MARCA)


def ruta_manifiesto(raiz: str, numero_at: int) -> str:
    return os.path.join(raiz, f'{numero_at // 1000:03d}', f'AT-{numero_at}.json')


def construir(expediente: Expediente) -> dict:
    """El manifiesto del expediente, como diccionario."""
    documentos = (Documento.query.filter_by(expediente_id=expediente.id)
                  .order_by(Documento.id).all())
    refs = [doc.fichero_ref for doc in documentos if doc.fichero_ref]
    hashes = dict(db.session.execute(
        select(Fichero.ref, Fichero.contenido_sha256).where(Fichero.ref.in_(refs))
    ).all()) if refs else {}

    pool = f'AT-{expediente.numero_at}/pool'
    entradas = []
    for doc in documentos:
        url = doc.url or ''
        if url.startswith('bddat://'):
            continue
        entradas.append({
            'id': doc.id,
            'nombre': doc.nombre_visible(),
            'carpeta': ruta_esftt_documento(doc) if doc.vinculos_tarea else pool,
            'ref': doc.fichero_ref,
            'contenido_sha256': hashes.get(doc.fichero_ref),
            'url': url if url.startswith(('http://', 'https://')) else None,
        })
    return {'formato': FORMATO, 'expediente': f'AT-{expediente.numero_at}', 'documentos': entradas}


def serializar(manifiesto: dict) -> bytes:
    """JSON legible y determinista: el mismo manifiesto da siempre los mismos bytes."""
    return (json.dumps(manifiesto, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def escribir(expediente: Expediente) -> bool:
    """Rehace el manifiesto del expediente. Devuelve si lo ha reescrito (False: no cambiaba).

    Lanza `ManifiestosNoDisponibles` si falta la carpeta o su marca.
    """
    raiz = _raiz()
    datos = serializar(construir(expediente))
    return _escribir_si_cambia(ruta_manifiesto(raiz, expediente.numero_at), datos)


def rehacer_todos() -> Iterator[Resultado]:
    """Rehace los manifiestos de todos los expedientes, por número.

    El fallo de un expediente se informa y se sigue con el resto; que la carpeta deje de
    estar disponible para la pasada entera (`ManifiestosNoDisponibles`).
    """
    _raiz()
    for expediente in Expediente.query.order_by(Expediente.numero_at).all():
        nombre = f'AT-{expediente.numero_at}'
        try:
            yield Resultado(nombre, escribir(expediente))
        except ManifiestosNoDisponibles:
            raise
        except Exception as exc:
            yield Resultado(nombre, False, f'{type(exc).__name__}: {exc}')


def _raiz() -> str:
    raiz = current_app.config.get('MANIFIESTOS_BASE', '')
    if not raiz:
        raise ManifiestosNoDisponibles('MANIFIESTOS_BASE no está configurado')
    if not os.path.isfile(os.path.join(raiz, MARCA)):
        raise ManifiestosNoDisponibles(
            f'Carpeta de manifiestos no disponible en {raiz}: falta {MARCA} '
            f'(¿carpeta sin montar o sin inicializar?)')
    return raiz


def _escribir_si_cambia(ruta: str, datos: bytes) -> bool:
    if _contiene(ruta, datos):
        return False
    carpeta = os.path.dirname(ruta)
    os.makedirs(carpeta, exist_ok=True)
    fd, temporal = tempfile.mkstemp(dir=carpeta, prefix='.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(datos)
            f.flush()
            os.fsync(f.fileno())
        _reemplazar(temporal, ruta, datos)
    except BaseException:
        _borrar(temporal)
        raise
    return True


def _reemplazar(temporal: str, ruta: str, datos: bytes) -> None:
    """Renombrado atómico, con el mismo cuidado que la librería del almacén: en Windows,
    renombrar sobre un fichero que otro está renombrando falla un instante. Si el destino
    ya tiene lo que íbamos a escribir, el resultado es el buscado."""
    for intento in range(_REINTENTOS_REEMPLAZO):
        try:
            os.replace(temporal, ruta)
            return
        except PermissionError:
            if _contiene(ruta, datos):
                _borrar(temporal)
                return
            if intento == _REINTENTOS_REEMPLAZO - 1:
                raise
            time.sleep(_ESPERA_REEMPLAZO)


def _contiene(ruta: str, datos: bytes) -> bool:
    try:
        with open(ruta, 'rb') as f:
            return f.read() == datos
    except FileNotFoundError:
        return False


def _borrar(ruta: str) -> None:
    try:
        os.remove(ruta)
    except OSError:
        pass
