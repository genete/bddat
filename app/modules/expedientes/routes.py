"""
Blueprint para gestión de expedientes.

Rutas:
- GET  /expedientes/                                                            - Listado con scroll infinito (Fase 2)
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
import os
from datetime import date
from flask import current_app, send_file
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
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
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.decorators import role_required
from app.utils.permisos import (
    puede_cambiar_responsable,
    verificar_acceso_expediente
)
from app.utils.metadata import cargar_metadata
from app.models.tipos_expedientes import TipoExpediente

# template_folder apunta a app/modules/expedientes/templates/
bp = Blueprint('expedientes', __name__,
               url_prefix='/expedientes',
               template_folder='templates')


@bp.route('/seguimiento/')
@login_required
def seguimiento():
    """
    Listado inteligente de seguimiento: cola de trabajo multi-pista.

    Cada fila es una solicitud EN_TRAMITE (o con el estado seleccionado).
    El estado de cada pista se deduce dinámicamente vía API /api/expedientes/seguimiento.
    """
    meta = cargar_metadata('expedientes')
    columns = meta.get('seguimiento', {}).get('columns', [])
    tipos_expedientes = TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    return render_template(
        'expedientes/seguimiento.html',
        columns=columns,
        tipos_expedientes=tipos_expedientes,
    )


@bp.route('/')
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
    meta = cargar_metadata('expedientes')
    columns = meta.get('listado_v2', {}).get('columns', [])
    return render_template('expedientes/listado_v2.html', columns=columns)


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
    """Indicador visual de la solicitud deducido de sus fases (estado almacenado eliminado)."""
    if not solicitud.fases:
        return 'planificada'
    return 'en_curso'


def _estado_indicador_fase(fase):
    """Mapea el estado de una Fase al indicador visual del partial."""
    if fase.finalizada:
        return 'finalizada'
    if fase.en_curso:
        return 'en_curso'
    return 'planificada'


def _estado_indicador_tramite(tramite):
    """Mapea el estado de un Tramite al indicador visual del partial."""
    if tramite.finalizado:
        return 'finalizada'
    if tramite.en_curso:
        return 'en_curso'
    return 'planificada'


def _estado_indicador_tarea(tarea):
    """Mapea el estado de una Tarea al indicador visual del partial."""
    if tarea.ejecutada:
        return 'finalizada'
    if tarea.en_curso:
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
        tipos_str = s.tipo_solicitud.siglas if s.tipo_solicitud else f'Solicitud #{s.id}'
        fecha_sol = s.documento_solicitud.fecha_administrativa if s.documento_solicitud else None
        hijos.append({
            'nombre':        tipos_str,
            'fecha_inicio':  _fmt_fecha(fecha_sol),
            'estado':        _estado_indicador_solicitud(s),
            'url_detalle':   url_for('expedientes.tramitacion_bc_solicitud',
                                    exp_id=exp_id, sol_id=s.id),
        })

    columnas = [
        {'key': 'nombre',       'label': 'Tipos de solicitud'},
        {'key': 'fecha_inicio', 'label': 'F. Solicitud'},
    ]

    tipos_solicitud = TipoSolicitud.query.order_by(TipoSolicitud.siglas).all()

    return render_template(
        'expedientes/tramitacion_bc.html',
        expediente=expediente,
        hijos=hijos,
        columnas=columnas,
        tipos_solicitud=tipos_solicitud,
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
            'nombre':      f.tipo_fase.nombre if f.tipo_fase else f'Fase #{f.id}',
            'estado':      _estado_indicador_fase(f),
            'url_detalle': url_for('expedientes.tramitacion_bc_fase',
                                   exp_id=exp_id, sol_id=sol_id, fase_id=f.id),
        })

    columnas = [
        {'key': 'nombre',  'label': 'Fase'},
    ]

    tipos_fase = TipoFase.query.order_by(TipoFase.nombre).all()

    return render_template(
        'expedientes/tramitacion_bc_solicitud.html',
        expediente=expediente,
        solicitud=solicitud,
        hijos=hijos,
        columnas=columnas,
        tipos_fase=tipos_fase,
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
            'nombre':      t.tipo_tramite.nombre if t.tipo_tramite else f'Trámite #{t.id}',
            'estado':      _estado_indicador_tramite(t),
            'url_detalle': url_for('expedientes.tramitacion_bc_tramite',
                                   exp_id=exp_id, sol_id=sol_id,
                                   fase_id=fase_id, tram_id=t.id),
        })

    columnas = [
        {'key': 'nombre',  'label': 'Trámite'},
    ]

    resultados_fase = TipoResultadoFase.query.order_by(TipoResultadoFase.nombre).all()
    tipos_tramite = TipoTramite.query.order_by(TipoTramite.nombre).all()

    return render_template(
        'expedientes/tramitacion_bc_fase.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        hijos=hijos,
        columnas=columnas,
        resultados_fase=resultados_fase,
        tipos_tramite=tipos_tramite,
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
            'nombre':      t.tipo_tarea.nombre if t.tipo_tarea else f'Tarea #{t.id}',
            'estado':      _estado_indicador_tarea(t),
            'url_detalle': url_for('expedientes.tramitacion_bc_tarea',
                                   exp_id=exp_id, sol_id=sol_id,
                                   fase_id=fase_id, tram_id=tram_id, tarea_id=t.id),
        })

    columnas = [
        {'key': 'nombre',  'label': 'Tarea'},
    ]

    tipos_tarea = TipoTarea.query.order_by(TipoTarea.nombre).all()

    return render_template(
        'expedientes/tramitacion_bc_tramite.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        tramite=tramite,
        hijos=hijos,
        columnas=columnas,
        tipos_tarea=tipos_tarea,
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

    codigo_tipo = tarea.tipo_tarea.codigo if tarea.tipo_tarea else ''
    requiere_doc_usado     = codigo_tipo in _TIPOS_REQUIEREN_DOC_USADO
    doc_usado_opcional     = codigo_tipo in _TIPOS_DOC_USADO_OPCIONAL
    requiere_doc_producido = codigo_tipo in _TIPOS_REQUIEREN_DOC_PRODUCIDO
    es_tarea_redactar      = (codigo_tipo == 'REDACTAR')

    return render_template(
        'expedientes/tramitacion_bc_tarea.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        tramite=tramite,
        tarea=tarea,
        requiere_doc_usado=requiere_doc_usado,
        doc_usado_opcional=doc_usado_opcional,
        requiere_doc_producido=requiere_doc_producido,
        es_tarea_redactar=es_tarea_redactar,
    )


# Conjuntos de tipos de tarea que requieren documentos (espejo de invariantes_esftt.py)
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALISIS', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}
_TIPOS_DOC_USADO_OPCIONAL      = {'REDACTAR'}   # visible en UI pero no obligatorio al finalizar
_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'INCORPORAR', 'ANALISIS', 'REDACTAR', 'FIRMAR', 'NOTIFICAR', 'PUBLICAR'}


# ===========================================================================
# POOL DE DOCUMENTOS — issue #180
# Gestión masiva del pool documental de un expediente (Vía 1)
# ===========================================================================

def _documento_es_referenciado(doc):
    """
    True si el documento tiene referencias activas que impiden su borrado.

    Usa únicamente backrefs SQLAlchemy — NO hardcodear SQL directo.
    Si en el futuro se añade una nueva tabla con FK a documentos.id:
      1. Añadir el backref en el modelo correspondiente.
      2. Añadir un check aquí.

    Backrefs consultados:
      doc.proyecto_vinculado  → DocumentoProyecto.documento_id  (uselist=False)
      doc.tareas_que_usan     → Tarea.documento_usado_id        (lista)
      doc.tarea_productora    → Tarea.documento_producido_id    (lista, UNIQUE en BD)
    """
    if doc.proyecto_vinculado:
        return True
    if doc.tareas_que_usan:
        return True
    if doc.tarea_productora:
        return True
    return False


@bp.route('/<int:id>/documentos')
@login_required
def pool_documentos(id):
    """Pool de documentos — listado del expediente."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    documentos_raw = Documento.query.filter_by(
        expediente_id=id
    ).order_by(Documento.id.desc()).all()

    docs_lista = []
    for doc in documentos_raw:
        filename = doc.url.replace('\\', '/').rsplit('/', 1)[-1] if doc.url else ''
        # Eliminar fragment (#...) y query string (?...) para nombre y extensión limpios
        filename_limpio = filename.split('?')[0].split('#')[0]
        nombre = filename_limpio or f'Documento {doc.id}'
        partes = filename_limpio.rsplit('.', 1)
        extension = partes[1].lower() if len(partes) == 2 and partes[1] else ''
        es_url_externa = (doc.url or '').startswith(('http://', 'https://'))
        docs_lista.append({
            'doc':             doc,
            'nombre_display':  nombre,
            'extension':       extension,
            'es_url_externa':  es_url_externa,
            'es_referenciado': _documento_es_referenciado(doc),
        })

    tipos_doc = TipoDocumento.query.order_by(TipoDocumento.nombre).all()

    return render_template(
        'expedientes/pool_documentos.html',
        expediente=expediente,
        docs_lista=docs_lista,
        tipos_doc=tipos_doc,
    )


