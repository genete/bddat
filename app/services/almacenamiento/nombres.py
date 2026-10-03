"""Saneado del nombre de un fichero que llega de fuera (ADR-050 §C).

El nombre entra saneado con las reglas de nombres de Windows y, desde entonces, no
lo cambia nadie: `documentos.nombre_fichero` es lo que se enseña y lo que se usa
como nombre de descarga. Sanear no es cambiar el nombre; lo que no se modifica es
el nombre ya saneado.

Salió de `rutas_esftt` (ADR-032 §4, #666, #1007) para que el subsistema no dependa
de un módulo que el PR 5 retira. `rutas_esftt._saneado_nombre_pool` sigue
existiendo, como alias de esta función, mientras viva el modelo de rutas.
"""
import os
import re

# Los caracteres no válidos en un nombre de fichero de Windows, más los de control
# (0-31: salto de línea, tabulador, NUL…): el nombre pasa a la interfaz y a la cabecera
# de descarga, donde un salto de línea no es inocuo.
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

# Nombres de dispositivo reservados en Windows (con o sin extensión): CON.txt también es inválido.
_NOMBRES_RESERVADOS_WINDOWS = {
    'CON', 'PRN', 'AUX', 'NUL',
    'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
    'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
}


def sanear_nombre(nombre_original: str) -> str:
    """Sanea un nombre de fichero recibido del navegador (`FileStorage.filename`,
    dato controlado por el cliente) para uso seguro como nombre de fichero (ADR-050 §C,
    ADR-032 §4, #666). Solo correctivo — nunca trunca por longitud (ver ADR-032 §4 para
    el porqué).

    - Descarta cualquier componente de directorio (previene path traversal:
      '../../algo' o '..\\..\\algo' se reduce a 'algo').
    - Sustituye por '_' los caracteres inválidos en Windows y los de control.
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
