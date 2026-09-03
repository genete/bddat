"""Manifiesto de registros estructurales requeridos en tablas de catálogo (#347).

validar_catalogo() es la única fuente de verdad de qué códigos deben existir
para que el sistema funcione. Llamar desde create_app() tras db.init_app().

Desde #827 comprueba además una relación, no solo presencias: que toda fase
finalizadora esté nombrada por las reglas de precedencia del art. 82.1 LPACAP.
Es el precio de haber escrito esas reglas con sujeto explícito en vez de un
`ANY/ANY/ANY` con una condición "es finalizadora" (ADR-043 §C) — el sujeto
explícito documenta a quién aplica la regla, y este aviso es lo que evita que una
finalizadora nueva se quede fuera en silencio.
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
        # De los siete trámites que sostenían las suspensiones de plazo (#173)
        # solo queda CONSULTA_SEPARATA, y no por los plazos: la instancia
        # consultas_organismos.enviar_consultas por código. Los otros seis
        # —SOLICITUD_INFORME, SOLICITUD_COMPATIBILIDAD y los cuatro RECEPCION_*—
        # salieron en #778: qué suspende es dato de catalogo_plazos y el rescate
        # por trámite hermano desapareció, así que ningún servicio los nombra ya.
        # Siguen existiendo como tipos de trámite; lo que ya no existe es código
        # que dependa de su código.
        'CONSULTA_SEPARATA',
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
                      'JUSTIFICANTE_PAGO_TASA',
                      # #780 — consumido por la variable de motor tiene_punto_acceso_conexion
                      'PERMISO_ACCESO_CONEXION'],
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

    faltantes.extend(_validar_finalizadoras_con_regla())

    if faltantes:
        log.error(
            'catalogo: faltan registros estructurales requeridos:\n%s',
            '\n'.join(f'  - {f}' for f in faltantes),
        )

    return faltantes


def _validar_finalizadoras_con_regla() -> List[str]:
    """Toda `TipoFase.es_finalizadora` debe estar nombrada por una regla de
    precedencia del art. 82.1 (#827, ADR-043 §C) y por el mapa del emisor.

    Las reglas se escribieron con sujeto explícito —una fila por finalizadora— en
    vez de un sujeto genérico con una condición Python, para que el supervisor lea
    en la fila a quién aplica. El precio es acordarse de añadir la fila si aparece
    una tercera fase finalizadora, y este check es quien lo cobra: sin él, la
    finalizadora nueva quedaría abierta sin comprobar el fin de instrucción y nada
    lo diría.

    Se compara contra el ÚLTIMO segmento del sujeto (`ANY/ANY/RESOLUCION` →
    `RESOLUCION`), que es donde el sujeto calificado nombra la fase.

    Mismo grado de defensividad que el resto del módulo (#347): sin contexto de
    aplicación o sin BD no puede comprobarse nada y no se avisa de nada — un
    manifiesto de catálogo nunca debe ser el motivo de que el arranque falle.
    A diferencia de las comprobaciones de presencia, esta consulta modelos
    directamente y no pasa por `_importar`, así que necesita ese guardián propio.
    """
    from flask import has_app_context
    from sqlalchemy.exc import OperationalError, ProgrammingError

    if not has_app_context():
        return []

    try:
        from app.models.tipos_fases import TipoFase
        from app.models.motor_reglas import ReglaMotor
        from app.services.cert_fin_instruccion import (
            _FASE_FINALIZADORA_POR_SIGLAS, _FASE_FINALIZADORA_DEFECTO,
        )

        finalizadoras = {
            tf.codigo for tf in TipoFase.query.filter_by(es_finalizadora=True).all()
        }
        if not finalizadoras:
            return []

        nombradas = {
            r.sujeto.rsplit('/', 1)[-1]
            for r in ReglaMotor.query.filter_by(
                accion='CREAR', activa=True, articulo='82', apartado='1').all()
        }
    except (OperationalError, ProgrammingError) as exc:
        log.warning('catalogo: no se pudo validar reglas de fase finalizadora — %s', exc)
        try:
            from app import db as _db
            _db.session.rollback()
        except Exception:
            pass
        return []

    conocidas_por_emisor = set(_FASE_FINALIZADORA_POR_SIGLAS.values()) | {
        _FASE_FINALIZADORA_DEFECTO}

    avisos: List[str] = []
    for codigo in sorted(finalizadoras - nombradas):
        avisos.append(
            f"TipoFase.codigo='{codigo}' es finalizadora y ninguna regla activa del "
            f'art. 82.1 la nombra → se abriría sin comprobar el fin de instrucción (#827)'
        )
    for codigo in sorted(finalizadoras - conocidas_por_emisor):
        avisos.append(
            f"TipoFase.codigo='{codigo}' es finalizadora y no está en el mapa de "
            f'cert_fin_instruccion → el certificado se auditaría contra otra fase (#827)'
        )
    return avisos


def _importar(modulo: str, clase: str):
    try:
        import importlib
        mod = importlib.import_module(modulo)
        return getattr(mod, clase, None)
    except Exception:
        return None
