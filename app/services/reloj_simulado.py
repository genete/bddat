"""Reloj de desarrollo — fecha "hoy" simulable para testear guardas de plazos (#820).

Almacén: `instance/reloj_simulado.txt` (carpeta ya en `.gitignore`). Se lee de
disco en cada llamada a propósito — así cualquier proceso que lo escriba (CLI
`flask reloj`, o la interfaz web) se ve reflejado en un `python run.py` ya en
marcha, sin reiniciar: una variable de entorno no serviría, cada proceso tiene
su propia copia y un `flask reloj set` en un proceso aparte no la propagaría
al proceso del servidor ya arrancado.

Punto único de lectura/escritura, en dos niveles:

  - `obtener()` / `fijar()` / `borrar()` — acceso crudo al almacén, sin
    distinguir entorno. Los usan el comando CLI y el blueprint web, que ya
    solo existen con `DEBUG=True`.
  - `hoy()` — la fecha de trabajo del sistema, con el candado por `DEBUG`
    aplicado aquí. Desde #824 hay dos consumidores (el motor de plazos y la
    validación de `Documento.fecha_administrativa`) y el candado vive en un
    solo sitio: escrito en cada consumidor es cuestión de tiempo que uno de
    ellos se despiste y la fecha simulada deje de valer para la mitad del
    sistema.
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
    """Quita la fecha simulada; a partir de aquí `hoy()` vuelve a la real."""
    ruta = _ruta_fichero()
    if os.path.isfile(ruta):
        os.remove(ruta)


def hoy() -> date:
    """Fecha de trabajo del sistema: la simulada si el reloj está activo, la real si no.

    Doble candado para que el reloj simulado se aplique: `DEBUG=True`
    (estructural — `ProductionConfig.DEBUG = False`) y el fichero presente a la
    vez. En producción devuelve siempre `date.today()`.

    Sin contexto de aplicación no hay reloj que leer y manda el de pared: un test
    unitario que instancia un modelo sin `app` (p. ej.
    `test_574_fecha_administrativa_certificados.py`) o un script que aún no ha
    creado la app entran por aquí, y quedarse sin fecha no es una opción.
    """
    from flask import has_app_context
    if has_app_context() and current_app.config.get('DEBUG'):
        simulada = obtener()
        if simulada is not None:
            return simulada
    return date.today()
