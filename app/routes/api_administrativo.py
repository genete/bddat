"""API de la vista "Mi trabajo" del administrativo (#501, ADR-017).

ENDPOINT:
    GET /api/administrativo/cola — Cola transversal de tareas administrativas
        pendientes (NOTIFICAR / ELABORAR / ESPERAR_PLAZO no finalizadas), con
        contexto por fila y paginación por cursor.

        Params:
            cursor             (int, default 0)            — Paginación por Tarea.id
            limit              (int, default 50, max 100)  — Filas por página
            search             (str, opcional)             — Nº AT / titular
            tipo_expediente_id (int, opcional)             — Filtra por tipo de expediente
            pendiente          (str, opcional)             — Código de estado de dominio
            plazo              (str, opcional)             — vencido|hoy|semana|sin_plazo

        Respuesta: {'data': [...], 'next_cursor': int, 'has_more': bool}

La SUBIDA de documentos NO tiene endpoint propio: reutiliza el flujo del pool ya
existente (expedientes.pool_registrar_rutas / pool_registrar_url_externa), abierto
a todos los roles vía permiso 'subir_documento' (ADR-027 / #501).

La cola es visible para todos los roles (ADR-013): solo requiere sesión.
"""
import logging

from flask import Blueprint, request, jsonify
from flask_login import login_required

from app.services.cola_administrativo import construir_cola

api_administrativo_bp = Blueprint('api_administrativo', __name__, url_prefix='/api/administrativo')

log = logging.getLogger(__name__)


@api_administrativo_bp.route('/cola', methods=['GET'])
@login_required
def cola():
    """Página de la cola de trabajo administrativo (ADR-017 §2)."""
    try:
        cursor = int(request.args.get('cursor', 0))
        if cursor < 0:
            return jsonify({'error': 'cursor debe ser >= 0'}), 400
        limit = int(request.args.get('limit', 50))
    except ValueError:
        return jsonify({'error': 'Parámetros numéricos inválidos'}), 400

    filtros = {
        'search':    request.args.get('search', '').strip(),
        'pendiente': request.args.get('pendiente', '').strip() or None,
        'plazo':     request.args.get('plazo', '').strip() or None,
    }

    tipo_exp_raw = request.args.get('tipo_expediente_id', '').strip()
    if tipo_exp_raw:
        try:
            filtros['tipo_expediente_id'] = int(tipo_exp_raw)
        except ValueError:
            return jsonify({'error': 'tipo_expediente_id debe ser entero'}), 400

    resultado = construir_cola(cursor=cursor, limit=limit, filtros=filtros)
    return jsonify(resultado)
