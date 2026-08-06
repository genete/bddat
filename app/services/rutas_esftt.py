"""
Servicio de cálculo de rutas ESFTT (Expediente-Solicitud-Fase-Trámite-Tarea) y de
la carpeta de entrada al pool (ADR-032 §4, #665), y del movimiento físico real
al vincularse/desvincularse un documento de una tarea (ADR-032 §3, #667).

También resuelve el nombrado único de entrada al pool (#666, ADR-032 §4).
"""
import hashlib
import os
import re
import secrets
import shutil

from app import db
from app.models.documentos import Documento
from app.models.tareas import Tarea

# Caracteres no válidos en nombres de carpeta Windows (mismo patrón que generador_escritos.py)
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')
_LONGITUD_MAX_FALLBACK_ORGANISMO = 30

# Nombres de dispositivo reservados en Windows (con o sin extensión): CON.txt también es inválido.
_NOMBRES_RESERVADOS_WINDOWS = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}

# Longitud inicial del prefijo de hash en el nombre de fichero del pool (ADR-032 §4,
# git-style: se extiende un carácter más ante colisión real con contenido distinto).
_LONGITUD_PREFIJO_HASH = 8


def _segmento(instancia_id: int, codigo: str) -> str:
    """Segmento de ruta con prefijo determinista del id de la instancia.

    Evita colisión cuando el mismo código de catálogo se repite en el mismo nivel
    (doble ESPERAR_PLAZO en un trámite, trámite repetido en una fase, fase repetida
    en una solicitud) y, al ser el id autoincremental, ordena el directorio en el
    mismo orden en que se crearon las instancias.
    """
    return f'{instancia_id:06d}_{codigo}'


def _texto_organismo(entidad) -> str:
    """Texto del segmento organismo: abrev si está relleno, si no nombre_completo
    saneado (dato histórico sin backfill de abrev — nunca falla solo por esto)."""
    texto = (entidad.abrev or entidad.nombre_completo or '').strip()
    texto = _CARACTERES_INVALIDOS.sub('_', texto)
    return texto[:_LONGITUD_MAX_FALLBACK_ORGANISMO]


