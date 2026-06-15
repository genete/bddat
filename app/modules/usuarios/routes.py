from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from app import db
from app.models.usuarios import Usuario, Rol
from app.decorators import require_permiso
from app.utils.metadata import cargar_metadata
from app.utils.permisos import tiene_permiso

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
@require_permiso('acceder_usuarios')
def index():
    # Roles para el modal de creación y el filtro por rol; columnas del listado_v2.
    # Los usuarios ya no se cargan en Jinja: el listado los pide a /api/usuarios.
    todos_los_roles = Rol.query.all()
    columns = cargar_metadata('usuarios').get('listado_v2', {}).get('columns', [])

    # Variable para controlar si mostrar modal y preservar datos
    form_data = None
    error_siglas = None
    error_email = None

    if request.method == 'POST':
        from flask import abort
        from app.utils.permisos import tiene_permiso as _tp
        if not _tp('gestionar_usuarios'):
            abort(403)
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
                                     columns=columns,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     error_siglas=error_siglas,
                                     show_modal=True)

            # Validación: al menos un rol obligatorio
            if not roles_ids:
                flash('Debes asignar al menos un rol al usuario', 'danger')
                return render_template('usuarios/index.html',
                                     columns=columns,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)

            # Validación de contraseñas
            if password != confirm_password:
                flash('Las contraseñas no coinciden', 'danger')
                return render_template('usuarios/index.html',
                                     columns=columns,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)

            # NUEVA VALIDACIÓN: SUPERVISOR no puede asignar rol ADMIN
            if not current_user_es_admin():
                rol_admin = Rol.query.filter_by(nombre='ADMIN').first()
                if rol_admin and str(rol_admin.id) in roles_ids:
                    flash('No tienes permisos para asignar el rol ADMIN', 'danger')
                    return render_template('usuarios/index.html',
                                         columns=columns,
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
            return redirect(url_for('usuarios.index', sel=nuevo_usuario.id))

        except IntegrityError as e:
            db.session.rollback()
            # Detectar si es error de email duplicado
            if 'usuarios_email_key' in str(e.orig):
                error_email = 'Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'
                return render_template('usuarios/index.html',
                                     columns=columns,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     error_email=error_email,
                                     show_modal=True)
            else:
                flash(f'Error de integridad al crear usuario: {str(e)}', 'danger')
                return render_template('usuarios/index.html',
                                     columns=columns,
                                     roles=todos_los_roles,
                                     form_data=form_data,
                                     show_modal=True)
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear usuario: {str(e)}', 'danger')
            return render_template('usuarios/index.html',
                                 columns=columns,
                                 roles=todos_los_roles,
                                 form_data=form_data,
                                 show_modal=True)

    # GET: Listar todos los usuarios
    return render_template('usuarios/index.html', columns=columns, roles=todos_los_roles)


@bp.route('/<int:id>')
@login_required
@require_permiso('acceder_usuarios')
def detalle(id):
    """Redirige al listado con el inspector abierto en ese usuario (ADR-023 §9 / #544)."""
    Usuario.query.get_or_404(id)
    return redirect(url_for('usuarios.index', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_usuarios')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector (ADR-023 §9 / #544)."""
    usuario = Usuario.query.get_or_404(id)
    # El botón "Editar" solo se ofrece si quien mira puede editar a ESTE usuario:
    # con gestionar_usuarios y, salvo que sea admin, no sobre un usuario ADMIN.
    # Evita que el inspector llegue al 403 de editar_fragmento (SUPERVISOR→ADMIN).
    puede_editar = (
        tiene_permiso('gestionar_usuarios')
        and (current_user_es_admin() or not usuario_es_admin(usuario))
    )
    return render_template('usuarios/_detalle_fragmento.html',
                           usuario=usuario, puede_editar=puede_editar)


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_usuarios')
def editar_fragmento(id):
    """Fragmento HTML de edición para el inspector (ADR-023 §5 / #544)."""
    usuario = Usuario.query.get_or_404(id)
    # SUPERVISOR no puede editar usuarios ADMIN
    if not current_user_es_admin() and usuario_es_admin(usuario):
        return ('<div class="p-3"><div class="alert alert-danger mb-0">'
                'No tienes permisos para editar usuarios ADMIN.</div></div>'), 403
    todos_los_roles = Rol.query.all()
    return render_template('usuarios/_editar_fragmento.html',
                           usuario=usuario, roles=todos_los_roles,
                           puede_editar_siglas=current_user.es_admin,
                           puede_editar_admin=current_user.es_admin)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_usuarios')
def editar(id):
    """Edición de usuario (ADR-023 §5 / #544).

    GET  → redirect al listado con el inspector abierto.
    POST → JSON {ok, errors|message} si X-Requested-With:XMLHttpRequest;
           flash + redirect a ?sel como fallback sin JS.

    Preserva las reglas de negocio: siglas/email únicos, último ADMIN,
    SUPERVISOR no toca ADMIN, no autodesactivarse, contraseñas.
    """
    usuario = Usuario.query.get_or_404(id)
    todos_los_roles = Rol.query.all()
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'GET':
        return redirect(url_for('usuarios.index', sel=id))

    def _responder_errores(errores):
        """Devuelve los errores como JSON (XHR) o flash + redirect (fallback)."""
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('usuarios.index', sel=id))

    # SUPERVISOR no puede editar usuarios ADMIN
    if not current_user_es_admin() and usuario_es_admin(usuario):
        return _responder_errores(['No tienes permisos para editar usuarios ADMIN'])

    # --- Recoger datos ---
    nuevas_siglas    = request.form.get('siglas', '').strip()
    nombre           = request.form.get('nombre', '').strip()
    apellido1        = request.form.get('apellido1', '').strip()
    apellido2        = request.form.get('apellido2', '').strip() or None
    email            = request.form.get('email', '').strip()
    activo_nuevo     = 'activo' in request.form
    roles_ids        = request.form.getlist('roles')
    nueva_password   = request.form.get('nueva_password', '')
    confirm_password = request.form.get('confirm_password', '')

    roles_seleccionados  = Rol.query.filter(Rol.id.in_(roles_ids)).all() if roles_ids else []
    roles_nombres_nuevos = [r.nombre for r in roles_seleccionados]
    user_roles_actuales  = [rol.nombre for rol in usuario.roles]

    # --- Validaciones (se acumulan para devolverlas juntas) ---
    errores = []

    if not nuevas_siglas:
        errores.append('Las siglas son obligatorias.')
    elif nuevas_siglas != usuario.siglas and Usuario.query.filter_by(siglas=nuevas_siglas).first():
        errores.append(f'Las siglas "{nuevas_siglas}" ya están en uso. Por favor, elige otras.')

    if not nombre:
        errores.append('El nombre es obligatorio.')
    if not apellido1:
        errores.append('El primer apellido es obligatorio.')

    # SUPERVISOR no puede asignar/quitar el rol ADMIN
    if not current_user_es_admin():
        rol_admin = Rol.query.filter_by(nombre='ADMIN').first()
        admin_en_form = bool(rol_admin and str(rol_admin.id) in roles_ids)
        if admin_en_form and not usuario_es_admin(usuario):
            errores.append('No tienes permisos para asignar el rol ADMIN')
        if usuario_es_admin(usuario) and not admin_en_form:
            errores.append('No tienes permisos para quitar el rol ADMIN')

    # No quitar el rol ADMIN al último administrador
    if 'ADMIN' in user_roles_actuales and 'ADMIN' not in roles_nombres_nuevos:
        admins_totales = Usuario.query.join(Usuario.roles).filter(Rol.nombre == 'ADMIN').count()
        if admins_totales <= 1:
            errores.append('No puedes quitar el rol ADMIN del último administrador')

    # No desactivarse a sí mismo
    if usuario.id == current_user.id and not activo_nuevo:
        errores.append('No puedes desactivar tu propia cuenta')

    # No desactivar el último ADMIN activo
    if usuario.activo and not activo_nuevo and 'ADMIN' in user_roles_actuales:
        admins_activos = Usuario.query.join(Usuario.roles).filter(
            Rol.nombre == 'ADMIN', Usuario.activo == True
        ).count()
        if admins_activos <= 1:
            errores.append('No puedes desactivar el último administrador activo del sistema')

    # Contraseñas
    if nueva_password and nueva_password != confirm_password:
        errores.append('Las contraseñas no coinciden')

    if errores:
        return _responder_errores(errores)

    # --- Aplicar cambios ---
    try:
        usuario.siglas    = nuevas_siglas
        usuario.nombre    = nombre
        usuario.apellido1 = apellido1
        usuario.apellido2 = apellido2
        usuario.email     = email  # el setter del modelo convierte '' a None
        usuario.activo    = activo_nuevo
        usuario.roles     = roles_seleccionados
        if nueva_password:
            usuario.set_password(nueva_password)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        if 'usuarios_email_key' in str(e.orig):
            return _responder_errores(['Este email ya está registrado por otro usuario. Usa uno diferente o déjalo vacío.'])
        return _responder_errores([f'Error de integridad al actualizar usuario: {str(e)}'])
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al actualizar usuario: {str(e)}'])

    msg = f'Usuario {usuario.siglas} actualizado correctamente'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('usuarios.index', sel=id))