@bp.route('/<int:id>/documentos/json')
@login_required
def pool_documentos_json(id):
    """API JSON — lista de documentos del expediente para SelectorBusqueda (issue #166).

    Devuelve: { "ok": true, "docs": [{"v": "42", "t": "informe.pdf — Informe técnico — 15/01/2026"}, ...] }
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return jsonify({'ok': False, 'error': 'Acceso denegado'}), 403

    documentos = Documento.query.filter_by(
        expediente_id=id
    ).order_by(Documento.id.desc()).all()

    docs = []
    for doc in documentos:
        filename = doc.url.replace('\\', '/').rsplit('/', 1)[-1] if doc.url else ''
        filename_limpio = filename.split('?')[0].split('#')[0]
        nombre = filename_limpio or f'Documento {doc.id}'
        tipo_nombre = doc.tipo_doc.nombre if doc.tipo_doc else 'Sin tipo'
        if doc.fecha_administrativa:
            fecha_str = doc.fecha_administrativa.strftime('%d/%m/%Y')
        else:
            fecha_str = 'Sin fecha'
        texto = f'{nombre} — {tipo_nombre} — {fecha_str}'
        docs.append({'v': str(doc.id), 't': texto})

    return jsonify({'ok': True, 'docs': docs})


def _path_seguro(ruta_relativa, base):
    """
    Devuelve ruta absoluta si está dentro de base; None si intenta path traversal.
    ruta_relativa usa '/' como separador (enviado por JS).
    """
    base_norm = os.path.normpath(os.path.abspath(base))
    if ruta_relativa:
        ruta_full = os.path.normpath(os.path.join(base, ruta_relativa.replace('/', os.sep)))
    else:
        ruta_full = base_norm
    if ruta_full != base_norm and not ruta_full.startswith(base_norm + os.sep):
        return None
    return ruta_full


@bp.route('/<int:id>/documentos/explorador-fs')
@login_required
def pool_explorador_fs(id):
    """Explorador de carpetas del servidor de ficheros — devuelve JSON."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base or not os.path.isdir(base):
        return jsonify({'ok': False, 'error': 'Servidor de ficheros no accesible'}), 503

    ruta_rel = request.args.get('ruta', '').strip('/\\ ')
    ruta_abs = _path_seguro(ruta_rel, base)
    if not ruta_abs or not os.path.isdir(ruta_abs):
        return jsonify({'ok': False, 'error': 'Ruta no válida'}), 400

    try:
        dirs, files = [], []
        for e in sorted(os.scandir(ruta_abs), key=lambda x: (not x.is_dir(), x.name.lower())):
            rel = os.path.relpath(e.path, base).replace(os.sep, '/')
            if e.is_dir(follow_symlinks=False):
                dirs.append({'nombre': e.name, 'ruta': rel})
            elif e.is_file(follow_symlinks=False):
                ext = e.name.rsplit('.', 1)[-1].lower() if '.' in e.name else ''
                files.append({'nombre': e.name, 'ruta': rel,
                              'tamano': e.stat().st_size, 'ext': ext})
    except PermissionError:
        return jsonify({'ok': False, 'error': 'Sin permisos en esta carpeta'}), 403

    partes = ruta_rel.split('/') if ruta_rel else []
    return jsonify({'ok': True, 'partes': partes, 'directorios': dirs, 'ficheros': files})