def _segmento_organismo(tramite) -> str | None:
    """Segmento adicional para trámites ligados a un organismo (CONSULTA_SEPARATA,
    CONSULTA_TRASLADO_TITULAR, CONSULTA_TRASLADO_ORGANISMO — ADR-011). Varios de
    estos trámites pueden coexistir en paralelo en la misma fase, uno por organismo
    consultado; el código de trámite por sí solo no los distingue.

    None si el trámite no tiene TramiteOrganismo asociado (caso general).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    vinculo = TramiteOrganismo.query.filter_by(tramite_id=tramite.id).first()
    if vinculo is None:
        return None
    return _segmento(vinculo.id, _texto_organismo(vinculo.organismo_expediente.organismo))


def ruta_esftt_documento(documento_o_tarea) -> str:
    """
    Calcula la ruta ESFTT legible (relativa a FILESYSTEM_BASE, sin nombre de
    fichero) donde debe vivir un documento, derivada de los códigos inmutables de
    catálogo (tipos_fases.codigo, tipos_tramites.codigo, tipos_tareas.codigo) y las
    siglas de tipos_solicitudes.

    Acepta:
    - Tarea: construye la ruta directamente a partir de tarea.tramite.fase.solicitud
      (punto de entrada natural cuando #667 mueva un documento al vincularse).
    - Documento: resuelve la tarea "propietaria" por su primera vinculación
      (menor id en documentos_tarea) — la primera vinculación fija la ubicación,
      ADR-032 §3. Lanza ValueError si el documento no tiene ninguna vinculación
      (aún huérfano en el pool, sin destino ESFTT).
    """
    if isinstance(documento_o_tarea, Documento):
        vinculos = sorted(documento_o_tarea.vinculos_tarea, key=lambda v: v.id)
        if not vinculos:
            raise ValueError(
                f'Documento id={documento_o_tarea.id} no tiene ninguna tarea vinculada: '
                'aún no tiene destino ESFTT (usar ruta_pool_documento mientras esté huérfano)'
            )
        tarea = vinculos[0].tarea
    elif isinstance(documento_o_tarea, Tarea):
        tarea = documento_o_tarea
    else:
        raise TypeError(
            f'ruta_esftt_documento espera Documento o Tarea, recibido {type(documento_o_tarea)!r}'
        )

    tramite = tarea.tramite
    fase = tramite.fase
    solicitud = fase.solicitud
    expediente = solicitud.expediente

    segmentos = [
        f'AT-{expediente.numero_at}',
        _segmento(solicitud.id, solicitud.tipo_solicitud.siglas),
        _segmento(fase.id, fase.tipo_fase.codigo),
    ]

    segmento_organismo = _segmento_organismo(tramite)
    if segmento_organismo is not None:
        segmentos.append(segmento_organismo)

    segmentos.append(_segmento(tramite.id, tramite.tipo_tramite.codigo))
    segmentos.append(_segmento(tarea.id, tarea.tipo_tarea.codigo))

    return '/'.join(segmentos)


def ruta_destino_esftt_fichero(tarea, nombre_fichero: str) -> str:
    """
    Ruta absoluta donde debe escribirse un documento generado directamente para
    esta tarea (#730) — sustituye al intermedio en `AT-N/` raíz
    (`ruta_destino_documento`, #167) que dejó de tener sentido en cuanto existió
    la carpeta ESFTT propia de la tarea (ADR-032 §3): escribir ahí y mover
    después era el paso que rompía la regeneración, porque el documento nunca
    volvía a estar en la ruta donde se le buscaba.

    Crea el subdirectorio si no existe (mismo patrón que ruta_pool_documento).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio_rel = ruta_esftt_documento(tarea)
    directorio_abs = os.path.normpath(os.path.join(base, directorio_rel.replace('/', os.sep)))
    os.makedirs(directorio_abs, exist_ok=True)

    return os.path.join(directorio_abs, nombre_fichero)


def ruta_pool_documento(expediente) -> str:
    """
    Ruta absoluta de la carpeta pool/ del expediente (AT-N/pool, landing zone física
    de documentos huérfanos — ADR-032 §1/§4). Crea el directorio si no existe
    (mismo patrón que ruta_destino_documento en generador_escritos.py).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio = os.path.join(base, f'AT-{expediente.numero_at}', 'pool')
    os.makedirs(directorio, exist_ok=True)

    return directorio


def _saneado_nombre_pool(nombre_original: str) -> str:
    """
    Sanea un nombre de fichero recibido del navegador (`FileStorage.filename`,
    dato controlado por el cliente) para uso seguro como nombre de fichero en
    disco (ADR-032 §4, #666). Solo correctivo — nunca trunca por longitud
    (ver ADR-032 §4 para el porqué).

    - Descarta cualquier componente de directorio (previene path traversal:
      '../../algo' o '..\\..\\algo' se reduce a 'algo').
    - Sustituye caracteres inválidos en Windows por '_'.
    - Recorta espacios y puntos finales (Windows los ignora al escribir;
      normalizarlo aquí evita que BD y disco diverjan).
    - Evita nombres de dispositivo reservados de Windows (CON, NUL, COM1…).
    """
    nombre = (nombre_original or '').replace('\\', '/').rsplit('/', 1)[-1]
    nombre = _CARACTERES_INVALIDOS.sub('_', nombre)
    nombre = nombre.rstrip(' .')
    if not nombre:
        nombre = 'documento'

    base, _ext = os.path.splitext(nombre)
    if base.upper() in _NOMBRES_RESERVADOS_WINDOWS:
        nombre = f'_{nombre}'

    return nombre


def _hash_md5_fichero(ruta: str) -> str:
    """MD5 completo de un fichero ya existente en disco, por bloques."""
    hasher = hashlib.md5()
    with open(ruta, 'rb') as f:
        for bloque in iter(lambda: f.read(65536), b''):
            hasher.update(bloque)
    return hasher.hexdigest()


def nombre_pool_unico(hash_md5: str, nombre_original: str, directorio: str) -> tuple[str, bool]:
    """
    Calcula el nombre de fichero único para la entrada al pool (ADR-032 §4, #666):
    prefijo abreviado del hash MD5 completo + nombre original saneado (sin
    truncar por longitud).

    Ante colisión de prefijo con un fichero ya existente en `directorio` de
    contenido DISTINTO, extiende el prefijo un carácter más (git-style) y
    reintenta, hasta encontrar hueco o agotar el hash completo (caso extremo:
    añade un carácter aleatorio al nombre).

    No escribe nada — solo calcula. El caller decide si escribe el fichero
    usando el segundo valor devuelto.

    Returns:
        (nombre_fichero, ya_existe_identico) — ya_existe_identico es True
        cuando el destino ya existe en disco con el mismo contenido
        (duplicado exacto, p.ej. re-subida del mismo fichero): el caller no
        debe reescribirlo, pero puede seguir creando su propio `Documento`.
    """
    nombre_saneado = _saneado_nombre_pool(nombre_original)
    n = _LONGITUD_PREFIJO_HASH
    while n <= len(hash_md5):
        candidato = f'{hash_md5[:n]}_{nombre_saneado}'
        ruta_candidata = os.path.join(directorio, candidato)
        if not os.path.exists(ruta_candidata):
            return candidato, False
        if _hash_md5_fichero(ruta_candidata) == hash_md5:
            return candidato, True
        n += 1

    # Caso extremo, "altamente improbable" (ADR-032 §4): agotado el hash completo
    # como prefijo y sigue habiendo colisión con contenido distinto.
    candidato = f'{hash_md5}_{secrets.token_hex(1)}_{nombre_saneado}'
    return candidato, False


def _nombre_original_pool(documento: Documento, nombre_actual: str) -> str:
    """
    Recupera el nombre original a partir del nombre con prefijo hash del pool
    (ADR-032 §4): '<prefijo-hash>_<nombre-original>'. Si el documento no tiene
    hash_md5 (no entró por multipart — registro in situ), nombre_actual ya es
    el original, se devuelve tal cual.
    """
    if not documento.hash_md5:
        return nombre_actual
    hash_md5 = documento.hash_md5
    for n in range(_LONGITUD_PREFIJO_HASH, len(hash_md5) + 1):
        prefijo = hash_md5[:n] + '_'
        if nombre_actual.startswith(prefijo):
            return nombre_actual[len(prefijo):]
    return nombre_actual


def _destino_sin_colision(directorio_abs: str, nombre: str, documento_id: int, origen_abs: str) -> str:
    """Ruta destino en directorio_abs para `nombre`; si ya existe un fichero DISTINTO
    del propio origen, sufija con el id del documento (#667) para no pisarlo."""
    destino = os.path.join(directorio_abs, nombre)
    if os.path.exists(destino) and os.path.normpath(destino) != os.path.normpath(origen_abs):
        base_nombre, ext = os.path.splitext(nombre)
        destino = os.path.join(directorio_abs, f'{base_nombre}_{documento_id}{ext}')
    return destino


def mover_a_esftt(documento: Documento, tarea: Tarea) -> bool:
    """
    Mueve el fichero físico del documento desde su ubicación de entrada (pool/ u
    otra ruta bajo FILESYSTEM_BASE) a su carpeta ESFTT legible, al vincularse
    por primera vez a una tarea (ADR-032 §3, #667).

    No-op (devuelve False) si:
    - documento.url no es esquema local (bddat://, http(s)://) — no hay
      fichero físico que mover.
    - el documento ya está en la carpeta ESFTT destino (idempotente ante
      llamadas repetidas para el mismo documento/tarea).

    Patrón seguro (ADR-032 §3): copiar a destino → actualizar Documento.url y
    hacer commit → borrar origen solo tras commit exitoso. Si el commit falla,
    Documento.url no llega a apuntar al destino y el origen sigue intacto.
    """
    if '://' in (documento.url or ''):
        return False

    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio_destino_rel = ruta_esftt_documento(tarea)
    directorio_actual_rel = os.path.dirname(documento.url).replace('\\', '/')
    if directorio_actual_rel == directorio_destino_rel:
        return False  # ya está en su sitio

    origen_abs = documento.ruta_absoluta()
    directorio_destino_abs = os.path.normpath(
        os.path.join(base, directorio_destino_rel.replace('/', os.sep)))
    os.makedirs(directorio_destino_abs, exist_ok=True)

    nombre = _nombre_original_pool(documento, os.path.basename(documento.url))
    destino_abs = _destino_sin_colision(directorio_destino_abs, nombre, documento.id, origen_abs)

    shutil.copy2(origen_abs, destino_abs)
    documento.url = os.path.relpath(destino_abs, base).replace(os.sep, '/')
    db.session.commit()

    if os.path.normpath(origen_abs) != os.path.normpath(destino_abs):
        os.remove(origen_abs)

    return True


def mover_a_pool(documento: Documento, expediente) -> bool:
    """
    Mueve el fichero físico del documento de vuelta a AT-N/pool/ cuando pierde
    su último vínculo con una tarea (queda huérfano de nuevo — ADR-027 §2,
    ADR-032 §3, #667). Espejo inverso de mover_a_esftt().

    `expediente` se recibe explícito (igual que mover_a_esftt recibe la tarea)
    en vez de derivarlo de documento.expediente — más simple de testear y el
    caller (editar_tarea) ya lo tiene calculado.

    No-op (devuelve False) si documento.url no es esquema local, o si ya está
    en pool/. Mismo patrón seguro copiar→commit→borrar.
    """
    if '://' in (documento.url or ''):
        return False

    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio_pool_abs = ruta_pool_documento(expediente)
    origen_abs = documento.ruta_absoluta()
    if os.path.normpath(os.path.dirname(origen_abs)) == os.path.normpath(directorio_pool_abs):
        return False  # ya está en pool

    nombre = os.path.basename(documento.url)
    destino_abs = _destino_sin_colision(directorio_pool_abs, nombre, documento.id, origen_abs)

    shutil.copy2(origen_abs, destino_abs)
    documento.url = os.path.relpath(destino_abs, base).replace(os.sep, '/')
    db.session.commit()

    if os.path.normpath(origen_abs) != os.path.normpath(destino_abs):
        os.remove(origen_abs)

    return True
