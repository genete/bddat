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

# Regla de recepción de #764 (ADR-004 y ADR-010, notas 2026-08-07;
# `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §5): el vínculo PRODUCIDO de
# ESPERAR_PLAZO es de cardinalidad 1 y se reserva al documento que acredita el
# hecho y porta su fecha administrativa; los anexos que lleguen con él entran al
# pool y los consume el ANALIZAR siguiente. La regla no estaba en ninguna parte
# de la interfaz y quien tramita no sabía cuál de los documentos recién llegados
# elegir (#766).
#
# GEMELO EN REACT: `AYUDA_PRODUCIDO_ESPERAR_PLAZO` en
# `react-src/src/expediente-arbol/components/Despensa.jsx` — misma redacción para
# los dos sitios donde aparece la decisión (aquí, la cola; allí, el árbol, que es
# donde se vincula de verdad). Si cambia una, cambiar la otra.
AYUDA_PRODUCIDO_ESPERAR_PLAZO = (
    'Vincula el documento que acredita la recepción y su fecha: registro de entrada, '
    'solicitud, justificante de BandeJA o acuse de publicación. Los anexos que lo '
    'acompañen se consumen después, en la tarea de análisis.'
)


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
    codigo_tarea = tarea.tipo_tarea.codigo if tarea.tipo_tarea else None
    return render_template(
        'tareas_y_subidas/_inspector_cola.html',
        detalle=detalle,
        expediente=expediente,
        tarea_id=tarea_id,
        # #766: la ayuda solo tiene sentido en ESPERAR_PLAZO, que es la única
        # tarea cuyo producido es un documento recibido de fuera.
        ayuda_producido=(AYUDA_PRODUCIDO_ESPERAR_PLAZO
                         if codigo_tarea == 'ESPERAR_PLAZO' else None),
    )
