"""Blueprint "Control y Gestión" (#579 ADR-028, universalizado #588 ADR-029).

El universo se organiza en dos bloques (ADR-028 §1):

    CONTROL  → lectura/visualización: estadísticas, auditoría, semáforos, informes.
    GESTIÓN  → escritura/administración: configuración del motor, plazos, usuarios,
               operaciones masivas.

RUTAS:
    GET /gestion_y_control/              → hub de dos bloques (vista nuclear de partida).
    GET /gestion_y_control/estadisticas  → hoja del panel de estadísticas (CONTROL).
                                            Placeholder: su diseño se decide en sesión aparte.

El nombre interno del blueprint ('supervisor') y el paquete se mantienen — es
detalle de implementación sin efecto en la URL pública ni en url_for() (#588).

Entrada de sidebar propia vía `metadata.json` (ADR-029 §2, enmienda ADR-028 §1):
antes sin metadata.json a propósito, alcanzable solo por "Mi trabajo"; ahora
también accesible como "Control y Gestión" en el sidebar — redundancia asumida,
mismo patrón que ya tiene Usuarios. El acceso lo controla `acceder_gestion_control`,
universal a los 4 roles (ADR-029 §2): no hay razón declarada para ocultarlo.
"""
from flask import Blueprint, jsonify, render_template

from app.decorators import require_permiso
from app.services.estadisticas_supervisor import calcular_estadisticas

bp = Blueprint('supervisor', __name__,
               url_prefix='/gestion_y_control',
               template_folder='templates')


@bp.route('/')
@require_permiso('acceder_gestion_control')
def index():
    """Hub de dos bloques (CONTROL / GESTIÓN) — vista de partida de Control y Gestión."""
    return render_template('supervisor/index.html')


@bp.route('/estadisticas')
@require_permiso('acceder_gestion_control')
def estadisticas():
    """Hoja del panel de estadísticas (bloque CONTROL).

    La hoja monta la isla React `estadisticas`, que consume el endpoint JSON
    `supervisor.api_estadisticas`. Los agregados se construyen sobre el núcleo
    `estado_dominio` (#558) vía `estadisticas_supervisor`.
    """
    return render_template('supervisor/estadisticas.html')


@bp.route('/api/estadisticas')
@require_permiso('acceder_gestion_control')
def api_estadisticas():
    """Agregados del panel de estadísticas: {kpis, por_estado, por_tecnico}.

    Lo consume la isla React `estadisticas`. La autorización real la impone el
    decorador (las islas no autentican, ADR-015); el cálculo reusa el núcleo de
    estado sin reimplementar reglas (ver `estadisticas_supervisor`).
    """
    return jsonify(calcular_estadisticas())
