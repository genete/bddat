from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.usuarios import Usuario, Rol
from app.decorators import role_required

# Definimos el Blueprint con template_folder propio (convención app/modules/)
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios',
               template_folder='templates')

def usuario_es_admin(usuario):
    """Verifica si un usuario tiene el rol ADMIN"""
    return any(rol.nombre == 'ADMIN' for rol in usuario.roles)

def current_user_es_admin():
    """Verifica si el usuario actual tiene el rol ADMIN"""
    return any(rol.nombre == 'ADMIN' for rol in current_user.roles)

@bp.route('/', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def index():
    # Recuperamos todos los roles para el formulario
    todos_los_roles = Rol.query.all()
    usuarios = Usuario.query.all()

    # Variable para controlar si mostrar modal y preservar datos
    form_data = None
    error_siglas = None
    error_email = None

    if request.method == 'POST':
        # Lógica para crear usuario
        try:
            siglas = request.form['siglas']
            nombre = request.form['nombre']
            apellido1 = request.form['apellido1']
            apellido2 = request.form.get('apellido2')
            email = request.form.get('email')

            password = request.form['password']
            confirm_password = request.form['confirm_password']

            # Capturar roles seleccionados para preservarlos
            roles_ids = request.form.getlist('roles')

            # Preparar datos del formulario para devolver en caso de error
            form_data = {
                'siglas': siglas,
                'nombre': nombre,
                'apellido1': apellido1,
                'apellido2': apellido2,
                'email': email,
                'roles_ids': roles_ids
            }

            # VALIDACIÓN PREVENTIVA: Verificar si las siglas ya existen
            if Usuario.query.filter_by(siglas=siglas).first():
                error_siglas = f'Las siglas "{siglas}" ya están en uso. Por favor, elige otras.'
                return render_template('usuarios/index.html',
                                     usuarios=usuarios,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     error_siglas=error_siglas,
                                     show_modal=True)

            # Validación: al menos un rol obligatorio
            if not roles_ids:
                flash('Debes asignar al menos un rol al usuario', 'danger')
                return render_template('usuarios/index.html',
                                     usuarios=usuarios,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)

            # Validación de contraseñas
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('usuarios/index.html',
                                     usuarios=usuarios,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)

            # NUEVA VALIDACIÓN: SUPERVISOR no puede asignar rol ADMIN
            if not current_user_es_admin():
                rol_admin = Rol.query.filter_by(nombre='ADMIN').first()
                if rol_admin and str(rol_admin.id) in roles_ids:
                    flash('No tienes permisos para asignar el rol ADMIN', 'danger')
                    return render_template('usuarios/index.html',
                                         usuarios=usuarios,
                                         roles=todos_los_roles,
                                         form_data=form_data,
                                         show_modal=True)

            # Crear instancia del modelo
            nuevo_usuario = Usuario(
                siglas=siglas,
                nombre=nombre,
                apellido1=apellido1,
                apellido2=apellido2
            )

            # Asignar email (el setter del modelo convertirá '' a None)
            nuevo_usuario.email = email

            # Establecer contraseña (hash)
            nuevo_usuario.set_password(password)

            # Asignar Roles
            if roles_ids:
                roles_seleccionados = Rol.query.filter(Rol.id.in_(roles_ids)).all()
                nuevo_usuario.roles.extend(roles_seleccionados)

            # Guardar en BD
            db.session.add(nuevo_usuario)
            db.session.commit()

            flash('Usuario creado correctamente con roles y contraseña', 'success')
            return redirect(url_for('usuarios.index'))

        except IntegrityError as e:
            db.session.rollback()
            # Detectar si es error de email duplicado
            if 'usuarios_email_key' in str(e.orig):
                error_email = 'Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'
                return render_template('usuarios/index.html',
                                     usuarios=usuarios,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     error_email=error_email,
                                     show_modal=True)
            else:
                flash(f'Error de integridad al crear usuario: {str(e)}', 'danger')
                return render_template('usuarios/index.html',
                                     usuarios=usuarios,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')
            return render_template('usuarios/index.html',
                                 usuarios=usuarios,
                                 roles=todos_los_roles,
                                 form_data=form_data,
                                 show_modal=True)

    # GET: Listar todos los usuarios
    return render_template('usuarios/index.html', usuarios=usuarios, roles=todos_los_roles)


@bp.route('/<int:id>')
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def detalle(id):
    usuario = Usuario.query.get_or_404(id)
    roles = Rol.query.all()
    return render_template('usuarios/detalle.html',
                           usuario=usuario, roles=roles,
                           modo='ver',
                           puede_editar_siglas=current_user.es_admin,
                           puede_editar_admin=current_user.es_admin)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def editar(id):
    usuario = Usuario.query.get_or_404(id)
    todos_los_roles = Rol.query.all()

    # NUEVA VALIDACIÓN: SUPERVISOR no puede editar usuarios ADMIN
    if not current_user_es_admin() and usuario_es_admin(usuario):
        flash('No tienes permisos para editar usuarios ADMIN', 'danger')
        return redirect(url_for('usuarios.index'))

    # Variables para errores
    error_siglas = None
    error_email = None

    if request.method == 'POST':
        try:
            # VALIDACIÓN PREVENTIVA: Verificar si las siglas ya existen (excepto el usuario actual)
            nuevas_siglas = request.form['siglas']
            if nuevas_siglas != usuario.siglas:  # Solo validar si cambiaron las siglas
                usuario_existente = Usuario.query.filter_by(siglas=nuevas_siglas).first()
                if usuario_existente:
                    error_siglas = f'Las siglas "{nuevas_siglas}" ya están en uso. Por favor, elige otras.'
                    # Preparar form_data para mantener los valores
                    form_data = {
                        'siglas': nuevas_siglas,
                        'nombre': request.form['nombre'],
                        'apellido1': request.form['apellido1'],
                        'apellido2': request.form.get('apellido2'),
                        'email': request.form.get('email'),
                        'activo': 'activo' in request.form,
                        'roles_ids': request.form.getlist('roles')
                    }
                    return render_template('usuarios/detalle.html',
                                         usuario=usuario,
                                         roles=todos_los_roles,
                                         modo='editar',
                                         puede_editar_siglas=current_user.es_admin,
                                         puede_editar_admin=current_user.es_admin,
                                         error_siglas=error_siglas,
                                         form_data=form_data)

            # VALIDACIÓN 1: No permitir quitar rol ADMIN al último ADMIN
            roles_ids = request.form.getlist('roles')
            roles_seleccionados = Rol.query.filter(Rol.id.in_(roles_ids)).all()
            roles_nombres_nuevos = [r.nombre for r in roles_seleccionados]

            # Si el usuario actual es ADMIN y se está quitando el rol
            user_roles_actuales = [rol.nombre for rol in usuario.roles]

            # NUEVA VALIDACIÓN: SUPERVISOR no puede asignar/quitar rol ADMIN
            if not current_user_es_admin():
                rol_admin = Rol.query.filter_by(nombre='ADMIN').first()

                # Verificar si intenta asignar ADMIN
                if rol_admin and str(rol_admin.id) in roles_ids and not usuario_es_admin(usuario):
                    flash('No tienes permisos para asignar el rol ADMIN', 'danger')
                    return render_template('usuarios/detalle.html', usuario=usuario, roles=todos_los_roles,
                                         modo='editar', puede_editar_siglas=current_user.es_admin,
                                         puede_editar_admin=current_user.es_admin)

                # Verificar si intenta quitar ADMIN
                if usuario_es_admin(usuario) and (not rol_admin or str(rol_admin.id) not in roles_ids):
                    flash('No tienes permisos para quitar el rol ADMIN', 'danger')
                    return render_template('usuarios/detalle.html', usuario=usuario, roles=todos_los_roles,
                                         modo='editar', puede_editar_siglas=current_user.es_admin,
                                         puede_editar_admin=current_user.es_admin)

            if 'ADMIN' in user_roles_actuales and 'ADMIN' not in roles_nombres_nuevos:
                # Contar cuántos ADMIN hay en total (activos e inactivos)
                admins_totales = Usuario.query.join(Usuario.roles).filter(
                    Rol.nombre == 'ADMIN'
                ).count()

                if admins_totales <= 1:
                    flash('No puedes quitar el rol ADMIN del último administrador', 'danger')
                    return redirect(url_for('usuarios.editar', id=id))

            # VALIDACIÓN 2: No permitir desactivarse a sí mismo
            activo_nuevo = 'activo' in request.form
            if usuario.id == current_user.id and not activo_nuevo:
                flash('No puedes desactivar tu propia cuenta', 'warning')
                return redirect(url_for('usuarios.editar', id=id))

            # VALIDACIÓN 3: No permitir desactivar el último ADMIN activo
            if usuario.activo and not activo_nuevo:  # Si está intentando desactivar
                if 'ADMIN' in user_roles_actuales:
                    # Contar cuántos ADMIN activos hay
                    admins_activos = Usuario.query.join(Usuario.roles).filter(
                        Rol.nombre == 'ADMIN',
                        Usuario.activo == True
                    ).count()

                    if admins_activos <= 1:
                        flash('No puedes desactivar el último administrador activo del sistema', 'danger')
                        return redirect(url_for('usuarios.editar', id=id))

            # Actualizar datos personales
            usuario.siglas = nuevas_siglas
            usuario.nombre = request.form['nombre']
            usuario.apellido1 = request.form['apellido1']
            usuario.apellido2 = request.form.get('apellido2')
            usuario.email = request.form.get('email')  # El setter del modelo convertirá '' a None

            # Actualizar estado activo (sin mensaje flash - es reversible)
            usuario.activo = activo_nuevo

            # Actualizar roles
            usuario.roles = []
            if roles_ids:
                usuario.roles.extend(roles_seleccionados)

            # Cambiar contraseña solo si se proporciona
            nueva_password = request.form.get('nueva_password')
            if nueva_password:
                confirm_password = request.form.get('confirm_password')
                if nueva_password != confirm_password:
                    # Preparar form_data y mantener diálogo abierto
                    form_data = {
                        'siglas': nuevas_siglas,
                        'nombre': request.form['nombre'],
                        'apellido1': request.form['apellido1'],
                        'apellido2': request.form.get('apellido2'),
                        'email': request.form.get('email'),
                        'activo': activo_nuevo,
                        'roles_ids': roles_ids
                    }
                    flash('Las contraseñas no coinciden', 'danger')
                    return render_template('usuarios/detalle.html',
                                         usuario=usuario,
                                         roles=todos_los_roles,
                                         modo='editar',
                                         puede_editar_siglas=current_user.es_admin,
                                         puede_editar_admin=current_user.es_admin,
                                         form_data=form_data)
                usuario.set_password(nueva_password)

            db.session.commit()
            flash(f'Usuario {usuario.siglas} actualizado correctamente', 'success')
            return redirect(url_for('usuarios.detalle', id=id))

        except IntegrityError as e:
            db.session.rollback()
            # Detectar si es error de email duplicado
            if 'usuarios_email_key' in str(e.orig):
                error_email = 'Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'
                # Preparar form_data para mantener los valores
                form_data = {
                    'siglas': request.form['siglas'],
                    'nombre': request.form['nombre'],
                    'apellido1': request.form['apellido1'],
                    'apellido2': request.form.get('apellido2'),
                    'email': request.form.get('email'),
                    'activo': 'activo' in request.form,
                    'roles_ids': request.form.getlist('roles')
                }
                return render_template('usuarios/detalle.html',
                                     usuario=usuario,
                                     roles=todos_los_roles,
                                     modo='editar',
                                     puede_editar_siglas=current_user.es_admin,
                                     puede_editar_admin=current_user.es_admin,
                                     error_email=error_email,
                                     form_data=form_data)
            else:
                flash(f'Error de integridad al actualizar usuario: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')

    # GET: Mostrar formulario de edición
    return render_template('usuarios/detalle.html', usuario=usuario, roles=todos_los_roles,
                           modo='editar',
                           puede_editar_siglas=current_user.es_admin,
                           puede_editar_admin=current_user.es_admin)


@bp.route('/<int:id>/toggle_estado', methods=['POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR')
def toggle_estado(id):
    """Toggle rápido del estado activo/inactivo"""
    usuario = Usuario.query.get_or_404(id)

    # NUEVA VALIDACIÓN: SUPERVISOR no puede desactivar usuarios ADMIN
    if not current_user_es_admin() and usuario_es_admin(usuario):
        flash('No tienes permisos para modificar el estado de usuarios ADMIN', 'danger')
        return redirect(url_for('usuarios.index'))

    # VALIDACIÓN 1: No permitir desactivarse a sí mismo
    if usuario.id == current_user.id:
        flash('No puedes desactivar tu propia cuenta', 'warning')
        return redirect(url_for('usuarios.index'))

    # VALIDACIÓN 2: No permitir desactivar el último ADMIN
    if usuario.activo:  # Si está intentando desactivar
        user_roles = [rol.nombre for rol in usuario.roles]
        if 'ADMIN' in user_roles:
            # Contar cuántos ADMIN activos hay
            admins_activos = Usuario.query.join(Usuario.roles).filter(
                Rol.nombre == 'ADMIN',
                Usuario.activo == True
            ).count()

            if admins_activos <= 1:
                flash('No puedes desactivar el último administrador del sistema', 'danger')
                return redirect(url_for('usuarios.index'))

    try:
        usuario.activo = not usuario.activo
        db.session.commit()

        # Sin mensaje flash - acción reversible y no destructiva
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')

    return redirect(url_for('usuarios.index'))
