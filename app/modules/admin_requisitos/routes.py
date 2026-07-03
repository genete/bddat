"""
Blueprint para administración del catálogo de requisitos documentales (#583).

Interfaz de configuración para el Supervisor sobre `requisitos_documentales` +
`condiciones_requisito` — mismo patrón ADR-023 (listado + inspector overlay)
que `admin_plantillas` (#545), y mismo patrón de alta vía modal que `usuarios`.

Rutas de formulario:
- GET  /admin/requisitos/                    — Listado (scroll infinito + inspector)
- POST /admin/requisitos/crear                — Alta (modal en el listado)
- GET  /admin/requisitos/<id>/                — Redirige al listado con el inspector abierto
- GET  /admin/requisitos/<id>/fragmento       — Fragmento de lectura para el inspector
- GET  /admin/requisitos/<id>/editar-fragmento — Fragmento de edición (incluye condiciones)
- POST /admin/requisitos/<id>/editar          — Guardar cambios (campos + condiciones)
- POST /admin/requisitos/<id>/activar         — Alternar activo/inactivo (baja lógica)
- POST /admin/requisitos/<id>/eliminar        — Baja física, solo si no tiene usos
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.decorators import require_permiso
from app.models.motor_reglas import CatalogoVariable, Norma
from app.models.requisitos_documentales import CondicionRequisito, RequisitoDocumental
from app.models.tipos_documentos import TipoDocumento
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'admin_requisitos',
    __name__,
    url_prefix='/admin/requisitos',
    template_folder='templates',
)

# Mismos operadores que CondicionRegla (#170) — ver CondicionRequisito.__doc__
OPERADORES = [
    ('EQ',       'Igual a (=)'),
    ('NEQ',      'Distinto de (≠)'),
    ('IN',       'Está en (lista)'),
    ('NOT_IN',   'No está en (lista)'),
    ('IS_NULL',  'No informado'),
    ('NOT_NULL', 'Informado'),
]
_OPERADORES_VALIDOS = {codigo for codigo, _ in OPERADORES}
_OPERADORES_SIN_VALOR = {'IS_NULL', 'NOT_NULL'}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _selects_context():
    """Querysets para los selects del formulario (alta y edición)."""
    return {
        # Documentos que puede aportar el interesado (excluye los de generación
        # puramente interna de la administración, p.ej. resoluciones).
        'tipos_documento': (
            TipoDocumento.query
            .filter(TipoDocumento.origen != 'INTERNO')
            .order_by(TipoDocumento.nombre)
            .all()
        ),
        'normas': Norma.query.order_by(Norma.codigo).all(),
        # Solo variables activas en el Variable Registry (misma regla que reglas_motor)
        'variables': CatalogoVariable.query.filter_by(activa=True).order_by(CatalogoVariable.etiqueta).all(),
        'operadores': OPERADORES,
    }


def _rellenar_requisito(requisito) -> list[str]:
    """Rellena los campos escalares de un RequisitoDocumental desde request.form.

    Devuelve la lista de errores de validación (vacía si todo OK). No incluye
    las condiciones anidadas — ver _construir_condiciones.
    """
    errores = []
    tipo_documento_id = request.form.get('tipo_documento_id') or None
    if not tipo_documento_id:
        errores.append('El tipo de documento es obligatorio.')

    orden_raw = request.form.get('orden', '').strip()
    orden = int(orden_raw) if orden_raw.isdigit() else 1

    norma_id_raw = request.form.get('norma_id') or None

    if errores:
        return errores

    requisito.tipo_documento_id = int(tipo_documento_id)
    requisito.descripcion_legal = request.form.get('descripcion_legal', '').strip() or None
    requisito.norma_id          = int(norma_id_raw) if norma_id_raw else None
    requisito.articulo          = request.form.get('articulo', '').strip() or None
    requisito.orden             = orden
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
    """Coacciona el valor bruto del formulario al JSON que espera CondicionRequisito.valor.

    Devuelve (valor, error_msg_o_None).
    """
    if operador in _OPERADORES_SIN_VALOR:
        return None, None

    if operador in ('IN', 'NOT_IN'):
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

    if not (valor_raw or '').strip():
        return None, f'la condición sobre «{etiqueta_var}» necesita un valor.'
    return _coerce_escalar(tipo_dato, valor_raw)


def _valor_display(valor) -> str:
    """Representación de texto de CondicionRequisito.valor para prellenar el input.

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
    """Reconstruye la lista completa de CondicionRequisito desde las filas del formulario.

    Las filas llegan como campos repetidos sin indexar (cond_variable_id,
    cond_operador, cond_valor, cond_orden) — el navegador conserva el orden del
    DOM en FormData, así que zip() empareja correctamente cada fila.
    Las filas sin variable seleccionada se descartan (fila añadida y no rellenada).

    Devuelve (condiciones_nuevas, errores). No muta el requisito — el llamador
    decide sustituir requisito.condiciones solo si no hay errores.
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

        condiciones.append(CondicionRequisito(
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
@require_permiso('acceder_requisitos_documentales')
def listado():
    """Listado del catálogo — scroll infinito + inspector overlay (ADR-023).

    Pasa tipos_documento y normas también para el modal de alta (siempre
    presente en el DOM del listado, no solo en el camino de error de crear()).
    """
    ctx = _selects_context()
    return render_template(
        'admin_requisitos/listado.html',
        tipos_documento=ctx['tipos_documento'],
        normas=ctx['normas'],
    )


@bp.route('/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_requisitos_documentales')
def crear():
    """Alta de un requisito nuevo — modal en el listado (patrón `usuarios`).

    Las condiciones se añaden después, editando desde el inspector — la alta
    solo cubre los campos escalares (decisión de diseño #583).
    """
    requisito = RequisitoDocumental()
    errores = _rellenar_requisito(requisito)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        return render_template(
            'admin_requisitos/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    db.session.add(requisito)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return render_template(
            'admin_requisitos/listado.html',
            show_modal=True, form_data=request.form,
            **_selects_context(),
        )

    flash('Requisito documental creado correctamente.', 'success')
    return redirect(url_for('admin_requisitos.listado', sel=requisito.id))


@bp.route('/<int:id>/')
@login_required
@require_permiso('acceder_requisitos_documentales')
def detalle(id):
    """Redirige al listado con el inspector abierto (conserva enlaces/marcadores)."""
    RequisitoDocumental.query.get_or_404(id)
    return redirect(url_for('admin_requisitos.listado', sel=id))


@bp.route('/<int:id>/fragmento')
@login_required
@require_permiso('acceder_requisitos_documentales')
def fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    requisito = RequisitoDocumental.query.get_or_404(id)
    return render_template(
        'admin_requisitos/_detalle_fragmento.html',
        requisito=requisito,
        puede_editar=tiene_permiso('gestionar_requisitos_documentales'),
        puede_eliminar=tiene_permiso('eliminar_requisitos_documentales'),
    )


@bp.route('/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_requisitos_documentales')
def editar_fragmento(id):
    """Fragmento de edición para el inspector — incluye el editor de condiciones."""
    requisito = RequisitoDocumental.query.get_or_404(id)
    valor_display = {c.id: _valor_display(c.valor) for c in requisito.condiciones}
    return render_template(
        'admin_requisitos/_editar_fragmento.html',
        requisito=requisito,
        valor_display=valor_display,
        **_selects_context(),
    )


@bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@require_permiso('gestionar_requisitos_documentales')
def editar(id):
    requisito = RequisitoDocumental.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # GET → la edición vive en el inspector; el acceso directo redirige.
    if request.method == 'GET':
        return redirect(url_for('admin_requisitos.listado', sel=id))

    def _responder_errores(errores):
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('admin_requisitos.listado', sel=id))

    errores = _rellenar_requisito(requisito)
    if errores:
        return _responder_errores(errores)

    variables_por_id = {v.id: v for v in CatalogoVariable.query.filter_by(activa=True).all()}
    nuevas_condiciones, errores_cond = _construir_condiciones(variables_por_id)
    if errores_cond:
        return _responder_errores(errores_cond)

    requisito.condiciones = nuevas_condiciones

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al guardar: {e}'])

    msg = 'Requisito actualizado correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('admin_requisitos.listado', sel=id))


@bp.route('/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_requisitos_documentales')
def activar(id):
    """Alterna activo/inactivo — baja lógica (decisión humana, no automática, #583)."""
    requisito = RequisitoDocumental.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    requisito.activo = not requisito.activo
    db.session.commit()
    estado = 'activado' if requisito.activo else 'desactivado'
    msg = f'Requisito {estado}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activo': requisito.activo})
    flash(msg, 'success')
    return redirect(url_for('admin_requisitos.listado', sel=id))


@bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@require_permiso('eliminar_requisitos_documentales')
def eliminar(id):
    """Baja física — solo ADMIN (más restrictivo que gestionar; el SUPERVISOR
    puede crear/editar/activar-desactivar pero no borrar en firme, #583).

    Solo procede si el requisito no tiene documentos vinculados en ninguna
    solicitud (usos vacío). Si los tiene, usar 'activar' (baja lógica) para no
    dejar huérfanos los DocumentoRequisito de expedientes ya tramitados.

    Navegación normal (no XHR): tras borrar, el fragmento del inspector ya no
    existe — un refresh() del inspector 404earía, así que este botón es un
    <form> plano (no data-inspector-form) que recarga el listado completo.
    """
    requisito = RequisitoDocumental.query.get_or_404(id)
    if requisito.usos:
        flash(
            f'No se puede eliminar: {len(requisito.usos)} solicitud(es) tienen un '
            'documento vinculado a este requisito. Desactívalo en su lugar.',
            'danger',
        )
        return redirect(url_for('admin_requisitos.listado', sel=id))

    db.session.delete(requisito)
    db.session.commit()
    flash('Requisito eliminado correctamente.', 'success')
    return redirect(url_for('admin_requisitos.listado'))
