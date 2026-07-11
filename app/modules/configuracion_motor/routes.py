"""
Blueprint "Configuración del motor" (#479, ADR-028 bloque Gestión).

Hoy solo cubre el selector de modo global (#479; backend de #323). La sección
de reglas del motor (#170) se añadirá a esta misma página cuando se construya
— es la misma ruta prevista en el hub del supervisor para "Configuración del
motor", no una pantalla aparte.

RUTAS:
    GET  /configuracion-motor/              → página con el selector + próximamente reglas.
    POST /configuracion-motor/modo-global    → guarda el modo elegido.
    GET  /configuracion-motor/estado         → JSON {modo} de solo lectura, para el
                                               semáforo de la topbar (visible a los 4 roles).
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import require_permiso
from app.models.configuracion_sistema import ConfiguracionSistema
from app.services import bitacora as bitacora_svc
from app.services.motor_modo_global import CLAVE_MODO
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'configuracion_motor',
    __name__,
    url_prefix='/configuracion-motor',
    template_folder='templates',
)

MODOS = [
    ('BLOQUEAR', 'Bloquear',
     'Comportamiento normal: el motor bloquea y advierte según las reglas.'),
    ('SOLO_ADVERTIR', 'Solo advertir',
     'Las prohibiciones se convierten en advertencias. Ninguna acción queda bloqueada.'),
    ('INACTIVO', 'Inactivo',
     'El motor no evalúa. Toda acción se permite sin restricciones.'),
]
_MODOS_VALIDOS = {codigo for codigo, _, _ in MODOS}
_ETIQUETAS = {codigo: etiqueta for codigo, etiqueta, _ in MODOS}
_CLASES_SEMAFORO = {'BLOQUEAR': 'success', 'SOLO_ADVERTIR': 'warning', 'INACTIVO': 'danger'}


@bp.route('/')
@login_required
@require_permiso('acceder_reglas_motor')
def index():
    modo_actual = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return render_template(
        'configuracion_motor/index.html',
        modos=MODOS,
        modo_actual=modo_actual,
        puede_gestionar=tiene_permiso('gestionar_reglas_motor'),
    )


@bp.route('/modo-global', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def guardar_modo_global():
    nuevo_modo = request.form.get('modo')
    if nuevo_modo not in _MODOS_VALIDOS:
        flash('Modo no válido.', 'danger')
        return redirect(url_for('configuracion_motor.index'))

    modo_anterior = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    if nuevo_modo != modo_anterior:
        ConfiguracionSistema.set(CLAVE_MODO, nuevo_modo)
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'configuracion_sistema', 0,
            columna=CLAVE_MODO,
            detalle={'de': modo_anterior, 'a': nuevo_modo},
        )
        db.session.commit()
        flash(f'Modo global del motor actualizado a «{nuevo_modo}».', 'success')
    else:
        flash('El modo elegido ya estaba activo.', 'info')

    return redirect(url_for('configuracion_motor.index'))


@bp.route('/estado')
@login_required
def estado():
    """Solo lectura, sin permiso de gestión — el semáforo lo ve cualquier rol autenticado.

    Devuelve también etiqueta/clase para que el JS de la topbar no duplique el mapeo.
    """
    modo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return jsonify({
        'modo': modo,
        'etiqueta': _ETIQUETAS.get(modo, modo),
        'clase': _CLASES_SEMAFORO.get(modo, 'secondary'),
    })


def estado_semaforo() -> dict:
    """Helper para el context processor global (primer render, sin esperar al polling JS)."""
    modo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return {
        'modo': modo,
        'etiqueta': _ETIQUETAS.get(modo, modo),
        'clase': _CLASES_SEMAFORO.get(modo, 'secondary'),
    }
