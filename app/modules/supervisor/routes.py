"""Blueprint "Mi trabajo del supervisor" (#579, ADR-028).

El universo del supervisor se organiza en dos bloques (ADR-028 §1):

    CONTROL  → lectura/visualización: estadísticas, auditoría, semáforos, informes.
    GESTIÓN  → escritura/administración: configuración del motor, plazos, usuarios,
               operaciones masivas.

RUTAS:
    GET /supervisor/              → hub de dos bloques (vista nuclear de partida).
    GET /supervisor/estadisticas  → hoja del panel de estadísticas (CONTROL).
                                     Placeholder: su diseño se decide en sesión aparte.

La entrada de sidebar NO vive aquí (este módulo no tiene metadata.json): se reusa
"Mi trabajo" (ADR-013), cuyo index redirige al supervisor a `supervisor.index`.
El acceso lo controla `acceder_supervision` (ADR-028, grano grueso).
"""
from flask import Blueprint, render_template

from app.decorators import require_permiso

bp = Blueprint('supervisor', __name__,
               url_prefix='/supervisor',
               template_folder='templates')


@bp.route('/')
@require_permiso('acceder_supervision')
def index():
    """Hub de dos bloques (CONTROL / GESTIÓN) — vista de partida del supervisor."""
    return render_template('supervisor/index.html')


@bp.route('/estadisticas')
@require_permiso('acceder_supervision')
def estadisticas():
    """Hoja del panel de estadísticas (bloque CONTROL).

    Placeholder funcional: la vista existe y es navegable, pero el diseño de los
    agregados (tartas por estado, barras de plazos, stats por técnico) se decide
    en sesión aparte y se construirá sobre el núcleo `estado_dominio` (#558).
    """
    return render_template('supervisor/estadisticas.html')
