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
import subprocess
import sys
import json as _json
from datetime import date
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

    return render_template(
        'expedientes/tramitacion_bc_tarea.html',
        expediente=expediente,
        solicitud=solicitud,
        fase=fase,
        tramite=tramite,
        tarea=tarea,
    )


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
        filename = doc.url.rsplit('/', 1)[-1].rsplit('\\', 1)[-1] if doc.url else ''
        nombre = filename or f'Documento {doc.id}'
        # Extensión para mostrar en la tabla (vacía si no hay punto en el nombre)
        partes = filename.rsplit('.', 1)
        extension = partes[1].lower() if len(partes) == 2 and partes[1] else ''
        # ¿Es una URL clickable? Solo http/https y file:// (UNC \\ no funciona en browser)
        url = doc.url or ''
        es_clickable = url.startswith(('http://', 'https://', 'file:///'))
        docs_lista.append({
            'doc':             doc,
            'nombre_display':  nombre,
            'extension':       extension,
            'es_clickable':    es_clickable,
            'es_referenciado': _documento_es_referenciado(doc),
        })

    tipos_doc = TipoDocumento.query.order_by(TipoDocumento.nombre).all()

    return render_template(
        'expedientes/pool_documentos.html',
        expediente=expediente,
        docs_lista=docs_lista,
        tipos_doc=tipos_doc,
    )


@bp.route('/<int:id>/documentos/carga-masiva', methods=['POST'])
@login_required
def pool_carga_masiva(id):
    """Carga masiva de documentos al pool — recibe JSON, devuelve JSON."""
    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    datos = request.get_json(silent=True) or []
    creados = 0
    try:
        for entrada in datos:
            url = (entrada.get('url') or '').strip()
            if not url or entrada.get('excluir'):
                continue
            tipo_doc_id = entrada.get('tipo_doc_id') or 1
            fecha_raw = entrada.get('fecha_administrativa') or None
            fecha_admin = None
            if fecha_raw:
                try:
                    fecha_admin = date.fromisoformat(fecha_raw)
                except ValueError:
                    pass
            doc = Documento(
                expediente_id=id,
                url=url,
                tipo_doc_id=int(tipo_doc_id),
                fecha_administrativa=fecha_admin,
                asunto=(entrada.get('asunto') or '').strip() or None,
                prioridad=1 if entrada.get('prioridad') else 0,
            )
            db.session.add(doc)
            creados += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'error': str(e)}), 500

    return jsonify({'ok': True, 'creados': creados})


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
    url = (datos.get('url') or '').strip()
    if not url:
        return jsonify({'ok': False, 'error': 'La URL es obligatoria'}), 400

    fecha_raw = datos.get('fecha_administrativa') or None
    fecha_admin = None
    if fecha_raw:
        try:
            fecha_admin = date.fromisoformat(fecha_raw)
        except ValueError:
            pass

    try:
        doc.url = url
        doc.tipo_doc_id = int(datos.get('tipo_doc_id') or 1)
        doc.fecha_administrativa = fecha_admin
        doc.asunto = (datos.get('asunto') or '').strip() or None
        doc.prioridad = 1 if datos.get('prioridad') else 0
        doc.observaciones = (datos.get('observaciones') or '').strip() or None
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


# Scripts tkinter para el selector nativo (se ejecutan en subproceso independiente).
# sys.argv[1] recibe el último directorio usado para abrir el diálogo en él directamente.
_SCRIPT_FICHEROS = """\
import tkinter as tk
from tkinter import filedialog
import json, pathlib, sys

initialdir = sys.argv[1] if len(sys.argv) > 1 else ''
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', True)
rutas = list(filedialog.askopenfilenames(
    title='Seleccionar ficheros \u2014 BDDAT Pool',
    initialdir=initialdir or None,
))
rutas = [str(pathlib.Path(r)) for r in rutas]
root.destroy()
print(json.dumps(rutas))
"""

_SCRIPT_CARPETA = """\
import tkinter as tk
from tkinter import filedialog
import json, pathlib, sys

initialdir = sys.argv[1] if len(sys.argv) > 1 else ''
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', True)
carpeta = filedialog.askdirectory(
    title='Seleccionar carpeta \u2014 BDDAT Pool',
    initialdir=initialdir or None,
)
rutas = []
if carpeta:
    p = pathlib.Path(carpeta)
    rutas = [str(f) for f in sorted(p.iterdir()) if f.is_file()]
root.destroy()
print(json.dumps(rutas))
"""

# Último directorio usado — persiste en memoria durante la sesión del servidor.
# Permite que el diálogo se abra directamente en la carpeta del uso anterior.
_ultimo_directorio = ''


@bp.route('/<int:id>/documentos/selector-nativo', methods=['POST'])
@login_required
def pool_selector_nativo(id):
    """
    Abre un selector de ficheros o carpeta nativo del SO mediante tkinter
    en un subproceso y devuelve las rutas completas como JSON.

    - Funciona cuando Flask corre en la misma máquina que el usuario (desarrollo/admin local).
    - En producción con servidor remoto el diálogo se abriría en el servidor: no usar.
      Para ese escenario, el usuario rellena la columna URL editable manualmente.

    Recibe: { modo: 'ficheros' | 'carpeta' }
    Devuelve: { ok: true, rutas: ['C:\\\\...', ...] }
    """
    global _ultimo_directorio

    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'editar')
    if resultado:
        return resultado

    datos = request.get_json(silent=True) or {}
    modo = datos.get('modo', 'ficheros')
    script = _SCRIPT_CARPETA if modo == 'carpeta' else _SCRIPT_FICHEROS

    try:
        proc = subprocess.run(
            [sys.executable, '-c', script, _ultimo_directorio],
            capture_output=True,
            text=True,
            timeout=120,
        )
        rutas = _json.loads(proc.stdout.strip() or '[]')
    except subprocess.TimeoutExpired:
        return jsonify({'ok': False, 'error': 'Tiempo de espera agotado (120 s)'}), 408
    except _json.JSONDecodeError:
        detalle = proc.stderr.strip() if proc.stderr else 'sin detalle'
        return jsonify({'ok': False, 'error': f'Error en el selector: {detalle}'}), 500
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

    # Memorizar el directorio de la primera ruta seleccionada para la próxima vez
    if rutas:
        import pathlib as _pl
        _ultimo_directorio = str(_pl.Path(rutas[0]).parent)

    return jsonify({'ok': True, 'rutas': rutas})