@bp.route('/<int:id>/documentos/registrar-rutas', methods=['POST'])
@login_required
def pool_registrar_rutas(id):
    """
    Registra ficheros del servidor de ficheros en el pool del expediente.

    Recibe JSON: [{ruta, tipo_doc_id, fecha_administrativa, asunto, prioridad}, ...]
    donde ruta es relativa a FILESYSTEM_BASE (con '/' como separador).
    Almacena la ruta absoluta normalizada en Documento.url.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base or not os.path.isdir(base):
        return jsonify({'ok': False, 'error': 'Servidor de ficheros no accesible'}), 503

    items = request.get_json(silent=True)
    if not isinstance(items, list) or not items:
        return jsonify({'ok': False, 'error': 'Payload inválido'}), 400

    creados = 0
    try:
        for item in items:
            ruta_rel = (item.get('ruta') or '').strip()
            if not ruta_rel:
                continue
            ruta_abs = _path_seguro(ruta_rel, base)
            if not ruta_abs or not os.path.isfile(ruta_abs):
                continue

            fecha_admin = None
            fecha_raw = item.get('fecha_administrativa') or None
            if fecha_raw:
                try:
                    fecha_admin = date.fromisoformat(fecha_raw)
                except ValueError:
                    pass

            doc = Documento(
                expediente_id=id,
                url=ruta_abs,
                tipo_doc_id=int(item.get('tipo_doc_id') or 1),
                fecha_administrativa=fecha_admin,
                asunto=(item.get('asunto') or '').strip() or None,
                prioridad=1 if item.get('prioridad') else 0,
            )
            db.session.add(doc)
            creados += 1

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True, 'creados': creados})


@bp.route('/<int:id>/documentos/<int:doc_id>/fichero')
@login_required
def pool_descargar_documento(id, doc_id):
    """Sirve un fichero del servidor de ficheros. Para URLs externas, redirige."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    url = doc.url or ''
    if url.startswith(('http://', 'https://')):
        return redirect(url)

    ruta_abs = os.path.normpath(os.path.abspath(url))
    if not os.path.isfile(ruta_abs):
        abort(404)

    base = current_app.config.get('FILESYSTEM_BASE', '')
    if base:
        base_norm = os.path.normpath(os.path.abspath(base))
        if not ruta_abs.startswith(base_norm):
            abort(403)

    return send_file(ruta_abs, as_attachment=False,
                     download_name=os.path.basename(ruta_abs))


