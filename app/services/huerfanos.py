"""Servicio de candidatas del radar de huérfanos (#630, ADR-038 §4).

Usa `tramites_tareas_documentos` (catálogo de tipo de documento admisible por
`(tipo_tramite, orden_tarea, rol)`) — hasta ahora solo editado desde
`tablas_maestras`, nunca consultado en runtime. `Tarea` no persiste `orden`
(solo `tramite_id` + `tipo_tarea_id`), así que no se desambigua el slot
exacto cuando un mismo tipo de tarea se repite en el trámite (p.ej. doble
ESPERAR_PLAZO de ANUNCIO_BOE) — decisión de v1 (ADR-038 §4, opción B):
cubre la mayoría de trámites reales; el caso doble-slot da candidatas algo
menos precisas, nunca incorrectas.

Reglas de exclusión por seguridad (ADR-038 §4): sustituir un PRODUCIDO
dispara consecuencias encadenadas (hooks, ADR-033 §5) mientras que añadir un
CONSUMIDO es aditivo — por eso el filtro es distinto por rol.
"""
from app import db
from app.models.tareas import Tarea
from app.models.tramites import Tramite
from app.models.fases import Fase
from app.models.solicitudes import Solicitud
from app.models.tramites_tareas import TramiteTarea
from app.models.tramites_tareas_documentos import TramiteTareaDocumento


def tareas_candidatas(documento) -> list[dict]:
    """Tareas del mismo expediente candidatas a recibir `documento` (huérfano).

    Devuelve una lista de {tarea_id, tramite_nombre, tarea_nombre, rol,
    coincidencia}, `rol` ∈ {'CONSUMIDO', 'PRODUCIDO'} — una misma tarea puede
    aparecer dos veces si admite ambos roles. `coincidencia` ∈ {'exacta',
    'polimorfica'} — exacta si el catálogo fija el tipo de documento,
    polimórfica si el slot admite cualquier tipo (tipo_documento_id NULL).
    """
    tareas = (
        Tarea.query
        .join(Tramite, Tarea.tramite_id == Tramite.id)
        .join(Fase, Tramite.fase_id == Fase.id)
        .join(Solicitud, Fase.solicitud_id == Solicitud.id)
        .filter(Solicitud.expediente_id == documento.expediente_id)
        .all()
    )
    if not tareas:
        return []

    tipos_tramite_ids = {t.tramite.tipo_tramite_id for t in tareas}

    slots = (
        TramiteTarea.query
        .filter(TramiteTarea.tipo_tramite_id.in_(tipos_tramite_ids))
        .all()
    )
    # (tipo_tramite_id, orden) → tipo_tarea_id
    orden_a_tipo_tarea = {(s.tipo_tramite_id, s.orden): s.tipo_tarea_id for s in slots}

    catalogo = (
        TramiteTareaDocumento.query
        .filter(TramiteTareaDocumento.tipo_tramite_id.in_(tipos_tramite_ids))
        .filter(db.or_(
            TramiteTareaDocumento.tipo_documento_id == documento.tipo_doc_id,
            TramiteTareaDocumento.tipo_documento_id.is_(None),
        ))
        .all()
    )

    # (tipo_tramite_id, tipo_tarea_id, rol_catalogo) → 'exacta' | 'polimorfica'
    # Si hay slots exacto y polimórfico para la misma clave, gana 'exacta'.
    admite: dict[tuple, str] = {}
    for fila in catalogo:
        tipo_tarea_id = orden_a_tipo_tarea.get((fila.tipo_tramite_id, fila.orden_tarea))
        if tipo_tarea_id is None:
            continue
        clave = (fila.tipo_tramite_id, tipo_tarea_id, fila.rol)
        coincidencia = 'exacta' if fila.tipo_documento_id is not None else 'polimorfica'
        if admite.get(clave) != 'exacta':
            admite[clave] = coincidencia

    candidatas = []
    for tarea in tareas:
        tipo_tramite_id = tarea.tramite.tipo_tramite_id

        clave_entrada = (tipo_tramite_id, tarea.tipo_tarea_id, 'ENTRADA')
        if clave_entrada in admite and not tarea.ejecutada:
            candidatas.append({
                'tarea_id':       tarea.id,
                'tramite_nombre': tarea.tramite.tipo_tramite.nombre,
                'tarea_nombre':   tarea.tipo_tarea.nombre,
                'rol':            'CONSUMIDO',
                'coincidencia':   admite[clave_entrada],
            })

        clave_salida = (tipo_tramite_id, tarea.tipo_tarea_id, 'SALIDA')
        if clave_salida in admite and tarea.documento_producido is None:
            candidatas.append({
                'tarea_id':       tarea.id,
                'tramite_nombre': tarea.tramite.tipo_tramite.nombre,
                'tarea_nombre':   tarea.tipo_tarea.nombre,
                'rol':            'PRODUCIDO',
                'coincidencia':   admite[clave_salida],
            })

    # Exactas primero, luego polimórficas — dentro de cada grupo, orden estable de tarea.id
    candidatas.sort(key=lambda c: (c['coincidencia'] != 'exacta', c['tarea_id']))
    return candidatas
