"""Exportador de expedientes: del manifiesto al árbol de carpetas legible.

Programa independiente (ADR-050 §H de BDDAT): solo usa la biblioteca estándar de
Python y la librería del almacén, y no sabe nada de la base de datos ni de la
aplicación. Con Flask y PostgreSQL parados, quien tenga Python y lectura sobre el
almacén reconstruye el árbol ESFTT de un expediente a partir de su manifiesto. Es un
salvavidas para volver al «papel», no el expediente: copia ficheros a carpetas y nada
más.

Es el único código que reparte documentos en carpetas: la reconstrucción a mano, y
más adelante el ZIP y la exportación al finalizar, pasan por él.

Línea de órdenes
================

Desde la carpeta que contiene `almacen/` y `exportador/`:

    python -m exportador --almacen <raíz del almacén> --destino <carpeta> MANIFIESTO...

MANIFIESTO es un fichero `AT-N.json` o una carpeta de manifiestos, que se recorre
entera. Sale con 0 si se exportó todo, con 1 si hubo alguna incidencia (se informan
todas y se sigue con el resto) y con 2 si la orden está mal.

API
===

    cargar(ruta) -> dict
    exportar(manifiesto, destino, almacen) -> Informe

`almacen` es **cualquier objeto con `leer(ref)`** que devuelva un flujo binario (lo
cierra el exportador). Quien llama decide cómo se lee: usado solo, la librería
(`almacen.AlmacenDisco(raiz)`, es lo que hace la línea de órdenes); desde BDDAT, su
adaptador, para que la lectura pase por su tiempo límite y su semáforo.

El manifiesto
=============

    {"formato": 1,
     "expediente": "AT-123",
     "documentos": [
        {"id": 345, "nombre": "Proyecto.pdf",
         "carpeta": "AT-123/000045_AAP/000067_INSTRUCCION/000071_X/000077_ANALIZAR",
         "ref": "3af1…", "contenido_sha256": "3af1…", "url": null}]}

- Con `ref`: se copia a `<destino>/<carpeta>/<nombre>`.
- Con `url` (un enlace): no hay fichero que copiar; figura en el informe.
- Sin ninguna de las dos: no tiene contenido en el almacén, y es una incidencia.

Qué decide al escribir
======================

- **No mezcla.** Si `<destino>/AT-N` ya existe, ese expediente no se exporta: un árbol
  a medias de otra vez, mezclado con el nuevo, daría por presentes documentos que ya no
  lo están.
- **Comprueba el hash** de cada fichero al copiarlo, a trozos. Si no coincide, no deja
  el fichero con su nombre: lo informa como dañado.
- **Repite el saneado** de caracteres y nombres reservados de Windows en cada carpeta y
  cada nombre, aunque BDDAT ya los guarde saneados: lee un manifiesto, y no da por bueno
  lo que no ha comprobado él.
- **Choques de nombre** en una carpeta (sin distinguir mayúsculas, como Windows): mismo
  nombre y mismo contenido, un solo fichero; contenido distinto, sufijo `_<id del
  documento>`, que no depende del orden en que se exporte.
- **Longitud:** si la ruta completa pasa de `LONGITUD_MAXIMA` caracteres (el límite del
  Explorador de Windows), se acorta el nombre conservando la extensión; si ni así cabe,
  se informa y no se copia.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from typing import NamedTuple

__all__ = ['FORMATO', 'LONGITUD_MAXIMA', 'ManifiestoInvalido', 'Linea', 'Informe', 'cargar', 'exportar']

FORMATO = 1
# Caracteres de la ruta completa: MAX_PATH de Windows (260) sin el carácter nulo final.
LONGITUD_MAXIMA = 259
# Por debajo de esto, un nombre acortado ya no dice qué es: mejor informar que copiar.
_BASE_MINIMA = 8
_TROZO = 1024 * 1024

# Los caracteres no válidos en un nombre de Windows, más los de control (0-31).
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
# Nombres de dispositivo reservados de Windows. Se comprueba lo que va antes del
# primer punto: «CON.tar.gz» es tan inválido como «CON.txt».
_RESERVADOS = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}


class ManifiestoInvalido(ValueError):
    """El manifiesto no se puede leer o no tiene la forma que entiende este exportador."""


class Linea(NamedTuple):
    id: int | None      # id del documento; None si la línea es del expediente entero
    texto: str          # la ruta copiada (relativa al destino), la url o el motivo


@dataclass
class Informe:
    expediente: str
    copiados: list[Linea] = field(default_factory=list)
    enlaces: list[Linea] = field(default_factory=list)
    incidencias: list[Linea] = field(default_factory=list)

    @property
    def completo(self) -> bool:
        return not self.incidencias


def cargar(ruta: str) -> dict:
    """Lee un manifiesto de disco."""
    try:
        with open(ruta, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise ManifiestoInvalido(f'No se puede leer {ruta}: {exc}') from exc


def exportar(manifiesto: dict, destino: str, almacen) -> Informe:
    """Reconstruye en `destino/AT-N/` el árbol del expediente descrito en `manifiesto`.

    Lanza `ManifiestoInvalido` si el manifiesto no tiene la forma esperada. Todo lo
    demás (un contenido que no se puede leer, dañado, una ruta que no cabe) es una
    incidencia del informe, y se sigue con el resto.
    """
    expediente, documentos = _validar(manifiesto)
    informe = Informe(expediente)
    destino = os.path.abspath(destino)
    raiz = os.path.join(destino, _sanear(expediente, 'expediente'))
    if os.path.exists(raiz):
        informe.incidencias.append(Linea(None, (
            f'Ya existe {raiz}: exporta a otra carpeta (el exportador no mezcla con lo '
            f'que haya)')))
        return informe
    os.makedirs(raiz)

    # (carpeta, nombre) en minúsculas -> hash del fichero que ya ocupa ese nombre.
    ocupados: dict[tuple[str, str], str] = {}
    for doc in sorted(documentos, key=lambda d: d['id']):
        _exportar_documento(doc, destino, raiz, almacen, ocupados, informe)
    return informe


def _exportar_documento(doc, destino, raiz, almacen, ocupados, informe) -> None:
    id_doc, nombre = doc['id'], doc['nombre']
    if doc['ref'] is None:
        if doc['url']:
            informe.enlaces.append(Linea(id_doc, doc['url']))
        else:
            informe.incidencias.append(Linea(id_doc, f'«{nombre}»: sin contenido en el almacén'))
        return

    segmentos = [_sanear(s, '_') for s in doc['carpeta'].split('/') if s]
    if not segmentos or segmentos[0] != os.path.basename(raiz):
        informe.incidencias.append(Linea(id_doc, (
            f'«{nombre}»: su carpeta ({doc["carpeta"]}) no está dentro del expediente')))
        return
    directorio = os.path.join(destino, *segmentos)
    sha = doc['contenido_sha256'].lower()

    elegido = _elegir_nombre(directorio, _sanear(nombre, 'documento'), id_doc, sha, ocupados)
    if elegido is None:
        informe.incidencias.append(Linea(id_doc, (
            f'«{nombre}»: la ruta no cabe en {LONGITUD_MAXIMA} caracteres en {directorio}')))
        return
    nombre_final, ya_copiado = elegido
    ruta = os.path.join(directorio, nombre_final)
    relativa = os.path.relpath(ruta, destino).replace(os.sep, '/')
    if ya_copiado:
        informe.copiados.append(Linea(id_doc, relativa))
        return

    fallo = _copiar(almacen, doc['ref'], sha, ruta, raiz)
    if fallo:
        # El nombre queda libre: otro documento con el mismo contenido no puede darse
        # por copiado sobre un fichero que no llegó a escribirse.
        del ocupados[(directorio.casefold(), nombre_final.casefold())]
        informe.incidencias.append(Linea(id_doc, f'«{nombre}»: {fallo}'))
    else:
        informe.copiados.append(Linea(id_doc, relativa))


def _validar(manifiesto) -> tuple[str, list]:
    if not isinstance(manifiesto, dict):
        raise ManifiestoInvalido('El manifiesto no es un objeto JSON')
    if manifiesto.get('formato') != FORMATO:
        raise ManifiestoInvalido(
            f'Formato de manifiesto {manifiesto.get("formato")!r}: este exportador lee el {FORMATO}')
    expediente = manifiesto.get('expediente')
    documentos = manifiesto.get('documentos')
    if not isinstance(expediente, str) or not expediente or not isinstance(documentos, list):
        raise ManifiestoInvalido('Al manifiesto le falta «expediente» o «documentos»')
    for doc in documentos:
        if not (isinstance(doc, dict)
                and isinstance(doc.get('id'), int)
                and isinstance(doc.get('nombre'), str)
                and isinstance(doc.get('carpeta'), str)
                and isinstance(doc.get('ref'), (str, type(None)))
                and isinstance(doc.get('url'), (str, type(None)))
                and (doc.get('ref') is None or isinstance(doc.get('contenido_sha256'), str))):
            raise ManifiestoInvalido(f'Entrada de documento mal formada: {doc!r}')
    return expediente, documentos


def _sanear(componente: str, defecto: str) -> str:
    """Un nombre de carpeta o de fichero válido en Windows."""
    texto = _CARACTERES_INVALIDOS.sub('_', componente).rstrip(' .')
    if not texto:
        return defecto
    if texto.split('.')[0].rstrip(' ').upper() in _RESERVADOS:
        texto = f'_{texto}'
    return texto


def _elegir_nombre(directorio, nombre, id_doc, sha, ocupados):
    """El nombre con que queda este contenido en `directorio`, y si ya estaba copiado.

    None si la ruta no cabe ni acortando el nombre.
    """
    base, ext = os.path.splitext(nombre)
    sufijos = ['', f'_{id_doc}'] + [f'_{id_doc}_{n}' for n in range(2, 100)]
    for sufijo in sufijos:
        candidato = _ajustar_longitud(directorio, base, sufijo, ext)
        if candidato is None:
            return None
        clave = (directorio.casefold(), candidato.casefold())
        previo = ocupados.get(clave)
        if previo is None:
            ocupados[clave] = sha
            return candidato, False
        if previo == sha:
            return candidato, True
    return None


def _ajustar_longitud(directorio, base, sufijo, ext):
    disponible = LONGITUD_MAXIMA - len(directorio) - len(os.sep) - len(sufijo) - len(ext)
    if len(base) <= disponible:
        return f'{base}{sufijo}{ext}'
    if disponible < _BASE_MINIMA:
        return None
    return f'{base[:disponible].rstrip(" .")}{sufijo}{ext}'


def _copiar(almacen, ref, sha, ruta, raiz) -> str | None:
    """Copia el contenido a `ruta` comprobando su hash. Devuelve el motivo si falla.

    Escribe en un temporal y lo renombra al final: un corte a mitad nunca deja un
    fichero incompleto con el nombre bueno. El temporal va en la raíz del expediente,
    que tiene la ruta corta, para no tropezar con la longitud.
    """
    try:
        flujo = almacen.leer(ref)
    except Exception as exc:  # cualquier almacén: su propio error, tal cual en el informe
        return f'no se pudo leer del almacén ({type(exc).__name__}: {exc})'

    temporal = None
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        fd, temporal = tempfile.mkstemp(dir=raiz, prefix='.x')
        hasher = hashlib.sha256()
        with os.fdopen(fd, 'wb') as salida:
            for trozo in iter(lambda: flujo.read(_TROZO), b''):
                hasher.update(trozo)
                salida.write(trozo)
        if hasher.hexdigest() != sha:
            return 'contenido dañado: su hash no coincide con el del manifiesto'
        os.replace(temporal, ruta)
        temporal = None
        return None
    except OSError as exc:
        return f'fallo al copiar: {exc}'
    finally:
        flujo.close()
        if temporal is not None:
            _borrar(temporal)


def _borrar(ruta: str) -> None:
    try:
        os.remove(ruta)
    except OSError:
        pass
