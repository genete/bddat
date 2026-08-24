"""Servicio de sugerencia de tipo de documento y asunto para subida inline
desde la Despensa (#367).

Gemelo de `tareas_candidatas()` (app/services/huerfanos.py, ADR-038 §4), pero
resuelve el problema inverso: dada una tarea, qué tipo de documento se espera
en los roles todavía disponibles — en vez de, dado un documento, qué tareas lo
aceptan. Comparte el mismo catálogo (`tramites_tareas_documentos`, #346) y la
misma limitación conocida y aceptada en ADR-038 §4: `Tarea` no persiste
`orden`, así que si un mismo tipo de tarea se repite en el trámite (p. ej.
doble ESPERAR_PLAZO de ANUNCIO_BOE) la resolución es por tipo de tarea, no por
slot exacto. Con más de un tipo exacto candidato tras ese agrupamiento, se
declara ambiguo y no se sugiere nada — nunca se sugiere algo incorrecto.
"""
from app.models.tramites_tareas import TramiteTarea
from app.models.tramites_tareas_documentos import TramiteTareaDocumento
from app.models.tipos_documentos import TipoDocumento


def sugerencia_subida(tarea) -> dict:
    """Sugerencia de {tipo_doc_id, asunto} para subir un documento nuevo
    desde la Despensa de `tarea` (#367). Solo lectura, no crea ni vincula nada.

    Devuelve {'tipo_doc_id': None, 'asunto': None} si no hay una única
    coincidencia exacta en el catálogo para los roles con hueco libre en esta
    tarea (ambigüedad, solo polimórfico, o catálogo sin filas para este
    trámite/tarea) — el formulario de subida queda entonces en blanco, igual
    que hoy en el pool.
    """
    tipo_tramite_id = tarea.tramite.tipo_tramite_id
    tipo_tarea_id = tarea.tipo_tarea_id

    ordenes = [
        s.orden for s in TramiteTarea.query.filter_by(
            tipo_tramite_id=tipo_tramite_id, tipo_tarea_id=tipo_tarea_id,
        ).all()
    ]
    if not ordenes:
        return {'tipo_doc_id': None, 'asunto': None}

    # Mismas reglas de exclusión por seguridad que tareas_candidatas()
    # (ADR-038 §4): sustituir un PRODUCIDO dispara consecuencias encadenadas
    # (hooks, ADR-033 §5); añadir un CONSUMIDO es aditivo.
    roles_disponibles = set()
    if not tarea.ejecutada:
        roles_disponibles.add('ENTRADA')
    if tarea.documento_producido is None:
        roles_disponibles.add('SALIDA')

    if not roles_disponibles:
        return {'tipo_doc_id': None, 'asunto': None}

    catalogo = (
        TramiteTareaDocumento.query
        .filter(TramiteTareaDocumento.tipo_tramite_id == tipo_tramite_id)
        .filter(TramiteTareaDocumento.orden_tarea.in_(ordenes))
        .filter(TramiteTareaDocumento.rol.in_(roles_disponibles))
        .filter(TramiteTareaDocumento.tipo_documento_id.isnot(None))  # solo exactas
        .all()
    )

    tipos_exactos = {fila.tipo_documento_id for fila in catalogo}

    if len(tipos_exactos) != 1:
        return {'tipo_doc_id': None, 'asunto': None}

    tipo_doc_id = next(iter(tipos_exactos))
    tipo_doc = TipoDocumento.query.get(tipo_doc_id)
    if tipo_doc is None:
        return {'tipo_doc_id': None, 'asunto': None}

    asunto = f'{tipo_doc.nombre} - {tarea.tramite.tipo_tramite.nombre}'
    return {'tipo_doc_id': tipo_doc_id, 'asunto': asunto}
