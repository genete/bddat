"""Expediente de prueba reproducible (#903): REFORMADO_ANALISIS_Y_CONSULTAS.

Propósito: primer expediente-tipo que ejercita `reformados_proyecto` (ADR-044) por el
circuito real. Verifica dos cosas de la ADR:

    §F — «se prohíbe crear una fase que cubra una versión ya cubierta por otra fase
         del mismo tipo»: sin reformado, una segunda ANALISIS_SOLICITUD o una segunda
         CONSULTAS del mismo expediente se bloquearían. Con el reformado declarado,
         ambas se permiten — misma regla de motor, sujeto genérico, no una por fase.
    §I — «ninguna fase se salda por la existencia de una posterior»: el organismo
         que nunca contesta en la CONSULTAS de la versión inicial ("el organismo
         enquistado", ejemplo textual de §I) se queda pendiente para siempre, aunque
         la CONSULTAS del reformado —posterior— se cierre limpia.

Por qué CONSULTAS y no un defecto de checklist documental para el hueco: `evaluar_
requisitos` (app/services/requisitos.py) resuelve la cobertura de un requisito con
`ultimo_reformado(expediente_id)` evaluado EN EL MOMENTO de la llamada, con fallback a
`reformado_id IS NULL` — no "como estaba cuando se analizó esa fase". Dejar un requisito
documental sin cubrir en la v1 lo dejaría igual de sin cubrir en la v2 (mismo fallback a
NULL), y la ANALISIS_SOLICITUD del reformado dejaría de estar "limpia". Solo
JUSTIFICANTE_PAGO_TASA está marcado `afectado_por_reformado=True` en catálogo hoy, y
tocar ese flag en un requisito real para forzar el escenario mutaría catálogo compartido
por todo el sistema — descartado. `OrganismoExpediente`, en cambio, es `fase_id`-scoped
(`UniqueConstraint('fase_id','organismo_id')`): cada ronda de consultas es una fila
aparte, sin fallback ni ambigüedad entre versiones.

Escenario: línea aérea de 66 kV entre las subestaciones de Guadalcacín y Nueva Jarilla,
en suelo rústico de Jerez de la Frontera (AAP+AAC, un solo municipio), EXENTA de
instrumento ambiental por longitud, tensión y suelos que recorre — mismo perfil
administrativo que CONSULTAS_VARIOS_ESTADOS (#862), para no arrastrar huecos de
catálogo nuevos: el objetivo de este expediente-tipo es la mecánica de reformados, no
la variedad administrativa. El titular presenta la declaración responsable de no
necesidad de DUP.

    v1 (reformado_id NULL):
        ANALISIS_SOLICITUD — checklist sin defectos, diagnóstico favorable, se
        comunica el inicio. No se cierra formalmente (mismo patrón que los dos
        expedientes-tipo ya existentes: PDTE_CIERRE).
        CONSULTAS — el trazado inicial solo afecta al término municipal de Jerez:
        se consulta al Ayuntamiento. Nunca contesta — silencio, plazo vencido, sin
        ANALIZAR. Es el hueco vivo: nada en este escenario lo resuelve.

    El titular presenta un reformado voluntario que reencauza el tramo final para
    evitar una zona de servidumbres de vuelo, y el nuevo trazado cruza la línea de
    ferrocarril Jerez—Cádiz.

    v2 (reformado, `reformado_id` = id del corte):
        ANALISIS_SOLICITUD — segunda fase del mismo tipo, permitida por §F.
        Checklist limpio: todo lo aplicable ya está cubierto por el fallback de R4
        (#899) a la versión inicial (ningún requisito documental de este escenario
        está marcado `afectado_por_reformado`), así que no hace falta aportar nada
        nuevo — diagnóstico favorable directo.
        CONSULTAS — segunda fase del mismo tipo, permitida por §F. Se consulta de
        nuevo al Ayuntamiento (el trazado dentro de su término cambió) — mismo
        organismo, ronda distinta, `UNIQUE(fase_id, organismo_id)` sin conflicto — y
        a ADIF, nuevo por el cruce ferroviario que el reformado introduce. Ambos
        contestan favorable dentro de plazo, se trasladan al titular, y cierran
        `cerrado_favorable`.

Circuito real — nunca INSERT SQL directo (ver README.md de esta carpeta):
    - Alta expediente/proyecto/solicitud: `app.services.alta_expediente`.
    - El corte de versión: `declarar_desde_metadatos` (`app.services.reformados`),
      disparado por la subida multipart real con `es_principal`/`abre_reformado`/
      `origen_reformado` en los metadatos (`_comun.subir`, extendido en #903).
    - Fase/trámite/tarea y organismos: `app.services.mutaciones_arbol` (pasa por el
      motor de reglas real). `crear_fase` engancha `reformado_id` solo, del último
      reformado del expediente en ese momento — no es parámetro.
    - Separatas y traslados: `app.services.consultas_organismos` — `enviar_consultas`
      y `crear_traslado`, las mismas entradas que usa la UI (ADR-042 §C/§D).
    - Checklist y diagnósticos: endpoints del contenedor de ANALIZAR (ADR-033).
    - Alta de organismos y direcciones de notificación: rutas reales de `/entidades`,
      idempotente por NIF — igual que en CONSULTAS_VARIOS_ESTADOS, cuyos organismos
      reutiliza este script (catálogo de la aplicación, no datos del expediente).

Calendario: ninguna fecha absoluta. Todo cuelga hacia delante de `date.today() menos
DIAS_ESCENARIO` — lo bastante holgado para que cada plazo derivado en el camino siga
siendo anterior a hoy (`_comun.fecha_respuesta_en_plazo` aborta si no). Al terminar, el
reloj de desarrollo se borra: el organismo enquistado de la v1 sigue vencido se mire
desde la fecha que se mire, y las fechas cerradas de la v2 no dependen de qué diga hoy
el reloj simulado.

Reejecutable sin implementar borrado aquí: si ya existe un expediente marcado con este
código, sus observaciones pasan a '[RECICLAR] ...' y se crea uno nuevo desde cero. El
borrado real es `limpiar_reciclables.py`.

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/reformado_analisis_y_consultas.py
"""
import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

