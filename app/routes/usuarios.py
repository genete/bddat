from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.usuarios import Usuario, Rol
from app.decorators import role_required

# Definimos el Blueprint
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

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

    if request.method == 'POST':
        # Lógica para crear usuario
        try:
            siglas = request.form['siglas']
            nombre = request.form['nombre']
            apellido1 = request.form['apellido1']
            apellido2 = request.form.get('apellido2')
            
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            # VALIDACIÓN PREVENTIVA: Verificar si las siglas ya existen
            if Usuario.query.filter_by(siglas=siglas).first():
                flash(f'Las siglas "{siglas}" ya están en uso. Por favor, elige otras.', 'warning')
                usuarios = Usuario.query.all()
                return render_template('usuarios/index.html', usuarios=usuarios, roles=todos_los_roles)
            
            # Validación de contraseñas
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return redirect(url_for('usuarios.index'))
            
            # Recuperar roles seleccionados (lista de IDs)
            roles_ids = request.form.getlist('roles')
            
            # NUEVA VALIDACIÓN: SUPERVISOR no puede asignar rol ADMIN
            if not current_user_es_admin():
                rol_admin = Rol.query.filter_by(nombre='ADMIN').first()
                if rol_admin and str(rol_admin.id) in roles_ids:
                    flash('No tienes permisos para asignar el rol ADMIN', 'danger')
                    usuarios = Usuario.query.all()
                    return render_template('usuarios/index.html', usuarios=usuarios, roles=todos_los_roles)
            
            # Crear instancia del modelo
            nuevo_usuario = Usuario(
                siglas=siglas,
                nombre=nombre,
                apellido1=apellido1,
                apellido2=apellido2
            )
            
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
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    # GET: Listar todos los usuarios
    usuarios = Usuario.query.all()
    return render_template('usuarios/index.html', usuarios=usuarios, roles=todos_los_roles)


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
    
    if request.method == 'POST':
        try:
            # VALIDACIÓN PREVENTIVA: Verificar si las siglas ya existen (excepto el usuario actual)
            nuevas_siglas = request.form['siglas']
            if nuevas_siglas != usuario.siglas:  # Solo validar si cambiaron las siglas
                usuario_existente = Usuario.query.filter_by(siglas=nuevas_siglas).first()
                if usuario_existente:
                    flash(f'Las siglas "{nuevas_siglas}" ya están en uso. Por favor, elige otras.', 'warning')
                    return render_template('usuarios/editar.html', usuario=usuario, roles=todos_los_roles)
            
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
                    return render_template('usuarios/editar.html', usuario=usuario, roles=todos_los_roles)
                
                # Verificar si intenta quitar ADMIN
                if usuario_es_admin(usuario) and (not rol_admin or str(rol_admin.id) not in roles_ids):
                    flash('No tienes permisos para quitar el rol ADMIN', 'danger')
                    return render_template('usuarios/editar.html', usuario=usuario, roles=todos_los_roles)
            
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
            usuario.email = request.form.get('email')
            
            # Actualizar estado activo
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
                    flash('Las contraseñas no coinciden', 'danger')
                    return redirect(url_for('usuarios.editar', id=id))
                usuario.set_password(nueva_password)
            
            db.session.commit()
            flash(f'Usuario {usuario.siglas} actualizado correctamente', 'success')
            return redirect(url_for('usuarios.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
    
    # GET: Mostrar formulario
    return render_template('usuarios/editar.html', usuario=usuario, roles=todos_los_roles)


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
        
        estado = "activado" if usuario.activo else "desactivado"
        flash(f'Usuario {usuario.siglas} {estado} correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios.index'))