@bp.route('/<int:id>/documentos/url-externa', methods=['POST'])
@login_required
def pool_registrar_url_externa(id):
    """
    Registra una URL externa en el pool (BOE, Notifica, sede electrónica, etc.)
    sin subir ningún fichero. Recibe JSON, devuelve JSON.
    """
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    datos = request.get_json(silent=True) or {}
    url = (datos.get('url') or '').strip()
    if not url:
        return jsonify({'ok': False, 'error': 'La URL es obligatoria'}), 400

    fecha_admin = None
    fecha_raw = datos.get('fecha_administrativa') or None
    if fecha_raw:
        try:
            fecha_admin = date.fromisoformat(fecha_raw)
        except ValueError:
            pass

    try:
        doc = Documento(
            expediente_id=id,
            url=url,
            tipo_doc_id=int(datos.get('tipo_doc_id') or 1),
            fecha_administrativa=fecha_admin,
            asunto=(datos.get('asunto') or '').strip() or None,
            prioridad=1 if datos.get('prioridad') else 0,
        )
        db.session.add(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


@bp.route('/<int:id>/documentos/<int:doc_id>/editar', methods=['POST'])
@login_required
def pool_editar_documento(id, doc_id):
    """Editar metadatos de un documento del pool — devuelve JSON."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    datos = request.get_json(silent=True) or {}
    # Solo se actualizan los campos presentes en el payload.
    # Esto permite edición masiva parcial (p.ej. solo cambiar prioridad)
    # sin sobreescribir los demás metadatos.

    try:
        url_nueva = (datos.get('url') or '').strip()
        if url_nueva:
            doc.url = url_nueva

        if 'tipo_doc_id' in datos:
            doc.tipo_doc_id = int(datos['tipo_doc_id'] or 1)

        if 'fecha_administrativa' in datos:
            fecha_raw = datos['fecha_administrativa']
            doc.fecha_administrativa = None
            if fecha_raw:
                try:
                    doc.fecha_administrativa = date.fromisoformat(fecha_raw)
                except ValueError:
                    pass

        if 'asunto' in datos:
            doc.asunto = (datos['asunto'] or '').strip() or None

        if 'prioridad' in datos:
            doc.prioridad = 1 if datos['prioridad'] else 0

        if 'observaciones' in datos:
            doc.observaciones = (datos['observaciones'] or '').strip() or None

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


@bp.route('/<int:id>/documentos/<int:doc_id>/borrar', methods=['POST'])
@login_required
def pool_borrar_documento(id, doc_id):
    """Borrar un documento del pool si no está referenciado — devuelve JSON."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    if _documento_es_referenciado(doc):
        return jsonify({
            'ok': False,
            'error': 'El documento está referenciado en tramitación y no puede eliminarse'
        }), 422

    try:
        db.session.delete(doc)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True})


@bp.route('/<int:id>/documentos/<int:doc_id>/abrir-en-carpeta', methods=['POST'])
@login_required
def pool_abrir_en_carpeta(id, doc_id):
    """
    Abre el Explorador de Windows enfocando el archivo.

    Requiere que Flask corra en el mismo PC que el navegador (despliegue local).
    No funciona con URLs externas ni si el fichero no existe en disco.
    """
    import subprocess

    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    doc = Documento.query.get_or_404(doc_id)
    if doc.expediente_id != id:
        abort(404)

    url = doc.url or ''
    if url.startswith(('http://', 'https://')):
        return jsonify({'ok': False, 'error': 'No aplicable a URLs externas'}), 400

    ruta_abs = os.path.normpath(os.path.abspath(url))
    if not os.path.isfile(ruta_abs):
        return jsonify({'ok': False, 'error': 'Fichero no encontrado en disco'}), 404

    try:
        # shell=True necesario: explorer.exe no parsea /select,ruta como argumento de lista.
        # La ruta viene de BD (ya validada), no de input directo del usuario.
        subprocess.Popen(f'explorer /select,"{ruta_abs}"', shell=True)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


