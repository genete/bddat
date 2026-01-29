"""Blueprint para gestión de proyectos de instalaciones de alta tensión."""
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.usuarios import Usuario, Rol
from app.models.tipos_ia import TipoIA
from app.models.municipios import Municipio
from app.models.municipios_proyecto import MunicipioProyecto

bp = Blueprint('proyectos', __name__, url_prefix='/proyectos')


@bp.route('/')
@login_required
def index():
    """
    Listado de proyectos con filtros y ordenamiento.
    
    Parámetros GET:
    - tipo_ia: ID del tipo de instalación (instrumento ambiental)
    - provincia: Código de provincia (2 dígitos)
    - responsable: ID del usuario responsable (solo ADMIN/SUPERVISOR)
    - sort: Campo de ordenamiento (titulo, tipo_ia, expediente, responsable, fecha)
    - order: Dirección de ordenamiento (asc, desc)
    """
    # Query base con joins necesarios para ordenamiento
    # IMPORTANTE: outerjoin con Usuario para incluir expedientes sin responsable (NULL)
    query = db.session.query(Proyecto).join(
        Expediente
    ).outerjoin(
        Usuario, Expediente.responsable_id == Usuario.id
    ).outerjoin(
        TipoIA, Proyecto.ia_id == TipoIA.id
    )
    
    # Aplicar filtro de permisos según rol
    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        # TRAMITADOR puro: solo proyectos de sus expedientes
        query = query.filter(Expediente.responsable_id == current_user.id)
    # ADMIN y SUPERVISOR ven todos los proyectos (incluyendo huérfanos con responsable=NULL)
    
    # Filtro por tipo de instrumento ambiental
    tipo_ia_id = request.args.get('tipo_ia', type=int)
    if tipo_ia_id:
        query = query.filter(Proyecto.ia_id == tipo_ia_id)
    
    # Filtro por provincia (a través de municipios)
    provincia_codigo = request.args.get('provincia', type=str)
    if provincia_codigo:
        # Subconsulta para proyectos que tienen al menos un municipio de esa provincia
        subquery = db.session.query(MunicipioProyecto.proyecto_id).join(
            Municipio, MunicipioProyecto.municipio_id == Municipio.id
        ).filter(
            func.substring(func.cast(Municipio.codigo, db.String), 1, 2) == provincia_codigo
        ).distinct()
        
        query = query.filter(Proyecto.id.in_(subquery))
    
    # Filtro por responsable (solo para ADMIN/SUPERVISOR)
    if current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        responsable_id = request.args.get('responsable', type=int)
        if responsable_id:
            query = query.filter(Expediente.responsable_id == responsable_id)
    
    # Parámetros de ordenamiento
    sort_by = request.args.get('sort', 'fecha')
    order = request.args.get('order', 'desc')
    
    # Mapeo seguro de columnas para ordenamiento (prevenir SQL injection)
    sort_columns = {
        'titulo': Proyecto.titulo,
        'tipo_ia': TipoIA.siglas,
        'expediente': Expediente.numero_at,
        'responsable': Usuario.nombre,
        'fecha': Proyecto.fecha
    }
    
    # Aplicar ordenamiento
    if sort_by in sort_columns:
        column = sort_columns[sort_by]
        if order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        # Fallback a ordenamiento por defecto
        query = query.order_by(Proyecto.fecha.desc())
    
    # Ejecutar query
    proyectos = query.all()
    
    # Cargar datos para filtros
    tipos_ia = db.session.query(TipoIA).order_by(TipoIA.siglas).all()
    
    # Provincias de Andalucía
    provincias = [
        ('04', 'Almería'),
        ('11', 'Cádiz'),
        ('14', 'Córdoba'),
        ('18', 'Granada'),
        ('21', 'Huelva'),
        ('23', 'Jaén'),
        ('29', 'Málaga'),
        ('41', 'Sevilla')
    ]
    
    # Responsables (solo para ADMIN/SUPERVISOR)
    # Obtener usuarios que son responsables de al menos un expediente
    responsables = []
    if current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        responsables = db.session.query(Usuario).join(
            Expediente, Usuario.id == Expediente.responsable_id
        ).distinct().order_by(Usuario.nombre).all()
    
    return render_template(
        'proyectos/index.html',
        proyectos=proyectos,
        tipos_ia=tipos_ia,
        provincias=provincias,
        responsables=responsables,
        filtros_activos={
            'tipo_ia': tipo_ia_id,
            'provincia': provincia_codigo,
            'responsable': request.args.get('responsable', type=int)
        },
        sort_by=sort_by,
        order=order
    )


@bp.route('/<int:id>')
@login_required
def detalle(id):
    """
    Vista detallada de un proyecto individual.
    
    Muestra toda la información del proyecto: datos básicos, localización,
    expediente asociado, documentos (maqueta) y solicitudes futuras (maqueta).
    
    Parámetros:
        id (int): ID del proyecto
    
    Permisos:
        - TRAMITADOR: Solo ve proyectos de sus expedientes asignados
        - ADMIN/SUPERVISOR: Ve cualquier proyecto
    
    Returns:
        Template proyectos/detalle.html o 403/404
    """
    # Query con joins necesarios
    proyecto = db.session.query(Proyecto).join(
        Expediente
    ).outerjoin(
        Usuario, Expediente.responsable_id == Usuario.id
    ).outerjoin(
        TipoIA, Proyecto.ia_id == TipoIA.id
    ).filter(Proyecto.id == id).first()
    
    # 404 si no existe
    if not proyecto:
        abort(404)
    
    # Verificar permisos
    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        # TRAMITADOR solo ve proyectos de sus expedientes
        if proyecto.expediente.responsable_id != current_user.id:
            abort(403)
    
    return render_template(
        'proyectos/detalle.html',
        proyecto=proyecto
    )


@bp.route('/<int:id>/editar')
@login_required
def editar_proyecto(id):
    """
    Redirige a la edición del expediente asociado con scroll automático a proyecto.
    
    ESTRATEGIA: Opción A - Redirección inteligente (issue #41)
    En lugar de duplicar lógica de formulario, reutilizamos el formulario de
    expediente existente y redirigimos con anchor #proyecto para scroll automático.
    
    Ventajas:
    - Reutiliza lógica existente (DRY)
    - Mantiene coherencia con relación 1:1 expediente-proyecto
    - No duplica validaciones
    - Implementación simple y mantenible
    
    Parámetros:
        id (int): ID del proyecto
    
    Permisos:
        Mismos que vista detalle (verificados en editar_expediente)
    
    Returns:
        Redirect a /expedientes/<expediente_id>/editar#proyecto
    """
    # Buscar proyecto con expediente asociado
    proyecto = db.session.query(Proyecto).join(
        Expediente
    ).filter(Proyecto.id == id).first()
    
    # 404 si no existe
    if not proyecto:
        abort(404)
    
    # Verificar permisos (mismo criterio que detalle)
    if current_user.tiene_rol('TRAMITADOR') and not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        if proyecto.expediente.responsable_id != current_user.id:
            abort(403)
    
    # Redirigir a edición de expediente con anchor #proyecto
    return redirect(url_for('expedientes.editar_expediente', id=proyecto.expediente.id) + '#proyecto')
