"""Blueprint de la vista "Mi trabajo" (#501 ADR-017, dispatcher puro desde #588 ADR-029).

RUTAS:
    GET /mi_trabajo/  → dispatcher puro, role-adaptive:
        ADMINISTRATIVO    → redirect a tareas_y_subidas.index (cola + subir documento).
        SUPERVISOR/ADMIN  → redirect a supervisor.index (hub Control y Gestión).
        TRAMITADOR        → redirect al seguimiento (su "mi trabajo" actual).

La entrada de sidebar es única para todos los roles (ADR-013); la adaptación por
rol ocurre en el destino, no en la navegación. Los tres destinos son ahora
también accesibles como entradas de sidebar propias (redundancia asumida, ADR-029
§2) — este dispatcher deja de mezclar navegación genérica y vista concreta
(colisión semántica que señalaba ADR-017 "Deuda conocida", resuelta en #588).
"""
from flask import Blueprint, redirect, url_for, session
from flask_login import login_required

bp = Blueprint('mi_trabajo', __name__,
               url_prefix='/mi_trabajo',
               template_folder='templates')


@bp.route('/')
@login_required
def index():
    """Vista "Mi trabajo" — dispatcher puro role-adaptive (#501, #579, #588)."""
    rol_activo = session.get('rol_activo_nombre')
    if rol_activo in ('SUPERVISOR', 'ADMIN'):
        return redirect(url_for('supervisor.index'))
    if rol_activo == 'ADMINISTRATIVO':
        return redirect(url_for('tareas_y_subidas.index'))
    # TRAMITADOR: su "mi trabajo" hoy es el seguimiento (deuda conocida, ADR-017).
    return redirect(url_for('expedientes.seguimiento'))
