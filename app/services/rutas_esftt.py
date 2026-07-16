"""
Servicio de cálculo de rutas ESFTT (Expediente-Solicitud-Fase-Trámite-Tarea) y de
la carpeta de entrada al pool (ADR-032 §4, #665).

Solo calcula rutas — no crea directorios ESFTT ni mueve ficheros. El movimiento
físico real al vincularse un documento a una tarea es #667. También resuelve
el nombrado único de entrada al pool (#666, ADR-032 §4) — sigue sin mover
ficheros, la escritura real la hace el endpoint que llama a estas funciones.
"""
import hashlib
import os
import re
import secrets

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
