"""
Módulo de utilidades de la aplicación.
"""
from app.utils.permisos import (
    tiene_permiso,
    es_expediente_ajeno,
    puede_acceder_expediente,
    puede_editar_expediente,
    puede_cambiar_responsable,
    verificar_acceso_expediente,
)

__all__ = [
    'tiene_permiso',
    'es_expediente_ajeno',
    'puede_acceder_expediente',
    'puede_editar_expediente',
    'puede_cambiar_responsable',
    'verificar_acceso_expediente',
]
