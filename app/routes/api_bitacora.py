"""API del cuaderno de bitácora — endpoints para el dock global (#506)."""
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import text

from app import db
from app.models.bitacora import Bitacora

bp = Blueprint('api_bitacora', __name__, url_prefix='/api')

_ICONOS = {
    'ALTERAR': 'bi-pencil',
    'CREAR':   'bi-plus-circle',
    'BORRAR':  'bi-trash3',
}


def _descripcion(entrada):
    tabla   = entrada.tabla
    detalle = entrada.detalle or {}
    op      = entrada.operacion

    if tabla == 'expedientes':
        num = db.session.execute(
            text('SELECT numero_at FROM public.expedientes WHERE id = :id'),
            {'id': entrada.registro_id},
        ).scalar()
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
