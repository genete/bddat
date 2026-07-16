"""
Servicio de cálculo de rutas ESFTT (Expediente-Solicitud-Fase-Trámite-Tarea) y de
la carpeta de entrada al pool (ADR-032 §4, #665).

Solo calcula rutas — no crea directorios ESFTT ni mueve ficheros. El movimiento
físico real al vincularse un documento a una tarea es #667.
"""
import os
import re

from app.models.documentos import Documento
from app.models.tareas import Tarea

# Caracteres no válidos en nombres de carpeta Windows (mismo patrón que generador_escritos.py)
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')
_LONGITUD_MAX_FALLBACK_ORGANISMO = 30


def _segmento(instancia_id: int, codigo: str) -> str:
    """Segmento de ruta con prefijo determinista del id de la instancia.

    Evita colisión cuando el mismo código de catálogo se repite en el mismo nivel
    (doble ESPERAR_PLAZO en un trámite, trámite repetido en una fase, fase repetida
    en una solicitud) y, al ser el id autoincremental, ordena el directorio en el
    mismo orden en que se crearon las instancias.
    """
    return f'{instancia_id:06d}_{codigo}'


def _texto_organismo(entidad) -> str:
    """Texto del segmento organismo: abrev si está relleno, si no nombre_completo
    saneado (dato histórico sin backfill de abrev — nunca falla solo por esto)."""
    texto = (entidad.abrev or entidad.nombre_completo or '').strip()
    texto = _CARACTERES_INVALIDOS.sub('_', texto)
    return texto[:_LONGITUD_MAX_FALLBACK_ORGANISMO]


def _segmento_organismo(tramite) -> str | None:
    """Segmento adicional para trámites ligados a un organismo (CONSULTA_SEPARATA,
    CONSULTA_TRASLADO_TITULAR, CONSULTA_TRASLADO_ORGANISMO — ADR-011). Varios de
    estos trámites pueden coexistir en paralelo en la misma fase, uno por organismo
    consultado; el código de trámite por sí solo no los distingue.

    None si el trámite no tiene TramiteOrganismo asociado (caso general).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    vinculo = TramiteOrganismo.query.filter_by(tramite_id=tramite.id).first()
    if vinculo is None:
        return None
    return _segmento(vinculo.id, _texto_organismo(vinculo.organismo_expediente.organismo))


def ruta_esftt_documento(documento_o_tarea) -> str:
    """
    Calcula la ruta ESFTT legible (relativa a FILESYSTEM_BASE, sin nombre de
    fichero) donde debe vivir un documento, derivada de los códigos inmutables de
    catálogo (tipos_fases.codigo, tipos_tramites.codigo, tipos_tareas.codigo) y las
    siglas de tipos_solicitudes.

    Acepta:
    - Tarea: construye la ruta directamente a partir de tarea.tramite.fase.solicitud
      (punto de entrada natural cuando #667 mueva un documento al vincularse).
    - Documento: resuelve la tarea "propietaria" por su primera vinculación
      (menor id en documentos_tarea) — la primera vinculación fija la ubicación,
      ADR-032 §3. Lanza ValueError si el documento no tiene ninguna vinculación
      (aún huérfano en el pool, sin destino ESFTT).
    """
    if isinstance(documento_o_tarea, Documento):
        vinculos = sorted(documento_o_tarea.vinculos_tarea, key=lambda v: v.id)
        if not vinculos:
            raise ValueError(
                f'Documento id={documento_o_tarea.id} no tiene ninguna tarea vinculada: '
                'aún no tiene destino ESFTT (usar ruta_pool_documento mientras esté huérfano)'
            )
        tarea = vinculos[0].tarea
    elif isinstance(documento_o_tarea, Tarea):
        tarea = documento_o_tarea
    else:
        raise TypeError(
            f'ruta_esftt_documento espera Documento o Tarea, recibido {type(documento_o_tarea)!r}'
        )

    tramite = tarea.tramite
    fase = tramite.fase
    solicitud = fase.solicitud
    expediente = solicitud.expediente

    segmentos = [
        f'AT-{expediente.numero_at}',
        _segmento(solicitud.id, solicitud.tipo_solicitud.siglas),
        _segmento(fase.id, fase.tipo_fase.codigo),
    ]

    segmento_organismo = _segmento_organismo(tramite)
    if segmento_organismo is not None:
        segmentos.append(segmento_organismo)

    segmentos.append(_segmento(tramite.id, tramite.tipo_tramite.codigo))
    segmentos.append(_segmento(tarea.id, tarea.tipo_tarea.codigo))

    return '/'.join(segmentos)


def ruta_pool_documento(expediente) -> str:
    """
    Ruta absoluta de la carpeta pool/ del expediente (AT-N/pool, landing zone física
    de documentos huérfanos — ADR-032 §1/§4). Crea el directorio si no existe
    (mismo patrón que ruta_destino_documento en generador_escritos.py).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    directorio = os.path.join(base, f'AT-{expediente.numero_at}', 'pool')
    os.makedirs(directorio, exist_ok=True)

    return directorio
