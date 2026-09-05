import os
from dotenv import load_dotenv

load_dotenv()


def _ruta_base_env(nombre: str) -> str:
    """
    Lee una variable de entorno de ruta base y normaliza sus separadores
    (#699): en desarrollo suele configurarse con `/` (p.ej. `D:/BDDAT/...`),
    y los `os.path.join` posteriores en el código añaden tramos con `\\` en
    Windows, mezclando ambos en la misma cadena. Se normaliza aquí, una sola
    vez, para que los 15+ puntos del código que leen esta config no tengan
    que hacerlo cada uno por su cuenta.

    `os.path.normpath('')` devuelve `'.'`, no `''` — hay que evitarlo
    explícitamente para no romper los `if not base:` que detectan "no
    configurado" en cada consumidor.
    """
    valor = os.environ.get(nombre)
    return os.path.normpath(valor) if valor else ''


class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-fallback'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # Raíz del servidor de ficheros corporativo.
    # Desarrollo: cualquier carpeta local (p.ej. D:/BDDAT/docs_prueba)
    # Producción: W:\ALTA TENSION\Expedientes  o  \\HACACL0102\energia\ALTA TENSION\Expedientes
    FILESYSTEM_BASE = _ruta_base_env('FILESYSTEM_BASE')
    # Raíz de plantillas (.odt / .docx) para generación de escritos.
    # Estructura: PLANTILLAS_BASE/plantillas/ y PLANTILLAS_BASE/fragmentos/
    # Desarrollo: p.ej. D:/BDDAT/docs_prueba/plantillas_escritos
    PLANTILLAS_BASE = _ruta_base_env('PLANTILLAS_BASE')

class DevelopmentConfig(Config):
    """Desarrollo"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Producción"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Tests (#849).

    Base de datos PROPIA, nunca la de desarrollo: hasta este issue la suite
    corría contra `DATABASE_URL` y dependía del estado de una máquina
    concreta —174 `pytest.skip` repartidos por 52 ficheros podían
    autodesactivarse en silencio y el conjunto salía verde igual—.

    `DEBUG = False` no es un detalle: `reloj_simulado.hoy()` solo respeta el
    fichero `instance/reloj_simulado.txt` con DEBUG activo, así que los tests
    trabajan sobre la fecha real y dejan de depender de en qué día quedó el
    reloj de desarrollo. `SQLALCHEMY_ECHO` apagado por lo mismo que dice
    ANALISIS_ESCALABILIDAD §6.1: con el eco puesto se mide la consola.

    Sin fallback a DATABASE_URL a propósito: si TEST_DATABASE_URL no está
    configurada, es preferible que la suite falle al arrancar a que escriba
    en la BD de desarrollo creyendo que está aislada.

    Lo mismo vale para el disco. El aislamiento por SAVEPOINT revierte la BD,
    pero el sistema de ficheros no es transaccional: un test que genere un
    escrito o suba al pool deja el fichero puesto aunque la transacción se
    deshaga. Existe el fixture `fs_tmp` (#674) para redirigirlo, pero es
    opt-in — depende de que el autor del test se acuerde. Con una raíz propia,
    un olvido ensucia el árbol de tests y nunca el de desarrollo.
    """
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL')
    SQLALCHEMY_ECHO = False
    FILESYSTEM_BASE = _ruta_base_env('TEST_FILESYSTEM_BASE')
    PLANTILLAS_BASE = _ruta_base_env('TEST_PLANTILLAS_BASE')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def _nombre_bd(uri):
    """Nombre de la base dentro de una URL de conexión, o None si no se puede leer."""
    if not uri:
        return None
    from sqlalchemy.engine import make_url
    try:
        return make_url(uri).database
    except Exception:
        return None


def comprobar_aislamiento(app):
    """No dejar que un mundo trabaje con los datos del otro (#849).

    Los tests corren contra la base de tests; el servidor de desarrollo y la
    verificación en navegador, contra la de desarrollo. Cruzarlos no es un
    matiz: un servidor sirviendo la base de tests enseñaría pantallas que no
    reflejan nada real, y una suite apuntando a desarrollo es justo lo que este
    issue vino a arreglar. Se comprueba al arrancar en vez de confiarlo a la
    disciplina, porque un cruce no da síntomas hasta que ya ha hecho daño.
    """
    dev = _nombre_bd(os.environ.get('DATABASE_URL'))
    test = _nombre_bd(os.environ.get('TEST_DATABASE_URL'))
    actual = _nombre_bd(app.config.get('SQLALCHEMY_DATABASE_URI'))

    if actual is None:
        destino = 'TEST_DATABASE_URL' if app.config.get('TESTING') else 'DATABASE_URL'
        raise RuntimeError(
            f'Sin base de datos configurada: revisa {destino} en .env')

    if dev and test and dev == test:
        raise RuntimeError(
            f'DATABASE_URL y TEST_DATABASE_URL apuntan a la misma base ({dev}). '
            'La suite borraría los datos de desarrollo.')

    if app.config.get('TESTING') and dev and actual == dev:
        raise RuntimeError(
            f'Configuración de tests apuntando a la base de desarrollo ({actual}). '
            'Revisa TEST_DATABASE_URL.')

    if not app.config.get('TESTING') and test and actual == test:
        raise RuntimeError(
            f'Configuración de {"producción" if not app.config.get("DEBUG") else "desarrollo"} '
            f'apuntando a la base de tests ({actual}). Revisa DATABASE_URL.')
