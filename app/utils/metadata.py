"""
Utilidad para leer metadata.json de los módulos.

Uso:
    from app.utils.metadata import cargar_metadata
    meta = cargar_metadata('expedientes')
    columns = meta.get('listado_v2', {}).get('columns', [])
"""
import json
import os


def cargar_metadata(modulo: str) -> dict:
    """Lee el metadata.json del módulo dado. Devuelve {} si no existe o es inválido."""
    ruta = os.path.join(
        os.path.dirname(__file__), '..', 'modules', modulo, 'metadata.json'
    )
    try:
        with open(os.path.abspath(ruta), encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
