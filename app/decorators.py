from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """
    Decorador para restringir acceso por roles.
    Uso: @role_required('ADMIN', 'SUPERVISOR')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debe iniciar sesión para acceder', 'warning')
                return redirect(url_for('auth.login'))
            
            # Verificar si el usuario tiene alguno de los roles requeridos
            user_roles = [rol.nombre for rol in current_user.roles]
            
            if not any(rol in user_roles for rol in roles):
                flash('No tiene permisos suficientes para acceder a esta sección', 'danger')
                return redirect(url_for('perfil.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
