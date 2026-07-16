"""
Blueprint para administración del catálogo de ítems técnicos del proyecto (#594).

Interfaz de configuración para el Supervisor sobre `items_tecnicos` +
`condiciones_item_tecnico` — mismo patrón ADR-023 (listado + inspector overlay)
que `admin_requisitos` (#583). Sin `metadata.json`: entra como tarjeta del hub
del supervisor (ADR-029 §1 — configuración ocasional, no consulta diaria de un
rol no-supervisor), no como entrada propia de sidebar.

Rutas de formulario:
- GET  /items_tecnicos/                    — Listado (scroll infinito + inspector)
- POST /items_tecnicos/crear                — Alta (modal en el listado)
- GET  /items_tecnicos/<id>/                — Redirige al listado con el inspector abierto
- GET  /items_tecnicos/<id>/fragmento       — Fragmento de lectura para el inspector
- GET  /items_tecnicos/<id>/editar-fragmento — Fragmento de edición (incluye condiciones)
- POST /items_tecnicos/<id>/editar          — Guardar cambios (campos + condiciones)
- POST /items_tecnicos/<id>/activar         — Alternar activo/inactivo (baja lógica)
- POST /items_tecnicos/<id>/eliminar        — Baja física, solo si no tiene usos
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.items_tecnicos import CondicionItemTecnico, ItemTecnico
from app.models.motor_reglas import CatalogoVariable, Norma
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'items_tecnicos',
    __name__,
    url_prefix='/items_tecnicos',
    template_folder='templates',
)

# Mismos operadores que CondicionRequisito/CondicionRegla (#170).
# Paridad completa desde #660 (antes solo exponía 6 de los 12).
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
        'normas': Norma.query.order_by(Norma.codigo).all(),
        # Solo variables activas en el Variable Registry (misma regla que reglas_motor)
        'variables': CatalogoVariable.query.filter_by(activa=True).order_by(CatalogoVariable.etiqueta).all(),
        'operadores': OPERADORES,
    }


def _rellenar_item(item) -> list[str]:
    """Rellena los campos escalares de un ItemTecnico desde request.form.

    Devuelve la lista de errores de validación (vacía si todo OK). No incluye
    las condiciones anidadas — ver _construir_condiciones.
    """
    errores = []
    descripcion = request.form.get('descripcion', '').strip()
    if not descripcion:
        errores.append('La descripción del ítem es obligatoria.')

    orden_raw = request.form.get('orden', '').strip()
    orden = int(orden_raw) if orden_raw.isdigit() else 1

    norma_id_raw = request.form.get('norma_id') or None

    if errores:
        return errores

    item.descripcion = descripcion
    item.norma_id    = int(norma_id_raw) if norma_id_raw else None
    item.articulo    = request.form.get('articulo', '').strip() or None
    item.orden       = orden
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
    """Coacciona el valor bruto del formulario al JSON que espera CondicionItemTecnico.valor.

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
    """Representación de texto de CondicionItemTecnico.valor para prellenar el input.

    Espejo inverso de _coerce_valor/_coerce_escalar: listas → CSV, booleanos →
    'true'/'false' (mismos literales que acepta _coerce_escalar al reenviar).
    """
    if valor is None:
        return ''
    if isinstance(valor, list):
        return ', '.join(str(v) for v in valor)
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    return str(valor)


def _construir_condiciones(variables_por_id: dict) -> tuple[list, list[str]]:
    """Reconstruye la lista completa de CondicionItemTecnico desde las filas del formulario.

    Las filas llegan como campos repetidos sin indexar (cond_variable_id,
    cond_operador, cond_valor, cond_orden) — el navegador conserva el orden del
    DOM en FormData, así que zip() empareja correctamente cada fila.
    Las filas sin variable seleccionada se descartan (fila añadida y no rellenada).

    Devuelve (condiciones_nuevas, errores). No muta el ítem — el llamador
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

        condiciones.append(CondicionItemTecnico(
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
@require_permiso('acceder_items_tecnicos')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023).

    Pasa normas también para el modal de alta (siempre presente en el DOM del
    listado, no solo en el camino de error de crear()).
    """
    ctx = _selects_context()
    return render_template(
        'items_tecnicos/listado.html',
        normas=ctx['normas'],
    )


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_items_tecnicos')
def crear():
    """Alta de un ítem nuevo — modal en el listado (patrón `usuarios`).

    Las condiciones se añaden después, editando desde el inspector — la alta
    solo cubre los campos escalares (mismo criterio que #583).
    """
    item = ItemTecnico()
    errores = _rellenar_item(item)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'items_tecnicos/listado.html',
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
            'items_tecnicos/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    flash('Ítem técnico creado correctamente.', 'success')
    return redirect(url_for('items_tecnicos.listado', sel=item.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_items_tecnicos')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    ItemTecnico.query.get_or_404(id)
    return redirect(url_for('items_tecnicos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_items_tecnicos')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    item = ItemTecnico.query.get_or_404(id)
    return render_template(
        'items_tecnicos/_detalle_fragmento.html',
        item=item,
        puede_editar=tiene_permiso('gestionar_items_tecnicos'),
        puede_eliminar=tiene_permiso('eliminar_items_tecnicos'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_items_tecnicos')
def editar_fragmento(id):
    """Fragmento de edición para el inspector — incluye el editor de condiciones."""
    item = ItemTecnico.query.get_or_404(id)
    valor_display = {c.id: _valor_display(c.valor) for c in item.condiciones}
    return render_template(
        'items_tecnicos/_editar_fragmento.html',
        item=item,
        valor_display=valor_display,
        **_selects_context(),
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_items_tecnicos')
def editar(id):
    item = ItemTecnico.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('items_tecnicos.listado', sel=id))

    def _responder_errores(errores):
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('items_tecnicos.listado', sel=id))

    errores = _rellenar_item(item)
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

    msg = 'Ítem técnico actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('items_tecnicos.listado', sel=id))


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_items_tecnicos')
def activar(id):
    """Alterna activo/inactivo — baja lógica (decisión humana, no automática)."""
    item = ItemTecnico.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    item.activo = not item.activo
    db.session.commit()
    estado = 'activado' if item.activo else 'desactivado'
    msg = f'Ítem técnico {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': item.activo})
    flash(msg, 'success')
    return redirect(url_for('items_tecnicos.listado', sel=id))


@bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@require_permiso('eliminar_items_tecnicos')
def eliminar(id):
    """Baja física — solo ADMIN (más restrictivo que gestionar; el SUPERVISOR
    puede crear/editar/activar-desactivar pero no borrar en firme, mismo
    criterio que #583).

    Solo procede si el ítem no tiene coberturas vinculadas en ninguna
    solicitud (usos vacío). Si las tiene, usar 'activar' (baja lógica) para no
    dejar huérfanas las CoberturaItemTecnico de expedientes ya tramitados.

    Navegación normal (no XHR): tras borrar, el fragmento del inspector ya no
    existe — un refresh() del inspector 404earía, así que este botón es un
    <form> plano (no data-inspector-form) que recarga el listado completo.
    """
    item = ItemTecnico.query.get_or_404(id)
    if item.usos:
        flash(
            f'No se puede eliminar: {len(item.usos)} solicitud(es) tienen una '
            'verificación vinculada a este ítem. Desactívalo en su lugar.',
            'danger',
        )
        return redirect(url_for('items_tecnicos.listado', sel=id))

    db.session.delete(item)
    db.session.commit()
    flash('Ítem técnico eliminado correctamente.', 'success')
    return redirect(url_for('items_tecnicos.listado'))