CODIGO = 'REFORMADO_ANALISIS_Y_CONSULTAS'
PROPOSITO = (
    'Expediente para testear ADR-044: dos versiones de proyecto, con ANALISIS_SOLICITUD '
    'y CONSULTAS cortadas por el mismo reformado. La CONSULTAS de la versión inicial '
    'deja un organismo enquistado (hueco vivo, §I); la del reformado repite ese '
    'organismo y añade uno nuevo, ambos limpios (§F).'
)
MARCA = f'[DUMMY:{CODIGO}]'
OBSERVACIONES = f'{MARCA} {PROPOSITO}'

# Días naturales que dura el escenario completo: la CONSULTAS de la v1 necesita quedar
# vencida (30 días hábiles, art. 131.1) con margen antes de declarar el reformado, y
# después hace falta espacio para una ANALISIS_SOLICITUD y una CONSULTAS completas de
# la v2 (dos organismos, separata + traslado + respuesta del titular cada uno). Holgado
# a propósito — sobrar días solo aleja el alta en el calendario.
DIAS_ESCENARIO = 200

# Días hábiles desde que se notifica la separata de la v1 hasta que se da por vencida
# (>30 días hábiles del art. 131.1, con margen) y se declara el reformado.
HABILES_HASTA_VENCIMIENTO_V1 = 40

# Días hábiles ANTES del vencimiento real en que responde cada organismo de la v2, y
# desde la respuesta hasta el traslado / desde el traslado hasta que el titular
# contesta. Es lo único que elige el escenario — las fechas salen del plazo real que
# calcula `_comun.fecha_respuesta_en_plazo`, nunca de un número escrito a mano.
MARGEN_RESPUESTA_ORGANISMO_HABILES = 15
HABILES_HASTA_TRASLADO = 2
MARGEN_RESPUESTA_TITULAR_HABILES = 5

# Organismos. El Ayuntamiento se reutiliza en las dos rondas de CONSULTAS; ADIF entra
# solo en la del reformado. Mismas entidades que CONSULTAS_VARIOS_ESTADOS (#862) —
# catálogo de la aplicación, no datos del expediente: alta idempotente por NIF.
ORGANISMO_AYUNTAMIENTO = {
    'clave': 'ayuntamiento',
    'nombre_completo': 'Ayuntamiento de Jerez de la Frontera',
    'nif': 'P1102000J',
    'abrev': 'Ayto. Jerez',
    'email': 'registro@jerez.example',
    'direccion': 'Plaza del Arenal, s/n',
    'codigo_postal': '11403',
    'motivo': 'Ayuntamiento del término municipal afectado',
}
ORGANISMO_ADIF = {
    'clave': 'adif',
    'nombre_completo': 'ADIF - Administrador de Infraestructuras Ferroviarias',
    'nif': 'Q2801660H',
    'abrev': 'ADIF',
    'email': 'consultas@adif.example',
    'direccion': 'C/ Sor Ángela de la Cruz, 3',
    'codigo_postal': '28020',
    'motivo': 'Titular de la línea de ferrocarril que el reformado pasa a cruzar',
}

from app import create_app, db  # noqa: E402
from scripts.expedientes_dummy import _comun  # noqa: E402


# ---------------------------------------------------------------------------
# Catálogo — resuelto por clave natural, nunca PK hardcodeado
# ---------------------------------------------------------------------------

