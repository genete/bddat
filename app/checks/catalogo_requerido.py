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
        'PUBLICACION', 'NOTIFICACION',
        'REQUERIMIENTO_SUBSANACION', 'COMUNICACION_AUDIENCIA',
        # Suspensiones de plazo (#173)
        'SOLICITUD_INFORME', 'CONSULTA_SEPARATA', 'SOLICITUD_COMPATIBILIDAD',
        'RECEPCION_INFORME', 'RECEPCION_INFORME_VINCULANTE',
        'RECEPCION_DICTAMEN', 'RECEPCION_FIGURA',
        # Interesados del expediente (#374)
        'REGISTRO_INTERESADOS',
        # Traslados de consulta y análisis documental — auditoría 2026-07-04
        'CONSULTA_TRASLADO_ORGANISMO', 'CONSULTA_TRASLADO_TITULAR',
        'ANALISIS_DOCUMENTAL', 'RECEPCION_ALEGACION',
    ],
    'TipoTarea': [
        'ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO',
    ],
    'TipoFase': [
        'ANALISIS_SOLICITUD',
        'CONSULTAS', 'CONSULTA_MINISTERIO',
        'COMPATIBILIDAD_AMBIENTAL',
        'FIGURA_AMBIENTAL_EXTERNA',
        'AAU_AAUS_INTEGRADA',
        'INFORMACION_PUBLICA',
        'RESOLUCION',
        'RECONOCIMIENTO_INTERESADO',
    ],
    # TipoSolicitud usa 'siglas' como identificador estable (no 'codigo').
    # DUP añadida en #171: estaba hardcodeada en contiene_tipo('DUP')
    # (calculado.py, consultas_organismos.py — art. 131.1 RD 1955/2000) sin figurar aquí.
    'TipoSolicitud': ['AAC', 'AAP', 'DUP'],
    # TipoResultadoFase — código usado en invariantes_esftt (#419)
    'TipoResultadoFase': ['DESFAVORABLE', 'FAVORABLE', 'FAVORABLE_CONDICIONADO'],
    'TipoDocumento': ['CERT_FIN_INSTRUCCION', 'CERT_PLAZO_CUMPLIDO', 'BORRADOR_FIRMA', 'CERT_FIN_IP_CONSULTAS',
                      # #582 — consumido por la variable de motor tasa_impagada; lo puebla #408
                      'JUSTIFICANTE_PAGO_TASA'],
    # Rol usa 'nombre' como identificador estable — anclado en PERMISOS (app/utils/permisos.py)
    'Rol': ['ADMIN', 'SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'],
}

# Atributo del modelo que contiene el identificador estable.
# TipoSolicitud usa 'siglas'; Rol usa 'nombre'; el resto usa 'codigo'.
_CODIGO_ATTR: dict[str, str] = {
    'TipoTramite':        'codigo',
    'TipoTarea':          'codigo',
    'TipoFase':           'codigo',
    'TipoSolicitud':      'siglas',
    'TipoDocumento':      'codigo',
    'TipoResultadoFase':  'codigo',
    'Rol':                'nombre',
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
        'TipoTramite':       _importar('app.models.tipos_tramites',         'TipoTramite'),
        'TipoTarea':         _importar('app.models.tipos_tareas',           'TipoTarea'),
        'TipoFase':          _importar('app.models.tipos_fases',            'TipoFase'),
        'TipoSolicitud':     _importar('app.models.tipos_solicitudes',      'TipoSolicitud'),
        'TipoDocumento':     _importar('app.models.tipos_documentos',       'TipoDocumento'),
        'TipoResultadoFase': _importar('app.models.tipos_resultados_fases', 'TipoResultadoFase'),
        'Rol':               _importar('app.models.usuarios',               'Rol'),
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
            # Rollback necesario: en PostgreSQL un error aborta la transacción
            # y las queries siguientes fallarían con InFailedSqlTransaction.
            try:
                from app import db as _db
                _db.session.rollback()
            except Exception:
                pass
            continue

        for codigo in codigos:
            if codigo not in existentes:
                faltantes.append(f"{nombre_modelo}.{attr}='{codigo}' → no encontrado")

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
