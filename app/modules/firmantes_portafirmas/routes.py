"""
Blueprint para administración del catálogo de firmantes de Port@firmas (#728, ADR-039 §2).

Catálogo vivo (alta libre, a diferencia de `organo_propio`): quién puede
figurar como firmante de un oficio/resolución, desacoplado de `usuarios`
(`usuario_id` nullable — ver modelo `FirmantePortafirmas`). Mismo patrón
ADR-023 (listado + inspector overlay) que `tipos_documentos` (#621).

Baja lógica vía `vigente`/`fecha_baja` (no eliminación física): al desactivar
se fija `fecha_baja` a hoy; al reactivar se limpia. Mismo criterio que
`catalogo_plazos`/`reglas_motor` (alternar activo/inactivo, sin ruta
`eliminar`).

Sin `metadata.json` propio: entra como tarjeta del hub del supervisor
(ADR-029 §1bis).

Rutas:
- GET  /firmantes_portafirmas/                     — Listado (scroll infinito + inspector)
- POST /firmantes_portafirmas/crear                 — Alta (modal en el listado)
- GET  /firmantes_portafirmas/<id>/                 — Redirige al listado con el inspector abierto
- GET  /firmantes_portafirmas/<id>/fragmento        — Fragmento de lectura para el inspector
- GET  /firmantes_portafirmas/<id>/editar-fragmento — Fragmento de edición
- POST /firmantes_portafirmas/<id>/editar           — Guardar cambios
- POST /firmantes_portafirmas/<id>/activar          — Alternar vigente/no vigente (baja lógica)
"""
from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.organo_propio import FirmantePortafirmas, UnidadOrganoPropio
from app.models.usuarios import Usuario
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'firmantes_portafirmas',
    __name__,
    url_prefix='/firmantes_portafirmas',
    template_folder='templates',
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selects_context():
    """Querysets para los selects del formulario (alta y edición)."""
    return {
        'unidades': UnidadOrganoPropio.query.order_by(UnidadOrganoPropio.provincia).all(),
        'usuarios': Usuario.query.order_by(Usuario.siglas).all(),
    }


def _rellenar_firmante(item) -> list[str]:
    """Rellena los campos de un FirmantePortafirmas desde request.form.

    `vigente`/`fecha_baja` no se tocan aquí — se gestionan en la ruta `activar`.
    Devuelve la lista de errores de validación (vacía si todo OK).
    """
    errores = []

    cargo = request.form.get('cargo', '').strip()
    if not cargo:
        errores.append('El cargo es obligatorio.')
    elif len(cargo) > 200:
        errores.append('El cargo no puede superar 200 caracteres.')

    dni = request.form.get('dni', '').strip().upper()
    if not dni:
        errores.append('El DNI es obligatorio.')
    elif len(dni) > 15:
        errores.append('El DNI no puede superar 15 caracteres.')

    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        errores.append('El nombre es obligatorio.')
    elif len(nombre) > 200:
        errores.append('El nombre no puede superar 200 caracteres.')

    unidad_id_raw = (request.form.get('unidad_organo_id') or '').strip()
    unidad = UnidadOrganoPropio.query.get(int(unidad_id_raw)) if unidad_id_raw.isdigit() else None
    if not unidad:
        errores.append('La unidad territorial es obligatoria.')

    usuario_id_raw = (request.form.get('usuario_id') or '').strip()
    usuario = Usuario.query.get(int(usuario_id_raw)) if usuario_id_raw.isdigit() else None
    if usuario_id_raw and not usuario:
        errores.append('El usuario BDDAT seleccionado no existe.')

    if errores:
        return errores

    item.cargo = cargo
    item.dni = dni
    item.nombre = nombre
    item.unidad_organo_id = unidad.id
    item.usuario_id = usuario.id if usuario else None
    return []


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_firmantes_portafirmas')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023)."""
    return render_template('firmantes_portafirmas/listado.html', **_selects_context())


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_firmantes_portafirmas')
def crear():
    """Alta de un firmante nuevo — modal en el listado (patrón `tipos_documentos`)."""
    item = FirmantePortafirmas(vigente=True)
    errores = _rellenar_firmante(item)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'firmantes_portafirmas/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'firmantes_portafirmas/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    flash('Firmante creado correctamente.', 'success')
    return redirect(url_for('firmantes_portafirmas.listado', sel=item.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_firmantes_portafirmas')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    FirmantePortafirmas.query.get_or_404(id)
    return redirect(url_for('firmantes_portafirmas.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_firmantes_portafirmas')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    item = FirmantePortafirmas.query.get_or_404(id)
    return render_template(
        'firmantes_portafirmas/_detalle_fragmento.html',
        item=item,
        puede_editar=tiene_permiso('gestionar_firmantes_portafirmas'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_firmantes_portafirmas')
def editar_fragmento(id):
    """Fragmento de edición para el inspector."""
    item = FirmantePortafirmas.query.get_or_404(id)
    return render_template(
        'firmantes_portafirmas/_editar_fragmento.html',
        item=item,
        **_selects_context(),
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_firmantes_portafirmas')
def editar(id):
    item = FirmantePortafirmas.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('firmantes_portafirmas.listado', sel=id))

    errores = _rellenar_firmante(item)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('firmantes_portafirmas.listado', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('firmantes_portafirmas.listado', sel=id))

    msg = 'Firmante actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('firmantes_portafirmas.listado', sel=id))


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_firmantes_portafirmas')
def activar(id):
    """Alterna vigente/no vigente — baja lógica. Gestiona fecha_baja a la vez."""
    item = FirmantePortafirmas.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    item.vigente = not item.vigente
    item.fecha_baja = None if item.vigente else date.today()
    db.session.commit()
    estado = 'reactivado' if item.vigente else 'dado de baja'
    msg = f'Firmante {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'vigente': item.vigente})
    flash(msg, 'success')
    return redirect(url_for('firmantes_portafirmas.listado', sel=id))
