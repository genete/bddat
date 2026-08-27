"""Reloj de desarrollo — fecha "hoy" simulable para testear guardas de plazos (#820).

Almacén: `instance/reloj_simulado.txt` (carpeta ya en `.gitignore`). Se lee de
disco en cada llamada a propósito — así cualquier proceso que lo escriba (CLI
`flask reloj`, o la interfaz web) se ve reflejado en un `python run.py` ya en
marcha, sin reiniciar: una variable de entorno no serviría, cada proceso tiene
su propia copia y un `flask reloj set` en un proceso aparte no la propagaría
al proceso del servidor ya arrancado.

Punto único de lectura/escritura para los tres consumidores (`_hoy()` en
plazos.py, el comando CLI y el blueprint web) — el candado por `DEBUG` lo
aplica cada consumidor, no este módulo, que no distingue entorno.
"""
import os
from datetime import date

from flask import current_app

NOMBRE_FICHERO = 'reloj_simulado.txt'


def _ruta_fichero() -> str:
    return os.path.join(current_app.instance_path, NOMBRE_FICHERO)


def obtener() -> date | None:
    """Fecha simulada activa, o None si no hay ninguna fijada."""
    ruta = _ruta_fichero()
    if not os.path.isfile(ruta):
        return None
    with open(ruta, 'r', encoding='utf-8') as f:
        contenido = f.read().strip()
    if not contenido:
        return None
    return date.fromisoformat(contenido)


def fijar(fecha: date) -> None:
    """Fija la fecha simulada, creando `instance/` si no existe."""
    os.makedirs(current_app.instance_path, exist_ok=True)
    with open(_ruta_fichero(), 'w', encoding='utf-8') as f:
        f.write(fecha.isoformat())


def borrar() -> None:
    """Quita la fecha simulada; a partir de aquí `_hoy()` vuelve a la real."""
    ruta = _ruta_fichero()
    if os.path.isfile(ruta):
        os.remove(ruta)
