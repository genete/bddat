from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.expediente import Expediente

bp = Blueprint('dashboard', __name__, url_prefix='')

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """
    Dashboard principal - muestra bloques de navegación según rol del usuario
    """
    # Detectar roles del usuario actual
    user_roles = [rol.nombre for rol in current_user.roles]
    
    # Definir estructura de bloques con ítems y permisos
    bloques = {
        'Tramitación': {
            'items': [
                {'nombre': 'Mis expedientes', 'url': 'dashboard.mis_expedientes', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Listado expedientes', 'url': 'expedientes.index', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Nuevo expediente', 'url': 'expedientes.nuevo', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Solicitudes', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Fases', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Trámites', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Tareas', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Documentos', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
            ]
        },
        'Configuración': {
            'items': [
                {'nombre': 'Tablas maestras', 'url': '#', 'roles': ['SUPERVISOR', 'ADMIN']},
                {'nombre': 'Gestión estructura', 'url': '#', 'roles': ['SUPERVISOR', 'ADMIN']},
            ]
        },
        'Datos Legacy': {
            'items': [
                {'nombre': 'Consultar legacy', 'url': '#', 'roles': ['TRAMITADOR', 'ADMINISTRATIVO', 'SUPERVISOR', 'ADMIN']},
                {'nombre': 'Gestión legacy', 'url': '#', 'roles': ['ADMIN']},
            ]
        },
        'Sistema': {
            'items': [
                {'nombre': 'Migraciones BD', 'url': '#', 'roles': ['ADMIN']},
                {'nombre': 'Logs del sistema', 'url': '#', 'roles': ['SUPERVISOR', 'ADMIN']},
            ]
        },
    }
    
    # Filtrar ítems según roles del usuario
    bloques_visibles = {}
    for bloque_nombre, bloque_data in bloques.items():
        items_visibles = []
        for item in bloque_data['items']:
            # Verificar si el usuario tiene al menos uno de los roles requeridos
            if any(rol in user_roles for rol in item['roles']):
                items_visibles.append(item)
        
        # Solo incluir bloque si tiene al menos un ítem visible
        if items_visibles:
            bloques_visibles[bloque_nombre] = {'items': items_visibles}
    
    return render_template('dashboard/index.html', bloques=bloques_visibles)


@bp.route('/mis_expedientes')
@login_required
def mis_expedientes():
    """
    Lista expedientes asignados al usuario actual como responsable
    """
    expedientes = Expediente.query.filter_by(
        responsable_id=current_user.id
    ).order_by(Expediente.numero_at.desc()).all()
    
    return render_template(
        'dashboard/mis_expedientes.html',
        expedientes=expedientes,
        titulo='Mis Expedientes'
    )
