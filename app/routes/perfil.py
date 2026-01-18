from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.usuarios import Usuario

bp = Blueprint('perfil', __name__, url_prefix='/perfil')

@bp.route('/', methods=['GET'])
@login_required
def index():
    """Mostrar perfil del usuario actual"""
    return render_template('perfil/index.html', usuario=current_user)

@bp.route('/editar', methods=['POST'])
@login_required
def editar():
    """Editar datos personales del usuario actual"""
    try:
        # Actualizar datos editables
        current_user.nombre = request.form.get('nombre')
        current_user.apellido1 = request.form.get('apellido1')
        current_user.apellido2 = request.form.get('apellido2')
        
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
    """Solicitar cambio de rol (por ahora solo mensaje, futuro: notificación)"""
    # TODO: Implementar sistema de notificaciones o tickets
    flash('Tu solicitud de cambio de rol ha sido enviada. Un supervisor la revisará pronto.', 'info')
    return redirect(url_for('perfil.index'))
