"""
Blueprint para administración del catálogo de tipos de documento (#621).

Interfaz de configuración para el Supervisor sobre `tipos_documentos` —
gemelo simplificado de `catalogo_requerimientos` (#593): mismo patrón
ADR-023 (listado + inspector overlay), tabla plana sin condiciones
anidadas. Sin baja, ni lógica ni física (#621): el modelo no tiene columna
`activo` — decisión de Carlos, ver docs/CONTEXTO_ACTUAL.md.

`codigo` es inmutable tras el alta (mismo régimen que N019/`tablas_maestras`):
usado por el motor de reglas y por el código
(`app/checks/catalogo_requerido.py`, `REGISTROS_REQUERIDOS['TipoDocumento']`).

Sin `metadata.json` propio: entra como tarjeta del hub del supervisor
(ADR-029 §1) — el consumo diario del catálogo pasa por el selector de tipo
al incorporar un documento (#379), no por este CRUD.

Rutas:
- GET  /tipos_documentos/                     — Listado (scroll infinito + inspector)
- POST /tipos_documentos/crear                 — Alta (modal en el listado)
- GET  /tipos_documentos/<id>/                 — Redirige al listado con el inspector abierto
- GET  /tipos_documentos/<id>/fragmento        — Fragmento de lectura para el inspector
- GET  /tipos_documentos/<id>/editar-fragmento — Fragmento de edición (código bloqueado)
- POST /tipos_documentos/<id>/editar           — Guardar cambios (nombre/descripción/origen)
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS
from app.decorators import require_permiso
from app.models.tipos_documentos import TipoDocumento
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'tipos_documentos',
    __name__,
    url_prefix='/tipos_documentos',
    template_folder='templates',
)

ORIGENES = [
    ('INTERNO', 'Interno (generado por la administración)'),
    ('EXTERNO', 'Externo (aportado por el interesado)'),
    ('AMBOS',   'Ambos'),
]
_ORIGENES_VALIDOS = {codigo for codigo, _ in ORIGENES}

# Códigos con comportamiento hardcodeado en Python — informativo (#621, mismo
# patrón que `tablas_maestras/config.py`). No condiciona la inmutabilidad de
# `codigo`, que aplica a todas las filas por igual.
_CODIGOS_PROTEGIDOS = set(REGISTROS_REQUERIDOS.get('TipoDocumento', []))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rellenar_tipo(tipo, es_alta):
    """Rellena los campos de un TipoDocumento desde request.form.

    El código solo se acepta en alta; en edición ni se lee del form (es
    inmutable, #621). Devuelve la lista de errores de validación.
    """
    errores = []

    if es_alta:
        codigo = request.form.get('codigo', '').strip()
        if not codigo:
            errores.append('El código es obligatorio.')
        elif len(codigo) > 50:
            errores.append('El código no puede superar 50 caracteres.')
        else:
            tipo.codigo = codigo

    nombre = request.form.get('nombre', '').strip()
    if not nombre:
        errores.append('El nombre es obligatorio.')

    origen = request.form.get('origen', '').strip()
    if origen not in _ORIGENES_VALIDOS:
        errores.append('El origen no es válido.')

    if errores:
        return errores

    tipo.nombre = nombre
    tipo.descripcion = request.form.get('descripcion', '').strip() or None
    tipo.origen = origen
    return []


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_tipos_documentos')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023)."""
    return render_template('tipos_documentos/listado.html', origenes=ORIGENES)


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_tipos_documentos')
def crear():
    """Alta de un tipo nuevo — modal en el listado (patrón `usuarios`).

    El unique constraint de BD (`uq_tipos_documentos_codigo`) es la única
    validación de duplicados — igual que `tablas_maestras`, sin pre-check
    explícito: el error de commit ya lo comunica al Supervisor.
    """
    tipo = TipoDocumento()
    errores = _rellenar_tipo(tipo, es_alta=True)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'tipos_documentos/listado.html',
            show_modal=True, form_data=request.form, origenes=ORIGENES,
        )

    db.session.add(tipo)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'tipos_documentos/listado.html',
            show_modal=True, form_data=request.form, origenes=ORIGENES,
        )

    flash('Tipo de documento creado correctamente.', 'success')
    return redirect(url_for('tipos_documentos.listado', sel=tipo.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_tipos_documentos')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    TipoDocumento.query.get_or_404(id)
    return redirect(url_for('tipos_documentos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_tipos_documentos')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    tipo = TipoDocumento.query.get_or_404(id)
    return render_template(
        'tipos_documentos/_detalle_fragmento.html',
        tipo=tipo,
        origenes_labels=dict(ORIGENES),
        protegido=tipo.codigo in _CODIGOS_PROTEGIDOS,
        puede_editar=tiene_permiso('gestionar_tipos_documentos'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_tipos_documentos')
def editar_fragmento(id):
    """Fragmento de edición para el inspector — código bloqueado."""
    tipo = TipoDocumento.query.get_or_404(id)
    return render_template(
        'tipos_documentos/_editar_fragmento.html',
        tipo=tipo,
        origenes=ORIGENES,
        protegido=tipo.codigo in _CODIGOS_PROTEGIDOS,
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_tipos_documentos')
def editar(id):
    tipo = TipoDocumento.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('tipos_documentos.listado', sel=id))

    errores = _rellenar_tipo(tipo, es_alta=False)
    if errores:
        db.session.rollback()
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('tipos_documentos.listado', sel=id))

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = f'Error al guardar: {e}'
        if is_xhr:
            return jsonify({'ok': False, 'errors': [msg]})
        flash(msg, 'danger')
        return redirect(url_for('tipos_documentos.listado', sel=id))

    msg = 'Tipo de documento actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('tipos_documentos.listado', sel=id))
