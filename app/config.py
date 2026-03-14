import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-fallback'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    # Raíz del servidor de ficheros corporativo.
    # Desarrollo: cualquier carpeta local (p.ej. D:/BDDAT/docs_prueba)
    # Producción: W:\ALTA TENSION\Expedientes  o  \\HACACL0102\energia\ALTA TENSION\Expedientes
    FILESYSTEM_BASE = os.environ.get('FILESYSTEM_BASE') or ''
    # Raíz de plantillas .docx para generación de escritos.
    # Estructura: PLANTILLAS_BASE/plantillas/ y PLANTILLAS_BASE/fragmentos/
    # Desarrollo: p.ej. D:/BDDAT/docs_prueba/plantillas_escritos
    PLANTILLAS_BASE = os.environ.get('PLANTILLAS_BASE') or ''

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
