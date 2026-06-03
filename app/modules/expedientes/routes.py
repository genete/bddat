"""
Blueprint para gestión de expedientes.

Rutas:
- GET  /expedientes/                                                            - Listado con scroll infinito (Fase 2)
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
from app.models.proyectos import Proyecto
from app.models.usuarios import Usuario
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.solicitudes import Solicitud
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services.plazos import obtener_estado_plazo
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


@bp.route('/<int:id>/arbol')
@login_required
def arbol(id):
    """Vista de árbol del expediente (#500, ADR-016): isla React 'expediente-arbol'.

    El árbol y su detalle se sirven vía API (/api/expedientes/<id>/arbol). Aquí solo
    se renderiza el contenedor de la isla; el control de acceso real lo imponen tanto
    esta ruta como cada endpoint de la API.
    """
    expediente = Expediente.query.get_or_404(id)

    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    return render_template('expedientes/arbol.html', expediente=expediente)


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



@bp.route('/tarea/<int:tarea_id>/generar_cert', methods=['POST'])
@login_required
def generar_cert(tarea_id):
    """Genera el certificado de plazo cumplido para una tarea ESPERAR_PLAZO."""
    from app.services.certificados import crear_cert
    tarea = Tarea.query.get_or_404(tarea_id)
    resultado = verificar_acceso_expediente(tarea.tramite.fase.solicitud.expediente, 'editar')
    if resultado:
        return resultado
    try:
        crear_cert(tarea)
        flash('Certificado de plazo cumplido generado.', 'success')
    except (ValueError, NotImplementedError) as exc:
        flash(str(exc), 'danger')
    return redirect(request.referrer or url_for('expedientes.listado_v2'))


@bp.route('/cert/<int:cert_id>/pdf')
@login_required
def cert_pdf(cert_id):
    """Genera y devuelve el PDF de un certificado interno (bddat://)."""
    from app.models.certificados import Certificado
    from app.services.cert_pdf import generar_pdf_certificado

    cert = Certificado.query.get_or_404(cert_id)
    expediente = cert.documento.solicitud_expediente if hasattr(cert.documento, 'solicitud_expediente') else None

    # Acceder al expediente vía documento → expediente
    from app.models.expedientes import Expediente
    expediente = Expediente.query.get_or_404(cert.documento.expediente_id)

    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    tipo_cert = cert.documento.tipo_documento.codigo if cert.documento.tipo_documento else ''
    pdf_bytes = generar_pdf_certificado(cert, expediente, tipo_cert)

    from flask import Response
    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'inline; filename="cert_{tipo_cert}_{cert.id}.pdf"'
        },
    )


# Conjuntos de tipos de tarea que requieren documentos (espejo de invariantes_esftt.py)
_TIPOS_REQUIEREN_DOC_USADO     = {'ANALIZAR', 'NOTIFICAR'}
_TIPOS_DOC_USADO_OPCIONAL      = {'ELABORAR'}   # visible en UI pero no obligatorio al finalizar
_TIPOS_REQUIEREN_DOC_PRODUCIDO = {'ANALIZAR', 'ELABORAR', 'NOTIFICAR', 'ESPERAR_PLAZO'}


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
      doc.vinculos_tarea      → DocumentoTarea.documento_id     (lista, vínculos con rol)
    """
    if doc.proyecto_vinculado:
        return True
    if doc.vinculos_tarea:
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


@bp.route('/<int:id>/abrir-carpeta', methods=['POST'])
@login_required
def abrir_carpeta_expediente(id):
    """
    Abre el Explorador de Windows en la carpeta del expediente (FILESYSTEM_BASE/AT-N).

    Acción rápida del inspector de la vista de árbol (#500, ADR-016 §5). Misma
    limitación que pool_abrir_en_carpeta: Flask debe correr en el PC del navegador.
    """
    import subprocess

    expediente = Expediente.query.get_or_404(id)
    resultado = verificar_acceso_expediente(expediente, 'ver')
    if resultado:
        return resultado

    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base or not os.path.isdir(base):
        return jsonify({'ok': False, 'error': 'Servidor de ficheros no accesible'}), 503

    carpeta = os.path.normpath(os.path.join(os.path.abspath(base), f'AT-{expediente.numero_at}'))
    if not os.path.isdir(carpeta):
        return jsonify({'ok': False, 'error': 'La carpeta del expediente aún no existe'}), 404

    try:
        subprocess.Popen(f'explorer "{carpeta}"', shell=True)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


