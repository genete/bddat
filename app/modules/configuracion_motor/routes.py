"""
Blueprint "Configuración del motor" (#479/#170, ADR-028 bloque Gestión).

Cubre el selector de modo global (#479; backend de #323) y el CRUD de
`reglas_motor` + `condiciones_regla` + `excepciones_motor` +
`condiciones_excepcion` (#170, N016) — todo en la misma página, no pantallas
aparte (así lo fija el diseño original de #479).

Patrón ADR-023 (listado + inspector overlay), mismo que `catalogo_plazos`
(#632) y `admin_requisitos` (#583): el listado de reglas usa el componente
`ScrollInfinito` contra `api_reglas_motor.listar_reglas_motor`
(`/api/reglas-motor`), troceando el marcado de `layout/lista_v2_base.html`
dentro de la sección "Reglas del motor" en vez de heredarlo (esa página ya
extiende `base_app.html` para la sección de modo global, y una plantilla solo
puede extender un padre).

El editor de condiciones (variable + operador + valor + orden) reutiliza tal
cual `requisitos-inspector.js` (delegación de eventos a nivel `document`,
soporta múltiples instancias simultáneas — usado también dentro del modal de
excepciones). Mismos operadores que `CondicionPlazo`/`CondicionRequisito`.

Las excepciones son una colección con CRUD propio (cada una con sus propias
condiciones) → van a modal grande (ADR-023 §6, `AppModalLarge`), lanzado
desde el inspector de la regla — mismo patrón que
`entidades/_gestionar_direcciones_fragmento.html`.

El campo `sujeto` (patrón posicional ESFTT, `assembler._compilar_sujeto`)
nunca se teclea a mano: un typo no da error, la regla queda inerte en
silencio (matching por `==` exacto, `motor_reglas._sujeto_casa`). Se
construye/reconstruye en servidor a partir de un selector en cascada
(nivel → hasta 4 selects con las opciones reales de cada catálogo + "ANY").

RUTAS:
    GET  /configuracion-motor/                          → página completa.
    POST /configuracion-motor/modo-global                → guarda el modo elegido.
    GET  /configuracion-motor/estado                     → JSON {modo} de solo lectura.

    POST /configuracion-motor/reglas/crear
    GET  /configuracion-motor/reglas/<id>/fragmento
    GET  /configuracion-motor/reglas/<id>/editar-fragmento
    POST /configuracion-motor/reglas/<id>/editar
    POST /configuracion-motor/reglas/<id>/activar

    GET  /configuracion-motor/reglas/<regla_id>/excepciones/fragmento
    GET  /configuracion-motor/reglas/<regla_id>/excepciones/nueva-fragmento
    POST /configuracion-motor/reglas/<regla_id>/excepciones/crear
    GET  /configuracion-motor/reglas/<regla_id>/excepciones/<id>/editar-fragmento
    POST /configuracion-motor/reglas/<regla_id>/excepciones/<id>/editar
    POST /configuracion-motor/reglas/<regla_id>/excepciones/<id>/activar
"""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.decorators import require_permiso
from app.models.configuracion_sistema import ConfiguracionSistema
from app.models.motor_reglas import (
    CatalogoVariable, CondicionExcepcion, CondicionRegla, ExcepcionMotor, Norma, ReglaMotor,
)
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tramites import TipoTramite
from app.services import bitacora as bitacora_svc
from app.services.motor_modo_global import CLAVE_MODO
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'configuracion_motor',
    __name__,
    url_prefix='/configuracion-motor',
    template_folder='templates',
)

MODOS = [
    ('BLOQUEAR', 'Bloquear',
     'Comportamiento normal: el motor bloquea y advierte según las reglas.'),
    ('SOLO_ADVERTIR', 'Solo advertir',
     'Las prohibiciones se convierten en advertencias. Ninguna acción queda bloqueada.'),
    ('INACTIVO', 'Inactivo',
     'El motor no evalúa. Toda acción se permite sin restricciones.'),
]
_MODOS_VALIDOS = {codigo for codigo, _, _ in MODOS}
_ETIQUETAS = {codigo: etiqueta for codigo, etiqueta, _ in MODOS}
_CLASES_SEMAFORO = {'BLOQUEAR': 'success', 'SOLO_ADVERTIR': 'warning', 'INACTIVO': 'danger'}


