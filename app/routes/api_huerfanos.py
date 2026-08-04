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
                "enlace": "...", "externo": false, "puede_abrir_carpeta": true, "abrir_en": "enlace"
            }, ...],
            "next_cursor": 5, "has_more": true
        }
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy import cast, String, or_

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.services.detalle_nodo import info_apertura_documento
from app.services.huerfanos import tareas_candidatas

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
        .filter(~Documento.url.like('bddat://%'))
        .filter(*filtros)
    )

    if cursor > 0:
        query = query.filter(Documento.id > cursor)

    query = query.order_by(Documento.id.asc())
    docs_raw = query.limit(limit + 1).all()

    has_more = len(docs_raw) > limit
    docs = docs_raw[:limit]
    next_cursor = docs[-1].id if docs else cursor

    data = []
    for doc in docs:
        expediente = doc.expediente
        responsable = expediente.responsable if expediente else None
        data.append({
            'id':                   doc.id,
            'expediente_id':        expediente.id if expediente else None,
            'num_at':               expediente.numero_at if expediente else None,
            'responsable':          {'id': responsable.id, 'siglas': responsable.siglas} if responsable else None,
            'tipo_doc':             doc.tipo_doc.nombre if doc.tipo_doc else None,
            'asunto':               doc.asunto,
            'nombre':               (doc.url or '').replace('\\', '/').rsplit('/', 1)[-1].split('?')[0].split('#')[0] or f'Documento {doc.id}',
            **info_apertura_documento(expediente.id, doc),
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
