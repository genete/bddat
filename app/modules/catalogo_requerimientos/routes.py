"""
Blueprint para administración del catálogo de requerimientos (#593).

Interfaz de configuración para el Supervisor sobre `catalogo_requerimientos` —
gemelo simplificado de `admin_requisitos` (#583): mismo patrón ADR-023
(listado + inspector overlay), pero sin condiciones anidadas (esta tabla no
las tiene) y sin baja física (solo baja lógica, restringida a ADMIN).

Rutas:
- GET  /catalogo_requerimientos/                    — Listado (scroll infinito + inspector)
- POST /catalogo_requerimientos/crear                — Alta (modal en el listado)
- GET  /catalogo_requerimientos/<id>/                — Redirige al listado con el inspector abierto
- GET  /catalogo_requerimientos/<id>/fragmento       — Fragmento de lectura para el inspector
- GET  /catalogo_requerimientos/<id>/editar-fragmento — Fragmento de edición
- POST /catalogo_requerimientos/<id>/editar          — Guardar cambios (texto/categoría)
- POST /catalogo_requerimientos/<id>/activar         — Alternar activo/inactivo (baja lógica, solo ADMIN)
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.catalogo_requerimientos import CatalogoRequerimiento
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'catalogo_requerimientos',
    __name__,
    url_prefix='/catalogo_requerimientos',
    template_folder='templates',
)

# Mismos valores que el CHECK ck_catalogo_requerimientos_categoria
CATEGORIAS = [
    ('documental',      'Documental'),
    ('tecnica',         'Técnica'),
    ('administrativa',  'Administrativa'),
    ('tasas',           'Tasas'),
]
_CATEGORIAS_VALIDAS = {codigo for codigo, _ in CATEGORIAS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rellenar_requerimiento(requerimiento) -> list[str]:
    """Rellena los campos de un CatalogoRequerimiento desde request.form.

    Devuelve la lista de errores de validación (vacía si todo OK).
    """
    errores = []
    texto = request.form.get('texto', '').strip()
    if not texto:
        errores.append('El texto es obligatorio.')

    categoria = request.form.get('categoria', '').strip()
    if categoria not in _CATEGORIAS_VALIDAS:
        errores.append('La categoría no es válida.')

    if errores:
        return errores

    requerimiento.texto = texto
    requerimiento.categoria = categoria
    return []


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_catalogo_requerimientos')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023)."""
    return render_template('catalogo_requerimientos/listado.html', categorias=CATEGORIAS)


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_catalogo_requerimientos')
def crear():
    """Alta de un requerimiento nuevo — modal en el listado (patrón `usuarios`)."""
    requerimiento = CatalogoRequerimiento()
    errores = _rellenar_requerimiento(requerimiento)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'catalogo_requerimientos/listado.html',
            show_modal=True, form_data=request.form, categorias=CATEGORIAS,
        )

    db.session.add(requerimiento)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'catalogo_requerimientos/listado.html',
            show_modal=True, form_data=request.form, categorias=CATEGORIAS,
        )

    flash('Requerimiento creado correctamente.', 'success')
    return redirect(url_for('catalogo_requerimientos.listado', sel=requerimiento.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_catalogo_requerimientos')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    CatalogoRequerimiento.query.get_or_404(id)
    return redirect(url_for('catalogo_requerimientos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_catalogo_requerimientos')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    requerimiento = CatalogoRequerimiento.query.get_or_404(id)
    return render_template(
        'catalogo_requerimientos/_detalle_fragmento.html',
        requerimiento=requerimiento,
        categorias_labels=dict(CATEGORIAS),
        puede_editar=tiene_permiso('gestionar_catalogo_requerimientos'),
        puede_archivar=tiene_permiso('archivar_catalogo_requerimientos'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_catalogo_requerimientos')
def editar_fragmento(id):
    """Fragmento de edición para el inspector."""
    requerimiento = CatalogoRequerimiento.query.get_or_404(id)
    return render_template(
        'catalogo_requerimientos/_editar_fragmento.html',
        requerimiento=requerimiento,
        categorias=CATEGORIAS,
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_catalogo_requerimientos')
def editar(id):
    requerimiento = CatalogoRequerimiento.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('catalogo_requerimientos.listado', sel=id))

    errores = _rellenar_requerimiento(requerimiento)
    if errores:
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('catalogo_requerimientos.listado', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('catalogo_requerimientos.listado', sel=id))

    msg = 'Requerimiento actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('catalogo_requerimientos.listado', sel=id))


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('archivar_catalogo_requerimientos')
def activar(id):
    """Alterna activo/inactivo — baja lógica exclusiva de ADMIN (#593).

    Nunca DELETE físico: preserva historial en requerimientos_tarea.
    """
    requerimiento = CatalogoRequerimiento.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    requerimiento.activo = not requerimiento.activo
    db.session.commit()
    estado = 'activado' if requerimiento.activo else 'desactivado'
    msg = f'Requerimiento {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': requerimiento.activo})
    flash(msg, 'success')
    return redirect(url_for('catalogo_requerimientos.listado', sel=id))
