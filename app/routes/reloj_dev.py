"""Interfaz web del reloj de desarrollo (#820) — badge en la topbar.

Blueprint separado y con `abort(404)` propio (no solo oculto en el template):
en producción (`ProductionConfig.DEBUG = False`) las rutas ni siquiera
responden, sin depender de que nadie recuerde quitar el badge al desplegar.
Sin permiso de rol nuevo — el gate es el entorno (DEBUG), no quién ha
iniciado sesión; cualquier usuario autenticado en un entorno de desarrollo
puede tocar el reloj compartido.
"""
from datetime import date

from flask import Blueprint, abort, current_app, flash, redirect, request, url_for
from flask_login import login_required

bp = Blueprint('reloj_dev', __name__, url_prefix='/dev/reloj')


def _requiere_debug():
    if not current_app.config.get('DEBUG'):
        abort(404)


def _volver():
    return redirect(request.referrer or url_for('dashboard.index'))


@bp.route('/fijar', methods=['POST'])
@login_required
def fijar():
    _requiere_debug()
    from app.services.reloj_simulado import fijar as fijar_reloj

    try:
        fecha = date.fromisoformat(request.form.get('fecha', ''))
    except ValueError:
        flash('Fecha inválida.', 'danger')
        return _volver()

    fijar_reloj(fecha)
    flash(f'Reloj simulado fijado a {fecha.strftime("%d/%m/%Y")}.', 'warning')
    return _volver()


@bp.route('/borrar', methods=['POST'])
@login_required
def borrar():
    _requiere_debug()
    from app.services.reloj_simulado import borrar as borrar_reloj

    borrar_reloj()
    flash('Reloj simulado borrado — usando fecha real.', 'success')
    return _volver()
