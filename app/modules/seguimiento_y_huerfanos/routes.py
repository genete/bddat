"""Blueprint "Seguimiento y Huérfanos" (#630, ADR-038).

RUTAS:
    GET /seguimiento_y_huerfanos/                          → hub de dos pestañas
    GET /seguimiento_y_huerfanos/seguimiento/<id>/fragmento → inspector de seguimiento (ADR-023 §9)

Hub propio del TRAMITADOR — resuelve el tercer caso de la "Deuda conocida" de
ADR-017 (antes vista prestada en `/expedientes/seguimiento/`, extraída aquí
tal cual). Pestañas nav-tabs de Bootstrap (patrón `tablas_maestras/listado.html`),
no isla React — coherente con que Seguimiento ya es Jinja + `ScrollInfinito`.

    Seguimiento  → contenido movido sin cambios desde `expedientes.seguimiento`.
    Huérfanos    → radar de documentos del pool sin vínculo a tarea (ADR-027 §2).

`mi_trabajo.index` redirige aquí para TRAMITADOR en vez de a
`expedientes.seguimiento` — los tres roles quedan simétricos (ADR-029 §1bis).
"""
from flask import Blueprint, render_template

from app.decorators import require_permiso
from app.models.tipos_expedientes import TipoExpediente
from app.models.solicitudes import Solicitud
from app.utils.permisos import verificar_acceso_expediente
from app.utils.metadata import cargar_metadata

bp = Blueprint('seguimiento_y_huerfanos', __name__,
               url_prefix='/seguimiento_y_huerfanos',
               template_folder='templates')


@bp.route('/')
@require_permiso('acceder_seguimiento_y_huerfanos')
def index():
    """Hub de dos pestañas: Seguimiento (cola multi-pista) + Huérfanos (radar del pool)."""
    meta = cargar_metadata('seguimiento_y_huerfanos')
    columns = meta.get('seguimiento', {}).get('columns', [])
    tipos_expedientes = TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    return render_template(
        'seguimiento_y_huerfanos/index.html',
        columns=columns,
        tipos_expedientes=tipos_expedientes,
    )


@bp.route('/seguimiento/<int:solicitud_id>/fragmento')
@require_permiso('acceder_seguimiento_y_huerfanos')
def seguimiento_fragmento(solicitud_id):
    """Fragmento de lectura del inspector de seguimiento (ADR-023 §9 / #559).

    Detalle del agregado de una solicitud en el lenguaje del árbol (semáforo por
    nodo). Solo lectura: la edición se delega al árbol vía "Ir a tramitar". El color
    de cada nodo sale de estado_dominio (#558) → misma verdad que verás al saltar.
    """
    from app.services.arbol_expediente import construir_arbol_solicitud

    sol = Solicitud.query.get_or_404(solicitud_id)
    resultado = verificar_acceso_expediente(sol.expediente, 'ver')
    if resultado:
        return '', 403

    arbol = construir_arbol_solicitud(solicitud_id)
    if arbol is None:
        return '', 404

    return render_template(
        'seguimiento_y_huerfanos/_inspector_seguimiento.html',
        solicitud=arbol['solicitud'],
        expediente=arbol['expediente'],
        cuello_botella=arbol['cuello_botella'],
    )
