from flask import Blueprint, render_template, request, flash, redirect, url_for
from app import db
from app.models.usuarios import Usuario

# Definimos el Blueprint
bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Lógica básica para crear usuario
        try:
            siglas = request.form['siglas']
            nombre = request.form['nombre']
            apellido1 = request.form['apellido1']
            # apellido2 es opcional, usamos .get()
            apellido2 = request.form.get('apellido2')
            
            # Crear instancia del modelo
            nuevo_usuario = Usuario(
                siglas=siglas,
                nombre=nombre,
                apellido1=apellido1,
                apellido2=apellido2
            )
            
            # Guardar en BD
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash('Usuario creado correctamente', 'success')
            return redirect(url_for('usuarios.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')

    # GET: Listar todos los usuarios
    usuarios = Usuario.query.all()
    return render_template('usuarios/index.html', usuarios=usuarios)