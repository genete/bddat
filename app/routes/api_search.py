"""API de búsqueda para el Command Palette (ADR-018 / #531, #532).

ENDPOINT ACTUAL (recomendado):
    GET /api/search?q=...&tipos=expedientes,entidades,usuarios,plantillas&limit=10
        Búsqueda unificada multi-entidad. Devuelve {'grupos': [{tipo, resultados}]}
        en el orden de `tipos`, saltando los tipos cuyo permiso no tenga el rol
        activo (igual que el sidebar). Cada tipo aporta hasta `limit` resultados.

ENDPOINTS POR-ENTIDAD (transitorios, #532 fase 1):
    GET /api/search/expedientes?q=...&limit=10
    GET /api/search/entidades?q=...&limit=10
    GET /api/search/usuarios?q=...&limit=10
        Se conservan como respaldo hasta verificar el unificado en vivo; comparten
        la misma lógica (helpers _buscar_*), así que no hay deriva. Se retiran en
        la fase 2 cuando el unificado quede validado. NO añadir nuevos aquí:
        las entidades nuevas (p. ej. plantillas) entran solo en el registro.

Añadir una entidad buscable = un helper _buscar_X(q, limit) + una línea en BUSCADORES.
"""

from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required
from sqlalchemy import or_, case
from sqlalchemy.orm import joinedload

from app import db
from app.models.expedientes import Expediente
from app.models.entidad import Entidad
from app.models.proyectos import Proyecto
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.municipios import Municipio
from app.models.usuarios import Usuario
from app.models.plantillas import Plantilla
from app.utils.permisos import tiene_permiso

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


def _limit_param():
    """Tope de resultados por tipo: entre 1 y 20, por defecto 10."""
    try:
        return min(int(request.args.get('limit', 10)), 20)
    except ValueError:
        return 10


# ---------------------------------------------------------------------------
# Helpers de búsqueda por entidad. Cada uno recibe (q, limit) ya validados y
# devuelve la lista normalizada de resultados {tipo, id, label, breadcrumb, url}.
# Los consumen tanto las rutas por-entidad como el endpoint unificado.
# ---------------------------------------------------------------------------

def _buscar_expedientes(q, limit):
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

    return results


def _buscar_entidades(q, limit):
    # Sin filtro de activo: el palette busca TODO (como los listados, que muestran
    # activos e inactivos por defecto). Decisión #532.
    entidades = (
        Entidad.query
        .filter(
            or_(
                Entidad.nombre_completo.ilike(f'%{q}%'),
                Entidad.nif.ilike(f'%{q}%'),
            ),
        )
        .order_by(Entidad.nombre_completo.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            'tipo': 'entidad',
            'id': e.id,
            'label': e.nombre_completo,
            'breadcrumb': e.nif or '',
            'url': url_for('entidades.index', sel=e.id),
        }
        for e in entidades
    ]


def _buscar_usuarios(q, limit):
    # Todos los roles tienen 'acceder_usuarios' (ven la ficha); la edición se
    # protege aparte con 'gestionar_usuarios'. Aquí solo se localiza/navega.
    # Sin filtro de activo: el palette busca TODO (incluye usuarios desactivados).
    usuarios = (
        Usuario.query
        .filter(
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
            # Directo al listado con el inspector abierto (ADR-023): el detalle
            # solo redirige aquí. Coherente con entidades/plantillas.
            'url': url_for('usuarios.index', sel=u.id),
        })

    return results


def _buscar_plantillas(q, limit):
    # acceder_plantillas es de todos los roles (localizar); gestionar_plantillas
    # (editar) sigue en ADMIN/SUPERVISOR, sin tocar.
    # Sin filtro de activo: el palette busca TODO (incluye plantillas inactivas,
    # "ocultas en ELABORAR pero conservadas"; localizar para gestionar es válido).
    plantillas = (
        Plantilla.query
        .filter(
            or_(
                Plantilla.nombre.ilike(f'%{q}%'),
                Plantilla.codigo.ilike(f'%{q}%'),
                Plantilla.descripcion.ilike(f'%{q}%'),
                Plantilla.variante.ilike(f'%{q}%'),
            ),
        )
        .order_by(Plantilla.nombre.asc())
        .limit(limit)
        .all()
    )

    results = []
    for p in plantillas:
        breadcrumb = p.codigo + (f' · {p.variante}' if p.variante else '')
        results.append({
            'tipo': 'plantilla',
            'id': p.id,
            'label': p.nombre,
            'breadcrumb': breadcrumb,
            'url': url_for('admin_plantillas.listado', sel=p.id),
        })

    return results


# Registro de entidades buscables: tipo → permiso requerido + helper.
# El endpoint unificado salta los tipos cuyo permiso no tenga el rol activo.
BUSCADORES = {
    'expedientes': {'permiso': 'acceder_expediente', 'buscar': _buscar_expedientes},
    'entidades':   {'permiso': 'acceder_expediente', 'buscar': _buscar_entidades},
    'usuarios':    {'permiso': 'acceder_usuarios',   'buscar': _buscar_usuarios},
    'plantillas':  {'permiso': 'acceder_plantillas', 'buscar': _buscar_plantillas},
}


@api_search_bp.route('', methods=['GET'])
@login_required
def buscar():
    """Búsqueda unificada del Command Palette (#532).

    GET /api/search?q=&tipos=expedientes,entidades,usuarios,plantillas&limit=10
    → {'grupos': [{'tipo': ..., 'resultados': [...]}, ...]}
    """
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'grupos': []}), 200

    limit = _limit_param()
    pedidos = [t.strip() for t in request.args.get('tipos', '').split(',') if t.strip()]
    if not pedidos:
        pedidos = list(BUSCADORES)

    grupos = []
    for tipo in pedidos:
        cfg = BUSCADORES.get(tipo)
        if cfg is None:
            continue
        if cfg['permiso'] and not tiene_permiso(cfg['permiso']):
            continue
        grupos.append({'tipo': tipo, 'resultados': cfg['buscar'](q, limit)})

    return jsonify({'grupos': grupos}), 200


# ---------------------------------------------------------------------------
# Rutas por-entidad (transitorias, #532 fase 1). Thin wrappers sobre los helpers.
# ---------------------------------------------------------------------------

@api_search_bp.route('/expedientes', methods=['GET'])
@login_required
def buscar_expedientes():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200
    return jsonify({'results': _buscar_expedientes(q, _limit_param())}), 200


@api_search_bp.route('/entidades', methods=['GET'])
@login_required
def buscar_entidades():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200
    return jsonify({'results': _buscar_entidades(q, _limit_param())}), 200


@api_search_bp.route('/usuarios', methods=['GET'])
@login_required
def buscar_usuarios():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'results': []}), 200
    return jsonify({'results': _buscar_usuarios(q, _limit_param())}), 200
