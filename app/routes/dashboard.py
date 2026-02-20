from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__, url_prefix='')

@bp.route('/')
@bp.route('/dashboard')
@bp.route('/dashboard/')
@login_required
def index():
    """
    Dashboard principal V1 - Vista con layout fullwidth y grid de cards
    """
    # V1 usa template simplificado sin lógica de bloques
    # Los permisos están en el template (más simple para V1)
    return render_template('dashboard/index_v1.html')


@bp.route('/mis_expedientes')
@login_required
def mis_expedientes():
    """
    Redirección a listado de expedientes con filtro 'mis_expedientes=1'.
    Mantiene compatibilidad con enlaces del dashboard.
    """
    return redirect(url_for('expedientes.listado_v2'))
