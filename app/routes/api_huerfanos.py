"""API REST del radar de documentos huérfanos (#630, ADR-038).

Huérfano = Documento del pool sin ninguna fila en DOCUMENTOS_TAREA **y** con
esquema de fichero real, no bddat:// (ADR-027 §2: "El huérfano es siempre un
fichero" — los registros internos, diagnósticos y certificados, quedan
excluidos por definición, no solo porque nazcan vinculados por construcción.
La BD de desarrollo tiene residuos previos a esa salvaguarda —diagnósticos sin
vínculo por datos antiguos, no por un huérfano real— así que el filtro de
esquema es necesario en la consulta, no redundante).

ENDPOINT:
    GET /api/documentos/huerfanos — Listado paginado de documentos huérfanos.

    Params:
        cursor          (int, default 0)
        limit           (int, default 50, max 100)
        ver             (str, "mis"|"todos") — solo aplica a TRAMITADOR
        responsable_id  (int, opcional)      — solo aplica a SUPERVISOR/ADMIN/ADMINISTRATIVO
        search          (str, opcional)      — nº AT o titular

    Respuesta JSON — ver ADR-038 §3 (dato crudo, el render por rol lo decide el cliente):
        {
            "data": [{
                "id": 1, "expediente_id": 5, "num_at": 1234,
                "responsable": {"id": 3, "siglas": "CLG"} | null,
                "tipo_doc": "Alegación", "asunto": "...", "nombre": "fichero.pdf",
                "enlace": "...", "externo": false, "puede_abrir": true, "abrir_en": "enlace",
                "n_usos": 1, "usos": [{"codigo": "SOLICITUD", "texto": "Escrito de la solicitud AAP #3"}]
            }, ...],
            "next_cursor": 5, "has_more": true
        }

    DESTINO DECLARADO SIN TAREA (#881). Huérfano sigue significando «sin vínculo a tarea», pero un
    documento puede no tener tarea y sí estar referenciado por otra cosa: el escrito que ancla una
    solicitud, el proyecto principal, el corte de un reformado, un interesado al que acredita… Ese
    documento tiene destino, solo que ninguna tarea lo ha consumido todavía (el principal y los
    reformados esperan al ANALIZAR que los consuma). No sale del radar —si ninguna tarea llega a
    consumirlo, el recordatorio sigue haciendo falta— pero va marcado: `usos` dice qué lo referencia
    (`services/usos_documento.py`, el mismo registro que la columna de usos del pool) y el radar lo
    enseña. Sin usos, `n_usos` es 0 y es un documento del que nadie sabe nada.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import cast, String, or_

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.services.detalle_nodo import documento_fila, opciones_fila_documento
from app.services.huerfanos import tareas_candidatas
from app.services.usos_documento import opciones_usos_documento, usos_de_documentos

api_huerfanos_bp = Blueprint('api_huerfanos', __name__, url_prefix='/api')


@api_huerfanos_bp.route('/documentos/huerfanos', methods=['GET'])
@login_required
def listar_huerfanos():
    """GET /api/documentos/huerfanos — listado paginado de documentos sin vínculo a tarea."""
    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'cursor debe ser >= 0'}), 400
        limit = int(request.args.get('limit', 50))
        limit = min(max(limit, 1), 100)
    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    ver = request.args.get('ver', '').strip()
    search = request.args.get('search', '').strip()
    responsable_id_raw = request.args.get('responsable_id', '').strip()

    rol_activo = session.get('rol_activo_nombre')

    filtros = []
    if rol_activo == 'TRAMITADOR':
        # Solo TRAMITADOR puede ser responsable de expediente — 'mis' es el
        # default real para este rol (ADR-038 §3).
        if ver != 'todos':
            filtros.append(Expediente.responsable_id == current_user.id)
    elif responsable_id_raw:
        try:
            filtros.append(Expediente.responsable_id == int(responsable_id_raw))
        except ValueError:
            return jsonify({'error': 'responsable_id debe ser entero'}), 400

    if search:
        num_at_str = search.upper().removeprefix('AT-').removeprefix('AT')
        filtros.append(or_(
            cast(Expediente.numero_at, String).ilike(f'%{num_at_str}%'),
            Entidad.nombre_completo.ilike(f'%{search}%'),
        ))

    query = (
        db.session.query(Documento)
        .join(Expediente, Documento.expediente_id == Expediente.id)
        .join(Entidad, Expediente.titular_id == Entidad.id, isouter=True)
        .outerjoin(DocumentoTarea, DocumentoTarea.documento_id == Documento.id)
        .filter(DocumentoTarea.id.is_(None))
        # url NULL = contenido propio en el almacén (ADR-050): sin el IS NULL, el
        # NOT LIKE da NULL y el documento sale del radar sin ningún aviso.
        .filter(or_(Documento.url.is_(None), ~Documento.url.like('bddat://%')))
        .filter(*filtros)
        .options(*opciones_fila_documento(), *opciones_usos_documento())
    )

    if cursor > 0:
        query = query.filter(Documento.id > cursor)

    query = query.order_by(Documento.id.asc())
    docs_raw = query.limit(limit + 1).all()

    has_more = len(docs_raw) > limit
    docs = docs_raw[:limit]
    next_cursor = docs[-1].id if docs else cursor
    # Lo que referencia a cada documento, de una vez para toda la página (#881).
    usos = usos_de_documentos(docs)

    data = []
    for doc in docs:
        expediente = doc.expediente
        responsable = expediente.responsable if expediente else None
        data.append({
            # Lo propio del radar (el expediente y su responsable) y, para el documento, la fila
            # común (`documento_fila`, ADR-053 §E) más sus usos: un documento sin tarea pero con
            # destino declarado va marcado, no excluido.
            'expediente_id':        expediente.id if expediente else None,
            'num_at':               expediente.numero_at if expediente else None,
            'responsable':          {'id': responsable.id, 'siglas': responsable.siglas} if responsable else None,
            **documento_fila(expediente.id, doc, estricto=False),
            'n_usos':               len(usos[doc.id]),
            'usos':                 usos[doc.id],
        })

    return jsonify({
        'data':        data,
        'next_cursor': next_cursor,
        'has_more':    has_more,
    })


@api_huerfanos_bp.route('/documentos/<int:documento_id>/candidatas', methods=['GET'])
@login_required
def candidatas_huerfano(documento_id):
    """GET /api/documentos/<id>/candidatas — tareas candidatas a recibir el huérfano.

    Ver app/services/huerfanos.py — reglas de inferencia y exclusión (ADR-038 §4).
    """
    doc = Documento.query.get_or_404(documento_id)
    es_huerfano = (
        not (doc.url or '').startswith('bddat://')
        and DocumentoTarea.query.filter_by(documento_id=doc.id).first() is None
    )
    if not es_huerfano:
        return jsonify({'error': 'El documento ya no es huérfano'}), 409
    return jsonify({'data': tareas_candidatas(doc)}), 200