def _cargar_catalogo():
    from app.models.tipos_expedientes import TipoExpediente
    from app.models.tipos_solicitudes import TipoSolicitud
    from app.models.tipos_ia import TipoIA
    from app.models.municipios import Municipio

    _fase, _tramite = _comun.tipo_fase, _comun.tipo_tramite
    _tarea, _doc = _comun.tipo_tarea, _comun.tipo_documento
    entidad, usuario = _comun.titular_y_tramitador()

    cat = {
        'tipo_expediente': TipoExpediente.query.filter_by(tipo='Distribución').first(),
        'tipo_solicitud': TipoSolicitud.query.filter_by(siglas='AAP+AAC').first(),
        'ia_exento': TipoIA.query.filter_by(siglas='EXENTO').first(),
        'entidad': entidad,
        'usuario': usuario,
        'municipio': Municipio.query.filter_by(
            nombre='Jerez de la Frontera', provincia='Cádiz').first(),

        'fase_analisis_solicitud': _fase('ANALISIS_SOLICITUD'),
        'fase_consultas': _fase('CONSULTAS'),

        'tramite_analisis_documental': _tramite('ANALISIS_DOCUMENTAL'),
        'tramite_comunicacion_admision': _tramite('COMUNICACION_INICIO_ADMISION'),
        'tramite_separata': _tramite('CONSULTA_SEPARATA'),
        'tramite_traslado_titular': _tramite('CONSULTA_TRASLADO_TITULAR'),

        'tarea_analizar': _tarea('ANALIZAR'),
        'tarea_elaborar': _tarea('ELABORAR'),
        'tarea_notificar': _tarea('NOTIFICAR'),
        'tarea_esperar_plazo': _tarea('ESPERAR_PLAZO'),

        'doc_proyecto': _doc('DOC_PROYECTO'),
        'doc_justificante_pago_tasa': _doc('JUSTIFICANTE_PAGO_TASA'),
        'doc_dr_no_dup': _doc('DR_NO_DUP'),
        'doc_oficio_inicio_admision': _doc('OFICIO_INICIO_ADMISION'),
        'doc_justificante_notifica': _doc('JUSTIFICANTE_NOTIFICA'),
        'doc_justificante_sir': _doc('JUSTIFICANTE_SIR'),

        'doc_separata': _doc('DOC_SEPARATA'),
        'doc_oficio_separata': _doc('OFICIO_SEPARATA'),
        'doc_respuesta_organismo': _doc('RESPUESTA_ORGANISMO'),
        'doc_oficio_traslado_respuesta': _doc('OFICIO_TRASLADO_RESPUESTA'),
        'doc_respuesta_titular': _doc('RESPUESTA_TITULAR'),
    }
    _comun.abortar_si_catalogo_incompleto(cat)
    return cat


# ---------------------------------------------------------------------------
# Organismos: catálogo de entidades, no datos del expediente
# ---------------------------------------------------------------------------

def _asegurar_organismo(client, org):
    """Da de alta la entidad si falta, con su dirección de notificación, por las
    rutas reales de `/entidades`. Idempotente por NIF. Devuelve (Entidad, direccion_id).
    """
    from app.models.entidad import Entidad
    from app.models.direccion_notificacion import DireccionNotificacion

    entidad = Entidad.query.filter_by(nif=org['nif']).first()
    if entidad is None:
        client.post('/entidades/nueva', data={
            'nombre_completo': org['nombre_completo'],
            'nif': org['nif'],
            'rol_consultado': 'on',
            'email': org['email'],
            'activo': 'on',
            'notas': f"Organismo del expediente-tipo {CODIGO} — {org['motivo']}.",
        }, follow_redirects=True)
        entidad = Entidad.query.filter_by(nif=org['nif']).first()
        if entidad is None:
            print(f"ABORTADO: no se pudo dar de alta {org['nombre_completo']}")
            sys.exit(1)
        print(f"  entidad creada: {entidad.nombre_completo} ({entidad.nif}).")
    elif not entidad.rol_consultado:
        print(f"ABORTADO: la entidad {entidad.nombre_completo} existe sin "
              f"rol_consultado; revisarla en /entidades antes de reintentar.")
        sys.exit(1)

    direccion = (DireccionNotificacion.query
                 .filter_by(entidad_id=entidad.id, activo=True)
                 .order_by(DireccionNotificacion.id).first())
    if direccion is None:
        client.post(f'/entidades/{entidad.id}/direcciones/nueva', data={
            'descripcion': 'Registro general',
            'rol_consultado': 'on',
            'email': org['email'],
            'direccion': org['direccion'],
            'codigo_postal': org['codigo_postal'],
        }, follow_redirects=True)
        direccion = (DireccionNotificacion.query
                     .filter_by(entidad_id=entidad.id, activo=True)
                     .order_by(DireccionNotificacion.id).first())
        if direccion is None:
            print(f"ABORTADO: no se pudo crear la dirección de notificación de "
                  f"{entidad.nombre_completo}")
            sys.exit(1)

    return entidad, direccion.id


# ---------------------------------------------------------------------------
# Alta expediente/proyecto/solicitud — por el servicio real (#428)
# ---------------------------------------------------------------------------

