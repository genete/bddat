"""
Blueprint para gestión de expedientes.

Rutas:
- GET  /expedientes/        - Listar expedientes (filtrados por rol o parámetro)
- GET  /expedientes/nuevo   - Formulario crear expediente
- POST /expedientes/nuevo   - Crear expediente + proyecto
- GET  /expedientes/<id>    - Ver detalle expediente
- GET  /expedientes/<id>/editar  - Formulario editar expediente
- POST /expedientes/<id>/editar  - Actualizar expediente + proyecto
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.expedientes import Expediente
from app.models.proyectos import Proyecto
from app.models.usuarios import Usuario
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.municipios_proyecto import MunicipioProyecto
from app.decorators import role_required
from app.utils.permisos import (
    puede_cambiar_responsable,
    verificar_acceso_expediente
)

# Blueprint con convención snake_case
bp = Blueprint('expedientes', __name__, url_prefix='/expedientes')


@bp.route('/')
@login_required
def index():
    """
    Lista expedientes con filtrado inteligente.
    
    Parámetros URL:
    - ?mis_expedientes=1  : Filtra solo expedientes del usuario actual
    
    Lógica de filtrado:
    - Si parámetro mis_expedientes=1: Solo expedientes del usuario
    - Si TRAMITADOR sin parámetro: Solo sus expedientes (restricción de rol)
    - Si ADMIN/SUPERVISOR sin parámetro: Todos los expedientes
    """
    # Parámetro de filtro opcional
    solo_mis_expedientes = request.args.get('mis_expedientes') == '1'
    
    # TRAMITADOR siempre ve solo sus expedientes
    if not current_user.tiene_rol('ADMIN', 'SUPERVISOR'):
        expedientes = Expediente.query.filter_by(
            responsable_id=current_user.id
        ).order_by(Expediente.numero_at.desc()).all()
        vista_filtrada = True
    else:
        # ADMIN/SUPERVISOR puede filtrar opcionalmente
        if solo_mis_expedientes:
            expedientes = Expediente.query.filter_by(
                responsable_id=current_user.id
            ).order_by(Expediente.numero_at.desc()).all()
            vista_filtrada = True
        else:
            expedientes = Expediente.query.order_by(
                Expediente.numero_at.desc()
            ).all()
            vista_filtrada = False
    
    return render_template(
        'expedientes/index.html', 
        expedientes=expedientes,
        vista_filtrada=vista_filtrada
    )


@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('ADMIN', 'SUPERVISOR', 'TRAMITADOR')
def nuevo():
    """Crear nuevo expediente con proyecto asociado (relación 1:1)"""
    if request.method == 'POST':
        try:
            # ============================================
            # 1. VALIDAR MUNICIPIOS (OBLIGATORIO)
            # ============================================
            municipios_ids = request.form.getlist('municipios[]')
            if not municipios_ids:
                flash('Debe añadir al menos un municipio afectado', 'danger')
                # Redirigir manteniendo datos del formulario
                return redirect(url_for('expedientes.nuevo'))
            
            # Convertir a enteros y validar existencia
            try:
                municipios_ids = [int(mid) for mid in municipios_ids]
            except ValueError:
                flash('IDs de municipios inválidos', 'danger')
                return redirect(url_for('expedientes.nuevo'))
            
            # ============================================
            # 2. CREAR PROYECTO
            # ============================================
            nuevo_proyecto = Proyecto(
                titulo=request.form.get('titulo_proyecto') or None,
                descripcion=request.form.get('descripcion_proyecto') or None,
                finalidad=request.form.get('finalidad') or None,
                emplazamiento=request.form.get('emplazamiento') or None,
                ia_id=request.form.get('ia_id') or None
            )
            db.session.add(nuevo_proyecto)
            db.session.flush()  # Obtener ID sin commit
            
            # ============================================
            # 3. ASOCIAR MUNICIPIOS AL PROYECTO
            # ============================================
            for municipio_id in municipios_ids:
                mp = MunicipioProyecto(
                    municipio_id=municipio_id,
                    proyecto_id=nuevo_proyecto.id
                )
                db.session.add(mp)
            
            # ============================================
            # 4. CREAR EXPEDIENTE
            # ============================================
            # Generar número AT automático (próximo disponible)
            ultimo_numero = db.session.query(
                db.func.max(Expediente.numero_at)
            ).scalar() or 0
            numero_at = ultimo_numero + 1
            
            # responsable_id puede ser None (expediente huérfano sin asignar)
            responsable_id = request.form.get('responsable_id')
            nuevo_expediente = Expediente(
                numero_at=numero_at,
                responsable_id=int(responsable_id) if responsable_id else None,
                tipo_expediente_id=request.form.get('tipo_expediente_id') or None,
                heredado=request.form.get('heredado') == 'on',
                proyecto_id=nuevo_proyecto.id
            )
            
            db.session.add(nuevo_expediente)
            
            # ============================================
            # 5. COMMIT TRANSACCIONAL
            # ============================================
            db.session.commit()
            
            flash(f'Expediente AT-{numero_at} creado correctamente', 'success')
            return redirect(url_for('expedientes.detalle', id=nuevo_expediente.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear expediente: {str(e)}', 'danger')
            return redirect(url_for('expedientes.nuevo'))
    
    # GET: Mostrar formulario
    tipos_expedientes = TipoExpediente.query.all()
    tipos_ia = TipoIA.query.all()
    usuarios = Usuario.query.filter_by(activo=True).all()
    
    return render_template('expedientes/nuevo.html', 
                         tipos_expedientes=tipos_expedientes,
                         tipos_ia=tipos_ia,
                         usuarios=usuarios)


@bp.route('/<int:id>')
@login_required
def detalle(id):
    """Vista detallada de un expediente con toda su información"""
    expediente = Expediente.query.get_or_404(id)
    
    # Verificación usando la utilidad
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado
    
    return render_template('expedientes/detalle.html', expediente=expediente)


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar expediente y proyecto asociado"""
    expediente = Expediente.query.get_or_404(id)
    
    # Verificación usando la utilidad
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado
    
    if request.method == 'POST':
        try:
            # ============================================
            # 1. VALIDAR MUNICIPIOS (OBLIGATORIO)
            # ============================================
            municipios_ids = request.form.getlist('municipios[]')
            if not municipios_ids:
                flash('Debe añadir al menos un municipio afectado', 'danger')
                return redirect(url_for('expedientes.editar', id=id))
            
            try:
                municipios_ids = [int(mid) for mid in municipios_ids]
            except ValueError:
                flash('IDs de municipios inválidos', 'danger')
                return redirect(url_for('expedientes.editar', id=id))
            
            # ============================================
            # 2. ACTUALIZAR EXPEDIENTE
            # ============================================
            expediente.tipo_expediente_id = request.form.get('tipo_expediente_id') or None
            expediente.heredado = request.form.get('heredado') == 'on'
            
            if puede_cambiar_responsable():
                nuevo_responsable_id = request.form.get('responsable_id')
                expediente.responsable_id = int(nuevo_responsable_id) if nuevo_responsable_id else None
            
            # ============================================
            # 3. ACTUALIZAR PROYECTO
            # ============================================
            proyecto = expediente.proyecto
            proyecto.titulo = request.form.get('titulo_proyecto') or None
            proyecto.descripcion = request.form.get('descripcion_proyecto') or None
            proyecto.finalidad = request.form.get('finalidad') or None
            proyecto.emplazamiento = request.form.get('emplazamiento') or None
            proyecto.ia_id = request.form.get('ia_id') or None
            
            # ============================================
            # 4. ACTUALIZAR MUNICIPIOS (REEMPLAZAR)
            # ============================================
            # Eliminar asociaciones actuales
            MunicipioProyecto.query.filter_by(
                proyecto_id=proyecto.id
            ).delete()
            
            # Crear nuevas asociaciones
            for municipio_id in municipios_ids:
                mp = MunicipioProyecto(
                    municipio_id=municipio_id,
                    proyecto_id=proyecto.id
                )
                db.session.add(mp)
            
            # ============================================
            # 5. COMMIT TRANSACCIONAL
            # ============================================
            db.session.commit()
            
            flash(f'Expediente AT-{expediente.numero_at} actualizado correctamente', 'success')
            return redirect(url_for('expedientes.detalle', id=expediente.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar expediente: {str(e)}', 'danger')
    
    # GET: Mostrar formulario
    tipos_expedientes = TipoExpediente.query.all()
    tipos_ia = TipoIA.query.all()
    usuarios = Usuario.query.filter_by(activo=True).all()
    
    return render_template('expedientes/editar.html',
                         expediente=expediente,
                         tipos_expedientes=tipos_expedientes,
                         tipos_ia=tipos_ia,
                         usuarios=usuarios)
