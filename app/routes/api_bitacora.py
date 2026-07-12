"""API del cuaderno de bitácora — endpoints para el dock global (#506)."""
import logging

from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import text

from app import db
from app.models.bitacora import Bitacora

log = logging.getLogger(__name__)

bp = Blueprint('api_bitacora', __name__, url_prefix='/api')

_ICONOS = {
    'ALTERAR': 'bi-pencil',
    'CREAR':   'bi-plus-circle',
    'BORRAR':  'bi-trash3',
}

_VERBOS_OP = {'CREAR': 'creación', 'BORRAR': 'borrado'}


def _descripcion(entrada):
    tabla   = entrada.tabla
    detalle = entrada.detalle or {}
    op      = entrada.operacion

    # Vía de escape del motor (#324/#616): mutaciones_arbol.py y api_bc.py graban
    # {escape, justificacion, sujeto} en detalle para CREAR/BORRAR en cualquier
    # tabla — priorizar sobre el genérico para que la justificación sea visible.
    if detalle.get('escape'):
        sujeto = detalle.get('sujeto') or f'{tabla} #{entrada.registro_id}'
        verbo = _VERBOS_OP.get(op, op.lower())
        justificacion = detalle.get('justificacion')
        return f'Forzó {verbo} de {sujeto} — {justificacion}' if justificacion else f'Forzó {verbo} de {sujeto}'

    # Creación permitida con advertencia (#616 feedback): mismo criterio que el
    # escape pero sin justificación — la crea el motor, solo avisa.
    if detalle.get('advertencia'):
        sujeto = detalle.get('sujeto') or f'{tabla} #{entrada.registro_id}'
        verbo = _VERBOS_OP.get(op, op.lower()).capitalize()
        motivo = detalle.get('motivo')
        return f'{verbo} con advertencia de {sujeto} — {motivo}' if motivo else f'{verbo} con advertencia de {sujeto}'

    if tabla == 'expedientes':
        try:
            num = db.session.execute(
                text('SELECT numero_at FROM public.expedientes WHERE id = :id'),
                {'id': entrada.registro_id},
            ).scalar()
        except Exception:
            log.exception('_descripcion: fallo al resolver expediente id=%s', entrada.registro_id)
            num = None
        ref = f'AT-{num}' if num else f'#{entrada.registro_id}'
        if detalle.get('actuacion_fuera_asignacion'):
            return f'Actuó fuera de asignación en {ref}'
        if detalle.get('accion') == 'editar':
            return f'Editó expediente {ref}'
        return f'{op.capitalize()} expediente {ref}'

    return f'{op.capitalize()} en {tabla} #{entrada.registro_id}'


@bp.route('/bitacora/reciente')
@login_required
def bitacora_reciente():
    try:
        entradas = (
            Bitacora.query
            .filter_by(usuario_id=current_user.id)
            .order_by(Bitacora.created_at.desc())
            .limit(50)
            .all()
        )
        return jsonify([
            {
                'hora':        e.created_at.strftime('%H:%M'),
                'icono':       _ICONOS.get(e.operacion, 'bi-circle'),
                'descripcion': _descripcion(e),
            }
            for e in entradas
        ])
    except Exception:
        log.exception('bitacora_reciente: error inesperado para usuario_id=%s', current_user.id)
        return jsonify({'error': 'Error interno'}), 500
