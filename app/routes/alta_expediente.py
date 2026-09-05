"""Alta de expediente — un formulario, un POST, una transacción (#428).

Sustituye al wizard de tres pasos de #67. El wizard era paginación sin
bifurcación: ningún campo del paso 2 o del 3 dependía de lo elegido en el 1, así
que lo único que aportaban las tres pantallas era estado en sesión —y con él, los
fallos de volver atrás con el navegador, abrir dos pestañas o dejar caducar la
sesión a mitad—. De propina arreglaba mal la validación: el paso 2 hacía `redirect`
sin repoblar, así que un campo mal puesto se llevaba por delante los otros siete.

Precio del cambio, y no hay forma de evitarlo: el navegador no deja repoblar un
`<input type="file">`, así que si la validación rebota hay que pedir de nuevo el
fichero. La plantilla lo avisa en vez de fingir que sigue puesto.

La ruta valida el formulario y acumula errores para repintarlos todos juntos; la
transacción entera vive en `app/services/alta_expediente.py`, compartida con los
scripts de expediente-tipo.

Solo multipart, sin explorador in situ (ADR-032 §1): al crear el expediente su
carpeta `AT-N/` todavía no existe, así que la vía «el fichero ya está en su sitio»
no tiene sitio al que apuntar.
"""
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models.autorizados_titular import AutorizadoTitular
from app.models.entidad import Entidad
from app.models.municipios import Municipio
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_ia import TipoIA
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.usuarios import Usuario
from app.services.alta_expediente import (
    DatosAlta, DocumentoSolicitud, alta_expediente,
)

bp = Blueprint('alta_expediente', __name__, url_prefix='/expedientes/nuevo')


def _contexto_formulario(**extra):
    """Catálogos que pinta el formulario, más lo que traiga el repintado."""
    entidades_titulares = (
        Entidad.query.filter_by(activo=True, rol_titular=True)
        .order_by(Entidad.nombre_completo).all()
    )
    contexto = {
        'tipos_expedientes': TipoExpediente.query.order_by(TipoExpediente.tipo).all(),
        'usuarios': Usuario.query.filter_by(activo=True).order_by(
            Usuario.apellido1, Usuario.nombre).all(),
        'tipos_ia': TipoIA.query.order_by(TipoIA.siglas).all(),
        'tipos_solicitudes': TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'entidades_opts': [
            {'v': str(e.id),
             't': f'{e.nombre_completo} ({e.nif})' if e.nif else e.nombre_completo}
            for e in entidades_titulares
        ],
        'form': {},
        'municipios_previos': [],
        'errores': [],
    }
    contexto.update(extra)
    return contexto


def _municipios_previos(ids):
    """Los municipios ya elegidos, con su nombre, para repintar las etiquetas.

    Sin esto el rebote de validación los perdería: el formulario los lleva como
    `<input hidden>` con solo el id, y la etiqueta la puso el selector en su
    momento a partir de una llamada a la API.
    """
    if not ids:
        return []
    filas = Municipio.query.filter(Municipio.id.in_(ids)).all()
    return [{'id': m.id, 'nombre': m.nombre} for m in filas]


