"""
Carpeta ESFTT (Expediente-Solicitud-Fase-Trámite-Tarea) legible de un documento
(ADR-032 §3, #665).

Hoy la usa solo el manifiesto (ADR-050 §H): es la carpeta en la que el exportador
reconstruye cada documento. El movimiento de ficheros al vincular y el nombrado
del pool en disco salieron con el modelo de rutas (#1007, PR 5): el contenido vive
en el almacén y vincular no mueve nada.
"""
import re

from app.models.documentos import Documento
from app.models.tareas import Tarea

# Caracteres no válidos en nombres de carpeta Windows (mismo patrón que generador_escritos.py),
# incluidos los de control (0-31), como en el saneado de nombres de fichero.
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
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

    Numerado por `organismo_expediente_id`, no por el id de la fila TramiteOrganismo
    (#396 bloque 7): varios trámites del mismo organismo comparten organismo_expediente_id,
    así que caen en la misma carpeta — antes cada uno abría una carpeta distinta.

    None si el trámite no tiene TramiteOrganismo asociado (caso general).
    """
    from app.models.tramites_organismos import TramiteOrganismo
    vinculo = TramiteOrganismo.query.filter_by(tramite_id=tramite.id).first()
    if vinculo is None:
        return None
    return _segmento(vinculo.organismo_expediente_id,
                      _texto_organismo(vinculo.organismo_expediente.organismo))


def ruta_esftt_documento(documento_o_tarea) -> str:
    """
    Calcula la carpeta ESFTT legible (`AT-N/…`, sin nombre de fichero) que le toca
    a un documento, derivada de los códigos inmutables de catálogo
    (tipos_fases.codigo, tipos_tramites.codigo, tipos_tareas.codigo) y las siglas
    de tipos_solicitudes. Es relativa a la raíz del árbol legible que reconstruye
    el exportador a partir del manifiesto (ADR-050 §H).

    Acepta:
    - Tarea: construye la ruta directamente a partir de tarea.tramite.fase.solicitud.
    - Documento: resuelve la tarea "propietaria" por su primera vinculación
      (menor id en documentos_tarea) — la primera vinculación fija la carpeta,
      ADR-032 §3. Lanza ValueError si el documento no tiene ninguna vinculación
      (aún huérfano: el manifiesto lo pone en `AT-N/pool`).
    """
    if isinstance(documento_o_tarea, Documento):
        vinculos = sorted(documento_o_tarea.vinculos_tarea, key=lambda v: v.id)
        if not vinculos:
            raise ValueError(
                f'Documento id={documento_o_tarea.id} no tiene ninguna tarea vinculada: '
                'aún no tiene carpeta ESFTT (huérfano, va a AT-N/pool)'
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
