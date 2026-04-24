"""Wizard de creación de expediente + proyecto + solicitud.

FLUJO:
    Paso 1 → Datos básicos del expediente (tipo, responsable, heredado)
    Paso 2 → Datos del proyecto técnico (título, descripción, municipios, etc.)
    Paso 3 → Solicitud (entidad titular, fecha, tipos de solicitud)

    Los datos de pasos 1 y 2 se guardan en sesión Flask (SESSION_KEY).
    El commit transaccional completo ocurre al finalizar el paso 3.

ISSUE: #67
VERSÓN: 1.0
FECHA: 2026-02-19
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from datetime import date
from app import db
from app.models.expedientes import Expediente
from app.models.proyectos import Proyecto
from app.models.usuarios import Usuario
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.municipios_proyecto import MunicipioProyecto
from app.models.entidad import Entidad
from app.models.solicitudes import Solicitud
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.autorizados_titular import AutorizadoTitular

bp = Blueprint('wizard_expediente', __name__, url_prefix='/expedientes/wizard')

SESSION_KEY = 'wizard_expediente'


# =============================================================================
# HELPERS DE SESIÓN
# =============================================================================

def _get_wizard():
    """Devuelve el dict de la sesión del wizard (o dict vacío)."""
    return session.get(SESSION_KEY, {})


def _save_wizard(data):
    """Persiste el dict en sesión y marca como modificada."""
    session[SESSION_KEY] = data
    session.modified = True


def _reset_wizard():
    """Elimina el dict del wizard de la sesión."""
    session.pop(SESSION_KEY, None)
    session.modified = True


# =============================================================================
# RUTAS
# =============================================================================

@bp.route('/')
@login_required
def index():
    """Redirige siempre al paso 1."""
    return redirect(url_for('wizard_expediente.paso1'))


@bp.route('/cancelar')
@login_required
def cancelar():
    """Limpia la sesión del wizard y vuelve al origen de la invocación."""
    data = _get_wizard()
    origen = data.get('origen', url_for('expedientes.listado_v2'))
    _reset_wizard()
    flash('Creación de expediente cancelada.', 'info')
    return redirect(origen)


@bp.route('/paso1', methods=['GET', 'POST'])
@login_required
def paso1():
    """
    Paso 1: Datos básicos del expediente.

    Campos:
        tipo_expediente_id  (obligatorio): Tipo normativo del expediente.
        responsable_id      (opcional):    Tramitador asignado. NULL = huérfano.
        heredado            (bool):        TRUE si proviene del sistema legacy.
    """
    data = _get_wizard()
    paso1_data = data.get('paso1', {})

    # En GET: guardar el origen solo si el wizard acaba de empezar (sin datos previos)
    if request.method == 'GET' and 'origen' not in data:
        data['origen'] = request.referrer or url_for('expedientes.listado_v2')
        _save_wizard(data)

    if request.method == 'POST':
        tipo_expediente_id = request.form.get('tipo_expediente_id') or None
        responsable_id = request.form.get('responsable_id') or None
        heredado = request.form.get('heredado') == 'on'

        if not tipo_expediente_id:
            flash('Debe seleccionar un tipo de expediente.', 'danger')
            return redirect(url_for('wizard_expediente.paso1'))

        tipo = TipoExpediente.query.get(int(tipo_expediente_id))
        if not tipo:
            flash('El tipo de expediente seleccionado no es válido.', 'danger')
            return redirect(url_for('wizard_expediente.paso1'))

        data['paso1'] = {
            'tipo_expediente_id': int(tipo_expediente_id),
            'responsable_id': int(responsable_id) if responsable_id else None,
            'heredado': heredado,
        }
        _save_wizard(data)
        return redirect(url_for('wizard_expediente.paso2'))

    tipos_expedientes = TipoExpediente.query.order_by(TipoExpediente.tipo).all()
    usuarios = Usuario.query.filter_by(activo=True).order_by(
        Usuario.apellido1, Usuario.nombre
    ).all()

    return render_template(
        'expedientes/wizard_paso1.html',
        tipos_expedientes=tipos_expedientes,
        usuarios=usuarios,
        paso1=paso1_data,
    )


@bp.route('/paso2', methods=['GET', 'POST'])
@login_required
def paso2():
    """
    Paso 2: Datos del proyecto técnico.

    Campos:
        titulo, descripcion, finalidad, emplazamiento  (obligatorios)
        fecha        (obligatorio): Fecha técnica del proyecto (firma/visado).
        ia_id        (opcional):   Instrumento ambiental aplicable.
        municipios_ids[] (obligatorio, mín. 1): Municipios afectados.

    Requiere paso 1 completado en sesión.
    """
    data = _get_wizard()
    if 'paso1' not in data:
        flash('Debe completar primero el paso 1.', 'warning')
        return redirect(url_for('wizard_expediente.paso1'))

    paso2_data = data.get('paso2', {})

    if request.method == 'POST':
        titulo = (request.form.get('titulo') or '').strip()
        descripcion = (request.form.get('descripcion') or '').strip()
        finalidad = (request.form.get('finalidad') or '').strip()
        emplazamiento = (request.form.get('emplazamiento') or '').strip()
        fecha_str = (request.form.get('fecha') or '').strip()
        ia_id = request.form.get('ia_id') or None
        municipios_ids = request.form.getlist('municipios_ids[]')

        errores = []
        if not titulo:
            errores.append('El título del proyecto es obligatorio.')
        if not descripcion:
            errores.append('La descripción del proyecto es obligatoria.')
        if not finalidad:
            errores.append('La finalidad del proyecto es obligatoria.')
        if not emplazamiento:
            errores.append('El emplazamiento es obligatorio.')
        if not municipios_ids:
            errores.append('Debe añadir al menos un municipio afectado.')

        try:
            fecha = date.fromisoformat(fecha_str) if fecha_str else date.today()
        except ValueError:
            errores.append('Fecha de proyecto inválida (formato esperado: YYYY-MM-DD).')
            fecha = date.today()

        if errores:
            for e in errores:
                flash(e, 'danger')
            return redirect(url_for('wizard_expediente.paso2'))

        try:
            municipios_ids = [int(mid) for mid in municipios_ids]
        except ValueError:
            flash('IDs de municipios inválidos.', 'danger')
            return redirect(url_for('wizard_expediente.paso2'))

        data['paso2'] = {
            'titulo': titulo,
            'descripcion': descripcion,
            'finalidad': finalidad,
            'emplazamiento': emplazamiento,
            'fecha': fecha.isoformat(),
            'ia_id': int(ia_id) if ia_id else None,
            'municipios_ids': municipios_ids,
        }
        _save_wizard(data)
        return redirect(url_for('wizard_expediente.paso3'))

    tipos_ia = TipoIA.query.order_by(TipoIA.siglas).all()

    return render_template(
        'expedientes/wizard_paso2.html',
        tipos_ia=tipos_ia,
        paso2=paso2_data,
    )


@bp.route('/paso3', methods=['GET', 'POST'])
@login_required
def paso3():
    """
    Paso 3: Solicitud (entidad titular, fecha, tipos de solicitud).

    Commit transaccional completo en este orden:
        1) Proyecto
        2) MunicipioProyecto x N
        3) Expediente  (signal after_insert → histórico INICIAL automático)
        4) Solicitud (con tipo_solicitud_id directo)

    Requiere pasos 1 y 2 completados en sesión.
    """
    data = _get_wizard()
    if 'paso1' not in data or 'paso2' not in data:
        flash('Debe completar primero los pasos anteriores.', 'warning')
        return redirect(url_for('wizard_expediente.paso1'))

    if request.method == 'POST':
        entidad_id = (request.form.get('entidad_id') or '').strip()
        observaciones = (request.form.get('observaciones') or '').strip() or None
        tipo_solicitud_id_raw = (request.form.get('tipo_solicitud_id') or '').strip()

        # --- Validaciones ---
        if not entidad_id:
            flash('Debe seleccionar un titular/solicitante.', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

        try:
            entidad = Entidad.query.filter_by(
                id=int(entidad_id), activo=True, rol_titular=True
            ).first()
        except ValueError:
            entidad = None

        if not entidad:
            flash('La entidad seleccionada no es válida como titular.', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

        # --- Solicitante (puede ser el titular o un tercero autorizado) ---
        solicitante_id_raw = (request.form.get('solicitante_id') or '').strip()
        try:
            solicitante_id = int(solicitante_id_raw) if solicitante_id_raw else entidad.id
        except ValueError:
            solicitante_id = entidad.id

        if solicitante_id != entidad.id:
            if not AutorizadoTitular.puede_actuar_como(solicitante_id, entidad.id):
                flash('El solicitante no tiene autorización vigente para actuar en nombre de este titular.', 'danger')
                return redirect(url_for('wizard_expediente.paso3'))
            solicitante = Entidad.query.get(solicitante_id)
            if not solicitante:
                flash('Solicitante no encontrado.', 'danger')
                return redirect(url_for('wizard_expediente.paso3'))
        else:
            solicitante = entidad

        if not tipo_solicitud_id_raw:
            flash('Debe seleccionar un tipo de solicitud.', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

        try:
            tipo_solicitud_id = int(tipo_solicitud_id_raw)
        except ValueError:
            flash('Tipo de solicitud inválido.', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

        tipo_solicitud = TipoSolicitud.query.get(tipo_solicitud_id)
        if not tipo_solicitud:
            flash('El tipo de solicitud seleccionado no existe.', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

        # --- Transacción ---
        try:
            paso1 = data['paso1']
            paso2 = data['paso2']

            # 1) Proyecto
            proyecto = Proyecto(
                titulo=paso2['titulo'],
                descripcion=paso2['descripcion'],
                finalidad=paso2['finalidad'],
                emplazamiento=paso2['emplazamiento'],
                fecha=date.fromisoformat(paso2['fecha']),
                ia_id=paso2['ia_id'],
            )
            db.session.add(proyecto)
            db.session.flush()  # → proyecto.id disponible

            # 2) Municipios del proyecto
            for municipio_id in paso2['municipios_ids']:
                mp = MunicipioProyecto(
                    municipio_id=municipio_id,
                    proyecto_id=proyecto.id,
                )
                db.session.add(mp)

            # 3) numero_at — tabla contador gapless (sin race condition ni huecos)
            #    UPDATE atómico: si la transacción hace rollback, el contador
            #    también revierte y no se produce ningún hueco en la numeración.
            #    Ver: docs/fuentesIA/numero_at_gapless.md
            numero_at = db.session.execute(
                db.text("UPDATE public.contador_numero_at SET valor = valor + 1 RETURNING valor")
            ).scalar()

            # 4) Expediente
            #    El signal after_insert crea automáticamente el histórico INICIAL
            expediente = Expediente(
                numero_at=numero_at,
                responsable_id=paso1['responsable_id'],
                tipo_expediente_id=paso1['tipo_expediente_id'],
                heredado=paso1['heredado'],
                proyecto_id=proyecto.id,
                titular_id=entidad.id,
            )
            db.session.add(expediente)
            db.session.flush()  # → expediente.id disponible

            # 5) Solicitud (entidad_id = solicitante, que puede ser distinto del titular)
            solicitud = Solicitud(
                expediente_id=expediente.id,
                entidad_id=solicitante.id,
                tipo_solicitud_id=tipo_solicitud_id,
                documento_solicitud_id=None,
                observaciones=observaciones,
            )
            db.session.add(solicitud)

            db.session.commit()
            _reset_wizard()

            flash(f'Expediente AT-{numero_at} creado correctamente.', 'success')
            return redirect(url_for('expedientes.listado_v2'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el expediente: {str(e)}', 'danger')
            return redirect(url_for('wizard_expediente.paso3'))

    # GET
    tipos_solicitudes = TipoSolicitud.query.order_by(TipoSolicitud.siglas).all()
    entidades_titulares = Entidad.query.filter_by(activo=True, rol_titular=True)\
        .order_by(Entidad.nombre_completo).all()
    entidades_opts = [
        {'v': str(e.id), 't': f'{e.nombre_completo} ({e.nif})' if e.nif else e.nombre_completo}
        for e in entidades_titulares
    ]

    return render_template(
        'expedientes/wizard_paso3.html',
        tipos_solicitudes=tipos_solicitudes,
        entidades_opts=entidades_opts,
    )