@bp.route('/', methods=['GET', 'POST'])
@login_required
def nuevo():
    """Formulario de alta y su envío."""
    if request.method == 'GET':
        return render_template('expedientes/alta_expediente.html',
                               **_contexto_formulario())

    errores = []

    # --- Expediente -------------------------------------------------------
    tipo_expediente_id = _entero(request.form.get('tipo_expediente_id'))
    if tipo_expediente_id is None:
        errores.append('Debe seleccionar un tipo de expediente.')
    elif TipoExpediente.query.get(tipo_expediente_id) is None:
        errores.append('El tipo de expediente seleccionado no es válido.')

    responsable_id = _entero(request.form.get('responsable_id'))
    heredado = request.form.get('heredado') == 'on'

    # --- Proyecto ---------------------------------------------------------
    titulo = (request.form.get('titulo') or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip()
    finalidad = (request.form.get('finalidad') or '').strip()
    emplazamiento = (request.form.get('emplazamiento') or '').strip()

    if not titulo:
        errores.append('El título del proyecto es obligatorio.')
    if not descripcion:
        errores.append('La descripción del proyecto es obligatoria.')
    if not finalidad:
        errores.append('La finalidad del proyecto es obligatoria.')
    if not emplazamiento:
        errores.append('El emplazamiento es obligatorio.')

    fecha_proyecto = _fecha(request.form.get('fecha'))
    if fecha_proyecto is None:
        errores.append('La fecha del proyecto es obligatoria (formato YYYY-MM-DD).')

    ia_id = _entero(request.form.get('ia_id'))

    municipios_ids = [_entero(x) for x in request.form.getlist('municipios_ids[]')]
    municipios_ids = [x for x in municipios_ids if x is not None]
    if not municipios_ids:
        errores.append('Debe añadir al menos un municipio afectado.')

    # --- Titular y solicitante -------------------------------------------
    titular = None
    titular_id = _entero(request.form.get('entidad_id'))
    if titular_id is None:
        errores.append('Debe seleccionar un titular/solicitante.')
    else:
        titular = Entidad.query.filter_by(
            id=titular_id, activo=True, rol_titular=True).first()
        if titular is None:
            errores.append('La entidad seleccionada no es válida como titular.')

    solicitante_id = _entero(request.form.get('solicitante_id'))
    if titular is not None:
        if solicitante_id is None or solicitante_id == titular.id:
            solicitante_id = titular.id
        elif not AutorizadoTitular.puede_actuar_como(solicitante_id, titular.id):
            errores.append('El solicitante no tiene autorización vigente para actuar '
                           'en nombre de este titular.')
        elif Entidad.query.get(solicitante_id) is None:
            errores.append('Solicitante no encontrado.')

    # --- Solicitud --------------------------------------------------------
    tipo_solicitud_id = _entero(request.form.get('tipo_solicitud_id'))
    if tipo_solicitud_id is None:
        errores.append('Debe seleccionar un tipo de solicitud.')
    elif TipoSolicitud.query.get(tipo_solicitud_id) is None:
        errores.append('El tipo de solicitud seleccionado no existe.')

    observaciones = (request.form.get('observaciones') or '').strip() or None

    # --- Escrito de solicitud (el ancla) ----------------------------------
    fichero = request.files.get('documento_solicitud')
    contenido = fichero.read() if fichero and fichero.filename else b''
    if not contenido:
        errores.append('Debe adjuntar el escrito de solicitud.')

    fecha_registro = _fecha(request.form.get('fecha_registro'))
    if fecha_registro is None:
        errores.append('La fecha de registro de entrada de la solicitud es obligatoria '
                       '(formato YYYY-MM-DD).')

    if errores:
        return _repintar(errores, municipios_ids)

    try:
        resultado = alta_expediente(DatosAlta(
            tipo_expediente_id=tipo_expediente_id,
            responsable_id=responsable_id,
            heredado=heredado,
            titulo=titulo,
            descripcion=descripcion,
            finalidad=finalidad,
            emplazamiento=emplazamiento,
            fecha_proyecto=fecha_proyecto,
            ia_id=ia_id,
            municipios_ids=municipios_ids,
            titular_id=titular.id,
            tipo_solicitud_id=tipo_solicitud_id,
            solicitante_id=solicitante_id,
            observaciones=observaciones,
            documento=DocumentoSolicitud(
                contenido=contenido,
                nombre_original=fichero.filename,
                fecha_registro=fecha_registro,
            ),
        ))
    except ValueError as exc:
        # Validación de negocio del servicio: falta de ancla, catálogo ausente o
        # fecha administrativa futura (#824). Se repinta junto al resto.
        return _repintar([str(exc)], municipios_ids)
    except Exception as exc:
        return _repintar([f'Error al crear el expediente: {exc}'], municipios_ids)

    flash(f'Expediente AT-{resultado.numero_at} creado correctamente.', 'success')
    return redirect(url_for('expedientes.listado_v2'))


def _repintar(errores, municipios_ids):
    """Devuelve el formulario con lo escrito y los errores, sin `redirect`.

    Un `redirect` aquí es lo que hacía el wizard, y por eso perdía los campos: la
    petición siguiente ya no lleva el cuerpo. El fichero es la única excepción
    —el navegador no permite repoblarlo— y la plantilla lo dice.
    """
    for e in errores:
        flash(e, 'danger')
    return render_template(
        'expedientes/alta_expediente.html',
        **_contexto_formulario(
            form=request.form,
            municipios_previos=_municipios_previos(municipios_ids),
            errores=errores,
        )
    ), 422


def _entero(valor):
    """`int` o None — vale para campo ausente, vacío y basura."""
    try:
        return int((valor or '').strip())
    except (ValueError, AttributeError):
        return None


def _fecha(valor):
    """`date` o None."""
    try:
        return date.fromisoformat((valor or '').strip())
    except ValueError:
        return None
