"""
Blueprint para administración del catálogo de plazos legales (#632).

Interfaz de configuración para el Supervisor sobre `catalogo_plazos` +
`condiciones_plazo` — mismo patrón ADR-023 (listado + inspector overlay) que
`items_tecnicos` (#594) y `admin_requisitos` (#583). Sin `metadata.json`: entra
como tarjeta del hub del supervisor (ADR-029 §1), no como entrada propia de
sidebar.

Selector en cascada de `campo_fecha` (DISEÑO_FECHAS_PLAZOS.md §3.2): el nivel
ESFTT (`tipo_elemento`) determina qué referencia de documento es válida —
FASE admite dos (documento propio de la fase o el de la solicitud, ver datos
reales en BD: #172/#341/#416/#448/#463), TRAMITE necesita la tarea hija
(`via_tarea_tipo`) + rol, TAREA solo el rol, SOLICITUD es fija (su único FK a
documentos). El bloque visible en el formulario lo decide el servidor según
el nivel actual (edición) o el valor por defecto del select (alta); el JS de
`catalogo-plazos-cascada.js` solo reacciona a cambios posteriores del select
de nivel — no hay que enganchar ningún evento de "fragmento cargado".

Sin ruta `eliminar` — fuera de alcance del issue (baja física); usar
`activar` (baja lógica) como el resto de catálogos normativos del proyecto.

Rutas de formulario:
- GET  /catalogo_plazos/                    — Listado (scroll infinito + inspector)
- POST /catalogo_plazos/crear                — Alta (modal en el listado)
- GET  /catalogo_plazos/<id>/                — Redirige al listado con el inspector abierto
- GET  /catalogo_plazos/<id>/fragmento       — Fragmento de lectura para el inspector
- GET  /catalogo_plazos/<id>/editar-fragmento — Fragmento de edición (incluye condiciones)
- POST /catalogo_plazos/<id>/editar          — Guardar cambios (campos + condiciones)
- POST /catalogo_plazos/<id>/activar         — Alternar activo/inactivo (baja lógica)
"""
from datetime import date

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.catalogo_plazos import CatalogoPlazo
from app.models.condiciones_plazo import CondicionPlazo
from app.models.efectos_plazo import EfectoPlazo
from app.models.motor_reglas import CatalogoVariable
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'catalogo_plazos',
    __name__,
    url_prefix='/catalogo_plazos',
    template_folder='templates',
)

# Nivel ESFTT → (modelo del catálogo de tipos, atributo que porta el código estable).
# TipoSolicitud usa 'siglas' — el resto usa 'codigo' (mismo mapeo que plazos.py).
_TIPO_MODELO = {
    'SOLICITUD': (TipoSolicitud, 'siglas'),
    'FASE':      (TipoFase, 'codigo'),
    'TRAMITE':   (TipoTramite, 'codigo'),
    'TAREA':     (TipoTarea, 'codigo'),
}
_NIVELES_VALIDOS = set(_TIPO_MODELO)
_UNIDADES_VALIDAS = {'DIAS_HABILES', 'DIAS_NATURALES', 'MESES', 'ANOS'}
_ROLES_VALIDOS = {'CONSUMIDO', 'PRODUCIDO'}
_FK_FASE_VALIDOS = {'documento_solicitud_id', 'documento_resultado_id'}

_FK_LABEL = {
    'documento_solicitud_id': 'Fecha administrativa del documento de solicitud',
    'documento_resultado_id': 'Fecha administrativa del documento de resultado de la fase',
}
_ROL_LABEL = {'CONSUMIDO': 'consumido', 'PRODUCIDO': 'producido'}

