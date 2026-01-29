"""Blueprint para gestión de proyectos de instalaciones de alta tensión."""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.usuarios import Usuario
from app.models.tipos_instalacion_at import TipoInstalacionAT

bp = Blueprint('proyectos', __name__, url_prefix='/proyectos')


@bp.route('/')
@login_required
def index():
    """
    Listado de proyectos con filtros opcionales.
    
    Filtros GET:
    - tipo_ia: ID del tipo de instalación
    - provincia: Código de provincia (2 dígitos)
    - responsable: ID del usuario responsable (solo ADMIN/SUPERVISOR)
    """
    # Query base con joins necesarios
    query = db.session.query(Proyecto).join(Expediente)
    
    # Aplicar filtro de permisos según rol
    if current_user.rol.nombre == 'TRAMITADOR':
        # TRAMITADOR: solo proyectos de sus expedientes
        query = query.filter(Expediente.id_responsable == current_user.id)
    # ADMIN y SUPERVISOR ven todos los proyectos
    
    # Filtro por tipo de instalación
    tipo_ia_id = request.args.get('tipo_ia', type=int)
    if tipo_ia_id:
        query = query.filter(Proyecto.id_tipo_ia == tipo_ia_id)
    
    # Filtro por provincia (a través de municipios)
    provincia_codigo = request.args.get('provincia', type=str)
    if provincia_codigo:
        # Subconsulta para proyectos que tienen al menos un municipio de esa provincia
        from app.models.municipios import Municipio, municipios_proyecto
        subquery = db.session.query(municipios_proyecto.c.id_proyecto).join(
            Municipio, municipios_proyecto.c.id_municipio == Municipio.id
        ).filter(
            func.substring(func.cast(Municipio.codigo, db.String), 1, 2) == provincia_codigo
        ).distinct()
        
        query = query.filter(Proyecto.id.in_(subquery))
    
    # Filtro por responsable (solo para ADMIN/SUPERVISOR)
    if current_user.rol.nombre in ['ADMIN', 'SUPERVISOR']:
        responsable_id = request.args.get('responsable', type=int)
        if responsable_id:
            query = query.filter(Expediente.id_responsable == responsable_id)
    
    # Ordenamiento por defecto: fecha creación DESC
    query = query.order_by(Proyecto.fecha_creacion.desc())
    
    # Ejecutar query
    proyectos = query.all()
    
    # Cargar datos para filtros
    tipos_ia = db.session.query(TipoInstalacionAT).order_by(TipoInstalacionAT.nombre).all()
    
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
    responsables = []
    if current_user.rol.nombre in ['ADMIN', 'SUPERVISOR']:
        from app.models.roles import Rol
        responsables = db.session.query(Usuario).join(Rol).filter(
            Rol.nombre == 'TRAMITADOR'
        ).order_by(Usuario.nombre).all()
    
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
        }
    )