def _crear_expediente(cat, fecha_base):
    from app.services.alta_expediente import (
        DatosAlta, DocumentoSolicitud, alta_expediente,
    )

    with open(os.path.join(_comun.FIXTURES_DIR, 'modelo_solicitud.pdf'), 'rb') as f:
        contenido = f.read()

    resultado = alta_expediente(DatosAlta(
        tipo_expediente_id=cat['tipo_expediente'].id,
        responsable_id=cat['usuario'].id,
        heredado=False,
        titulo='Línea aérea 66 kV SE Guadalcacín — SE Nueva Jarilla',
        descripcion=(
            'Nueva línea aérea de alta tensión 66 kV entre las subestaciones de '
            'Guadalcacín y Nueva Jarilla, en suelo rústico del término municipal '
            'de Jerez de la Frontera.'
        ),
        finalidad='Evacuación y distribución de energía eléctrica en alta tensión',
        emplazamiento='T.M. de Jerez de la Frontera (Cádiz)',
        fecha_proyecto=fecha_base,
        ia_id=cat['ia_exento'].id,
        municipios_ids=[cat['municipio'].id],
        titular_id=cat['entidad'].id,
        tipo_solicitud_id=cat['tipo_solicitud'].id,
        solicitante_id=cat['entidad'].id,
        observaciones=OBSERVACIONES,
        proyecto_extra={
            'es_modificacion': False,
            'sin_linea_aerea': False,
            'max_tension_nominal_kv': 66,
            'solo_suelo_urbano_urbanizable': False,
        },
        documento=DocumentoSolicitud(
            contenido=contenido,
            nombre_original='modelo_solicitud.pdf',
            fecha_registro=fecha_base,
        ),
    ))

    print(f"Expediente AT-{resultado.numero_at} creado "
          f"(id={resultado.expediente.id}, solicitud={resultado.solicitud.id}, "
          f"escrito de solicitud={resultado.documento.id}).")
    return resultado


def _editar_conservando_consumidos(tarea, nuevos_ids, producido_id, etiqueta):
    """`editar_tarea` tratando CONSUMIDO como conjunto completo (no aditivo): repite
    los que ya traía la tarea (hooks automáticos al crearla) o se liberan y con ellos
    el disparo del plazo (hallazgo de #825, ver `_comun.py` de este mismo directorio).
    """
    from app.services import mutaciones_arbol as svc

    previos = [d.id for d in tarea.documentos_consumidos]
    ids = list(dict.fromkeys(previos + list(nuevos_ids)))
    return _comun.check(
        svc.editar_tarea(tarea, documentos_consumidos_ids=ids,
                         documento_producido_id=producido_id, notas=None),
        etiqueta)


