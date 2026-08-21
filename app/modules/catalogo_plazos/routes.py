"""
Blueprint para administración del catálogo de plazos legales (#632).

Interfaz de configuración para el Supervisor sobre `catalogo_plazos` +
`condiciones_plazo` — mismo patrón ADR-023 (listado + inspector overlay) que
`items_tecnicos` (#594) y `admin_requisitos` (#583). Sin `metadata.json`: entra
como tarjeta del hub del supervisor (ADR-029 §1), no como entrada propia de
sidebar.

Dos cascadas independientes, ambas gobernadas por el nivel ESFTT y ambas
renderizadas por `_campo_fecha_macro.html`:

1. Camino SFTT (#785) — DÓNDE está el plazo en el árbol. Un select por nivel; el
   nivel elegido decide cuántos segmentos se piden (SOLICITUD 2, TAREA 5 — FASE y
   TRAMITE no son niveles seleccionables desde #788, aunque sus ancestros siguen
   pidiéndose como segmentos intermedios de una TAREA). Los ancestros admiten
   `ANY`; la hoja es obligatoria y nunca `ANY`, porque es el tipo del elemento
   evaluado y siempre se conoce. Sustituye al antiguo select único de
   `tipo_elemento_codigo`, que no distinguía dos puntos distintos del árbol con
   el mismo literal.

2. `campo_fecha` (DISEÑO_FECHAS_PLAZOS.md §3.2) — DESDE QUÉ documento se computa.
   Vocabulario cerrado desde #788: SOLICITUD es fija (su único FK a documentos),
   TAREA pide el rol (consumido/producido) y, opcionalmente, el tipo de
   documento que desempata cuando dos tareas del mismo tipo conviven en un
   trámite (las dos esperas de los `ANUNCIO_*`). FASE y TRAMITE ya no portan
   fecha — no hay filas de esos niveles ni forma de crearlas.

El bloque visible lo decide el servidor según el nivel actual (edición) o el
valor por defecto del select (alta); el JS de `catalogo-plazos-cascada.js` solo
reacciona a cambios posteriores del select de nivel — no hay que enganchar
ningún evento de "fragmento cargado".

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
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import require_permiso
from app.models.catalogo_plazos import CatalogoPlazo
from app.models.condiciones_plazo import CondicionPlazo
from app.models.efectos_plazo import EfectoPlazo
from app.models.motor_reglas import CatalogoVariable
from app.models.tipos_documentos import TipoDocumento
from app.models.tipos_expedientes import TipoExpediente
from app.models.tipos_fases import TipoFase
from app.models.tipos_solicitudes import TipoSolicitud
from app.models.tipos_tareas import TipoTarea
from app.models.tipos_tramites import TipoTramite
from app.models.tramites_tareas import TramiteTarea
from app.models.tramites_tareas_documentos import TramiteTareaDocumento
from app.utils.permisos import tiene_permiso

bp = Blueprint(
    'catalogo_plazos',
    __name__,
    url_prefix='/catalogo_plazos',
    template_folder='templates',
)

# Nivel ESFTT → (modelo del catálogo de tipos, atributo que porta el código estable).
# TipoSolicitud usa 'siglas' — el resto usa 'codigo' (mismo mapeo que plazos.py).
# Conserva sus 4 entradas a propósito (igual que plazos.py._TIPO_REL_CAMPO):
# _tipo_elemento_nombre() la usa para nombrar CUALQUIER segmento del camino,
# incluidos los ancestros Fase/Trámite de una TAREA — no es el mapa de niveles
# seleccionables, que es _NIVELES_VALIDOS.
_TIPO_MODELO = {
    'SOLICITUD': (TipoSolicitud, 'siglas'),
    'FASE':      (TipoFase, 'codigo'),
    'TRAMITE':   (TipoTramite, 'codigo'),
    'TAREA':     (TipoTarea, 'codigo'),
}

# Niveles con plazo posible (#788): los únicos dos portadores de fecha
# administrativa. FASE y TRAMITE son taxonomía ESFTT, no figuras jurídicas, y
# el CheckConstraint de catalogo_plazos ya los rechaza — esta validación da el
# error legible antes de llegar ahí.
_NIVELES_VALIDOS = {'SOLICITUD', 'TAREA'}

# Camino SFTT (#785): un segmento por nivel del árbol, de fuera a dentro. La
# longitud del camino codifica el nivel del elemento evaluado, así que el nivel
# elegido decide cuántos segmentos se piden. FASE y TRAMITE conservan su entrada
# aquí aunque ya no sean niveles seleccionables (#788): siguen siendo posiciones
# de ascendencia dentro del camino de 5 segmentos de una TAREA, y esta lista
# valida cada posición contra el catálogo de tipos que le toca.
#   (campo del formulario, nivel de tipo para validar, etiqueta para el error)
_SEGMENTOS_CAMINO = [
    ('camino_expediente', None,        'tipo de expediente'),
    ('camino_solicitud',  'SOLICITUD', 'tipo de solicitud'),
    ('camino_fase',       'FASE',      'tipo de fase'),
    ('camino_tramite',    'TRAMITE',   'tipo de trámite'),
    ('camino_tarea',      'TAREA',     'tipo de tarea'),
]
# Solo los dos niveles con plazo posible (#788): FASE y TRAMITE no portan fecha
# administrativa y quedan fuera del CheckConstraint de catalogo_plazos.
_SEGMENTOS_POR_NIVEL = {'SOLICITUD': 2, 'TAREA': 5}
_UNIDADES_VALIDAS = {'DIAS_HABILES', 'DIAS_NATURALES', 'MESES', 'ANOS'}
_ROLES_VALIDOS = {'CONSUMIDO', 'PRODUCIDO'}

_FK_LABEL = {
    'documento_solicitud_id': 'Fecha administrativa del documento de solicitud',
    'documento_cierre_id': 'Fecha administrativa del certificado de cierre de la solicitud',
}
_ROL_LABEL = {'CONSUMIDO': 'consumido', 'PRODUCIDO': 'producido'}

# Tope del art. 22.1.d: «Este plazo de suspensión no podrá exceder en ningún caso
# de tres meses». Recae sobre la suspensión, no sobre el plazo concedido al
# informante, y en la práctica no muerde: todos los plazos de informe que BDDAT
# maneja son de tres meses o menos. Se vigila AL DAR DE ALTA la entrada, con un
# aviso, y no con lógica de cómputo (ADR-041 §F) — el valor del plazo es el que
# fija la norma, y el cálculo no debe recortarlo por su cuenta.
#
# Equivalencias aproximadas y deliberadamente generosas: el aviso solo tiene que
# saltar cuando el plazo declarado excede claramente los tres meses.
_TOPE_SUSPENSION = {
    'MESES': 3,
    'ANOS': 0,               # cualquier plazo en años excede tres meses
    'DIAS_NATURALES': 90,
    'DIAS_HABILES': 65,      # ~3 meses de calendario laboral
}

# Rol en tramites_tareas_documentos (ENTRADA/SALIDA, #346) → rol de campo_fecha
# (CONSUMIDO/PRODUCIDO, ADR-010). Distinto vocabulario para el mismo concepto:
# el primero es el mapa semántico de catálogo, el segundo el vínculo
# operacional (documentos_tarea) — el formulario y el JS solo conocen el
# segundo.
_ROL_TTD_A_CF = {'ENTRADA': 'CONSUMIDO', 'SALIDA': 'PRODUCIDO'}

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
        'tipos_expediente': [
            t for (t,) in db.session.query(TipoExpediente.tipo)
            .distinct().order_by(TipoExpediente.tipo).all()
        ],
        'tipos_solicitud': TipoSolicitud.query.order_by(TipoSolicitud.siglas).all(),
        'tipos_fase':       TipoFase.query.order_by(TipoFase.codigo).all(),
        'tipos_tramite':    TipoTramite.query.order_by(TipoTramite.codigo).all(),
        'tipos_tarea':      TipoTarea.query.order_by(TipoTarea.codigo).all(),
        'efectos':          EfectoPlazo.query.order_by(EfectoPlazo.nombre).all(),
        'variables':        CatalogoVariable.query.filter_by(activa=True).order_by(CatalogoVariable.etiqueta).all(),
        'operadores':       OPERADORES,
        'tipo_documento_map': _tipo_documento_map(),
    }


def _tipo_documento_map() -> dict:
    """Mapa "tramite|tarea|rol" → tipos de documento candidatos para `tipo_documento` (#788 §2.3).

    Fuente: `tramites_tareas_documentos` (#346), que ya declara qué tipo de
    documento consume/produce cada tarea de cada trámite — no hay que
    mantenerlo aparte. Las filas con `tipo_documento_id` NULL (polimórficas)
    se descartan: no hay código que ofrecer en el desplegable para ellas, y es
    justamente el caso en que `tipo_documento` no hace falta (el justificante
    de CONSULTA_SEPARATA, por ejemplo).

    `rol` se expresa en el vocabulario de `campo_fecha` (CONSUMIDO/PRODUCIDO,
    ADR-010), no en el de `tramites_tareas_documentos` (ENTRADA/SALIDA) — el
    formulario y el JS solo conocen el primero.

    Sirve tanto para pintar las opciones iniciales en Jinja (server-side, mismo
    criterio que el resto de bloques de `_campo_fecha_macro.html`) como,
    serializado a JSON, para que el JS repueble el desplegable al cambiar de
    trámite/tarea/rol en la cascada.
    """
    filas = (
        TramiteTareaDocumento.query
        .filter(TramiteTareaDocumento.tipo_documento_id.isnot(None))
        .options(
            joinedload(TramiteTareaDocumento.tipo_tramite),
            joinedload(TramiteTareaDocumento.tipo_documento),
        )
        .all()
    )
    tareas_por_tramite_orden = {
        (tt.tipo_tramite_id, tt.orden): tt.tipo_tarea
        for tt in TramiteTarea.query.options(joinedload(TramiteTarea.tipo_tarea)).all()
    }

    mapa: dict = {}
    for fila in filas:
        tipo_tarea = tareas_por_tramite_orden.get((fila.tipo_tramite_id, fila.orden_tarea))
        rol_cf = _ROL_TTD_A_CF.get(fila.rol)
        if not tipo_tarea or not rol_cf:
            continue
        clave = f'{fila.tipo_tramite.codigo}|{tipo_tarea.codigo}|{rol_cf}'
        opciones = mapa.setdefault(clave, [])
        if not any(o['codigo'] == fila.tipo_documento.codigo for o in opciones):
            opciones.append({'codigo': fila.tipo_documento.codigo, 'nombre': fila.tipo_documento.nombre})
    return mapa


def _tipo_elemento_nombre(tipo_elemento: str, codigo: str) -> str:
    """Nombre legible del tipo de la hoja del camino."""
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


def _camino_legible(camino: str) -> list[dict]:
    """Descompone el camino en segmentos anotados para la vista de detalle.

    Devuelve [{'nivel': 'Fase', 'valor': 'RESOLUCION', 'nombre': 'Resolución',
               'any': False, 'hoja': True}, …] — 'any' marca los niveles sin
    concretar, 'hoja' el tipo del elemento evaluado.
    """
    partes = (camino or '').split('/')
    etiquetas = ['Expediente', 'Solicitud', 'Fase', 'Trámite', 'Tarea']
    salida = []
    for i, valor in enumerate(partes):
        es_any = valor == 'ANY'
        nivel_tipo = _SEGMENTOS_CAMINO[i][1] if i < len(_SEGMENTOS_CAMINO) else None
        salida.append({
            'nivel': etiquetas[i] if i < len(etiquetas) else f'Nivel {i + 1}',
            'valor': valor,
            'nombre': ('Cualquiera' if es_any
                       else (_tipo_elemento_nombre(nivel_tipo, valor) if nivel_tipo else valor)),
            'any': es_any,
            'hoja': i == len(partes) - 1,
        })
    return salida


def _descripcion_camino(camino: str) -> str:
    """Lectura humana en breadcrumb del camino, para mensajes de colisión (#786).

    Omite los segmentos 'ANY' (sin concretar); la hoja siempre aparece, porque
    nunca es ANY (ver CatalogoPlazo.camino). Mismo orden y mismas etiquetas que
    la cascada de selects del formulario (Expediente › Solicitud › Fase ›
    Trámite › Tarea) — el usuario no conoce el concepto interno "camino", solo
    a qué solicitud/fase/trámite/tarea concreta le ha puesto el plazo.
    """
    return ' › '.join(s['nombre'] for s in _camino_legible(camino) if not s['any'])


def _construir_camino(tipo_elemento: str):
    """Compone el camino SFTT desde los selects del formulario (#785).

    Devuelve (camino, error_msg_o_None). Los ancestros admiten 'ANY'; la hoja
    —el tipo del elemento evaluado— es obligatoria y debe existir en su catálogo:
    un camino con hoja 'ANY' no identificaría nada.
    """
    n = _SEGMENTOS_POR_NIVEL.get(tipo_elemento)
    if n is None:
        return None, 'Nivel ESFTT no reconocido.'

    segmentos = []
    for i in range(n):
        campo, nivel_tipo, etiqueta = _SEGMENTOS_CAMINO[i]
        valor = (request.form.get(campo) or '').strip()
        es_hoja = (i == n - 1)

        if not valor or (valor == 'ANY' and es_hoja):
            if es_hoja:
                return None, f'El {etiqueta} es obligatorio: es el elemento al que se aplica el plazo.'
            valor = 'ANY'

        if valor != 'ANY' and nivel_tipo:
            modelo, attr = _TIPO_MODELO[nivel_tipo]
            if not modelo.query.filter_by(**{attr: valor}).first():
                return None, f'El {etiqueta} «{valor}» no existe en el catálogo.'

        if '/' in valor:
            return None, f'El {etiqueta} no puede contener «/».'

        segmentos.append(valor)

    return '/'.join(segmentos), None


def _campo_fecha_legible(tipo_elemento: str, campo_fecha: dict) -> str:
    """Traduce el JSON de campo_fecha a texto legible.

    Vocabulario cerrado de dos ramas desde #788 (DISEÑO_FECHAS_PLAZOS.md §3.2):
    `fk` para SOLICITUD, `rol` [+ `tipo_documento` opcional] para TAREA. Ya no
    existe `via_tarea_tipo` — era la indirección que bajaba de un trámite a su
    tarea, y con la fila declarada en la tarea sobra.
    """
    campo_fecha = campo_fecha or {}
    fk = campo_fecha.get('fk')
    if fk:
        return _FK_LABEL.get(fk, f'Fecha administrativa vía «{fk}»')

    rol = campo_fecha.get('rol')
    if not rol:
        return 'Sin configurar'
    rol_txt = _ROL_LABEL.get(rol, rol)
    tipo_documento = campo_fecha.get('tipo_documento')
    if tipo_documento:
        tipo_doc = TipoDocumento.query.filter_by(codigo=tipo_documento).first()
        nombre_doc = tipo_doc.nombre if tipo_doc else tipo_documento
        return f'Fecha administrativa del documento {rol_txt} («{nombre_doc}»)'
    return f'Fecha administrativa del documento {rol_txt} por esta tarea'


def _campo_cumplimiento_legible(tipo_elemento: str, campo_cumplimiento: dict) -> str:
    """Traduce el JSON de campo_fecha_cumplimiento a texto legible (#778).

    Mismo vocabulario que `campo_fecha`, así que reutiliza su traductor. Lo que
    cambia es la lectura del vacío: ahí no es «sin configurar» sino una decisión
    —el plazo no alcanza CUMPLIDO y solo puede estar corriendo o vencido—, y la
    interfaz debe decirlo con esas palabras.
    """
    if not campo_cumplimiento:
        return 'Sin documento de cierre — el plazo solo puede estar en curso o vencido'
    return _campo_fecha_legible(tipo_elemento, campo_cumplimiento)


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

    Vocabulario cerrado de dos ramas desde #788: no hay un tercer portador de
    fecha al que apuntar, así que no es extensible. `_NIVELES_VALIDOS` ya
    descarta FASE y TRAMITE antes de llegar aquí — sin rama para ellos.

    Devuelve (campo_fecha_dict, error_msg_o_None).
    """
    if tipo_elemento == 'SOLICITUD':
        # Único FK a documentos en Solicitud — sin selección posible (§3.2).
        return {'fk': 'documento_solicitud_id'}, None

    if tipo_elemento == 'TAREA':
        rol = (request.form.get('campo_fecha_rol') or '').strip().upper()
        if rol not in _ROLES_VALIDOS:
            return None, 'El documento de referencia (consumido/producido) es obligatorio.'
        campo_fecha = {'rol': rol}

        # tipo_documento (§2.3): opcional, desempata cuando dos tareas del
        # mismo tipo conviven en un trámite (las dos esperas de un ANUNCIO_*).
        tipo_documento = (request.form.get('campo_fecha_tipo_documento') or '').strip()
        if tipo_documento:
            if not TipoDocumento.query.filter_by(codigo=tipo_documento).first():
                return None, f'El tipo de documento «{tipo_documento}» no existe en el catálogo.'
            campo_fecha['tipo_documento'] = tipo_documento

        return campo_fecha, None

    return None, 'Nivel ESFTT no reconocido.'


def _construir_campo_cumplimiento(tipo_elemento: str):
    """Traduce la selección del formulario al JSON de campo_fecha_cumplimiento (#778).

    Mismo vocabulario cerrado que `campo_fecha` —el problema es el mismo,
    localizar un documento desde el elemento— con dos diferencias:

    - En SOLICITUD el ancla es `documento_cierre_id`, no `documento_solicitud_id`:
      uno marca el inicio del plazo para resolver y notificar, el otro el fin.
      Fijo, sin selección posible, igual que su gemelo.
    - En TAREA el rol puede quedar vacío, y eso no es un formulario a medio
      rellenar: una entrada sin señalador de cumplimiento nunca alcanza CUMPLIDO,
      que es justo lo que hace falta en TABLON_AYUNTAMIENTOS (#416), donde el
      disparo y el único candidato a cierre son el mismo documento.

    Devuelve (campo_cumplimiento_dict_o_None, error_msg_o_None).
    """
    if tipo_elemento == 'SOLICITUD':
        return {'fk': 'documento_cierre_id'}, None

    if tipo_elemento == 'TAREA':
        rol = (request.form.get('campo_cumplimiento_rol') or '').strip().upper()
        if not rol:
            return None, None
        if rol not in _ROLES_VALIDOS:
            return None, 'El documento de cumplimiento debe ser consumido o producido.'
        campo = {'rol': rol}

        tipo_documento = (request.form.get('campo_cumplimiento_tipo_documento') or '').strip()
        if tipo_documento:
            if not TipoDocumento.query.filter_by(codigo=tipo_documento).first():
                return None, f'El tipo de documento «{tipo_documento}» no existe en el catálogo.'
            campo['tipo_documento'] = tipo_documento

        return campo, None

    return None, 'Nivel ESFTT no reconocido.'


def _aviso_tope_suspension(item) -> str | None:
    """Avisa si una entrada suspensora declara un plazo de más de tres meses.

    Art. 22.1.d: «Este plazo de suspensión no podrá exceder en ningún caso de tres
    meses». El límite recae sobre la suspensión, no sobre el plazo concedido al
    informante, así que no se recorta el valor del catálogo ni se mete lógica en
    el cómputo (ADR-041 §F): se avisa aquí, donde alguien puede decidir.

    No bloquea: puede haber un plazo sectorial mayor que el tramitador quiera
    registrar tal como lo fija su norma.
    """
    if not item.suspende_plazo_solicitud:
        return None
    tope = _TOPE_SUSPENSION.get(item.plazo_unidad)
    if tope is None or (item.plazo_valor or 0) <= tope:
        return None
    return (
        'Este plazo suspende el de la solicitud y dura más de tres meses. El '
        'art. 22.1.d LPACAP fija que la suspensión «no podrá exceder en ningún '
        'caso de tres meses»: revisa el valor o el efecto que le has dado.'
    )


def _rellenar_catalogo_plazo(item) -> list[str]:
    """Rellena los campos escalares de un CatalogoPlazo desde request.form.

    Devuelve la lista de errores de validación (vacía si todo OK). No incluye
    las condiciones anidadas — ver _construir_condiciones.
    """
    errores = []

    tipo_elemento = (request.form.get('tipo_elemento') or '').strip().upper()
    if tipo_elemento not in _NIVELES_VALIDOS:
        return ['El nivel ESFTT es obligatorio.']  # sin nivel no se puede validar el resto

    camino, err_camino = _construir_camino(tipo_elemento)
    if err_camino:
        errores.append(err_camino)

    campo_fecha, err_cf = _construir_campo_fecha(tipo_elemento)
    if err_cf:
        errores.append(err_cf)

    campo_cumplimiento, err_cc = _construir_campo_cumplimiento(tipo_elemento)
    if err_cc:
        errores.append(err_cc)

    # Solo las tareas suspenden: lo que el art. 22 suspende es el plazo de la
    # solicitud, y marcarla a ella significaría que se suspende a sí misma. El
    # CheckConstraint lo cubre en BD; aquí se ignora la casilla sin error, porque
    # el formulario no la ofrece en ese nivel.
    suspende = (
        tipo_elemento == 'TAREA'
        and bool(request.form.get('suspende_plazo_solicitud'))
    )

    # Entero positivo: 0 se rechaza a propósito (#789). "Plazo indefinido" (EP(0)
    # en ESTRUCTURA_FTT.md) no se registra como fila de catalogo_plazos — la
    # ausencia de fila ya produce el SIN_PLAZO/rojo persistente que se quiere ahí.
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
    item.camino = camino
    item.campo_fecha = campo_fecha
    item.campo_fecha_cumplimiento = campo_cumplimiento
    item.suspende_plazo_solicitud = suspende
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


def _validar_colision_camino(item, camino: str, tiene_condiciones: bool):
    """Detecta colisiones activas de `camino` con otras filas de catalogo_plazos (#786).

    Con identificación por camino (#785), dos filas solo son ambiguas si comparten
    el mismo `camino`: si además ninguna tiene condiciones, la de mayor `orden`/`id`
    queda siempre inerte (duplicado ciego) — se bloquea. Si alguna de las filas en
    colisión tiene condiciones, puede ser el patrón legítimo condición+reserva
    (`CONSULTA_SEPARATA`, `CONSULTAS`) o un solape legal real no discriminable en
    general (operadores arbitrarios) — se avisa, no se bloquea, y decide el Supervisor.

    Los mensajes citan `_descripcion_camino`, no el `camino` en crudo: al usuario le
    consta que ha puesto un plazo a una solicitud/fase/trámite/tarea concreta, no que
    existe un "camino" — concepto interno del catálogo.

    Devuelve (error_o_None, aviso_o_None).
    """
    from app.models.catalogo_plazos import CatalogoPlazo

    query = CatalogoPlazo.query.filter_by(camino=camino, activo=True)
    if item.id is not None:
        query = query.filter(CatalogoPlazo.id != item.id)
    colisiones = query.all()
    if not colisiones:
        return None, None

    descripcion = _descripcion_camino(camino)

    sin_condicion = [c for c in colisiones if not c.condiciones]
    if not tiene_condiciones and sin_condicion:
        return (
            f'Este plazo, aplicado a «{descripcion}», ya tiene una entrada activa '
            f'(#{sin_condicion[0].id}) sin condición que la distinga: dos filas sin '
            'condiciones para el mismo elemento son indistinguibles, y una de ellas '
            'queda siempre inerte.'
        ), None

    ids = ', '.join(f'#{c.id}' for c in colisiones)
    return None, (
        f'Este plazo, aplicado a «{descripcion}», ya tiene entrada(s) activa(s) con '
        f'la(s) que puede colisionar ({ids}). Revisa que las condiciones sean '
        'mutuamente excluyentes o que exista una entrada de reserva sin condiciones '
        'con orden más alto.'
    )


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


def _reabrir_modal_con_errores(errores):
    """Reabre el modal de alta con los errores visibles dentro (#786).

    Antes solo quedaban en el toast, que desaparece a los 8s (#44) — el
    Supervisor podía perderlo si el modal tapaba el toast o si tardaba en
    leerlo. Se sigue lanzando el flash (alimenta también la campana de avisos,
    por si el toast se pierde) y además se pasan a la plantilla para pintarlos
    dentro del `modal-body`, junto al resto de campos.
    """
    for msg in errores:
        flash(msg, 'danger')
    return render_template(
        'catalogo_plazos/listado.html',
        show_modal=True, form_data=request.form, errores=errores,
        **_selects_context(),
    )


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
        return _reabrir_modal_con_errores(errores)

    # Alta no admite condiciones propias (se añaden después, editando desde el
    # inspector — ver docstring de la ruta), así que la fila nueva siempre entra
    # sin condiciones (#786).
    error_colision, aviso_colision = _validar_colision_camino(item, item.camino, tiene_condiciones=False)
    if error_colision:
        return _reabrir_modal_con_errores([error_colision])

    db.session.add(item)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _reabrir_modal_con_errores([f'Error al guardar: {e}'])

    flash('Plazo creado correctamente.', 'success')
    for aviso in (aviso_colision, _aviso_tope_suspension(item)):
        if aviso:
            flash(aviso, 'warning')
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
        tipo_elemento_nombre=_tipo_elemento_nombre(item.tipo_elemento, item.hoja),
        camino_legible=_camino_legible(item.camino),
        campo_fecha_legible=_campo_fecha_legible(item.tipo_elemento, item.campo_fecha),
        campo_cumplimiento_legible=_campo_cumplimiento_legible(
            item.tipo_elemento, item.campo_fecha_cumplimiento),
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
    cc = item.campo_fecha_cumplimiento or {}
    # Ancestros trámite/tarea del camino (posiciones 4 y 5): el desplegable de
    # tipo_documento los necesita para pintar sus opciones iniciales server-side
    # (§2.3) — mismo criterio que el resto de bloques de la macro.
    segmentos = (item.camino or '').split('/')
    cf_tramite = segmentos[3] if len(segmentos) > 3 else ''
    cf_tarea = segmentos[4] if len(segmentos) > 4 else ''
    return render_template(
        'catalogo_plazos/_editar_fragmento.html',
        item=item,
        valor_display=valor_display,
        cf_fk=cf.get('fk', ''),
        cf_rol=cf.get('rol', ''),
        cf_tipo_documento=cf.get('tipo_documento', ''),
        cc_rol=cc.get('rol', ''),
        cc_tipo_documento=cc.get('tipo_documento', ''),
        cf_tramite=cf_tramite,
        cf_tarea=cf_tarea,
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

    error_colision, aviso_colision = _validar_colision_camino(
        item, item.camino, tiene_condiciones=bool(nuevas_condiciones)
    )
    if error_colision:
        return _responder_errores([error_colision])

    item.condiciones = nuevas_condiciones

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return _responder_errores([f'Error al guardar: {e}'])

    msg = 'Plazo actualizado correctamente.'
    avisos = [a for a in (aviso_colision, _aviso_tope_suspension(item)) if a]
    if is_xhr:
        return jsonify({'ok': True, 'message': msg, 'warnings': avisos})
    flash(msg, 'success')
    for aviso in avisos:
        flash(aviso, 'warning')
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
