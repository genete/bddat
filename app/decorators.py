from functools import wraps
from flask import flash, redirect, url_for, session
from flask_login import current_user


def require_permiso(nombre_permiso):
    """
    Decorador que verifica el permiso por nombre contra el dict PERMISOS (#174).
    Uso: @require_permiso('gestionar_plantillas')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))
            from app.utils.permisos import tiene_permiso
            if not tiene_permiso(nombre_permiso):
                flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                return redirect(url_for('perfil.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*roles):
    """
    Decorador para restringir acceso por roles.
    Comprueba el ROL ACTIVO de sesión, no todos los roles del usuario.
    Uso: @role_required('ADMIN', 'SUPERVISOR')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))

            # Verificar contra el rol activo de sesión (no todos los roles posibles)
            rol_activo = session.get('rol_activo_nombre')
            if not rol_activo or rol_activo not in roles:
                flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                return redirect(url_for('perfil.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
