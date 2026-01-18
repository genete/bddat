from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.usuarios import Usuario, Rol
from app.decorators import role_required

# Definimos el Blueprint
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

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
            
            # Validación de contraseñas
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return redirect(url_for('usuarios.index'))
            
            # Recuperar roles seleccionados (lista de IDs)
            roles_ids = request.form.getlist('roles')
            
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
    
    if request.method == 'POST':
        try:
            # Actualizar datos personales
            usuario.siglas = request.form['siglas']
            usuario.nombre = request.form['nombre']
            usuario.apellido1 = request.form['apellido1']
            usuario.apellido2 = request.form.get('apellido2')
            usuario.email = request.form.get('email')
            
            # Actualizar estado activo
            usuario.activo = 'activo' in request.form
            
            # Actualizar roles
            roles_ids = request.form.getlist('roles')
            usuario.roles = []  # Limpiar roles actuales
            if roles_ids:
                roles_seleccionados = Rol.query.filter(Rol.id.in_(roles_ids)).all()
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
    
    try:
        usuario.activo = not usuario.activo
        db.session.commit()
        
        estado = "activado" if usuario.activo else "desactivado"
        flash(f'Usuario {usuario.siglas} {estado} correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')
    
    return redirect(url_for('usuarios.index'))
