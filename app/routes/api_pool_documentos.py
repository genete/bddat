"""API REST del listado del pool de documentos de un expediente (#881, ADR-053 §F).

ENDPOINT:
    GET /api/expedientes/<id>/documentos — una página del pool, con cursor (scroll infinito).

    Params:
        cursor     (int, default 0)   — `id` del último documento recibido; 0 = desde arriba
        limit      (int, default 50, máx. 100)
        search     (str, opcional)    — texto en el nombre o en el asunto
        ext        (str, opcional)    — extensión del nombre (`pdf`)
        tipo       (int, opcional)    — `tipo_doc_id`
        prioridad  (str, opcional)    — `1` prioritarios · `0` no prioritarios

    Respuesta JSON: `{data, next_cursor, has_more, total}`. Cada fila es la fila común de
    ADR-053 §E (`detalle_nodo.documento_fila`) más `extension`, `n_usos` y `usos`
    (`[{codigo, texto}]`: qué usa el documento, ver `services/usos_documento.py`).

    Es otro contrato que `GET /api/expedientes/<id>/pool` (el pool entero, de una vez, que
    necesitan la Despensa y los editores del árbol): este es el listado paginado de la página.
    Orden, filtros y la regla de nombre y extensión: `services/listado_pool.py`.

    A diferencia de los listados de catálogo, `search` no exige un mínimo de caracteres: la
    regla de los dos caracteres protege tablas grandes y el pool de un expediente es acotado.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.models.expedientes import Expediente
from app.services.listado_pool import (
    LIMITE_MAXIMO, LIMITE_POR_DEFECTO, PRIORIDADES, pagina_pool,
)
from app.utils.permisos import verificar_acceso_expediente

api_pool_documentos_bp = Blueprint('api_pool_documentos', __name__, url_prefix='/api')


@api_pool_documentos_bp.route('/expedientes/<int:expediente_id>/documentos', methods=['GET'])
@login_required
def listar_documentos(expediente_id):
    """GET /api/expedientes/<id>/documentos — una página del pool del expediente."""
    expediente = Expediente.query.get_or_404(expediente_id)
    denegado = verificar_acceso_expediente(expediente)
    if denegado:
        return denegado

    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'cursor debe ser >= 0'}), 400
        limit = int(request.args.get('limit', LIMITE_POR_DEFECTO))
        if limit < 1:
            return jsonify({'error': 'limit debe ser >= 1'}), 400
        limit = min(limit, LIMITE_MAXIMO)
        tipo_raw = request.args.get('tipo', '').strip()
        tipo = int(tipo_raw) if tipo_raw else None
    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    prioridad = request.args.get('prioridad', '').strip()
    if prioridad not in PRIORIDADES:
        return jsonify({'error': "prioridad debe ser '1' o '0'"}), 400

    return jsonify(pagina_pool(
        expediente.id,
        cursor=cursor,
        limit=limit,
        search=request.args.get('search', '').strip(),
        ext=request.args.get('ext', '').strip().lstrip('.'),
        tipo=tipo,
        prioridad=prioridad,
    ))
