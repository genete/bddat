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
    # Raíz de plantillas .docx para generación de escritos.
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

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