# ---------------------------------------------------------------------------
# Reglas del motor — catálogos y constantes
# ---------------------------------------------------------------------------

_ACCIONES = [('CREAR', 'Crear'), ('BORRAR', 'Borrar')]
_EFECTOS = [('BLOQUEAR', 'Bloquear'), ('ADVERTIR', 'Advertir')]
_ACCIONES_VALIDAS = {codigo for codigo, _ in _ACCIONES}
_EFECTOS_VALIDOS = {codigo for codigo, _ in _EFECTOS}

# Nivel del sujeto → cuántos segmentos tiene, y de dónde sale cada uno.
# Coincide exactamente con la acumulación de app.services.assembler._compilar_sujeto.
_NIVELES_SUJETO = ['EXPEDIENTE', 'SOLICITUD', 'FASE', 'TRAMITE']
_SEGMENTO_MODELO = [
    (TipoExpediente, 'tipo',   'descripcion', 'tipo de expediente'),
    (TipoSolicitud,  'siglas', 'descripcion', 'tipo de solicitud'),
    (TipoFase,       'codigo', 'nombre',      'tipo de fase'),
    (TipoTramite,    'codigo', 'nombre',      'tipo de trámite'),
]

# Mismo juego de operadores que CondicionPlazo/CondicionRequisito (CHECK
# constraint idéntico en condiciones_regla/condiciones_excepcion).
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
# Helpers — modo global (#479, sin cambios)
# ---------------------------------------------------------------------------

def estado_semaforo() -> dict:
    """Helper para el context processor global (primer render, sin esperar al polling JS)."""
    modo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return {
        'modo': modo,
        'etiqueta': _ETIQUETAS.get(modo, modo),
        'clase': _CLASES_SEMAFORO.get(modo, 'secondary'),
    }


# ---------------------------------------------------------------------------
# Helpers — selects y sujeto
# ---------------------------------------------------------------------------

def _selects_context():
    """Querysets para los selects de reglas/excepciones (alta y edición)."""
    return {
        'acciones':         _ACCIONES,
        'efectos':          _EFECTOS,
        'niveles_sujeto':   _NIVELES_SUJETO,
        'tipos_expediente': TipoExpediente.query.order_by(TipoExpediente.tipo).all(),
        'tipos_solicitud':  TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'tipos_fase':       TipoFase.query.order_by(TipoFase.codigo).all(),
        'tipos_tramite':    TipoTramite.query.order_by(TipoTramite.codigo).all(),
        'normas':           Norma.query.order_by(Norma.codigo).all(),
        'variables':        CatalogoVariable.query.filter_by(activa=True).order_by(CatalogoVariable.etiqueta).all(),
        'operadores':       OPERADORES,
    }


def _construir_sujeto():
    """Reconstruye el string `sujeto` a partir del nivel + selects del formulario.

    Devuelve (nivel, sujeto, error_msg_o_None). Valida cada segmento contra su
    catálogo real (o 'ANY') — nunca acepta texto libre.
    """
    nivel = (request.form.get('sujeto_nivel') or '').strip().upper()
    if nivel not in _NIVELES_SUJETO:
        return None, None, 'El nivel del sujeto es obligatorio.'

    n_segmentos = _NIVELES_SUJETO.index(nivel) + 1
    segmentos = []
    for i in range(n_segmentos):
        modelo, attr, _label_attr, label = _SEGMENTO_MODELO[i]
        valor = (request.form.get(f'sujeto_seg{i}') or '').strip()
        if not valor:
            return None, None, f'Falta seleccionar «{label}».'
        if valor != 'ANY' and not modelo.query.filter_by(**{attr: valor}).first():
            return None, None, f'El valor de «{label}» no existe en el catálogo.'
        segmentos.append(valor)

    return nivel, '/'.join(segmentos), None


