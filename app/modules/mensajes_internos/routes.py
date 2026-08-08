"""
Blueprint de la bandeja de peticiones al Supervisor (#28, ADR-040).

Listado + inspector (ADR-023), sin patrones nuevos: `lista_v2_base.html` +
`ScrollInfinito` en modo `selection: { fragmentUrl }` + `_detalle_fragmento` /
`_editar_fragmento`, con `inspector:saved → reload()` ya cableado.

QUIÉN VE QUÉ — se decide aquí, nunca en el front (ADR-040 §7):
- `acceder_mensajes_internos` (4 roles): ve SOLO las peticiones que él envió.
- `gestionar_mensajes_internos` (ADMIN/SUPERVISOR): ve las de todos y es el
  único que puede resolverlas.
- El acuse es del REMITENTE y solo del remitente: un supervisor no puede acusar
  por otro, aunque pueda verla.

Rutas:
- GET  /mensajes_internos/                     — Listado (scroll infinito + inspector)
- GET  /mensajes_internos/<id>/                — Redirige al listado con el inspector abierto
- GET  /mensajes_internos/<id>/fragmento       — Fragmento de lectura
- GET  /mensajes_internos/<id>/editar-fragmento — Fragmento de resolución (solo gestionar)
- POST /mensajes_internos/<id>/resolver        — Cierra la petición (solo gestionar)
- POST /mensajes_internos/<id>/acusar          — Acuse del remitente
"""
from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from app import db
from app.decorators import require_permiso
from app.models.mensajes_internos import MensajeInterno
from app.services import mensajes_internos as servicio
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'mensajes_internos',
    __name__,
    url_prefix='/mensajes_internos',
    template_folder='templates',
)

ESTADOS = [
    ('pendiente', 'Pendientes'),
    ('resuelto',  'Resueltas sin acusar'),
    ('acusado',   'Acusadas'),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mensaje_o_403(id):
    """Devuelve el mensaje si el rol activo puede verlo; 404/403 si no.

    Ver una petición ajena exige `gestionar_mensajes_internos`. Sin él, la
    bandeja del usuario son sus propias peticiones y nada más — forzar un id
    ajeno por URL o por consola da 403.
    """
    mensaje = MensajeInterno.query.get_or_404(id)
    if tiene_permiso('gestionar_mensajes_internos'):
        return mensaje
    if mensaje.remitente_usuario_id == current_user.id:
        return mensaje
    abort(403)


def _es_xhr():
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _responder(ok, msg, id, *, errores=None):
    """Respuesta dual XHR/navegación, como el resto de inspectores del proyecto."""
    if _es_xhr():
        if ok:
            return jsonify({'ok': True, 'message': msg})
        return jsonify({'ok': False, 'errors': errores or [msg]})
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('mensajes_internos.listado', sel=id))


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_mensajes_internos')
def listado():
    """Listado de la bandeja — scroll infinito + inspector overlay (ADR-023)."""
    return render_template(
        'mensajes_internos/listado.html',
        estados=ESTADOS,
        tipos=[(t.codigo, t.etiqueta) for t in servicio.TIPOS.values()],
    )


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_mensajes_internos')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    _mensaje_o_403(id)
    return redirect(url_for('mensajes_internos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_mensajes_internos')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    mensaje = _mensaje_o_403(id)
    es_remitente = mensaje.remitente_usuario_id == current_user.id
    return render_template(
        'mensajes_internos/_detalle_fragmento.html',
        mensaje=mensaje,
        campos=servicio.describir(mensaje),
        etiqueta_tipo=servicio.etiqueta_tipo(mensaje.tipo),
        etiquetas_resultado=servicio.ETIQUETAS_RESULTADO,
        etiquetas_estado=servicio.ETIQUETAS_ESTADO,
        # Resolver es de quien gestiona; acusar, del remitente y solo suyo.
        puede_resolver=tiene_permiso('gestionar_mensajes_internos') and not mensaje.hecho,
        puede_acusar=es_remitente and mensaje.hecho and mensaje.acusado_at is None,
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_mensajes_internos')
def editar_fragmento(id):
    """Fragmento de resolución para el inspector (veredicto + notas)."""
    mensaje = MensajeInterno.query.get_or_404(id)
    return render_template(
        'mensajes_internos/_editar_fragmento.html',
        mensaje=mensaje,
        campos=servicio.describir(mensaje),
        etiqueta_tipo=servicio.etiqueta_tipo(mensaje.tipo),
        resultados=[(codigo, servicio.ETIQUETAS_RESULTADO[codigo])
                    for codigo in servicio.RESULTADOS],
    )


@bp.route('/<int:id>/resolver', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_mensajes_internos')
def resolver(id):
    """Cierra la petición: veredicto + notas sobre la MISMA fila (ADR-040 §3)."""
    mensaje = MensajeInterno.query.get_or_404(id)

    # GET → la resolución vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('mensajes_internos.listado', sel=id))

    if mensaje.hecho:
        return _responder(False, 'Esta petición ya estaba resuelta.', id)

    try:
        servicio.resolver(
            mensaje,
            resultado=request.form.get('resultado', '').strip(),
            notas=request.form.get('notas', ''),
            usuario_id=current_user.id,
        )
        db.session.commit()
    except servicio.PayloadInvalido as e:
        db.session.rollback()
        return _responder(False, str(e), id)
    except Exception as e:
        db.session.rollback()
        return _responder(False, f'Error al guardar: {e}', id)

    return _responder(True, 'Petición resuelta. El remitente la verá en su bandeja.', id)


@bp.route('/<int:id>/acusar', methods=['POST'])
@login_required
@require_permiso('acceder_mensajes_internos')
def acusar(id):
    """Acuse explícito del remitente (ADR-040 §7).

    Solo el remitente, aunque quien gestiona pueda ver la fila: el acuse dice
    "me he enterado", y de eso no puede responder un tercero.
    """
    mensaje = MensajeInterno.query.get_or_404(id)
    if mensaje.remitente_usuario_id != current_user.id:
        abort(403)

    try:
        servicio.acusar(mensaje)
        db.session.commit()
    except servicio.PayloadInvalido as e:
        db.session.rollback()
        return _responder(False, str(e), id)

    return _responder(True, 'Respuesta acusada.', id)
