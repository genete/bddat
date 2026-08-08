"""Blueprint "Mi Perfil" (migrado desde app/routes/perfil.py en #589, ADR-029).

Sin metadata.json a propósito: no encaja en el criterio revisado de ADR-029 §1
(página-destino de rol u objeto de dominio) — se alcanza por el menú de usuario
del topbar (_topbar.html), no por sidebar ni Command Palette. La tarjeta del
dashboard sigue hardcodeada, misma excepción que "Inicio".
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.mensajes_internos import MensajeInterno
from app.models.usuarios import Rol, Usuario
from app.services import mensajes_internos as servicio_mensajes

bp = Blueprint('perfil', __name__, url_prefix='/perfil', template_folder='templates')

@bp.route('/', methods=['GET'])
@login_required
def index():
    """Mostrar perfil del usuario actual"""
    # Roles que aún no tiene — los únicos que tiene sentido pedir.
    propios = {r.nombre for r in current_user.roles}
    roles_solicitables = [r for r in Rol.query.order_by(Rol.nombre).all()
                          if r.nombre not in propios]

    # Peticiones de rol suyas aún sin resolver: se AVISA, no se bloquea. Pedir
    # dos veces no rompe nada y puede ser legítimo (cambió el motivo, se olvidó
    # la anterior); quien decide es el Supervisor, que las verá las dos.
    pendientes_rol = MensajeInterno.query.filter(
        MensajeInterno.remitente_usuario_id == current_user.id,
        MensajeInterno.tipo == 'CAMBIO_ROL',
        MensajeInterno.hecho.is_(False),
    ).order_by(MensajeInterno.created_at.desc()).all()

    return render_template(
        'perfil/index.html',
        usuario=current_user,
        roles_solicitables=roles_solicitables,
        pendientes_rol=pendientes_rol,
    )

@bp.route('/editar', methods=['POST'])
@login_required
def editar():
    """Editar datos personales del usuario actual"""
    try:
        # Actualizar datos editables
        current_user.nombre = request.form.get('nombre')
        current_user.apellido1 = request.form.get('apellido1')
        current_user.apellido2 = request.form.get('apellido2')
        current_user.siglas_escritos = request.form.get('siglas_escritos', '').strip() or None
        
        # Email (validar que no esté en uso por otro usuario)
        nuevo_email = request.form.get('email')
        if nuevo_email != current_user.email:
            email_existente = Usuario.query.filter_by(email=nuevo_email).first()
            if email_existente and email_existente.id != current_user.id:
                flash('El email ya está en uso por otro usuario', 'danger')
                return redirect(url_for('perfil.index'))
            current_user.email = nuevo_email
        
        db.session.commit()
        flash('Datos actualizados correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar datos: {str(e)}', 'danger')
    
    return redirect(url_for('perfil.index'))

@bp.route('/cambiar-contrasena', methods=['POST'])
@login_required
def cambiar_contrasena():
    """Cambiar contraseña del usuario actual"""
    try:
        password_actual = request.form.get('password_actual')
        password_nueva = request.form.get('password_nueva')
        password_confirmar = request.form.get('password_confirmar')
        
        # Validar contraseña actual
        if not current_user.check_password(password_actual):
            flash('La contraseña actual es incorrecta', 'danger')
            return redirect(url_for('perfil.index'))
        
        # Validar coincidencia de nueva contraseña
        if password_nueva != password_confirmar:
            flash('Las contraseñas nuevas no coinciden', 'danger')
            return redirect(url_for('perfil.index'))
        
        # Cambiar contraseña
        current_user.set_password(password_nueva)
        db.session.commit()
        
        flash('Contraseña cambiada correctamente', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar contraseña: {str(e)}', 'danger')
    
    return redirect(url_for('perfil.index'))

@bp.route('/solicitar-cambio-rol', methods=['POST'])
@login_required
def solicitar_cambio_rol():
    """Crea una petición CAMBIO_ROL en la bandeja del Supervisor (#28, N054).

    Hasta #28 esto era un `flash` que no persistía nada: el usuario creía haber
    pedido algo que no llegaba a ninguna parte. Ahora el rol pretendido y la
    justificación son datos, no una intención.
    """
    try:
        servicio_mensajes.crear(
            'CAMBIO_ROL',
            current_user.id,
            rol_solicitado=request.form.get('rol_solicitado', ''),
            justificacion=request.form.get('justificacion', ''),
        )
        db.session.commit()
    except servicio_mensajes.PayloadInvalido as e:
        db.session.rollback()
        flash(str(e), 'danger')
        return redirect(url_for('perfil.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al enviar la solicitud: {e}', 'danger')
        return redirect(url_for('perfil.index'))

    flash('Solicitud enviada. La verás resuelta en tu bandeja de mensajes.', 'success')
    return redirect(url_for('perfil.index'))