def _sujeto_a_partes(sujeto: str):
    """(nivel, [4 segmentos]) a partir de un `sujeto` ya guardado — para prellenar la cascada.

    Siempre devuelve una lista de longitud fija (len(_NIVELES_SUJETO)),
    rellenando con '' los segmentos que no aplican al nivel actual —
    así el template no necesita comprobar longitudes.
    """
    partes = (sujeto or '').split('/') if sujeto else []
    n = len(partes)
    nivel = _NIVELES_SUJETO[n - 1] if 1 <= n <= len(_NIVELES_SUJETO) else _NIVELES_SUJETO[0]
    partes_rellenas = partes + [''] * (len(_NIVELES_SUJETO) - len(partes))
    return nivel, partes_rellenas


def _sujeto_partes_desde_form():
    """(nivel, [4 segmentos]) reconstruidos desde request.form — para repintar el
    modal de alta tras un error de validación sin perder lo ya seleccionado."""
    nivel = (request.form.get('sujeto_nivel') or 'SOLICITUD').strip().upper()
    if nivel not in _NIVELES_SUJETO:
        nivel = 'SOLICITUD'
    partes = [(request.form.get(f'sujeto_seg{i}') or '') for i in range(len(_NIVELES_SUJETO))]
    return nivel, partes


def _sujeto_legible(sujeto: str) -> str:
    """Traduce cada segmento del `sujeto` a su nombre legible, para el fragmento de lectura."""
    partes = (sujeto or '').split('/')
    etiquetas = []
    for i, valor in enumerate(partes):
        if i >= len(_SEGMENTO_MODELO):
            etiquetas.append(valor)
            continue
        if valor == 'ANY':
            etiquetas.append('Cualquiera')
            continue
        modelo, attr, label_attr, _ = _SEGMENTO_MODELO[i]
        row = modelo.query.filter_by(**{attr: valor}).first()
        etiquetas.append(getattr(row, label_attr) if row else valor)
    return ' / '.join(etiquetas)


