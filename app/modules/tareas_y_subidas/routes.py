"""Blueprint "Tareas y Subidas" (#501 ADR-017, extraído en #588 ADR-029).

RUTAS:
    GET /tareas_y_subidas/                     → isla React (cola + subir documento).
    GET /tareas_y_subidas/tarea/<id>/fragmento → parcial de lectura del inspector de
        la cola (ADR-023 §9 / Opción A): detalle de la tarea en lenguaje del árbol,
        con "Ir a tramitar". La edición se delega al árbol.

Contenido antes exclusivo de ADMINISTRATIVO, renderizado en la raíz de
`mi_trabajo` (colisión semántica leve señalada en ADR-017 "Deuda conocida").
Ahora ruta propia y universal (`acceder_tareas_y_subidas`, ADR-029 §1: consulta
diaria de cualquier rol → entrada propia de sidebar). `mi_trabajo.index`
redirige aquí para ADMINISTRATIVO igual que ya redirige a `supervisor.index`
para SUPERVISOR/ADMIN — dispatcher puro y simétrico para los tres roles.
"""
from flask import Blueprint, render_template

from app.decorators import require_permiso
from app.models.tareas import Tarea
from app.models.tipos_expedientes import TipoExpediente
from app.utils.permisos import verificar_acceso_expediente
from app.services.detalle_nodo import detalle_de_nodo

bp = Blueprint('tareas_y_subidas', __name__,
               url_prefix='/tareas_y_subidas',
               template_folder='templates')


@bp.route('/')
@require_permiso('acceder_tareas_y_subidas')
def index():
    """Cola de tareas administrativas + subida de documentos al pool (#501)."""
    tipos_expediente = [
        {'id': te.id, 'tipo': te.tipo}
        for te in TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    ]
    return render_template('tareas_y_subidas/index.html', tipos_expediente=tipos_expediente)


@bp.route('/tarea/<int:tarea_id>/fragmento')
@require_permiso('acceder_tareas_y_subidas')
def tarea_fragmento(tarea_id):
    """Fragmento de lectura del inspector de la cola (ADR-023 §9 / #501).

    Reutiliza detalle_nodo (el mismo detalle que el inspector del árbol). Solo
    lectura: toda mutación se delega al árbol vía "Ir a tramitar".
    """
    tarea = Tarea.query.get_or_404(tarea_id)
    expediente = tarea.tramite.fase.solicitud.expediente
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return '', 403

    detalle = detalle_de_nodo(expediente, 'tarea', tarea_id)
    return render_template(
        'tareas_y_subidas/_inspector_cola.html',
        detalle=detalle,
        expediente=expediente,
        tarea_id=tarea_id,
    )
