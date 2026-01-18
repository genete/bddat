from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required
from app import db
from app.models.usuarios import Usuario

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        siglas = request.form.get('siglas')
        password = request.form.get('password')
        
        # Buscar usuario por siglas
        usuario = Usuario.query.filter_by(siglas=siglas).first()
        
        # Validar usuario, contraseña y estado activo
        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta con el administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            login_user(usuario)
            flash(f'Bienvenido, {usuario.nombre}!', 'success')
            
            # Redirigir a la página solicitada o al inicio
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('usuarios.index'))
        else:
            flash('Siglas o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
