"""
Blueprint "Delegación Territorial propia" (#728, ADR-039 §1).

Pantalla de mantenimiento de `consejerias_delegaciones_territoriales`
(composición de Consejerías, fila única) y `unidades_organo_propio` (una
fila por provincia, 8 ya sembradas). Solo edición: sin alta ni baja — las
filas son estructuralmente fijas (decisión de Carlos, #728). Si algún día
hiciera falta una unidad nueva (p.ej. servicios centrales), se añade por
migración, no desde esta pantalla.

Sin `metadata.json` propio: configuración institucional pura, entra como
tarjeta del hub «Control y Gestión» (ADR-029 §1bis).

No usa ScrollInfinito/API: ambas tablas son de tamaño fijo y pequeño (1 y 8
filas), a diferencia de los catálogos vivos del resto de `app/modules/`. La
delegación se edita con un formulario siempre visible en la página (patrón
`configuracion_motor` "modo global"); las unidades usan el inspector overlay
(ADR-023) contra un `<table>` estático — `AppInspector.open()` no depende de
ScrollInfinito, solo necesita una `fragmentUrl`.

RUTAS:
    GET  /organo_propio/                       → página (delegación + tabla de unidades).
    POST /organo_propio/delegacion/editar       → guarda consejeria_1/2_nombre.

    GET  /organo_propio/unidades/<id>/fragmento         → fragmento de lectura (inspector).
    GET  /organo_propio/unidades/<id>/editar-fragmento  → fragmento de edición (inspector).
    POST /organo_propio/unidades/<id>/editar            → guarda sede_*/codigo_bandeja_texto.
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.organo_propio import ConsejeriaDelegacionTerritorial, UnidadOrganoPropio
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'organo_propio',
    __name__,
    url_prefix='/organo_propio',
    template_folder='templates',
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rellenar_delegacion(item) -> list[str]:
    """Rellena consejeria_1/2_nombre desde request.form. Devuelve errores."""
    errores = []

    consejeria_1 = request.form.get('consejeria_1_nombre', '').strip()
    if not consejeria_1:
        errores.append('La primera Consejería es obligatoria.')
    elif len(consejeria_1) > 200:
        errores.append('El nombre de la primera Consejería no puede superar 200 caracteres.')

    consejeria_2 = request.form.get('consejeria_2_nombre', '').strip() or None
    if consejeria_2 and len(consejeria_2) > 200:
        errores.append('El nombre de la segunda Consejería no puede superar 200 caracteres.')

    if errores:
        return errores

    item.consejeria_1_nombre = consejeria_1
    item.consejeria_2_nombre = consejeria_2
    return []


def _rellenar_unidad(item) -> list[str]:
    """Rellena sede_*/codigo_bandeja_texto desde request.form. Provincia y
    consejerias_delegacion_id no se tocan: son fijos (#728)."""
    errores = []

    codigo_bandeja_texto = request.form.get('codigo_bandeja_texto', '').strip() or None
    if codigo_bandeja_texto and len(codigo_bandeja_texto) > 200:
        errores.append('El rótulo de BandeJA no puede superar 200 caracteres.')

    sede_direccion = request.form.get('sede_direccion', '').strip() or None
    if sede_direccion and len(sede_direccion) > 300:
        errores.append('La dirección no puede superar 300 caracteres.')

    sede_telefono = request.form.get('sede_telefono', '').strip() or None
    if sede_telefono and len(sede_telefono) > 30:
        errores.append('El teléfono no puede superar 30 caracteres.')

    sede_correo = request.form.get('sede_correo', '').strip() or None
    if sede_correo and len(sede_correo) > 150:
        errores.append('El correo no puede superar 150 caracteres.')

    if errores:
        return errores

    item.codigo_bandeja_texto = codigo_bandeja_texto
    item.sede_direccion = sede_direccion
    item.sede_telefono = sede_telefono
    item.sede_correo = sede_correo
    return []


# ---------------------------------------------------------------------------
# Rutas — página
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_organo_propio')
def index():
    return render_template(
        'organo_propio/index.html',
        delegacion=ConsejeriaDelegacionTerritorial.query.first(),
        unidades=UnidadOrganoPropio.query.order_by(UnidadOrganoPropio.provincia).all(),
        puede_gestionar=tiene_permiso('gestionar_organo_propio'),
    )


# ---------------------------------------------------------------------------
# Rutas — Delegación (fila única, formulario siempre visible en la página)
# ---------------------------------------------------------------------------

@bp.route('/delegacion/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_organo_propio')
def editar_delegacion():
    delegacion = ConsejeriaDelegacionTerritorial.query.first_or_404()

    errores = _rellenar_delegacion(delegacion)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('organo_propio.index'))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return redirect(url_for('organo_propio.index'))

    flash('Delegación Territorial actualizada correctamente.', 'success')
    return redirect(url_for('organo_propio.index'))


# ---------------------------------------------------------------------------
# Rutas — Unidades por provincia (inspector overlay, ADR-023)
# ---------------------------------------------------------------------------

@bp.route('/unidades/<int:id>/fragmento')
@login_required
@require_permiso('acceder_organo_propio')
def unidad_fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    unidad = UnidadOrganoPropio.query.get_or_404(id)
    return render_template(
        'organo_propio/_unidad_detalle_fragmento.html',
        unidad=unidad,
        puede_editar=tiene_permiso('gestionar_organo_propio'),
    )


@bp.route('/unidades/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_organo_propio')
def unidad_editar_fragmento(id):
    """Fragmento de edición para el inspector — provincia/consejería son de solo lectura."""
    unidad = UnidadOrganoPropio.query.get_or_404(id)
    return render_template('organo_propio/_unidad_editar_fragmento.html', unidad=unidad)


@bp.route('/unidades/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_organo_propio')
def unidad_editar(id):
    unidad = UnidadOrganoPropio.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    errores = _rellenar_unidad(unidad)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('organo_propio.index'))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('organo_propio.index'))

    msg = f'Unidad de {unidad.provincia or "servicios centrales"} actualizada correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('organo_propio.index'))
