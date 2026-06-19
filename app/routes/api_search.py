"""API de búsqueda para Command Palette (ADR-018 / #531).

ENDPOINTS:
    GET /api/search/expedientes?q=...&limit=10
    GET /api/search/entidades?q=...&limit=10
    GET /api/search/usuarios?q=...&limit=10   (#532: todos ven, edición aparte)
"""

from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required
from sqlalchemy import or_, case
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.proyectos import Proyecto
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.municipios import Municipio
from app.models.usuarios import Usuario

api_search_bp = Blueprint('api_search', __name__, url_prefix='/api/search')


def _parse_numero_at(q: str):
    """Devuelve el entero AT si q es '123' o 'AT-123'; None en caso contrario."""
    stripped = q.strip().upper()
    if stripped.startswith('AT-'):
        stripped = stripped[3:]
    try:
        return int(stripped)
    except ValueError:
        return None


@api_search_bp.route('/expedientes', methods=['GET'])
@login_required
def buscar_expedientes():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200

    try:
        limit = min(int(request.args.get('limit', 10)), 20)
    except ValueError:
        limit = 10

    num = _parse_numero_at(q)

    conditions = []
    if num is not None:
        conditions.append(Expediente.numero_at == num)
    conditions.append(
        Expediente.titular.has(Entidad.nombre_completo.ilike(f'%{q}%'))
    )
    conditions.append(
        Expediente.proyecto.has(Proyecto.titulo.ilike(f'%{q}%'))
    )
    conditions.append(
        Expediente.proyecto.has(
            Proyecto.municipios_afectados.any(
                MunicipioProyecto.municipio.has(
                    Municipio.nombre.ilike(f'%{q}%')
                )
            )
        )
    )

    sort_key = (
        case((Expediente.numero_at == num, 0), else_=1)
        if num is not None
        else Expediente.id
    )

    expedientes = (
        db.session.query(Expediente)
        .options(
            joinedload(Expediente.proyecto)
            .joinedload(Proyecto.municipios_afectados)
            .joinedload(MunicipioProyecto.municipio)
        )
        .filter(or_(*conditions))
        .order_by(sort_key, Expediente.id.asc())
        .limit(limit)
        .all()
    )

    results = []
    for exp in expedientes:
        label = (
            f'AT-{exp.numero_at} — {exp.proyecto.titulo}'
            if exp.proyecto
            else f'AT-{exp.numero_at}'
        )

        titular_nombre = exp.titular.nombre_completo if exp.titular else ''
        primer_mun = (
            exp.proyecto.municipios_afectados[0].municipio
            if exp.proyecto and exp.proyecto.municipios_afectados
            else None
        )
        breadcrumb = (
            f'{titular_nombre} · {primer_mun.nombre}'
            if titular_nombre and primer_mun
            else titular_nombre
        )

        results.append({
            'tipo': 'expediente',
            'id': exp.id,
            'label': label,
            'breadcrumb': breadcrumb,
            'url': url_for('expedientes.arbol', id=exp.id),
        })

    return jsonify({'results': results}), 200


@api_search_bp.route('/entidades', methods=['GET'])
@login_required
def buscar_entidades():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200

    try:
        limit = min(int(request.args.get('limit', 10)), 20)
    except ValueError:
        limit = 10

    entidades = (
        Entidad.query
        .filter(
            Entidad.activo == True,
            or_(
                Entidad.nombre_completo.ilike(f'%{q}%'),
                Entidad.nif.ilike(f'%{q}%'),
            ),
        )
        .order_by(Entidad.nombre_completo.asc())
        .limit(limit)
        .all()
    )

    results = [
        {
            'tipo': 'entidad',
            'id': e.id,
            'label': e.nombre_completo,
            'breadcrumb': e.nif or '',
            'url': url_for('entidades.index', sel=e.id),
        }
        for e in entidades
    ]

    return jsonify({'results': results}), 200


@api_search_bp.route('/usuarios', methods=['GET'])
@login_required
@require_permiso('acceder_usuarios')
def buscar_usuarios():
    # Todos los roles tienen 'acceder_usuarios' (ven la ficha); la edición se
    # protege aparte con 'gestionar_usuarios'. Aquí solo se localiza/navega.
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200

    try:
        limit = min(int(request.args.get('limit', 10)), 20)
    except ValueError:
        limit = 10

    usuarios = (
        Usuario.query
        .filter(
            Usuario.activo == True,
            or_(
                Usuario.siglas.ilike(f'%{q}%'),
                Usuario.nombre.ilike(f'%{q}%'),
                Usuario.apellido1.ilike(f'%{q}%'),
                Usuario.apellido2.ilike(f'%{q}%'),
            ),
        )
        .order_by(Usuario.apellido1.asc(), Usuario.nombre.asc())
        .limit(limit)
        .all()
    )

    results = []
    for u in usuarios:
        nombre_completo = ' '.join(p for p in [u.nombre, u.apellido1, u.apellido2] if p)
        roles = ' / '.join(r.nombre for r in u.roles) if u.roles else ''
        breadcrumb = f'{u.siglas} · {roles}' if roles else u.siglas
        results.append({
            'tipo': 'usuario',
            'id': u.id,
            'label': nombre_completo or u.siglas,
            'breadcrumb': breadcrumb,
            'url': url_for('usuarios.detalle', id=u.id),
        })

    return jsonify({'results': results}), 200
