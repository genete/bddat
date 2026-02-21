"""
Blueprint para gestión de expedientes.

Rutas:
- GET  /expedientes/listado-v2           - Listado con scroll infinito (Fase 2)
- GET  /expedientes/<id>/tramitacion_v3  - Tramitación Vista V3 con sidebar acordeón
- GET  /expedientes/<id>                 - Ver detalle expediente (pendiente actualizar #TBD)
- GET  /expedientes/<id>/editar          - Formulario editar expediente (pendiente actualizar #TBD)
- POST /expedientes/<id>/editar          - Actualizar expediente + proyecto
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
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

# template_folder apunta a app/modules/expedientes/templates/
bp = Blueprint('expedientes', __name__,
               url_prefix='/expedientes',
               template_folder='templates')


@bp.route('/listado-v2')
@login_required
def listado_v2():
    """
    Listado de expedientes con scroll infinito (Fase 2).

    Usa estructura CSS v2 (Grid A/B/C) con carga dinámica de datos
    mediante JavaScript + API /api/expedientes.

    Características:
    - Scroll infinito con paginación cursor
    - Filtros dinámicos (búsqueda, estado)
    - Header/Footer sticky
    - Tabla con thead sticky
    - Botón scroll-to-top

    Nota: Esta ruta NO carga expedientes iniciales, solo renderiza
          la estructura HTML. Los datos se cargan vía AJAX.
    """
    return render_template('expedientes/listado_v2.html')


@bp.route('/<int:id>/tramitacion_v3')
@login_required
def tramitacion_v3(id):
    """
    Vista V3 - Tramitación con Sidebar Acordeón (Fase 1).

    Patrón de vista para navegación jerárquica dentro de UN expediente:
    - Sidebar acordeón: Expediente > Solicitudes > Fases > Trámites > Tareas
    - Panel detalle: Tabs [Datos] [Documentos] [Historial]
    - Contexto fijo: Expediente/Proyecto siempre visible
    - Paneles de hijos directos con listados (grupo C2.D de Vista 2)

    Fase 1 (actual): Mockup estático con estructura completa
    Fase 2+: JavaScript funcional + APIs backend

    Referencias:
    - Epic #93 - Sistema de Navegación UI Modular
    - docs/arquitectura/PATRONES_UI.md - Patrón Vista 3
    """
    expediente = Expediente.query.get_or_404(id)

    # Verificación de acceso
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    return render_template(
        'expedientes/tramitacion_v3.html',
        expediente=expediente
    )


@bp.route('/<int:id>')
@login_required
def detalle(id):
    """Vista detallada de un expediente con toda su información"""
    expediente = Expediente.query.get_or_404(id)

    # Verificación usando la utilidad
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    return render_template('expedientes/detalle.html', expediente=expediente, modo='ver')


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

    return render_template('expedientes/detalle.html',
                         expediente=expediente,
                         modo='editar',
                         tipos_expedientes=tipos_expedientes,
                         tipos_ia=tipos_ia,
                         usuarios=usuarios)
