from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__, url_prefix='')

@bp.route('/')
@bp.route('/dashboard')
@bp.route('/dashboard/')
def index():
    """
    Dashboard principal V1 - Vista con layout fullwidth y grid de cards
    """
    # Sin `@login_required`: entrar por la raíz sin sesión es lo normal, no un acceso denegado.
    # Va al login sin el aviso «Debe iniciar sesión…» ni `?next=/` (tras el login el destino por
    # defecto ya es esta misma pantalla). Las demás rutas conservan el aviso y el `next`.
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

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
    return redirect(url_for('expedientes.listado_v2', responsable='yo'))
