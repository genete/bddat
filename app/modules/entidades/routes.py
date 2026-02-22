"""Blueprint entidades - Vistas HTML para gestión de entidades.

RUTAS:
    GET  /entidades/          → listado (shell V2, datos vía API)
    GET  /entidades/nueva     → formulario nueva entidad
    POST /entidades/nueva     → crear entidad
    GET  /entidades/<id>      → detalle entidad V4 solo lectura (#134)
    GET  /entidades/<id>/editar → placeholder edición (#134, próximamente)

VERSIÓN: 1.1
FECHA: 2026-02-22
ISSUE: #134
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.entidad import Entidad
from app.models.autorizados_titular import AutorizadoTitular

# template_folder apunta a app/modules/entidades/templates/
bp = Blueprint('entidades', __name__,
               url_prefix='/entidades',
               template_folder='templates')


# =============================================================================
# LISTADO  (shell V2 — datos cargados por ScrollInfinito vía API)
# =============================================================================

@bp.route('/')
@login_required
def index():
    """Vista listado de entidades. Sin datos de BD en Jinja2."""
    return render_template('entidades/index.html')


# =============================================================================
# NUEVA ENTIDAD
# =============================================================================

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    """Formulario de alta de entidad (GET muestra, POST crea)."""

    if request.method == 'GET':
        return render_template('entidades/nueva.html')

    # --- POST: recoger y validar ---
    nombre_completo = request.form.get('nombre_completo', '').strip()
    nif_raw         = request.form.get('nif', '').strip()
    rol_titular     = 'rol_titular'     in request.form
    rol_consultado  = 'rol_consultado'  in request.form
    rol_publicador  = 'rol_publicador'  in request.form
    email           = request.form.get('email',    '').strip() or None
    telefono        = request.form.get('telefono', '').strip() or None
    notas           = request.form.get('notas',    '').strip() or None
    activo          = 'activo' in request.form

    errores = []

    if not nombre_completo:
        errores.append('El nombre / razón social es obligatorio.')

    if not (rol_titular or rol_consultado or rol_publicador):
        errores.append('Debe asignarse al menos un rol a la entidad.')

    # Normalizar y comprobar NIF duplicado
    nif = Entidad.normalizar_nif(nif_raw) if nif_raw else None
    if nif and Entidad.query.filter_by(nif=nif).first():
        errores.append(f'Ya existe una entidad con el NIF {nif}.')

    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template('entidades/nueva.html')

    # --- Crear ---
    entidad = Entidad(
        nombre_completo=nombre_completo,
        nif=nif,
        rol_titular=rol_titular,
        rol_consultado=rol_consultado,
        rol_publicador=rol_publicador,
        email=email,
        telefono=telefono,
        notas=notas,
        activo=activo,
    )

    db.session.add(entidad)
    db.session.commit()

    flash(f'Entidad "{entidad.nombre_completo}" creada correctamente.', 'success')
    return redirect(url_for('entidades.index'))


# =============================================================================
# DETALLE  V4 solo lectura (#134)
# =============================================================================

@bp.route('/<int:entidad_id>')
@login_required
def detalle(entidad_id):
    """Vista detalle de entidad — patrón V4 solo lectura."""
    entidad = Entidad.query.get_or_404(entidad_id)

    # Cargar autorizaciones vigentes si es titular
    autorizaciones = []
    if entidad.rol_titular:
        autorizaciones = AutorizadoTitular.obtener_autorizados_de_titular(entidad_id)

    return render_template(
        'entidades/detalle.html',
        entidad=entidad,
        autorizaciones=autorizaciones,
        modo='ver',
    )


@bp.route('/<int:entidad_id>/editar')
@login_required
def editar(entidad_id):
    """Placeholder edición — implementar en issue hijo de #134."""
    Entidad.query.get_or_404(entidad_id)
    flash('La edición de entidades estará disponible próximamente.', 'info')
    return redirect(url_for('entidades.detalle', entidad_id=entidad_id))
