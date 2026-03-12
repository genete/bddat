from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.usuarios import Usuario

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Vista V0 (Login) - Split-screen con información y formulario.
    Tras validar credenciales:
      - 0 roles  → denegar acceso
      - 1 rol    → guardar en sesión y redirigir al dashboard
      - 2+ roles → re-renderizar el formulario con <select> de roles (segunda pasada)
    Segunda pasada (rol_id presente en el POST):
      - Recuperar usuario de session['pending_login_id']
      - Validar que el rol pertenece al usuario
      - Guardar en sesión y redirigir al dashboard
    """
    if request.method == 'POST':
        rol_id = request.form.get('rol_id')

        # Segunda pasada: el usuario ya validó credenciales y ahora elige rol
        if rol_id and 'pending_login_id' in session:
            from app.models.usuarios import Rol
            usuario = Usuario.query.get(session.pop('pending_login_id'))
            if not usuario:
                flash('La sesión ha expirado. Vuelve a introducir tus credenciales.', 'warning')
                return redirect(url_for('auth.login'))

            try:
                rol = usuario.rol_por_id(int(rol_id))
            except (ValueError, AttributeError):
                rol = None

            if not rol:
                flash('El rol seleccionado no está asignado a tu cuenta.', 'danger')
                return render_template('auth/login_v0.html', roles=usuario.roles)

            login_user(usuario)
            session['rol_activo_id'] = rol.id
            session['rol_activo_nombre'] = rol.nombre
            flash(f'Bienvenido, {usuario.nombre}! Trabajando como {rol.nombre}.', 'success')
            next_page = session.pop('next_after_rol', None) or request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard.index'))

        # Primera pasada: validar credenciales
        siglas = request.form.get('siglas')
        password = request.form.get('password')
        usuario = Usuario.query.filter_by(siglas=siglas).first()

        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta está desactivada. Contacta con el administrador.', 'danger')
                return redirect(url_for('auth.login'))

            if not usuario.roles:
                flash('Tu cuenta no tiene ningún rol asignado. Contacta con el administrador.', 'danger')
                return redirect(url_for('auth.login'))

            if len(usuario.roles) == 1:
                login_user(usuario)
                rol = usuario.roles[0]
                session['rol_activo_id'] = rol.id
                session['rol_activo_nombre'] = rol.nombre
                flash(f'Bienvenido, {usuario.nombre}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page if next_page else url_for('dashboard.index'))
            else:
                # Guardar usuario pendiente y next en sesión para la segunda pasada
                session['pending_login_id'] = usuario.id
                next_page = request.args.get('next')
                if next_page:
                    session['next_after_rol'] = next_page
                return render_template('auth/login_v0.html', roles=usuario.roles)
        else:
            flash('Siglas o contraseña incorrectos.', 'danger')

    return render_template('auth/login_v0.html')


@bp.route('/seleccionar-rol', methods=['GET', 'POST'])
@login_required
def seleccionar_rol():
    """
    Pantalla de selección de rol activo para usuarios con múltiples roles.
    GET  → muestra cards con los roles del usuario actual.
    POST → valida rol_id y lo almacena en sesión.
    """
    if request.method == 'POST':
        try:
            rol_id = int(request.form.get('rol_id', ''))
        except ValueError:
            flash('Selección no válida.', 'danger')
            return redirect(url_for('auth.seleccionar_rol'))

        rol = current_user.rol_por_id(rol_id)
        if not rol:
            # Protección contra escalada de privilegios
            flash('El rol seleccionado no está asignado a tu cuenta.', 'danger')
            return redirect(url_for('auth.seleccionar_rol'))

        session['rol_activo_id'] = rol.id
        session['rol_activo_nombre'] = rol.nombre
        flash(f'Bienvenido, {current_user.nombre}! Trabajando como {rol.nombre}.', 'success')

        next_page = session.pop('next_after_rol', None)
        return redirect(next_page if next_page else url_for('dashboard.index'))

    return render_template('auth/seleccionar_rol.html', roles=current_user.roles)


@bp.route('/cambiar-rol/<int:rol_id>')
@login_required
def cambiar_rol(rol_id):
    """Cambia el rol activo desde el dropdown del navbar (GET directo)."""
    rol = current_user.rol_por_id(rol_id)
    if not rol:
        flash('El rol seleccionado no está asignado a tu cuenta.', 'danger')
        return redirect(url_for('dashboard.index'))

    session['rol_activo_id'] = rol.id
    session['rol_activo_nombre'] = rol.nombre
    flash(f'Rol cambiado a {rol.nombre}.', 'info')
    return redirect(request.referrer or url_for('dashboard.index'))


@bp.route('/logout')
@login_required
def logout():
    session.pop('rol_activo_id', None)
    session.pop('rol_activo_nombre', None)
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))
