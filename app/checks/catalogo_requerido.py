"""Manifiesto de registros estructurales requeridos en tablas de catálogo (#347).

validar_catalogo() es la única fuente de verdad de qué códigos deben existir
para que el sistema funcione. Llamar desde create_app() tras db.init_app().
"""
from __future__ import annotations

import logging
from typing import List

log = logging.getLogger(__name__)

# Mapa modelo → lista de códigos que el código fuente espera encontrar.
# Añadir aquí cuando se use un código nuevo en cualquier servicio o ruta.
REGISTROS_REQUERIDOS: dict = {
    'TipoTramite': [
        'AAC', 'AAP',
        'PUBLICACION', 'NOTIFICACION',
        'SUBSANACION', 'AUDIENCIA',
        'ADMISIBILIDAD_TECNICA',
        'INFORME_AAPP', 'INFORME_SERVICIOS',
    ],
    'TipoTarea': [
        'ANALIZAR', 'REDACTAR', 'FIRMAR',
        'NOTIFICAR', 'PUBLICAR',
        'ESPERAR_PLAZO', 'INCORPORAR',
    ],
    'TipoFase': [
        'ANALISIS_SOLICITUD',
        'CONSULTAS', 'CONSULTA_MINISTERIO',
        'COMPATIBILIDAD_AMBIENTAL',
        'FIGURA_AMBIENTAL_EXTERNA',
        'AAU_AAUS_INTEGRADA',
        'INFORMACION_PUBLICA',
        'RESOLUCION',
    ],
    # TipoSolicitud usa 'siglas' como identificador estable (no 'codigo')
    'TipoSolicitud': ['AAC', 'AAP'],
}

# Atributo del modelo que contiene el identificador estable.
# TipoSolicitud usa 'siglas'; el resto usa 'codigo'.
_CODIGO_ATTR: dict[str, str] = {
    'TipoTramite':   'codigo',
    'TipoTarea':     'codigo',
    'TipoFase':      'codigo',
    'TipoSolicitud': 'siglas',
}


def validar_catalogo() -> List[str]:
    """
    Comprueba que todos los códigos de REGISTROS_REQUERIDOS existen en BD.

    Returns:
        Lista de strings describiendo cada registro ausente.
        Lista vacía → catálogo completo.
        No lanza excepción; si la BD no está disponible loguea y devuelve lista vacía.
    """
    from sqlalchemy.exc import OperationalError, ProgrammingError

    _MODELOS = {
        'TipoTramite':   _importar('app.models.tipos_tramites',  'TipoTramite'),
        'TipoTarea':     _importar('app.models.tipos_tareas',    'TipoTarea'),
        'TipoFase':      _importar('app.models.tipos_fases',     'TipoFase'),
        'TipoSolicitud': _importar('app.models.tipos_solicitudes', 'TipoSolicitud'),
    }

    faltantes: List[str] = []

    for nombre_modelo, codigos in REGISTROS_REQUERIDOS.items():
        modelo = _MODELOS.get(nombre_modelo)
        if modelo is None:
            log.error('catalogo: no se pudo importar modelo %s', nombre_modelo)
            continue

        attr = _CODIGO_ATTR.get(nombre_modelo, 'codigo')
        try:
            attr_col = getattr(modelo, attr)
            existentes = {
                getattr(row, attr)
                for row in modelo.query.with_entities(attr_col).all()
            }
        except (OperationalError, ProgrammingError) as exc:
            log.warning('catalogo: tabla de %s no disponible — %s', nombre_modelo, exc)
            continue

        for codigo in codigos:
            if codigo not in existentes:
                faltantes.append(f"{nombre_modelo}.codigo='{codigo}' → no encontrado")

    if faltantes:
        log.error(
            'catalogo: faltan registros estructurales requeridos:\n%s',
            '\n'.join(f'  - {f}' for f in faltantes),
        )

    return faltantes


def _importar(modulo: str, clase: str):
    try:
        import importlib
        mod = importlib.import_module(modulo)
        return getattr(mod, clase, None)
    except Exception:
        return None
