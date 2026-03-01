"""
Blueprint para gestión de expedientes.

Rutas:
- GET  /expedientes/listado-v2                                                  - Listado con scroll infinito (Fase 2)
- GET  /expedientes/<id>/tramitacion_v3                                         - Tramitación Vista V3 con tabs (legacy)
- GET  /expedientes/<exp_id>/tramitacion                                        - Tramitación BC: nivel Expediente (#157)
- GET  /expedientes/<exp_id>/tramitacion/solicitud/<sol_id>                     - Tramitación BC: nivel Solicitud (#157)
- GET  /expedientes/<exp_id>/tramitacion/solicitud/<sol_id>/fase/<fase_id>      - Tramitación BC: nivel Fase (#157)
- GET  /expedientes/<exp_id>/tramitacion/solicitud/<sol_id>/fase/<fase_id>/tramite/<tram_id>            - Tramitación BC: nivel Trámite (#157)
- GET  /expedientes/<exp_id>/tramitacion/solicitud/<sol_id>/fase/<fase_id>/tramite/<tram_id>/tarea/<tarea_id> - Tramitación BC: nivel Tarea (#157)
- GET  /expedientes/<id>                 - Ver detalle expediente
- GET  /expedientes/<id>/editar          - Formulario editar expediente
- POST /expedientes/<id>/editar          - Actualizar expediente + proyecto
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required
from app import db
from app.models.expedientes import Expediente
from app.routes.vista3 import _get_solicitudes_con_stats, _construir_arbol
from app.models.proyectos import Proyecto
from app.models.usuarios import Usuario
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_fases import TipoFase
from app.models.tipos_tramites import TipoTramite
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_resultados_fases import TipoResultadoFase
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
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
    Vista V3 - Tramitación con Tabs Anidados (4 niveles) — issue #150.

    Reemplaza el acordeón lazy-loading por tabs renderizados en servidor:
    - Nivel 1: Solicitudes (tabs horizontales)
    - Nivel 2: Fases (tabs anidados dentro de cada solicitud)
    - Nivel 3: Trámites (tabs anidados dentro de cada fase)
    - Nivel 4: Tareas (tabs anidados dentro de cada trámite)
    - Edición inline V4 (toggle ver/editar sin modal)
    - Creación de entidades hijas via modal Bootstrap
    """
    expediente = Expediente.query.get_or_404(id)

    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    return render_template(
        'expedientes/tramitacion_v3.html',
        expediente=expediente,
        solicitudes_arbol=_construir_arbol(expediente.id),
        tipos_solicitud=TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        tipos_fase=TipoFase.query.order_by(TipoFase.nombre).all(),
        tipos_tramite=TipoTramite.query.order_by(TipoTramite.nombre).all(),
        tipos_tarea=TipoTarea.query.order_by(TipoTarea.nombre).all(),
        resultados_fase=TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all(),
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


# ===========================================================================
# TRAMITACIÓN BREADCRUMBS — issue #157
# Arquitectura: un nivel por URL, breadcrumb dinámico
# ===========================================================================

def _estado_indicador_solicitud(solicitud):
    """Mapea el estado de una Solicitud al indicador visual del partial."""
    if solicitud.estado == 'EN_TRAMITE':
        return 'en_curso'
    elif solicitud.estado in ('RESUELTA', 'DESISTIDA', 'ARCHIVADA'):
        return 'finalizada'
    return 'planificada'


def _estado_indicador_fase(fase):
    """Mapea el estado de una Fase al indicador visual del partial."""
    if fase.finalizada:
        return 'finalizada'
    if fase.en_curso:
        return 'en_curso'
    return 'planificada'


def _estado_indicador_tramite(tramite):
    """Mapea el estado de un Tramite al indicador visual del partial."""
    if tramite.fecha_fin is not None:
        return 'finalizada'
    if tramite.fecha_inicio is not None:
        return 'en_curso'
    return 'planificada'


def _estado_indicador_tarea(tarea):
    """Mapea el estado de una Tarea al indicador visual del partial."""
    if tarea.fecha_fin is not None:
        return 'finalizada'
    if tarea.fecha_inicio is not None:
        return 'en_curso'
    return 'planificada'


def _fmt_fecha(d):
    """Formatea una fecha para mostrar en tabla, devuelve '—' si es None."""
    return d.strftime('%d/%m/%Y') if d else '—'


@bp.route('/<int:exp_id>/tramitacion')
@login_required
def tramitacion_bc(exp_id):
    """Tramitación BC — nivel Expediente: muestra lista de Solicitudes."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    solicitudes_raw = Solicitud.query.filter_by(
        expediente_id=exp_id
    ).order_by(Solicitud.id).all()

    hijos = []
    for s in solicitudes_raw:
        tipos_str = ' + '.join(
            st.tipo_solicitud.siglas
            for st in s.solicitud_tipos
        ) if s.solicitud_tipos else f'Solicitud #{s.id}'
        hijos.append({
            'nombre':        tipos_str,
            'fecha_inicio':  _fmt_fecha(s.fecha_solicitud),
            'fecha_fin':     _fmt_fecha(s.fecha_fin),
            'estado':        _estado_indicador_solicitud(s),
            'estado_texto':  s.estado,
            'url_detalle':   url_for('expedientes.tramitacion_bc_solicitud',
                                    exp_id=exp_id, sol_id=s.id),
        })

    columnas = [
        {'key': 'nombre',       'label': 'Tipos de solicitud'},
        {'key': 'fecha_inicio', 'label': 'F. Solicitud'},
        {'key': 'fecha_fin',    'label': 'F. Resolución'},
        {'key': 'estado_texto', 'label': 'Estado'},
    ]

    return render_template(
        'expedientes/tramitacion_bc.html',
        expediente=expediente,
        hijos=hijos,
        columnas=columnas,
    )


@bp.route('/<int:exp_id>/tramitacion/solicitud/<int:sol_id>')
@login_required
def tramitacion_bc_solicitud(exp_id, sol_id):
    """Tramitación BC — nivel Solicitud: muestra lista de Fases."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    solicitud = Solicitud.query.get_or_404(sol_id)
    if solicitud.expediente_id != exp_id:
        abort(404)

    fases_raw = Fase.query.filter_by(
        solicitud_id=sol_id
    ).order_by(Fase.id).all()

    hijos = []
    for f in fases_raw:
        hijos.append({
            'nombre':       f.tipo_fase.nombre if f.tipo_fase else f'Fase #{f.id}',
            'fecha_inicio': _fmt_fecha(f.fecha_inicio),
            'fecha_fin':    _fmt_fecha(f.fecha_fin),
            'estado':       _estado_indicador_fase(f),
            'url_detalle':  url_for('expedientes.tramitacion_bc_fase',
                                    exp_id=exp_id, sol_id=sol_id, fase_id=f.id),
        })

    columnas = [
        {'key': 'nombre',       'label': 'Fase'},
        {'key': 'fecha_inicio', 'label': 'F. Inicio'},
        {'key': 'fecha_fin',    'label': 'F. Fin'},
    ]

    return render_template(
        'expedientes/tramitacion_bc_solicitud.html',
        expediente=expediente,
        solicitud=solicitud,
        hijos=hijos,
        columnas=columnas,
    )


@bp.route('/<int:exp_id>/tramitacion/solicitud/<int:sol_id>/fase/<int:fase_id>')
@login_required
def tramitacion_bc_fase(exp_id, sol_id, fase_id):
    """Tramitación BC — nivel Fase: muestra lista de Trámites."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    solicitud = Solicitud.query.get_or_404(sol_id)
    if solicitud.expediente_id != exp_id:
        abort(404)

    fase = Fase.query.get_or_404(fase_id)
    if fase.solicitud_id != sol_id:
        abort(404)

    tramites_raw = Tramite.query.filter_by(
        fase_id=fase_id
    ).order_by(Tramite.id).all()

    hijos = []
    for t in tramites_raw:
        hijos.append({
            'nombre':       t.tipo_tramite.nombre if t.tipo_tramite else f'Trámite #{t.id}',
            'fecha_inicio': _fmt_fecha(t.fecha_inicio),
            'fecha_fin':    _fmt_fecha(t.fecha_fin),
            'estado':       _estado_indicador_tramite(t),
            'url_detalle':  url_for('expedientes.tramitacion_bc_tramite',
                                    exp_id=exp_id, sol_id=sol_id,
                                    fase_id=fase_id, tram_id=t.id),
        })

    columnas = [
        {'key': 'nombre',       'label': 'Trámite'},
        {'key': 'fecha_inicio', 'label': 'F. Inicio'},
        {'key': 'fecha_fin',    'label': 'F. Fin'},
    ]

    return render_template(
        'expedientes/tramitacion_bc_fase.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        hijos=hijos,
        columnas=columnas,
    )


@bp.route('/<int:exp_id>/tramitacion/solicitud/<int:sol_id>/fase/<int:fase_id>/tramite/<int:tram_id>')
@login_required
def tramitacion_bc_tramite(exp_id, sol_id, fase_id, tram_id):
    """Tramitación BC — nivel Trámite: muestra lista de Tareas."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    solicitud = Solicitud.query.get_or_404(sol_id)
    if solicitud.expediente_id != exp_id:
        abort(404)

    fase = Fase.query.get_or_404(fase_id)
    if fase.solicitud_id != sol_id:
        abort(404)

    tramite = Tramite.query.get_or_404(tram_id)
    if tramite.fase_id != fase_id:
        abort(404)

    tareas_raw = Tarea.query.filter_by(
        tramite_id=tram_id
    ).order_by(Tarea.id).all()

    hijos = []
    for t in tareas_raw:
        hijos.append({
            'nombre':       t.tipo_tarea.nombre if t.tipo_tarea else f'Tarea #{t.id}',
            'fecha_inicio': _fmt_fecha(t.fecha_inicio),
            'fecha_fin':    _fmt_fecha(t.fecha_fin),
            'estado':       _estado_indicador_tarea(t),
            'url_detalle':  url_for('expedientes.tramitacion_bc_tarea',
                                    exp_id=exp_id, sol_id=sol_id,
                                    fase_id=fase_id, tram_id=tram_id, tarea_id=t.id),
        })

    columnas = [
        {'key': 'nombre',       'label': 'Tarea'},
        {'key': 'fecha_inicio', 'label': 'F. Inicio'},
        {'key': 'fecha_fin',    'label': 'F. Fin'},
    ]

    return render_template(
        'expedientes/tramitacion_bc_tramite.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        tramite=tramite,
        hijos=hijos,
        columnas=columnas,
    )


@bp.route('/<int:exp_id>/tramitacion/solicitud/<int:sol_id>/fase/<int:fase_id>/tramite/<int:tram_id>/tarea/<int:tarea_id>')
@login_required
def tramitacion_bc_tarea(exp_id, sol_id, fase_id, tram_id, tarea_id):
    """Tramitación BC — nivel Tarea: detalle + documentos (sin tabla de hijos)."""
    expediente = Expediente.query.get_or_404(exp_id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    solicitud = Solicitud.query.get_or_404(sol_id)
    if solicitud.expediente_id != exp_id:
        abort(404)

    fase = Fase.query.get_or_404(fase_id)
    if fase.solicitud_id != sol_id:
        abort(404)

    tramite = Tramite.query.get_or_404(tram_id)
    if tramite.fase_id != fase_id:
        abort(404)

    tarea = Tarea.query.get_or_404(tarea_id)
    if tarea.tramite_id != tram_id:
        abort(404)

    return render_template(
        'expedientes/tramitacion_bc_tarea.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        tramite=tramite,
        tarea=tarea,
    )
