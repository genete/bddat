"""
Blueprint para administración del catálogo de efectos del vencimiento de plazo (#633).

Interfaz de configuración para el Supervisor sobre `efectos_plazo` — gemelo
simplificado de `tipos_documentos` (#621): tabla plana (`codigo` + `nombre`),
sin condiciones anidadas. Mismo patrón ADR-023 (listado + inspector overlay).

Sin `metadata.json` propio: entra como tarjeta del hub del supervisor
(ADR-029 §1bis, catálogo de configuración pura, citado por nombre como
"Plazos legales" — mismo régimen aplica a su catálogo de efectos).

`codigo` es inmutable tras el alta (mismo régimen que tipos_documentos/#621):
su valor se propaga como string al motor de reglas (variable `efecto_plazo`,
ver `app/services/plazos.py`), así que renombrarlo en caliente invalidaría
condiciones ya configuradas que lo comparen por valor.

Baja física solo si el efecto no está en uso por ninguna fila de
`catalogo_plazos.efecto_vencimiento_id` (FK `ondelete='RESTRICT'`) — mismo
criterio de protección que items_tecnicos (#594), incluida la restricción de
permiso a solo ADMIN.

Rutas:
- GET  /efectos_plazo/                     — Listado (scroll infinito + inspector)
- POST /efectos_plazo/crear                 — Alta (modal en el listado)
- GET  /efectos_plazo/<id>/                 — Redirige al listado con el inspector abierto
- GET  /efectos_plazo/<id>/fragmento        — Fragmento de lectura para el inspector
- GET  /efectos_plazo/<id>/editar-fragmento — Fragmento de edición (código bloqueado)
- POST /efectos_plazo/<id>/editar           — Guardar cambios (nombre)
- POST /efectos_plazo/<id>/eliminar         — Baja física, solo si no está en uso
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.efectos_plazo import EfectoPlazo
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'efectos_plazo',
    __name__,
    url_prefix='/efectos_plazo',
    template_folder='templates',
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rellenar_efecto(efecto, es_alta):
    """Rellena los campos de un EfectoPlazo desde request.form.

    El código solo se acepta en alta; en edición ni se lee del form (es
    inmutable). Devuelve la lista de errores de validación.
    """
    errores = []

    if es_alta:
        codigo = request.form.get('codigo', '').strip()
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 60:
            errores.append('El código no puede superar 60 caracteres.')
        else:
            efecto.codigo = codigo

    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        errores.append('El nombre es obligatorio.')
    elif len(nombre) > 200:
        errores.append('El nombre no puede superar 200 caracteres.')

    if errores:
        return errores

    efecto.nombre = nombre
    return []


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_efectos_plazo')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023)."""
    return render_template('efectos_plazo/listado.html')


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_efectos_plazo')
def crear():
    """Alta de un efecto nuevo — modal en el listado (patrón `tipos_documentos`).

    El unique constraint de BD (`uq_efectos_plazo_codigo`) es la única
    validación de duplicados — sin pre-check explícito.
    """
    efecto = EfectoPlazo()
    errores = _rellenar_efecto(efecto, es_alta=True)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'efectos_plazo/listado.html',
            show_modal=True, form_data=request.form,
        )

    db.session.add(efecto)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'efectos_plazo/listado.html',
            show_modal=True, form_data=request.form,
        )

    flash('Efecto de plazo creado correctamente.', 'success')
    return redirect(url_for('efectos_plazo.listado', sel=efecto.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_efectos_plazo')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    EfectoPlazo.query.get_or_404(id)
    return redirect(url_for('efectos_plazo.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_efectos_plazo')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    efecto = EfectoPlazo.query.get_or_404(id)
    return render_template(
        'efectos_plazo/_detalle_fragmento.html',
        efecto=efecto,
        en_uso=bool(efecto.plazos),
        puede_editar=tiene_permiso('gestionar_efectos_plazo'),
        puede_eliminar=tiene_permiso('eliminar_efectos_plazo'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_efectos_plazo')
def editar_fragmento(id):
    """Fragmento de edición para el inspector — código bloqueado."""
    efecto = EfectoPlazo.query.get_or_404(id)
    return render_template('efectos_plazo/_editar_fragmento.html', efecto=efecto)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_efectos_plazo')
def editar(id):
    efecto = EfectoPlazo.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('efectos_plazo.listado', sel=id))

    errores = _rellenar_efecto(efecto, es_alta=False)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('efectos_plazo.listado', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('efectos_plazo.listado', sel=id))

    msg = 'Efecto de plazo actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('efectos_plazo.listado', sel=id))


@bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@require_permiso('eliminar_efectos_plazo')
def eliminar(id):
    """Baja física — solo ADMIN (mismo criterio que items_tecnicos, #594).

    Solo procede si el efecto no está referenciado por ninguna fila de
    `catalogo_plazos` (`efecto_vencimiento_id`, FK `ondelete='RESTRICT'`).

    Navegación normal (no XHR): tras borrar, el fragmento del inspector ya no
    existe — este botón es un <form> plano (no data-inspector-form) que
    recarga el listado completo.
    """
    efecto = EfectoPlazo.query.get_or_404(id)
    if efecto.plazos:
        flash(
            f'No se puede eliminar: {len(efecto.plazos)} plazo(s) del catálogo '
            'usan este efecto como consecuencia del vencimiento.',
            'danger',
        )
        return redirect(url_for('efectos_plazo.listado', sel=id))

    db.session.delete(efecto)
    db.session.commit()
    flash('Efecto de plazo eliminado correctamente.', 'success')
    return redirect(url_for('efectos_plazo.listado'))