def main(app=None, *, efectos_desarrollo=True):
    """Construye el expediente-tipo sobre la app que se le pase.

    `efectos_desarrollo=False` es como lo invoca la semilla de la base de tests
    (#849): deja fuera lo que solo tiene sentido en la máquina de desarrollo — mover
    el reloj simulado. El escenario que se construye es el mismo.
    """
    from flask_login import login_user
    from app.services import mutaciones_arbol as svc
    from app.services import consultas_organismos as svc_consultas
    from app.services import reloj_simulado
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.organismos_expediente import OrganismoExpediente
    from app.models.tramites_organismos import TramiteOrganismo

    if app is None:
        app = create_app()

    def _fijar_reloj(fecha):
        if efectos_desarrollo:
            reloj_simulado.fijar(fecha)

    with app.test_request_context():
        cat = _cargar_catalogo()
        _comun.reciclar_si_existe(MARCA)

        login_user(cat['usuario'])
        client = _comun.abrir_cliente(app, cat['usuario'])

        fecha_base = date.today() - timedelta(days=DIAS_ESCENARIO)
        print(f"Ancla: alta el {fecha_base} ({DIAS_ESCENARIO} días naturales antes de hoy).")
        _fijar_reloj(fecha_base)

        alta = _crear_expediente(cat, fecha_base)
        expediente, solicitud = alta.expediente, alta.solicitud
        exp_id = expediente.id

        # =====================================================================
        # v1 — proyecto original
        # =====================================================================
        docs = {'MODELO_SOLICITUD': alta.documento.id}
        docs['DOC_PROYECTO'] = _comun.subir(
            client, exp_id, 'DOC_PROYECTO', cat['doc_proyecto'].id, fecha_base,
            'Proyecto técnico de la línea aérea 66 kV', es_principal=True)
        docs['JUSTIFICANTE_PAGO_TASA'] = _comun.subir(
            client, exp_id, 'JUSTIFICANTE_PAGO_TASA',
            cat['doc_justificante_pago_tasa'].id, fecha_base,
            'Justificante de pago de la tasa')
        _comun.cubrir_requisito_tasa(solicitud, docs['JUSTIFICANTE_PAGO_TASA'])
        docs['DR_NO_DUP'] = _comun.subir(
            client, exp_id, 'DR_NO_DUP', cat['doc_dr_no_dup'].id, fecha_base,
            'Declaración responsable de no necesidad de DUP')

        # --- ANALISIS_SOLICITUD v1, sin defectos -----------------------------
        fase1_id = _comun.check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                                'crear_fase ANALISIS_SOLICITUD v1')
        fase1_analisis = Fase.query.get(fase1_id)

        tramite_ad1_id = _comun.check(
            svc.crear_tramite(fase1_analisis, cat['tramite_analisis_documental']),
            'crear_tramite ANALISIS_DOCUMENTAL v1')
        tramite_ad1 = Tramite.query.get(tramite_ad1_id)

        tarea_analizar1_id = _comun.check(
            svc.crear_tarea(tramite_ad1, cat['tarea_analizar']), 'crear_tarea ANALIZAR v1')

        aportados = []
        for codigo in _comun.requisitos_aplicables(solicitud, fase1_analisis):
            if codigo not in docs:
                tipo_doc = _comun.tipo_documento(codigo)
                fichero = os.path.join(_comun.FIXTURES_DIR, f'{codigo.lower()}.pdf')
                if tipo_doc is None or not os.path.isfile(fichero):
                    print(f"ABORTADO: el requisito {codigo} aplica a esta solicitud y "
                          f"no hay documento dummy para cubrirlo "
                          f"({os.path.basename(fichero)}).")
                    sys.exit(1)
                docs[codigo] = _comun.subir(client, exp_id, codigo, tipo_doc.id,
                                            fecha_base, f'{tipo_doc.nombre} (presentación)')
            aportados.append((codigo, docs[codigo]))

        _comun.casar_requisitos(client, exp_id, tarea_analizar1_id, aportados, 'presentación v1')
        doc_diagnostico1_id = _comun.producir_diagnostico(
            client, exp_id, tarea_analizar1_id, 'ANALISIS_DOCUMENTAL v1')

        # --- COMUNICACION_INICIO_ADMISION ------------------------------------
        fecha_admision = _comun.avanzar_habiles(fecha_base, 3)
        _fijar_reloj(fecha_admision)

        tramite_com_id = _comun.check(
            svc.crear_tramite(fase1_analisis, cat['tramite_comunicacion_admision']),
            'crear_tramite COMUNICACION_INICIO_ADMISION')
        tramite_com = Tramite.query.get(tramite_com_id)

        tarea_com_elab_id = _comun.check(
            svc.crear_tarea(tramite_com, cat['tarea_elaborar']), 'crear_tarea ELABORAR admision')
        doc_admision_id = _comun.subir(
            client, exp_id, 'OFICIO_INICIO_ADMISION', cat['doc_oficio_inicio_admision'].id,
            fecha_admision, 'Comunicación de inicio y admisión a trámite')
        _editar_conservando_consumidos(
            Tarea.query.get(tarea_com_elab_id), [doc_diagnostico1_id], doc_admision_id,
            'vincular producido ELABORAR admision')

        tarea_com_notif_id = _comun.check(
            svc.crear_tarea(tramite_com, cat['tarea_notificar']), 'crear_tarea NOTIFICAR admision')
        doc_justif_admision_id = _comun.subir(
            client, exp_id, 'JUSTIFICANTE_NOTIFICA', cat['doc_justificante_notifica'].id,
            fecha_admision, 'Justificante de notificación de la comunicación de inicio')
        _comun.notificar(Tarea.query.get(tarea_com_notif_id), doc_admision_id,
                         doc_justif_admision_id, fecha_admision, 'admision')
        print("COMUNICACION_INICIO_ADMISION: elaborada y notificada.")

        # --- CONSULTAS v1: el Ayuntamiento, enquistado -----------------------
        fecha_alta_organismo = _comun.avanzar_habiles(fecha_admision, 1)
        _fijar_reloj(fecha_alta_organismo)

        fase1_consultas_id = _comun.check(
            svc.crear_fase(solicitud, cat['fase_consultas']), 'crear_fase CONSULTAS v1')
        fase1_consultas = Fase.query.get(fase1_consultas_id)

        entidad_ayto, dir_ayto_id = _asegurar_organismo(client, ORGANISMO_AYUNTAMIENTO)
        oe_ayto_v1_id = _comun.check(
            svc.crear_organismo(fase1_consultas, entidad_ayto, via='consulta'),
            'crear_organismo Ayto. Jerez v1')
        oe_ayto_v1 = OrganismoExpediente.query.get(oe_ayto_v1_id)
        _comun.check(
            svc.editar_organismo(oe_ayto_v1, via='consulta', resultado=None,
                                 direccion_notificacion_id=dir_ayto_id, documento_id=None),
            'editar_organismo Ayto. Jerez v1 (dirección)')

        res_envio1 = svc_consultas.enviar_consultas(fase1_consultas, {})
        if not res_envio1.ok:
            motivo = res_envio1.bloqueo.motivo if res_envio1.bloqueo else res_envio1.error
            print(f"ABORTADO en enviar_consultas v1: {motivo}")
            sys.exit(1)
        tramite_sep_ayto_v1 = Tramite.query.get(res_envio1.ids[0])

        tarea_elab_v1 = Tarea.query.get(_comun.check(
            svc.crear_tarea(tramite_sep_ayto_v1, cat['tarea_elaborar']),
            'crear_tarea ELABORAR separata Ayto. v1'))
        doc_separata_v1_id = _comun.subir(
            client, exp_id, 'DOC_SEPARATA', cat['doc_separata'].id, fecha_alta_organismo,
            'Separata del proyecto para el Ayuntamiento de Jerez (v1)')
        doc_oficio_v1_id = _comun.subir(
            client, exp_id, 'OFICIO_SEPARATA', cat['doc_oficio_separata'].id,
            fecha_alta_organismo, 'Oficio de consulta al Ayuntamiento de Jerez (v1)')
        _editar_conservando_consumidos(
            tarea_elab_v1, [doc_separata_v1_id], doc_oficio_v1_id,
            'vincular producido ELABORAR separata Ayto. v1')

        fecha_notif_v1 = _comun.avanzar_habiles(fecha_alta_organismo, 1)
        _fijar_reloj(fecha_notif_v1)
        tarea_notif_v1 = Tarea.query.get(_comun.check(
            svc.crear_tarea(tramite_sep_ayto_v1, cat['tarea_notificar']),
            'crear_tarea NOTIFICAR separata Ayto. v1'))
        doc_justif_sir_v1_id = _comun.subir(
            client, exp_id, 'JUSTIFICANTE_SIR', cat['doc_justificante_sir'].id,
            fecha_notif_v1, 'Justificante SIR del envío de la separata al Ayuntamiento (v1)')
        _comun.notificar(tarea_notif_v1, doc_oficio_v1_id, doc_justif_sir_v1_id,
                         fecha_notif_v1, 'separata Ayto. v1', canal='SIR')

        tarea_esp_v1 = Tarea.query.get(_comun.check(
            svc.crear_tarea(tramite_sep_ayto_v1, cat['tarea_esperar_plazo']),
            'crear_tarea ESPERAR_PLAZO separata Ayto. v1'))
        _editar_conservando_consumidos(
            tarea_esp_v1, [doc_oficio_v1_id], None, 'disparar plazo separata Ayto. v1')
        print(f"CONSULTA_SEPARATA Ayto. Jerez (v1): elaborada, notificada por SIR y en "
              f"espera (plazo legal: {oe_ayto_v1.plazo_legal_dias} días).")

        # No se toca nada más: el Ayuntamiento no contesta nunca en esta ronda. Su
        # ESPERAR_PLAZO se queda sin documento producido — el hueco vivo de §I.
        fecha_vencido_v1 = _comun.avanzar_habiles(fecha_notif_v1, HABILES_HASTA_VENCIMIENTO_V1)
        _fijar_reloj(fecha_vencido_v1)
        print(f"CONSULTA_SEPARATA Ayto. Jerez (v1): sin respuesta — a día {fecha_vencido_v1} "
              f"el plazo de 30 días hábiles (art. 131.1) lleva vencido "
              f"{HABILES_HASTA_VENCIMIENTO_V1 - 30} días hábiles. Organismo enquistado, "
              f"pendiente de analizar el silencio para siempre en este escenario.")

        # =====================================================================
        # El reformado: segunda versión del proyecto
        # =====================================================================
        docs['DOC_PROYECTO_REFORMADO'] = _comun.subir(
            client, exp_id, 'DOC_PROYECTO', cat['doc_proyecto'].id, fecha_vencido_v1,
            'Reformado de proyecto: reencauce del tramo final para evitar '
            'servidumbres de vuelo, cruzando ahora la línea de ferrocarril',
            fichero='doc_proyecto_reformado.pdf',
            abre_reformado=True, origen_reformado='VOLUNTARIO')

        from app.services.reformados import ultimo_reformado
        reformado = ultimo_reformado(expediente.id)
        if reformado is None:
            print("ABORTADO: el reformado no quedó declarado tras la subida del "
                  "segundo DOC_PROYECTO.")
            sys.exit(1)
        print(f"Reformado declarado: reformados_proyecto.id={reformado.id} "
              f"(documento={reformado.documento_id}, origen={reformado.origen}).")

        # =====================================================================
        # v2 — ANALISIS_SOLICITUD y CONSULTAS del reformado, permitidas por §F
        # =====================================================================
        fase2_id = _comun.check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                                'crear_fase ANALISIS_SOLICITUD v2 (reformado)')
        fase2_analisis = Fase.query.get(fase2_id)
        if fase2_analisis.reformado_id != reformado.id:
            print(f"ABORTADO: ANALISIS_SOLICITUD v2 nació con reformado_id="
                  f"{fase2_analisis.reformado_id}, se esperaba {reformado.id}.")
            sys.exit(1)

        tramite_ad2_id = _comun.check(
            svc.crear_tramite(fase2_analisis, cat['tramite_analisis_documental']),
            'crear_tramite ANALISIS_DOCUMENTAL v2')
        tramite_ad2 = Tramite.query.get(tramite_ad2_id)
        tarea_analizar2_id = _comun.check(
            svc.crear_tarea(tramite_ad2, cat['tarea_analizar']), 'crear_tarea ANALIZAR v2')

        # Nada que casar: todos los requisitos aplicables ya están cubiertos por el
        # fallback a la versión inicial (§E bis, R4 #899) — ninguno de los de este
        # escenario está marcado `afectado_por_reformado`, así que no hace falta (ni
        # se debe) volver a vincular el mismo documento bajo la versión nueva.
        doc_diagnostico2_id = _comun.producir_diagnostico(
            client, exp_id, tarea_analizar2_id, 'ANALISIS_DOCUMENTAL v2 (reformado)')

        fecha_consultas_v2 = _comun.avanzar_habiles(fecha_vencido_v1, 2)
        _fijar_reloj(fecha_consultas_v2)

        fase2_consultas_id = _comun.check(
            svc.crear_fase(solicitud, cat['fase_consultas']),
            'crear_fase CONSULTAS v2 (reformado)')
        fase2_consultas = Fase.query.get(fase2_consultas_id)
        if fase2_consultas.reformado_id != reformado.id:
            print(f"ABORTADO: CONSULTAS v2 nació con reformado_id="
                  f"{fase2_consultas.reformado_id}, se esperaba {reformado.id}.")
            sys.exit(1)

        entidad_adif, dir_adif_id = _asegurar_organismo(client, ORGANISMO_ADIF)

        oe_v2_por_clave = {}
        for org, entidad, dir_id in (
            (ORGANISMO_AYUNTAMIENTO, entidad_ayto, dir_ayto_id),
            (ORGANISMO_ADIF, entidad_adif, dir_adif_id),
        ):
            oe_id = _comun.check(
                svc.crear_organismo(fase2_consultas, entidad, via='consulta'),
                f"crear_organismo {org['abrev']} v2")
            oe = OrganismoExpediente.query.get(oe_id)
            _comun.check(
                svc.editar_organismo(oe, via='consulta', resultado=None,
                                     direccion_notificacion_id=dir_id, documento_id=None),
                f"editar_organismo {org['abrev']} v2 (dirección)")
            oe_v2_por_clave[org['clave']] = oe
        print(f"CONSULTAS v2: {len(oe_v2_por_clave)} organismos dados de alta "
              f"(1 repetido, 1 nuevo) — UNIQUE(fase_id, organismo_id) sin conflicto "
              f"con la ronda de la v1.")

        res_envio2 = svc_consultas.enviar_consultas(fase2_consultas, {})
        if not res_envio2.ok:
            motivo = res_envio2.bloqueo.motivo if res_envio2.bloqueo else res_envio2.error
            print(f"ABORTADO en enviar_consultas v2: {motivo}")
            sys.exit(1)
        separata_v2_por_clave = {}
        for tramite_id in res_envio2.ids:
            vinculo = TramiteOrganismo.query.filter_by(tramite_id=tramite_id).first()
            clave = next(c for c, oe in oe_v2_por_clave.items()
                         if oe.id == vinculo.organismo_expediente_id)
            separata_v2_por_clave[clave] = Tramite.query.get(tramite_id)

        fecha_notif_v2 = _comun.avanzar_habiles(fecha_consultas_v2, 1)
        _fijar_reloj(fecha_notif_v2)

        espera_v2_por_clave = {}
        for org, _entidad, _dir_id in (
            (ORGANISMO_AYUNTAMIENTO, entidad_ayto, dir_ayto_id),
            (ORGANISMO_ADIF, entidad_adif, dir_adif_id),
        ):
            clave, abrev = org['clave'], org['abrev']
            tramite_sep = separata_v2_por_clave[clave]

            tarea_elab = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_elaborar']),
                f'crear_tarea ELABORAR separata {abrev} v2'))
            doc_separata_id = _comun.subir(
                client, exp_id, 'DOC_SEPARATA', cat['doc_separata'].id, fecha_notif_v2,
                f"Separata del reformado del proyecto para {org['nombre_completo']}")
            doc_oficio_id = _comun.subir(
                client, exp_id, 'OFICIO_SEPARATA', cat['doc_oficio_separata'].id,
                fecha_notif_v2, f'Oficio de consulta a {abrev} sobre el reformado')
            _editar_conservando_consumidos(
                tarea_elab, [doc_separata_id], doc_oficio_id,
                f'vincular producido ELABORAR separata {abrev} v2')

            tarea_notif = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_notificar']),
                f'crear_tarea NOTIFICAR separata {abrev} v2'))
            doc_justif_id = _comun.subir(
                client, exp_id, 'JUSTIFICANTE_SIR', cat['doc_justificante_sir'].id,
                fecha_notif_v2, f'Justificante SIR del envío de la separata a {abrev}')
            _comun.notificar(tarea_notif, doc_oficio_id, doc_justif_id,
                             fecha_notif_v2, f'separata {abrev} v2', canal='SIR')

            tarea_esp = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_esperar_plazo']),
                f'crear_tarea ESPERAR_PLAZO separata {abrev} v2'))
            _editar_conservando_consumidos(
                tarea_esp, [doc_oficio_id], None, f'disparar plazo separata {abrev} v2')
            espera_v2_por_clave[clave] = (tarea_esp, tramite_sep)
            print(f"CONSULTA_SEPARATA {abrev} (v2): elaborada, notificada por SIR y en "
                  f"espera (plazo legal: {oe_v2_por_clave[clave].plazo_legal_dias} días).")

        def _ciclo_favorable(clave, abrev, oe, dir_id, asunto_respuesta):
            """Respuesta favorable dentro de plazo → traslado al titular → titular
            acepta dentro de plazo → cierre `cerrado_favorable`. Mismo patrón que
            el ciclo con condicionados de CONSULTAS_VARIOS_ESTADOS (#862), sin
            condicionados: toda respuesta con resultado (≠ sin_respuesta) exige
            traslado al titular (DISEÑO_CONSULTAS_ORGANISMOS.md, regla de creación
            de CONSULTA_TRASLADO_TITULAR).
            """
            tarea_esp, tramite_sep = espera_v2_por_clave[clave]
            fecha_resp = _comun.fecha_respuesta_en_plazo(
                tarea_esp, f'separata {abrev} v2', MARGEN_RESPUESTA_ORGANISMO_HABILES)
            _fijar_reloj(fecha_resp)

            doc_resp_id = _comun.subir(
                client, exp_id, 'RESPUESTA_ORGANISMO', cat['doc_respuesta_organismo'].id,
                fecha_resp, asunto_respuesta)
            _editar_conservando_consumidos(
                tarea_esp, [], doc_resp_id, f'cerrar plazo separata {abrev} v2')

            tarea_an = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_analizar']),
                f'crear_tarea ANALIZAR separata {abrev} v2'))
            _editar_conservando_consumidos(
                tarea_an, [doc_resp_id], None, f'vincular consumido ANALIZAR separata {abrev} v2')
            _comun.producir_diagnostico(client, exp_id, tarea_an.id, f'separata {abrev} v2',
                                        resultado='favorable')

            res_tr = svc_consultas.crear_traslado(
                fase2_consultas, {'organismo_expediente_id': oe.id, 'tipo': 'TITULAR'})
            tramite_tr = Tramite.query.get(_comun.check(res_tr, f'crear_traslado titular {abrev} v2'))

            fecha_traslado = _comun.avanzar_habiles(fecha_resp, HABILES_HASTA_TRASLADO)
            _fijar_reloj(fecha_traslado)

            tarea_elab_tr = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_elaborar']),
                f'crear_tarea ELABORAR traslado {abrev} v2'))
            doc_oficio_tr_id = _comun.subir(
                client, exp_id, 'OFICIO_TRASLADO_RESPUESTA',
                cat['doc_oficio_traslado_respuesta'].id, fecha_traslado,
                f'Traslado al titular de la respuesta de {abrev} sobre el reformado')
            _editar_conservando_consumidos(
                tarea_elab_tr, [doc_resp_id], doc_oficio_tr_id,
                f'vincular producido ELABORAR traslado {abrev} v2')

            tarea_notif_tr = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_notificar']),
                f'crear_tarea NOTIFICAR traslado {abrev} v2'))
            doc_justif_tr_id = _comun.subir(
                client, exp_id, 'JUSTIFICANTE_NOTIFICA', cat['doc_justificante_notifica'].id,
                fecha_traslado, f'Justificante de notificación del traslado ({abrev} v2)')
            _comun.notificar(tarea_notif_tr, doc_oficio_tr_id, doc_justif_tr_id,
                             fecha_traslado, f'traslado {abrev} v2')

            tarea_esp_tr = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_esperar_plazo']),
                f'crear_tarea ESPERAR_PLAZO traslado {abrev} v2'))
            _editar_conservando_consumidos(
                tarea_esp_tr, [doc_oficio_tr_id], None, f'disparar plazo traslado {abrev} v2')

            fecha_resp_titular = _comun.fecha_respuesta_en_plazo(
                tarea_esp_tr, f'traslado {abrev} v2', MARGEN_RESPUESTA_TITULAR_HABILES)
            _fijar_reloj(fecha_resp_titular)
            doc_resp_titular_id = _comun.subir(
                client, exp_id, 'RESPUESTA_TITULAR', cat['doc_respuesta_titular'].id,
                fecha_resp_titular, f'El titular acepta la respuesta de {abrev} al reformado')
            _editar_conservando_consumidos(
                tarea_esp_tr, [], doc_resp_titular_id, f'cerrar plazo traslado {abrev} v2')

            tarea_an_tr = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_analizar']),
                f'crear_tarea ANALIZAR traslado {abrev} v2'))
            _editar_conservando_consumidos(
                tarea_an_tr, [doc_resp_titular_id], None,
                f'vincular consumido ANALIZAR traslado {abrev} v2')
            _comun.producir_diagnostico(client, exp_id, tarea_an_tr.id, f'traslado {abrev} v2',
                                        resultado='favorable')

            _comun.check(
                svc.editar_organismo(oe, via='consulta', resultado='cerrado_favorable',
                                     direccion_notificacion_id=dir_id, documento_id=None),
                f'editar_organismo {abrev} v2 (resultado)')
            print(f"{abrev} (v2): respuesta favorable, traslado aceptado por el titular — "
                  f"organismo cerrado_favorable.")

        _ciclo_favorable('ayuntamiento', 'Ayto. Jerez', oe_v2_por_clave['ayuntamiento'],
                         dir_ayto_id,
                         'Informe del Ayuntamiento de Jerez: favorable al nuevo trazado '
                         'dentro de su término municipal')
        _ciclo_favorable('adif', 'ADIF', oe_v2_por_clave['adif'], dir_adif_id,
                         'Informe de ADIF: favorable al cruce de la línea de ferrocarril '
                         'con las medidas de protección estándar')

        # --- Fin del alcance --------------------------------------------------
        # El reloj vuelve a hoy: las fechas de la v2 ya quedaron fijadas en el
        # pasado, y el organismo enquistado de la v1 sigue vencido se mire desde
        # cuando se mire — no depende de qué diga el reloj simulado.
        if efectos_desarrollo:
            reloj_simulado.borrar()

        db.session.expire(fase1_consultas)
        db.session.expire(fase2_consultas)
        print(f"\nExpediente AT-{expediente.numero_at} (id={exp_id}) completado — "
              f"v1: ANALISIS_SOLICITUD limpia + CONSULTAS con el Ayto. enquistado; "
              f"v2 (reformado {reformado.id}): ANALISIS_SOLICITUD limpia + CONSULTAS "
              f"con Ayto. (repetido) y ADIF (nuevo), ambos cerrados favorable.")
        return expediente.numero_at, exp_id


if __name__ == '__main__':
    numero_at, exp_id = main()