# Operadores soportados por el CHECK constraint de condiciones_plazo — juego
# completo (a diferencia de items_tecnicos/admin_requisitos, que solo cubren
# EQ/NEQ/IN/NOT_IN/IS_NULL/NOT_NULL). BETWEEN/NOT_BETWEEN reutilizan el mismo
# input de texto que IN/NOT_IN (CSV), exigiendo exactamente 2 valores.
OPERADORES = [
    ('EQ',          'Igual a (=)'),
    ('NEQ',         'Distinto de (≠)'),
    ('IN',          'Está en (lista)'),
    ('NOT_IN',      'No está en (lista)'),
    ('IS_NULL',     'No informado'),
    ('NOT_NULL',    'Informado'),
    ('GT',          'Mayor que (>)'),
    ('GTE',         'Mayor o igual que (≥)'),
    ('LT',          'Menor que (<)'),
    ('LTE',         'Menor o igual que (≤)'),
    ('BETWEEN',     'Entre (rango)'),
    ('NOT_BETWEEN', 'Fuera de rango'),
]
_OPERADORES_VALIDOS = {codigo for codigo, _ in OPERADORES}
_OPERADORES_SIN_VALOR = {'IS_NULL', 'NOT_NULL'}
_OPERADORES_LISTA = {'IN', 'NOT_IN'}
_OPERADORES_RANGO = {'BETWEEN', 'NOT_BETWEEN'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selects_context():
    """Querysets para los selects del formulario (alta y edición)."""
    return {
        'tipos_solicitud': TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'tipos_fase':       TipoFase.query.order_by(TipoFase.codigo).all(),
        'tipos_tramite':    TipoTramite.query.order_by(TipoTramite.codigo).all(),
        'tipos_tarea':      TipoTarea.query.order_by(TipoTarea.codigo).all(),
        'efectos':          EfectoPlazo.query.order_by(EfectoPlazo.nombre).all(),
        'variables':        CatalogoVariable.query.filter_by(activa=True).order_by(CatalogoVariable.etiqueta).all(),
        'operadores':       OPERADORES,
    }


def _tipo_elemento_nombre(tipo_elemento: str, codigo: str) -> str:
    """Nombre legible del tipo referenciado por tipo_elemento_codigo."""
    modelo_attr = _TIPO_MODELO.get(tipo_elemento)
    if not modelo_attr or not codigo:
        return codigo or '—'
    modelo, attr = modelo_attr
    row = modelo.query.filter_by(**{attr: codigo}).first()
    if not row:
        return codigo
    if tipo_elemento == 'SOLICITUD':
        return f'{row.siglas} — {row.descripcion}'
    return row.nombre


def _campo_fecha_legible(tipo_elemento: str, campo_fecha: dict) -> str:
    """Traduce el JSON de campo_fecha a texto legible (DISEÑO_FECHAS_PLAZOS.md §3.2)."""
    campo_fecha = campo_fecha or {}
    fk = campo_fecha.get('fk')
    if fk:
        return _FK_LABEL.get(fk, f'Fecha administrativa vía «{fk}»')

    rol = campo_fecha.get('rol')
    if not rol:
        return 'Sin configurar'
    rol_txt = _ROL_LABEL.get(rol, rol)
    via = campo_fecha.get('via_tarea_tipo')
    if via:
        tipo_tarea = TipoTarea.query.filter_by(codigo=via).first()
        nombre_tarea = tipo_tarea.nombre if tipo_tarea else via
        return f'Fecha administrativa del documento {rol_txt} por la tarea «{nombre_tarea}»'
    return f'Fecha administrativa del documento {rol_txt} por esta tarea'


def _parse_fecha_opcional(valor_raw):
    """Devuelve (date_o_None, hubo_error). Cadena vacía → (None, False)."""
    valor_raw = (valor_raw or '').strip()
    if not valor_raw:
        return None, False
    try:
        return date.fromisoformat(valor_raw), False
    except ValueError:
        return None, True


def _construir_campo_fecha(tipo_elemento: str):
    """Traduce la selección en cascada del formulario al JSON de campo_fecha.

    Devuelve (campo_fecha_dict, error_msg_o_None).
    """
    if tipo_elemento == 'SOLICITUD':
        # Único FK a documentos en Solicitud — sin selección posible (§3.2).
        return {'fk': 'documento_solicitud_id'}, None

    if tipo_elemento == 'FASE':
        fk = (request.form.get('campo_fecha_fk') or '').strip()
        if fk not in _FK_FASE_VALIDOS:
            return None, 'El inicio de cómputo de la fase es obligatorio.'
        return {'fk': fk}, None

    if tipo_elemento == 'TRAMITE':
        via = (request.form.get('campo_fecha_via_tarea_tipo') or '').strip()
        rol = (request.form.get('campo_fecha_rol') or '').strip().upper()
        if not via or not TipoTarea.query.filter_by(codigo=via).first():
            return None, 'La tarea de referencia del inicio de cómputo no es válida.'
        if rol not in _ROLES_VALIDOS:
            return None, 'El documento de referencia (consumido/producido) es obligatorio.'
        return {'via_tarea_tipo': via, 'rol': rol}, None

    if tipo_elemento == 'TAREA':
        rol = (request.form.get('campo_fecha_rol') or '').strip().upper()
        if rol not in _ROLES_VALIDOS:
            return None, 'El documento de referencia (consumido/producido) es obligatorio.'
        return {'rol': rol}, None

    return None, 'Nivel ESFTT no reconocido.'


def _rellenar_catalogo_plazo(item) -> list[str]:
    """Rellena los campos escalares de un CatalogoPlazo desde request.form.

    Devuelve la lista de errores de validación (vacía si todo OK). No incluye
    las condiciones anidadas — ver _construir_condiciones.
    """
    errores = []

    tipo_elemento = (request.form.get('tipo_elemento') or '').strip().upper()
    if tipo_elemento not in _NIVELES_VALIDOS:
        return ['El nivel ESFTT es obligatorio.']  # sin nivel no se puede validar el resto

    modelo, attr_codigo = _TIPO_MODELO[tipo_elemento]
    tipo_elemento_codigo = (request.form.get('tipo_elemento_codigo') or '').strip()
    tipo_row = modelo.query.filter_by(**{attr_codigo: tipo_elemento_codigo}).first() if tipo_elemento_codigo else None
    if not tipo_row:
        errores.append(f'El tipo de {tipo_elemento.lower()} seleccionado no existe.')

    campo_fecha, err_cf = _construir_campo_fecha(tipo_elemento)
    if err_cf:
        errores.append(err_cf)

    plazo_valor_raw = (request.form.get('plazo_valor') or '').strip()
    plazo_valor = int(plazo_valor_raw) if plazo_valor_raw.isdigit() and int(plazo_valor_raw) > 0 else None
    if plazo_valor is None:
        errores.append('El valor del plazo debe ser un número entero positivo.')

    plazo_unidad = (request.form.get('plazo_unidad') or '').strip().upper()
    if plazo_unidad not in _UNIDADES_VALIDAS:
        errores.append('La unidad del plazo no es válida.')

    efecto_id_raw = (request.form.get('efecto_vencimiento_id') or '').strip()
    efecto = EfectoPlazo.query.get(int(efecto_id_raw)) if efecto_id_raw.isdigit() else None
    if not efecto:
        errores.append('El efecto del vencimiento es obligatorio.')

    vigencia_desde, err_desde = _parse_fecha_opcional(request.form.get('vigencia_desde'))
    vigencia_hasta, err_hasta = _parse_fecha_opcional(request.form.get('vigencia_hasta'))
    if err_desde:
        errores.append('La fecha de inicio de vigencia no es válida.')
    if err_hasta:
        errores.append('La fecha de fin de vigencia no es válida.')
    if vigencia_desde and vigencia_hasta and vigencia_hasta < vigencia_desde:
        errores.append('La vigencia hasta no puede ser anterior a la vigencia desde.')

    orden_raw = (request.form.get('orden') or '').strip()
    orden = int(orden_raw) if orden_raw.isdigit() else 100

    if errores:
        return errores

    item.tipo_elemento = tipo_elemento
    item.tipo_elemento_id = tipo_row.id  # DEPRECATED — se conserva por compatibilidad (#347)
    item.tipo_elemento_codigo = tipo_elemento_codigo
    item.campo_fecha = campo_fecha
    item.plazo_valor = plazo_valor
    item.plazo_unidad = plazo_unidad
    item.efecto_vencimiento_id = efecto.id
    item.norma_origen = request.form.get('norma_origen', '').strip() or None
    item.vigencia_desde = vigencia_desde
    item.vigencia_hasta = vigencia_hasta
    item.orden = orden
    return []


def _coerce_escalar(tipo_dato: str, valor: str):
    """Convierte un valor de texto al tipo Python esperado por tipo_dato.

    Devuelve (valor_convertido, error_msg_o_None).
    """
    if tipo_dato == 'boolean':
        low = valor.strip().lower()
        if low in ('true', '1', 'si', 'sí'):
            return True, None
        if low in ('false', '0', 'no'):
            return False, None
        return None, 'debe ser verdadero/falso'
    if tipo_dato == 'numerico':
        try:
            norm = valor.strip().replace(',', '.')
            return (float(norm) if '.' in norm else int(norm)), None
        except ValueError:
            return None, 'debe ser numérico'
    return valor.strip(), None  # texto | fecha | enum — se guarda tal cual


def _coerce_valor(tipo_dato: str, operador: str, valor_raw: str, etiqueta_var: str):
    """Coacciona el valor bruto del formulario al JSON que espera CondicionPlazo.valor.

    Devuelve (valor, error_msg_o_None).
    """
    if operador in _OPERADORES_SIN_VALOR:
        return None, None

    if operador in _OPERADORES_LISTA:
        items = [v.strip() for v in (valor_raw or '').split(',') if v.strip()]
        if not items:
            return None, f'la condición sobre «{etiqueta_var}» necesita al menos un valor (separados por comas).'
        valores = []
        for item in items:
            v, err = _coerce_escalar(tipo_dato, item)
            if err:
                return None, f'valor «{item}» inválido para «{etiqueta_var}»: {err}.'
            valores.append(v)
        return valores, None

    if operador in _OPERADORES_RANGO:
        items = [v.strip() for v in (valor_raw or '').split(',') if v.strip()]
        if len(items) != 2:
            return None, f'la condición sobre «{etiqueta_var}» necesita exactamente 2 valores (mínimo, máximo separados por coma).'
        valores = []
        for item in items:
            v, err = _coerce_escalar(tipo_dato, item)
            if err:
                return None, f'valor «{item}» inválido para «{etiqueta_var}»: {err}.'
            valores.append(v)
        if valores[0] > valores[1]:
            return None, f'la condición sobre «{etiqueta_var}»: el primer valor debe ser menor o igual que el segundo.'
        return valores, None

    if not (valor_raw or '').strip():
        return None, f'la condición sobre «{etiqueta_var}» necesita un valor.'
    return _coerce_escalar(tipo_dato, valor_raw)


def _valor_display(valor) -> str:
    """Representación de texto de CondicionPlazo.valor para prellenar el input.

    Espejo inverso de _coerce_valor/_coerce_escalar: listas → CSV (incluye
    BETWEEN/NOT_BETWEEN, que guardan [min, max]), booleanos → 'true'/'false'.
    """
    if valor is None:
        return ''
    if isinstance(valor, list):
        return ', '.join(str(v) for v in valor)
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    return str(valor)


def _construir_condiciones(variables_por_id: dict) -> tuple[list, list[str]]:
    """Reconstruye la lista completa de CondicionPlazo desde las filas del formulario.

    Las filas llegan como campos repetidos sin indexar (cond_variable_id,
    cond_operador, cond_valor, cond_orden) — el navegador conserva el orden del
    DOM en FormData, así que zip() empareja correctamente cada fila.
    Las filas sin variable seleccionada se descartan (fila añadida y no rellenada).

    Devuelve (condiciones_nuevas, errores). No muta el catálogo — el llamador
    decide sustituir item.condiciones solo si no hay errores.
    """
    variable_ids = request.form.getlist('cond_variable_id')
    operadores   = request.form.getlist('cond_operador')
    valores_raw  = request.form.getlist('cond_valor')
    ordenes_raw  = request.form.getlist('cond_orden')

    condiciones = []
    errores = []

    for i, variable_id_raw in enumerate(variable_ids):
        if not variable_id_raw.strip():
            continue  # fila incompleta descartada

        operador = operadores[i] if i < len(operadores) else ''
        if operador not in _OPERADORES_VALIDOS:
            errores.append(f'Fila {i + 1}: operador no válido.')
            continue

        variable = variables_por_id.get(int(variable_id_raw))
        if not variable:
            errores.append(f'Fila {i + 1}: variable no encontrada.')
            continue

        valor_raw = valores_raw[i] if i < len(valores_raw) else ''
        valor, err = _coerce_valor(variable.tipo_dato, operador, valor_raw, variable.etiqueta)
        if err:
            errores.append(f'Fila {i + 1}: {err}')
            continue

        orden_raw = ordenes_raw[i] if i < len(ordenes_raw) else ''
        orden = int(orden_raw) if orden_raw.strip().isdigit() else (i + 1)

        condiciones.append(CondicionPlazo(
            variable_id=variable.id,
            operador=operador,
            valor=valor,
            orden=orden,
        ))

    return condiciones, errores


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_catalogo_plazos')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023).

    Pasa los selects también para el modal de alta (siempre presente en el
    DOM del listado, no solo en el camino de error de crear()).
    """
    return render_template('catalogo_plazos/listado.html', **_selects_context())


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_catalogo_plazos')
def crear():
    """Alta de un plazo nuevo — modal en el listado (patrón `usuarios`).

    Las condiciones se añaden después, editando desde el inspector — la alta
    solo cubre los campos escalares (mismo criterio que #583/#594).
    """
    item = CatalogoPlazo()
    errores = _rellenar_catalogo_plazo(item)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'catalogo_plazos/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'catalogo_plazos/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    flash('Plazo creado correctamente.', 'success')
    return redirect(url_for('catalogo_plazos.listado', sel=item.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_catalogo_plazos')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    CatalogoPlazo.query.get_or_404(id)
    return redirect(url_for('catalogo_plazos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_catalogo_plazos')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    item = CatalogoPlazo.query.get_or_404(id)
    return render_template(
        'catalogo_plazos/_detalle_fragmento.html',
        item=item,
        tipo_elemento_nombre=_tipo_elemento_nombre(item.tipo_elemento, item.tipo_elemento_codigo),
        campo_fecha_legible=_campo_fecha_legible(item.tipo_elemento, item.campo_fecha),
        puede_editar=tiene_permiso('gestionar_catalogo_plazos'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_catalogo_plazos')
def editar_fragmento(id):
    """Fragmento de edición para el inspector — incluye el editor de condiciones."""
    item = CatalogoPlazo.query.get_or_404(id)
    valor_display = {c.id: _valor_display(c.valor) for c in item.condiciones}
    cf = item.campo_fecha or {}
    return render_template(
        'catalogo_plazos/_editar_fragmento.html',
        item=item,
        valor_display=valor_display,
        cf_fk=cf.get('fk', ''),
        cf_via_tarea_tipo=cf.get('via_tarea_tipo', ''),
        cf_rol=cf.get('rol', ''),
        **_selects_context(),
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_catalogo_plazos')
def editar(id):
    item = CatalogoPlazo.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('catalogo_plazos.listado', sel=id))

    def _responder_errores(errores):
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('catalogo_plazos.listado', sel=id))

    errores = _rellenar_catalogo_plazo(item)
    if errores:
        return _responder_errores(errores)

    variables_por_id = {v.id: v for v in CatalogoVariable.query.filter_by(activa=True).all()}
    nuevas_condiciones, errores_cond = _construir_condiciones(variables_por_id)
    if errores_cond:
        return _responder_errores(errores_cond)

    item.condiciones = nuevas_condiciones

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al guardar: {e}'])

    msg = 'Plazo actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('catalogo_plazos.listado', sel=id))


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_catalogo_plazos')
def activar(id):
    """Alterna activo/inactivo — baja lógica (decisión humana, no automática)."""
    item = CatalogoPlazo.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    item.activo = not item.activo
    db.session.commit()
    estado = 'activado' if item.activo else 'desactivado'
    msg = f'Plazo {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': item.activo})
    flash(msg, 'success')
    return redirect(url_for('catalogo_plazos.listado', sel=id))
