"""
Blueprint "Normas y variables del motor" (#637, N083).

CRUD del catálogo de `Norma` y `CatalogoVariable` (`app/models/motor_reglas.py`),
hoy consumidos en modo solo lectura desde `configuracion_motor`, `catalogo_plazos`,
`admin_requisitos`, `items_tecnicos`, `entidades` y la generación de escritos/
certificados — sin ningún punto de escritura hasta este issue.

Sin `metadata.json` propio: configuración pura del Supervisor, entra como
tarjeta del hub «Control y Gestión» (ADR-029 §1bis), no como entrada de sidebar.

Dos pestañas en una sola página (patrón visual de `tablas_maestras`, motor
propio — no comparte su config.py genérico, que no soporta select FK ni
validación custom):

- **Normas**: CRUD completo. `codigo` inmutable tras el alta (mismo régimen
  que N019/tipos_documentos, #621). Sin baja.
- **Variables del motor**: solo edición de filas existentes (`etiqueta`,
  `tipo_dato`, `norma_id`, `activa`). Sin alta: el "token" (`nombre`) que
  referencia el motor solo existe cuando el programador escribe la función
  `@variable(...)` correspondiente en `app/services/variables/` — el CRUD
  gestiona el catálogo, no crea capacidad de cálculo (ver
  `docs/referencia/DISEÑO_CONTEXT_ASSEMBLER.md` §"Ciclo de vida de una
  variable"). `activa` solo puede ponerse a `True` si `nombre` ya tiene
  función registrada en el Variable Registry — si no, se rechaza con error.

RUTAS:
    GET  /normas_variables/                              → página con las 2 pestañas.

    POST /normas_variables/normas/crear
    GET  /normas_variables/normas/<id>/fragmento
    GET  /normas_variables/normas/<id>/editar-fragmento
    POST /normas_variables/normas/<id>/editar

    GET  /normas_variables/variables/<id>/fragmento
    GET  /normas_variables/variables/<id>/editar-fragmento
    POST /normas_variables/variables/<id>/editar
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.motor_reglas import CatalogoVariable, Norma
from app.services.variables import get_registry
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'normas_variables',
    __name__,
    url_prefix='/normas_variables',
    template_folder='templates',
)

TIPOS_DATO = [
    ('boolean',  'Booleano'),
    ('numerico', 'Numérico'),
    ('texto',    'Texto'),
    ('fecha',    'Fecha'),
    ('enum',     'Enumerado'),
]
_TIPOS_DATO_VALIDOS = {codigo for codigo, _ in TIPOS_DATO}


# ---------------------------------------------------------------------------
# Helpers — Norma
# ---------------------------------------------------------------------------

def _rellenar_norma(norma, es_alta):
    """Rellena los campos de una Norma desde request.form.

    `codigo` solo se acepta en alta; en edición ni se lee del form (inmutable,
    mismo régimen que tipos_documentos #621). Devuelve la lista de errores.
    """
    errores = []

    if es_alta:
        codigo = request.form.get('codigo', '').strip()
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 30:
            errores.append('El código no puede superar 30 caracteres.')
        else:
            norma.codigo = codigo

    titulo = request.form.get('titulo', '').strip()
    if not titulo:
        errores.append('El título es obligatorio.')
    elif len(titulo) > 300:
        errores.append('El título no puede superar 300 caracteres.')

    if errores:
        return errores

    norma.titulo = titulo
    norma.url_eli = request.form.get('url_eli', '').strip() or None
    return []


# ---------------------------------------------------------------------------
# Helpers — CatalogoVariable
# ---------------------------------------------------------------------------

def _rellenar_variable(variable):
    """Rellena los campos editables de una CatalogoVariable desde request.form.

    `nombre` nunca se lee del form (inmutable, es el token del Variable
    Registry). `activa` solo se acepta si `nombre` tiene función registrada.
    """
    errores = []

    etiqueta = request.form.get('etiqueta', '').strip()
    if not etiqueta:
        errores.append('La etiqueta es obligatoria.')
    elif len(etiqueta) > 150:
        errores.append('La etiqueta no puede superar 150 caracteres.')

    tipo_dato = request.form.get('tipo_dato', '').strip()
    if tipo_dato not in _TIPOS_DATO_VALIDOS:
        errores.append('El tipo de dato no es válido.')

    norma_id_raw = (request.form.get('norma_id') or '').strip()
    norma = Norma.query.get(int(norma_id_raw)) if norma_id_raw.isdigit() else None
    if norma_id_raw and not norma:
        errores.append('La norma seleccionada no existe.')

    activa = request.form.get('activa') == 'on'
    if activa and variable.nombre not in get_registry():
        errores.append(
            f'No se puede activar «{variable.nombre}»: no existe ninguna función '
            'registrada para ese nombre en el Variable Registry (app/services/variables/). '
            'Activar esta variable exige que un programador la implemente primero.'
        )

    if errores:
        return errores

    variable.etiqueta = etiqueta
    variable.tipo_dato = tipo_dato
    variable.norma_id = norma.id if norma else None
    variable.activa = activa
    return []


# ---------------------------------------------------------------------------
# Rutas — página
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_normas_variables')
def index():
    return render_template(
        'normas_variables/index.html',
        tipos_dato=TIPOS_DATO,
        normas=Norma.query.order_by(Norma.codigo).all(),
        puede_gestionar=tiene_permiso('gestionar_normas_variables'),
    )


# ---------------------------------------------------------------------------
# Rutas — Normas
# ---------------------------------------------------------------------------

@bp.route('/normas/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_normas_variables')
def norma_crear():
    """Alta de una norma nueva — modal en la pestaña Normas (patrón tipos_documentos)."""
    norma = Norma()
    errores = _rellenar_norma(norma, es_alta=True)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'normas_variables/index.html',
            tipos_dato=TIPOS_DATO,
            normas=Norma.query.order_by(Norma.codigo).all(),
            puede_gestionar=tiene_permiso('gestionar_normas_variables'),
            show_modal_norma=True, form_data=request.form, tab_activa='normas',
        )

    db.session.add(norma)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return redirect(url_for('normas_variables.index'))

    flash('Norma creada correctamente.', 'success')
    return redirect(url_for('normas_variables.index', tab='normas', sel=norma.id))


@bp.route('/normas/<int:id>/fragmento')
@login_required
@require_permiso('acceder_normas_variables')
def norma_fragmento(id):
    norma = Norma.query.get_or_404(id)
    return render_template(
        'normas_variables/_norma_detalle_fragmento.html',
        norma=norma,
        puede_editar=tiene_permiso('gestionar_normas_variables'),
    )


@bp.route('/normas/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_normas_variables')
def norma_editar_fragmento(id):
    norma = Norma.query.get_or_404(id)
    return render_template('normas_variables/_norma_editar_fragmento.html', norma=norma)


@bp.route('/normas/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_normas_variables')
def norma_editar(id):
    norma = Norma.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    errores = _rellenar_norma(norma, es_alta=False)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('normas_variables.index', tab='normas', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('normas_variables.index', tab='normas', sel=id))

    msg = 'Norma actualizada correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('normas_variables.index', tab='normas', sel=id))


# ---------------------------------------------------------------------------
# Rutas — Variables del motor (sin alta, ver docstring del módulo)
# ---------------------------------------------------------------------------

@bp.route('/variables/<int:id>/fragmento')
@login_required
@require_permiso('acceder_normas_variables')
def variable_fragmento(id):
    variable = CatalogoVariable.query.get_or_404(id)
    return render_template(
        'normas_variables/_variable_detalle_fragmento.html',
        variable=variable,
        tipos_dato_labels=dict(TIPOS_DATO),
        en_registry=variable.nombre in get_registry(),
        puede_editar=tiene_permiso('gestionar_normas_variables'),
    )


@bp.route('/variables/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_normas_variables')
def variable_editar_fragmento(id):
    variable = CatalogoVariable.query.get_or_404(id)
    return render_template(
        'normas_variables/_variable_editar_fragmento.html',
        variable=variable,
        tipos_dato=TIPOS_DATO,
        normas=Norma.query.order_by(Norma.codigo).all(),
        en_registry=variable.nombre in get_registry(),
    )


@bp.route('/variables/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_normas_variables')
def variable_editar(id):
    variable = CatalogoVariable.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    errores = _rellenar_variable(variable)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('normas_variables.index', tab='variables', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('normas_variables.index', tab='variables', sel=id))

    msg = 'Variable actualizada correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('normas_variables.index', tab='variables', sel=id))
