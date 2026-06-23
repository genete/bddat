"""Blueprint de la vista "Mi trabajo" (#501, ADR-017).

RUTAS:
    GET /mi_trabajo/                         → role-adaptive:
        ADMINISTRATIVO    → isla React (cola + subir documento).
        SUPERVISOR/ADMIN  → hub de dos bloques del supervisor (#579, ADR-028).
        TRAMITADOR        → redirect al seguimiento (su "mi trabajo" actual).
    GET /mi_trabajo/tarea/<id>/fragmento     → parcial de lectura del inspector de
        la cola (ADR-023 §9 / Opción A): detalle de la tarea en lenguaje del árbol,
        con "Ir a tramitar". La edición se delega al árbol.

La entrada de sidebar es única para todos los roles (ADR-013); la adaptación por
rol ocurre en el destino, no en la navegación. El futuro "Mi trabajo del supervisor"
enriquecerá el caso no-administrativo sin tocar esta entrada.
"""
from flask import Blueprint, render_template, redirect, url_for, session
from flask_login import login_required

from app.models.tareas import Tarea
from app.models.tipos_expedientes import TipoExpediente
from app.utils.permisos import verificar_acceso_expediente
from app.services.detalle_nodo import detalle_de_nodo

bp = Blueprint('mi_trabajo', __name__,
               url_prefix='/mi_trabajo',
               template_folder='templates')


@bp.route('/')
@login_required
def index():
    """Vista "Mi trabajo" — role-adaptive (#501, #579).

    ADMINISTRATIVO ve la cola; SUPERVISOR/ADMIN su hub de dos bloques; el
    TRAMITADOR cae al seguimiento.
    """
    rol_activo = session.get('rol_activo_nombre')
    if rol_activo in ('SUPERVISOR', 'ADMIN'):
        # El "mi trabajo" del supervisor es su hub de dos bloques (#579, ADR-028).
        return redirect(url_for('supervisor.index'))
    if rol_activo != 'ADMINISTRATIVO':
        # Para el tramitador su "mi trabajo" hoy es el seguimiento.
        return redirect(url_for('expedientes.seguimiento'))

    tipos_expediente = [
        {'id': te.id, 'tipo': te.tipo}
        for te in TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    ]
    return render_template('mi_trabajo/index.html', tipos_expediente=tipos_expediente)


@bp.route('/tarea/<int:tarea_id>/fragmento')
@login_required
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
        'mi_trabajo/_inspector_cola.html',
        detalle=detalle,
        expediente=expediente,
        tarea_id=tarea_id,
    )
