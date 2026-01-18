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
