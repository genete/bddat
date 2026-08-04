"""Blueprint de la vista "Mi trabajo" (#501 ADR-017, dispatcher puro desde #588 ADR-029).

RUTAS:
    GET /mi_trabajo/  → dispatcher puro, role-adaptive:
        ADMINISTRATIVO    → redirect a tareas_y_subidas.index (cola + subir documento).
        SUPERVISOR/ADMIN  → redirect a supervisor.index (hub Control y Gestión).
        TRAMITADOR        → redirect a seguimiento_y_huerfanos.index (su hub propio).

La entrada de sidebar es única para todos los roles (ADR-013); la adaptación por
rol ocurre en el destino, no en la navegación. Los tres destinos son ahora
también accesibles como entradas de sidebar propias (redundancia asumida, ADR-029
§2) — este dispatcher deja de mezclar navegación genérica y vista concreta
(colisión semántica que señalaba ADR-017 "Deuda conocida", resuelta en #588 para
los dos primeros casos y en #630/ADR-038 para el tercero).
"""
from flask import Blueprint, redirect, url_for, session
from flask_login import login_required

bp = Blueprint('mi_trabajo', __name__,
               url_prefix='/mi_trabajo',
               template_folder='templates')


@bp.route('/')
@login_required
def index():
    """Vista "Mi trabajo" — dispatcher puro role-adaptive (#501, #579, #588, #630)."""
    rol_activo = session.get('rol_activo_nombre')
    if rol_activo in ('SUPERVISOR', 'ADMIN'):
        return redirect(url_for('supervisor.index'))
    if rol_activo == 'ADMINISTRATIVO':
        return redirect(url_for('tareas_y_subidas.index'))
    # TRAMITADOR: hub propio Seguimiento y Huérfanos (#630, ADR-038).
    return redirect(url_for('seguimiento_y_huerfanos.index'))
