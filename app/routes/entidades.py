"""Blueprint entidades - Vistas HTML para gestión de entidades.

RUTAS:
    GET  /entidades/          → listado (shell V2, datos vía API)
    GET  /entidades/nueva     → formulario nueva entidad
    POST /entidades/nueva     → crear entidad
    GET  /entidades/<id>      → detalle entidad (placeholder hasta fase 2 #61)

VERSIÓN: 1.0
FECHA: 2026-02-19
ISSUE: #61
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models.entidad import Entidad

bp = Blueprint('entidades', __name__, url_prefix='/entidades')


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
# DETALLE  (placeholder — fase 2 del Epic #61)
# =============================================================================

@bp.route('/<int:entidad_id>')
@login_required
def detalle(entidad_id):
    """Detalle/edición de entidad. Placeholder hasta fase 2 de #61."""
    entidad = Entidad.query.get_or_404(entidad_id)
    # TODO #61 fase 2: Implementar edición, direcciones de notificación y relaciones
    return render_template('entidades/detalle.html', entidad=entidad)
