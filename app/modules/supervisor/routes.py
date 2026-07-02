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
from flask import Blueprint, jsonify, render_template

from app.decorators import require_permiso
from app.services.estadisticas_supervisor import calcular_estadisticas

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

    La hoja monta la isla React `estadisticas`, que consume el endpoint JSON
    `supervisor.api_estadisticas`. Los agregados se construyen sobre el núcleo
    `estado_dominio` (#558) vía `estadisticas_supervisor`.
    """
    return render_template('supervisor/estadisticas.html')


@bp.route('/api/estadisticas')
@require_permiso('acceder_supervision')
def api_estadisticas():
    """Agregados del panel de estadísticas: {kpis, por_estado, por_tecnico}.

    Lo consume la isla React `estadisticas`. La autorización real la impone el
    decorador (las islas no autentican, ADR-015); el cálculo reusa el núcleo de
    estado sin reimplementar reglas (ver `estadisticas_supervisor`).
    """
    return jsonify(calcular_estadisticas())