# ---------------------------------------------------------------------------
# Helpers — condiciones (compartidos entre CondicionRegla y CondicionExcepcion)
# ---------------------------------------------------------------------------

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
    """Coacciona el valor bruto del formulario al JSON que espera *.valor.

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
    """Representación de texto del valor de una condición, para prellenar el input."""
    if valor is None:
        return ''
    if isinstance(valor, list):
        return ', '.join(str(v) for v in valor)
    if isinstance(valor, bool):
        return 'true' if valor else 'false'
    return str(valor)


def _construir_condiciones(modelo_condicion, variables_por_id: dict) -> tuple[list, list[str]]:
    """Reconstruye la lista de condiciones (CondicionRegla o CondicionExcepcion) desde request.form.

    Filas repetidas sin indexar (cond_variable_id, cond_operador, cond_valor,
    cond_orden) — el navegador conserva el orden del DOM en FormData, así que
    zip() por índice empareja correctamente cada fila. Filas sin variable
    seleccionada se descartan.
    """
    variable_ids = request.form.getlist('cond_variable_id')
    operadores   = request.form.getlist('cond_operador')
    valores_raw  = request.form.getlist('cond_valor')
    ordenes_raw  = request.form.getlist('cond_orden')

    condiciones = []
    errores = []

    for i, variable_id_raw in enumerate(variable_ids):
        if not variable_id_raw.strip():
            continue

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

        condiciones.append(modelo_condicion(
            variable_id=variable.id,
            operador=operador,
            valor=valor,
            orden=orden,
        ))

    return condiciones, errores


# ---------------------------------------------------------------------------
# Helpers — regla / excepción (campos escalares)
# ---------------------------------------------------------------------------

def _rellenar_regla(item: ReglaMotor) -> list[str]:
    """Rellena los campos escalares de una ReglaMotor desde request.form.

    Devuelve la lista de errores (vacía si todo OK). No incluye condiciones.
    """
    errores = []

    accion = (request.form.get('accion') or '').strip().upper()
    if accion not in _ACCIONES_VALIDAS:
        errores.append('La acción es obligatoria.')

    efecto = (request.form.get('efecto') or '').strip().upper()
    if efecto not in _EFECTOS_VALIDOS:
        errores.append('El efecto es obligatorio.')

    _nivel, sujeto, err_sujeto = _construir_sujeto()
    if err_sujeto:
        errores.append(err_sujeto)

    norma_id_raw = (request.form.get('norma_id') or '').strip()
    norma = Norma.query.get(int(norma_id_raw)) if norma_id_raw.isdigit() else None
    if norma_id_raw and not norma:
        errores.append('La norma seleccionada no existe.')

    prioridad_raw = (request.form.get('prioridad') or '').strip()
    prioridad = int(prioridad_raw) if prioridad_raw.isdigit() else 0

    if errores:
        return errores

    item.accion = accion
    item.efecto = efecto
    item.sujeto = sujeto
    item.norma_id = norma.id if norma else None
    item.articulo = (request.form.get('articulo') or '').strip() or None
    item.apartado = (request.form.get('apartado') or '').strip() or None
    item.prioridad = prioridad
    item.descripcion = (request.form.get('descripcion') or '').strip() or None
    return []


def _rellenar_excepcion(item: ExcepcionMotor) -> list[str]:
    """Rellena los campos escalares de una ExcepcionMotor desde request.form."""
    errores = []

    norma_id_raw = (request.form.get('norma_id') or '').strip()
    norma = Norma.query.get(int(norma_id_raw)) if norma_id_raw.isdigit() else None
    if norma_id_raw and not norma:
        errores.append('La norma seleccionada no existe.')

    if errores:
        return errores

    item.norma_id = norma.id if norma else None
    item.articulo = (request.form.get('articulo') or '').strip() or None
    item.apartado = (request.form.get('apartado') or '').strip() or None
    return []


# ---------------------------------------------------------------------------
# Rutas — página y modo global (#479, sin cambios de comportamiento)
# ---------------------------------------------------------------------------

@bp.route('/')
@login_required
@require_permiso('acceder_reglas_motor')
def index():
    modo_actual = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return render_template(
        'configuracion_motor/index.html',
        modos=MODOS,
        modo_actual=modo_actual,
        puede_gestionar=tiene_permiso('gestionar_reglas_motor'),
        sujeto_nivel='SOLICITUD',
        sujeto_partes=['', '', '', ''],
        **_selects_context(),
    )


@bp.route('/modo-global', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def guardar_modo_global():
    nuevo_modo = request.form.get('modo')
    if nuevo_modo not in _MODOS_VALIDOS:
        flash('Modo no válido.', 'danger')
        return redirect(url_for('configuracion_motor.index'))

    modo_anterior = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    if nuevo_modo != modo_anterior:
        ConfiguracionSistema.set(CLAVE_MODO, nuevo_modo)
        bitacora_svc.registrar(
            current_user.id, 'ALTERAR', 'configuracion_sistema', 0,
            columna=CLAVE_MODO,
            detalle={'de': modo_anterior, 'a': nuevo_modo},
        )
        db.session.commit()
        flash(f'Modo global del motor actualizado a «{nuevo_modo}».', 'success')
    else:
        flash('El modo elegido ya estaba activo.', 'info')

    return redirect(url_for('configuracion_motor.index'))


@bp.route('/estado')
@login_required
def estado():
    """Solo lectura, sin permiso de gestión — el semáforo lo ve cualquier rol autenticado.

    Devuelve también etiqueta/clase para que el JS de la topbar no duplique el mapeo.
    """
    modo = ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR')
    return jsonify({
        'modo': modo,
        'etiqueta': _ETIQUETAS.get(modo, modo),
        'clase': _CLASES_SEMAFORO.get(modo, 'secondary'),
    })


# ---------------------------------------------------------------------------
# Rutas — reglas del motor (#170)
# ---------------------------------------------------------------------------

@bp.route('/reglas/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def regla_crear():
    """Alta de una regla nueva — modal en el listado.

    Las condiciones se añaden después, editando desde el inspector — mismo
    criterio que catalogo_plazos/admin_requisitos.
    """
    item = ReglaMotor(activa=True)
    errores = _rellenar_regla(item)
    if errores:
        for msg in errores:
            flash(msg, 'danger')
        sujeto_nivel, sujeto_partes = _sujeto_partes_desde_form()
        return render_template(
            'configuracion_motor/index.html',
            modos=MODOS,
            modo_actual=ConfiguracionSistema.get(CLAVE_MODO, 'BLOQUEAR'),
            puede_gestionar=tiene_permiso('gestionar_reglas_motor'),
            show_modal_regla=True, form_data=request.form,
            sujeto_nivel=sujeto_nivel, sujeto_partes=sujeto_partes,
            **_selects_context(),
        )

    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {e}', 'danger')
        return redirect(url_for('configuracion_motor.index'))

    flash('Regla creada correctamente.', 'success')
    return redirect(url_for('configuracion_motor.index', sel=item.id))


@bp.route('/reglas/<int:id>/fragmento')
@login_required
@require_permiso('acceder_reglas_motor')
def regla_fragmento(id):
    """Fragmento HTML de lectura para el inspector."""
    item = ReglaMotor.query.get_or_404(id)
    return render_template(
        'configuracion_motor/_regla_detalle_fragmento.html',
        item=item,
        sujeto_legible=_sujeto_legible(item.sujeto),
        puede_editar=tiene_permiso('gestionar_reglas_motor'),
    )


@bp.route('/reglas/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_reglas_motor')
def regla_editar_fragmento(id):
    """Fragmento de edición para el inspector — incluye cascada de sujeto y condiciones."""
    item = ReglaMotor.query.get_or_404(id)
    nivel, partes = _sujeto_a_partes(item.sujeto)
    valor_display = {c.id: _valor_display(c.valor) for c in item.condiciones}
    return render_template(
        'configuracion_motor/_regla_editar_fragmento.html',
        item=item,
        valor_display=valor_display,
        sujeto_nivel=nivel,
        sujeto_partes=partes,
        **_selects_context(),
    )


@bp.route('/reglas/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def regla_editar(id):
    item = ReglaMotor.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def _responder_errores(errores):
        if is_xhr:
            return jsonify({'ok': False, 'errors': errores})
        for msg in errores:
            flash(msg, 'danger')
        return redirect(url_for('configuracion_motor.index', sel=id))

    errores = _rellenar_regla(item)
    if errores:
        return _responder_errores(errores)

    variables_por_id = {v.id: v for v in CatalogoVariable.query.filter_by(activa=True).all()}
    nuevas_condiciones, errores_cond = _construir_condiciones(CondicionRegla, variables_por_id)
    if errores_cond:
        return _responder_errores(errores_cond)

    item.condiciones = nuevas_condiciones

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al guardar: {e}'])

    msg = 'Regla actualizada correctamente.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg})
    flash(msg, 'success')
    return redirect(url_for('configuracion_motor.index', sel=id))


@bp.route('/reglas/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def regla_activar(id):
    """Alterna activa/inactiva — baja lógica (preserva trazabilidad, sin ruta eliminar)."""
    item = ReglaMotor.query.get_or_404(id)
    is_xhr = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    item.activa = not item.activa
    db.session.commit()
    estado_txt = 'activada' if item.activa else 'desactivada'
    msg = f'Regla {estado_txt}.'
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'activa': item.activa})
    flash(msg, 'success')
    return redirect(url_for('configuracion_motor.index', sel=id))


# ---------------------------------------------------------------------------
# Rutas — excepciones de una regla (#170) — modal grande, ADR-023 §6
# ---------------------------------------------------------------------------

@bp.route('/reglas/<int:regla_id>/excepciones/fragmento')
@login_required
@require_permiso('acceder_reglas_motor')
def excepciones_fragmento(regla_id):
    """Contenido del modal grande: listado de excepciones de la regla."""
    regla = ReglaMotor.query.get_or_404(regla_id)
    return render_template(
        'configuracion_motor/_excepciones_modal.html',
        regla=regla,
        puede_gestionar=tiene_permiso('gestionar_reglas_motor'),
    )


@bp.route('/reglas/<int:regla_id>/excepciones/nueva-fragmento')
@login_required
@require_permiso('gestionar_reglas_motor')
def excepcion_nueva_fragmento(regla_id):
    """Formulario de alta de una excepción — inyectado dentro del modal grande."""
    regla = ReglaMotor.query.get_or_404(regla_id)
    return render_template(
        'configuracion_motor/_excepcion_form_fragmento.html',
        regla=regla, item=None, valor_display={},
        **_selects_context(),
    )


@bp.route('/reglas/<int:regla_id>/excepciones/crear', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def excepcion_crear(regla_id):
    """Alta de una excepción — formulario interceptado por modal-large.js (data-modal-form)."""
    regla = ReglaMotor.query.get_or_404(regla_id)
    item = ExcepcionMotor(regla_id=regla.id, activa=True)

    errores = _rellenar_excepcion(item)
    variables_por_id = {v.id: v for v in CatalogoVariable.query.filter_by(activa=True).all()}
    condiciones, errores_cond = _construir_condiciones(CondicionExcepcion, variables_por_id)
    errores += errores_cond
    if errores:
        return jsonify({'ok': False, 'errors': errores})

    item.condiciones = condiciones
    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'errors': [f'Error al guardar: {e}']})

    return jsonify({'ok': True, 'message': 'Excepción creada correctamente.'})


@bp.route('/reglas/<int:regla_id>/excepciones/<int:id>/editar-fragmento')
@login_required
@require_permiso('gestionar_reglas_motor')
def excepcion_editar_fragmento(regla_id, id):
    """Formulario de edición de una excepción existente (con sus condiciones)."""
    regla = ReglaMotor.query.get_or_404(regla_id)
    item = ExcepcionMotor.query.filter_by(id=id, regla_id=regla_id).first_or_404()
    valor_display = {c.id: _valor_display(c.valor) for c in item.condiciones}
    return render_template(
        'configuracion_motor/_excepcion_form_fragmento.html',
        regla=regla, item=item, valor_display=valor_display,
        **_selects_context(),
    )


@bp.route('/reglas/<int:regla_id>/excepciones/<int:id>/editar', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def excepcion_editar(regla_id, id):
    item = ExcepcionMotor.query.filter_by(id=id, regla_id=regla_id).first_or_404()

    errores = _rellenar_excepcion(item)
    variables_por_id = {v.id: v for v in CatalogoVariable.query.filter_by(activa=True).all()}
    condiciones, errores_cond = _construir_condiciones(CondicionExcepcion, variables_por_id)
    errores += errores_cond
    if errores:
        return jsonify({'ok': False, 'errors': errores})

    item.condiciones = condiciones
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'ok': False, 'errors': [f'Error al guardar: {e}']})

    return jsonify({'ok': True, 'message': 'Excepción actualizada correctamente.'})


@bp.route('/reglas/<int:regla_id>/excepciones/<int:id>/activar', methods=['POST'])
@login_required
@require_permiso('gestionar_reglas_motor')
def excepcion_activar(regla_id, id):
    """Alterna activa/inactiva de una excepción — baja lógica, fetch directo (patrón `entidades`)."""
    item = ExcepcionMotor.query.filter_by(id=id, regla_id=regla_id).first_or_404()
    item.activa = not item.activa
    db.session.commit()
    estado_txt = 'activada' if item.activa else 'desactivada'
    return jsonify({'ok': True, 'message': f'Excepción {estado_txt}.', 'activa': item.activa})
