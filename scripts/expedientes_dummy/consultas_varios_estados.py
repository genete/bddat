"""Expediente de prueba reproducible (#862): CONSULTAS_VARIOS_ESTADOS.

Propósito: testear la fase de CONSULTAS con las tres separatas enviadas el mismo
día y cada organismo en un estado distinto a día de hoy. Expediente incompleto a
propósito: la fase sigue abierta, y es esa foto —no un expediente terminado— lo
que hace falta para trabajar en consultas.

Escenario: línea aérea de 66 kV entre dos subestaciones en suelo rústico de
Jerez de la Frontera (AAP+AAC, un solo municipio). Por longitud, tensión y suelos
que recorre está EXENTA de instrumento ambiental, de modo que no hay figura
ambiental ni información pública; el titular presenta además la declaración
responsable de no necesidad de DUP. El trazado cruza una carretera provincial y
una línea de ferrocarril, así que se consulta a tres organismos: el Ayuntamiento
de Jerez de la Frontera, ADIF y la Diputación Provincial de Cádiz.

Estado a día de hoy — 40 días hábiles después de notificar las separatas, que es
el ancla del escenario (el plazo del art. 131.1 son 30 días hábiles, así que ya
ha vencido para quien no contestó):

    Ayuntamiento   silencio. Plazo vencido y sin ANALIZAR: queda la decisión de
                   dar por buena la conformidad tácita (caso A de ADR-011 §6).
    ADIF           contestó pronto y con condicionados; traslado al titular
                   notificado, el titular aceptó dentro de plazo y el ciclo está
                   cerrado — organismo en 'cerrado_con_condicionados'.
    Diputación     contestó apurando el plazo y en sentido desfavorable; el
                   traslado al titular está notificado y su ESPERAR_PLAZO sigue
                   corriendo — sin respuesta y todavía en plazo a fecha de hoy.

Alcance: la fase ANALISIS_SOLICITUD se recorre sin defectos —todos los requisitos
que el catálogo considera aplicables quedan cubiertos en el primer ANALIZAR, sin
ninguna vuelta de subsanación— y se comunica el inicio. La fase CONSULTAS queda
abierta. No se emite el certificado de fin de consultas ni se abre RESOLUCION.

Circuito real — nunca INSERT SQL directo (ver README.md de esta carpeta):
    - Alta expediente/proyecto/solicitud: `app.services.alta_expediente`.
    - Fase/trámite/tarea y organismos: `app.services.mutaciones_arbol`.
    - Separatas y traslados: `app.services.consultas_organismos` —
      `enviar_consultas` (acción en bloque, una por organismo pendiente) y
      `crear_traslado`, que son las mismas entradas que usa la UI (ADR-042 §C/§D).
    - Checklist y diagnósticos: endpoints del contenedor de ANALIZAR (ADR-033).
      Ojo a la diferencia entre los dos ANALIZAR: el de ANALISIS_DOCUMENTAL es
      extendido y su sentido se deriva del checklist, mientras que el de las
      separatas y los traslados es simple y el sentido lo elige el tramitador —
      es lo que aquí distingue a ADIF (condicionado) de la Diputación
      (desfavorable).
    - Alta de organismos y sus direcciones de notificación: las rutas reales de
      `/entidades`, no `db.session.add`. Son catálogo de la aplicación, no datos
      del expediente: se crean solo si faltan, y se reutilizan si ya están.

Calendario: ninguna fecha absoluta. Todo cuelga de `hoy` hacia atrás — el ancla
es el día en que se notificaron las separatas, 40 días hábiles antes — y las
respuestas se derivan del vencimiento real que calcula el servicio de plazos,
retrocediendo el margen declarado para cada interviniente. Al terminar, el reloj
de desarrollo se borra: este expediente-tipo se lee «a fecha de hoy», y dejarlo
congelado en la última fecha del escenario lo falsearía.

Reejecutable sin implementar borrado aquí: si ya existe un expediente marcado con
este código, sus observaciones pasan a '[RECICLAR] ...' y se crea uno nuevo desde
cero. El borrado real es `limpiar_reciclables.py`.

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/consultas_varios_estados.py
"""
import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

CODIGO = 'CONSULTAS_VARIOS_ESTADOS'
PROPOSITO = (
    'Expediente para testear la fase de consultas con las separatas enviadas y '
    'cada organismo en un estado distinto: silencio vencido, ciclo cerrado con '
    'condicionados y traslado al titular pendiente de respuesta.'
)
MARCA = f'[DUMMY:{CODIGO}]'
OBSERVACIONES = f'{MARCA} {PROPOSITO}'

# Ancla del escenario: hoy es el día hábil nº 40 desde que se notificaron las
# separatas. Es el dato que fija la foto —con 30 días hábiles de plazo (art.
# 131.1), el silencio del Ayuntamiento ya venció y el traslado a la Diputación
# todavía no—, así que el escenario se construye hacia atrás desde aquí en vez de
# hacia delante desde el alta.
HABILES_DESDE_NOTIFICACION_SEPARATAS = 40

# Días naturales entre el alta y la notificación de las separatas: lo que dura la
# fase de análisis documental sin subsanaciones más el paso a consultas. Holgado
# a propósito; sobrar unos días solo aleja el alta en el calendario.
DIAS_ANALISIS_PREVIO = 15

# Días hábiles ANTES del vencimiento real en que contesta cada interviniente. Es
# lo único que elige el escenario: la fecha sale del plazo que diga el catálogo
# (ver `_comun.fecha_respuesta_en_plazo`), no de un número escrito a mano.
# ADIF contesta pronto —con margen amplio— porque después de su respuesta todavía
# tienen que caber el traslado al titular y la respuesta de este dentro de la
# misma ventana de 40 días; la Diputación apura, y por eso su traslado sigue vivo.
MARGEN_ADIF_HABILES = 15
MARGEN_DIPUTACION_HABILES = 3
MARGEN_TITULAR_HABILES = 5

# Días hábiles entre recibir la respuesta de un organismo y notificar el traslado
# al titular: el tiempo de leerla y redactar el oficio.
HABILES_HASTA_TRASLADO = 2

# Organismos consultados. Se dan de alta en el catálogo de entidades si no están
# (por NIF), con rol de consultado y una dirección de notificación. Datos de
# contacto ficticios —dominio .example, reservado por el RFC 2606— porque la base
# de desarrollo no debe llevar direcciones reales de organismos.
ORGANISMOS = [
    {
        'clave': 'ayuntamiento',
        'nombre_completo': 'Ayuntamiento de Jerez de la Frontera',
        'nif': 'P1102000J',
        'abrev': 'Ayto. Jerez',
        'email': 'registro@jerez.example',
        'direccion': 'Plaza del Arenal, s/n',
        'codigo_postal': '11403',
        'motivo': 'Ayuntamiento del término municipal afectado',
    },
    {
        'clave': 'adif',
        'nombre_completo': 'ADIF - Administrador de Infraestructuras Ferroviarias',
        'nif': 'Q2801660H',
        'abrev': 'ADIF',
        'email': 'consultas@adif.example',
        'direccion': 'C/ Sor Ángela de la Cruz, 3',
        'codigo_postal': '28020',
        'motivo': 'Titular de la línea de ferrocarril que cruza el trazado',
    },
    {
        'clave': 'diputacion',
        'nombre_completo': 'Diputación Provincial de Cádiz',
        'nif': 'P1100000B',
        'abrev': 'Dip. Cádiz',
        'email': 'carreteras@dipucadiz.example',
        'direccion': 'Plaza de España, 1',
        'codigo_postal': '11071',
        'motivo': 'Titular de la carretera provincial que cruza el trazado',
    },
]

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
        # Los tres trámites de consulta no se crean por despensa (creacion_generica
        # = False): salen de `enviar_consultas` y `crear_traslado`. Se comprueban
        # aquí para abortar con la lista de faltantes si el catálogo está a medias.
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
        # Canal entre administraciones: las separatas y los traslados a organismo
        # no van por Notifica, van por SIR.
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

def _asegurar_organismos(client):
    """Da de alta en el catálogo las entidades consultadas que falten, con su
    dirección de notificación, por las rutas reales de `/entidades`.

    Idempotente por NIF: en una base que ya los tiene (segunda ejecución, o la de
    tests tras la primera semilla) no crea nada y devuelve lo que hay. Devuelve
    {clave: (Entidad, direccion_notificacion_id)}.
    """
    from app.models.entidad import Entidad
    from app.models.direccion_notificacion import DireccionNotificacion

    resuelto = {}
    for org in ORGANISMOS:
        entidad = Entidad.query.filter_by(nif=org['nif']).first()
        if entidad is None:
            r = client.post('/entidades/nueva', data={
                'nombre_completo': org['nombre_completo'],
                'nif': org['nif'],
                'rol_consultado': 'on',
                'email': org['email'],
                'activo': 'on',
                'notas': f"Organismo del expediente-tipo {CODIGO} — {org['motivo']}.",
            }, follow_redirects=True)
            entidad = Entidad.query.filter_by(nif=org['nif']).first()
            if entidad is None:
                print(f"ABORTADO: no se pudo dar de alta {org['nombre_completo']} "
                      f"(HTTP {r.status_code})")
                sys.exit(1)
            print(f"  entidad creada: {entidad.nombre_completo} ({entidad.nif}).")
        elif not entidad.rol_consultado:
            # Existe pero sin el rol: crear_organismo la rechazaría más adelante
            # con un error que no diría de dónde viene.
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

        resuelto[org['clave']] = (entidad, direccion.id)
    return resuelto


# ---------------------------------------------------------------------------
# Alta expediente/proyecto/solicitud — por el servicio real (#428)
# ---------------------------------------------------------------------------

def _crear_expediente(cat, fecha_base):
    """Alta completa por `alta_expediente()`, la misma vía que el formulario.

    Devuelve el `ResultadoAlta`, que trae ya el escrito de solicitud creado: es
    el documento que ancla la solicitud y el que después cubre su requisito en el
    checklist documental.
    """
    from app.services.alta_expediente import (
        DatosAlta, DocumentoSolicitud, alta_expediente,
    )

    with open(os.path.join(_comun.FIXTURES_DIR, 'modelo_solicitud.pdf'), 'rb') as f:
        contenido = f.read()

    resultado = alta_expediente(DatosAlta(
        tipo_expediente_id=cat['tipo_expediente'].id,
        responsable_id=cat['usuario'].id,
        heredado=False,
        titulo='Línea aérea 66 kV SE Guadalcacín — SE Cartuja',
        descripcion=(
            'Nueva línea aérea de alta tensión 66 kV entre las subestaciones de '
            'Guadalcacín y Cartuja, en suelo rústico del término municipal de '
            'Jerez de la Frontera. El trazado cruza una carretera provincial y '
            'una línea de ferrocarril.'
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
        # Campos técnicos que el formulario no pide y este escenario sí fija: es
        # una línea aérea y no está en suelo urbano, al revés que el
        # expediente-tipo de #814. La exención de instrumento ambiental viene por
        # longitud y tensión, no por el tipo de suelo, y quien la declara es
        # `ia_id` — estos campos describen el proyecto, no la deducen.
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
    """`editar_tarea` tratando CONSUMIDO como conjunto completo (no aditivo): si
    la tarea ya traía consumidos —los que enganchan los hooks automáticos al
    crearla— hay que repetirlos, o se liberan y con ellos el disparo del plazo
    (hallazgo de #825).
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
    (#849): deja fuera lo que solo tiene sentido en la máquina de desarrollo —
    mover el reloj simulado, que escribe en `instance/`—. El escenario que se
    construye es el mismo.
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

        organismos = _asegurar_organismos(client)

        # --- Calendario, derivado del ancla ---------------------------------
        # De `date.today()` y no de `reloj_simulado.hoy()`: el reloj casi siempre
        # viene de la ejecución anterior de este mismo script, y anclarse a él
        # congelaría el expediente-tipo en el calendario del día en que se generó.
        hoy = date.today()
        fecha_notif_separatas = _comun.retroceder_habiles(
            hoy, HABILES_DESDE_NOTIFICACION_SEPARATAS)
        fecha_base = fecha_notif_separatas - timedelta(days=DIAS_ANALISIS_PREVIO)
        print(f"Ancla: separatas notificadas el {fecha_notif_separatas} "
              f"({HABILES_DESDE_NOTIFICACION_SEPARATAS} días hábiles antes de hoy); "
              f"alta el {fecha_base}.")

        _fijar_reloj(fecha_base)

        alta = _crear_expediente(cat, fecha_base)
        expediente, solicitud = alta.expediente, alta.solicitud
        exp_id = expediente.id

        # Pool documental de la presentación. El escrito de solicitud ya entró con
        # el alta (#428); el resto lo aporta el titular con ella.
        docs = {'MODELO_SOLICITUD': alta.documento.id}
        docs['DOC_PROYECTO'] = _comun.subir(
            client, exp_id, 'DOC_PROYECTO', cat['doc_proyecto'].id, fecha_base,
            'Proyecto técnico de la línea aérea 66 kV')
        docs['JUSTIFICANTE_PAGO_TASA'] = _comun.subir(
            client, exp_id, 'JUSTIFICANTE_PAGO_TASA',
            cat['doc_justificante_pago_tasa'].id, fecha_base,
            'Justificante de pago de la tasa')
        _comun.cubrir_requisito_tasa(solicitud, docs['JUSTIFICANTE_PAGO_TASA'])

        # Declaración responsable de no necesidad de DUP: el titular la presenta
        # porque no pide utilidad pública. Entra al pool y ahí se queda — hoy el
        # requisito DR_NO_DUP del catálogo está condicionado a
        # `solicitud_incluye_dup = true`, así que no aparece en el checklist de
        # una solicitud sin DUP y no hay a qué casarla.
        docs['DR_NO_DUP'] = _comun.subir(
            client, exp_id, 'DR_NO_DUP', cat['doc_dr_no_dup'].id, fecha_base,
            'Declaración responsable de no necesidad de DUP')

        # --- Fase ANALISIS_SOLICITUD, sin defectos --------------------------
        fase_id = _comun.check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                               'crear_fase ANALISIS_SOLICITUD')
        fase_analisis = Fase.query.get(fase_id)

        tramite_ad_id = _comun.check(
            svc.crear_tramite(fase_analisis, cat['tramite_analisis_documental']),
            'crear_tramite ANALISIS_DOCUMENTAL')
        tramite_ad = Tramite.query.get(tramite_ad_id)

        tarea_analizar_id = _comun.check(
            svc.crear_tarea(tramite_ad, cat['tarea_analizar']), 'crear_tarea ANALIZAR')

        # La lista de requisitos NO se escribe a mano: se le pregunta al evaluador
        # real cuáles aplican a esta solicitud. Así "sin defectos" sigue siendo
        # cierto cuando mañana entre un requisito nuevo en el catálogo — y si
        # aplica uno sin documento dummy, el script aborta diciendo cuál falta en
        # vez de producir un diagnóstico desfavorable silencioso.
        aportados = []
        for codigo in _comun.requisitos_aplicables(solicitud, fase_analisis):
            if codigo not in docs:
                tipo_doc = _comun.tipo_documento(codigo)
                fichero = os.path.join(_comun.FIXTURES_DIR, f'{codigo.lower()}.pdf')
                if tipo_doc is None or not os.path.isfile(fichero):
                    print(f"ABORTADO: el requisito {codigo} aplica a esta solicitud y "
                          f"no hay documento dummy para cubrirlo "
                          f"({os.path.basename(fichero)}). Generarlo con "
                          f"scripts/generar_documentos_dummy.py.")
                    sys.exit(1)
                docs[codigo] = _comun.subir(client, exp_id, codigo, tipo_doc.id,
                                            fecha_base, f'{tipo_doc.nombre} (presentación)')
            aportados.append((codigo, docs[codigo]))

        _comun.casar_requisitos(client, exp_id, tarea_analizar_id, aportados,
                                'presentación')
        doc_diagnostico_id = _comun.producir_diagnostico(
            client, exp_id, tarea_analizar_id, 'ANALISIS_DOCUMENTAL')

        # --- COMUNICACION_INICIO_ADMISION -----------------------------------
        fecha_admision = _comun.avanzar_habiles(fecha_base, 3)
        _fijar_reloj(fecha_admision)

        tramite_com_id = _comun.check(
            svc.crear_tramite(fase_analisis, cat['tramite_comunicacion_admision']),
            'crear_tramite COMUNICACION_INICIO_ADMISION')
        tramite_com = Tramite.query.get(tramite_com_id)

        tarea_com_elab_id = _comun.check(
            svc.crear_tarea(tramite_com, cat['tarea_elaborar']), 'crear_tarea ELABORAR admision')
        doc_admision_id = _comun.subir(
            client, exp_id, 'OFICIO_INICIO_ADMISION', cat['doc_oficio_inicio_admision'].id,
            fecha_admision, 'Comunicación de inicio y admisión a trámite')
        _editar_conservando_consumidos(
            Tarea.query.get(tarea_com_elab_id), [doc_diagnostico_id], doc_admision_id,
            'vincular producido ELABORAR admision')

        tarea_com_notif_id = _comun.check(
            svc.crear_tarea(tramite_com, cat['tarea_notificar']), 'crear_tarea NOTIFICAR admision')
        doc_justif_admision_id = _comun.subir(
            client, exp_id, 'JUSTIFICANTE_NOTIFICA', cat['doc_justificante_notifica'].id,
            fecha_admision, 'Justificante de notificación de la comunicación de inicio')
        _comun.notificar(Tarea.query.get(tarea_com_notif_id), doc_admision_id,
                         doc_justif_admision_id, fecha_admision, 'admision')
        print("COMUNICACION_INICIO_ADMISION: elaborada y notificada.")

        # --- Fase CONSULTAS: alta de organismos -----------------------------
        fase_consultas_id = _comun.check(
            svc.crear_fase(solicitud, cat['fase_consultas']), 'crear_fase CONSULTAS')
        fase_consultas = Fase.query.get(fase_consultas_id)

        fecha_separatas = _comun.retroceder_habiles(fecha_notif_separatas, 1)
        _fijar_reloj(fecha_separatas)

        oe_por_clave = {}
        for org in ORGANISMOS:
            entidad, direccion_id = organismos[org['clave']]
            oe_id = _comun.check(
                svc.crear_organismo(fase_consultas, entidad, via='consulta'),
                f"crear_organismo {org['abrev']}")
            oe = OrganismoExpediente.query.get(oe_id)
            # La dirección de notificación no es parámetro del alta: se fija
            # editando, que es como lo hace la UI (ADR-042 §C).
            _comun.check(
                svc.editar_organismo(oe, via='consulta', resultado=None,
                                     direccion_notificacion_id=direccion_id,
                                     documento_id=None),
                f"editar_organismo {org['abrev']} (dirección)")
            oe_por_clave[org['clave']] = oe
        print(f"Fase CONSULTAS: {len(oe_por_clave)} organismos dados de alta.")

        # --- Separatas: una por organismo, en bloque ------------------------
        res_envio = svc_consultas.enviar_consultas(fase_consultas, {})
        if not res_envio.ok:
            motivo = res_envio.bloqueo.motivo if res_envio.bloqueo else res_envio.error
            print(f"ABORTADO en enviar_consultas: {motivo}")
            sys.exit(1)
        separata_por_clave = {}
        for tramite_id in res_envio.ids:
            vinculo = TramiteOrganismo.query.filter_by(tramite_id=tramite_id).first()
            clave = next(c for c, oe in oe_por_clave.items()
                         if oe.id == vinculo.organismo_expediente_id)
            separata_por_clave[clave] = Tramite.query.get(tramite_id)
        print(f"Separatas creadas: {len(separata_por_clave)} "
              f"(plazo legal congelado: "
              f"{oe_por_clave['adif'].plazo_legal_dias} días).")

        espera_por_clave = {}
        for org in ORGANISMOS:
            clave, abrev = org['clave'], org['abrev']
            tramite_sep = separata_por_clave[clave]

            tarea_elab = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_elaborar']),
                f'crear_tarea ELABORAR separata {abrev}'))
            # Subir y vincular organismo a organismo, sin adelantar las tres
            # separatas: el pool no duplica el fichero cuando el contenido ya está
            # (mismo hash), de modo que tres DOC_SEPARATA subidos de golpe —los
            # tres son el mismo PDF dummy— comparten un solo fichero físico, y al
            # llevarse el primero a su carpeta ESFTT los otros dos se quedan
            # apuntando a un fichero que ya no existe. Verificado en AT-30.
            doc_separata_id = _comun.subir(
                client, exp_id, 'DOC_SEPARATA', cat['doc_separata'].id, fecha_separatas,
                f"Separata del proyecto para {org['nombre_completo']}")
            doc_oficio_id = _comun.subir(
                client, exp_id, 'OFICIO_SEPARATA', cat['doc_oficio_separata'].id,
                fecha_separatas, f'Oficio de consulta a {abrev}')
            _editar_conservando_consumidos(
                tarea_elab, [doc_separata_id], doc_oficio_id,
                f'vincular producido ELABORAR separata {abrev}')

            _fijar_reloj(fecha_notif_separatas)
            tarea_notif = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_notificar']),
                f'crear_tarea NOTIFICAR separata {abrev}'))
            doc_justif_id = _comun.subir(
                client, exp_id, 'JUSTIFICANTE_SIR', cat['doc_justificante_sir'].id,
                fecha_notif_separatas, f'Justificante SIR del envío de la separata a {abrev}')
            _comun.notificar(tarea_notif, doc_oficio_id, doc_justif_id,
                             fecha_notif_separatas, f'separata {abrev}', canal='SIR')

            tarea_esp = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_sep, cat['tarea_esperar_plazo']),
                f'crear_tarea ESPERAR_PLAZO separata {abrev}'))
            # Dispara el plazo del art. 131.1: CONSUMIDO = oficio ya notificado.
            _editar_conservando_consumidos(
                tarea_esp, [doc_oficio_id], None,
                f'disparar plazo separata {abrev}')
            espera_por_clave[clave] = tarea_esp
            print(f"CONSULTA_SEPARATA {abrev}: elaborada, notificada por SIR y en espera.")

        # --- Ayuntamiento: silencio -----------------------------------------
        # No se toca nada más. Su ESPERAR_PLAZO se queda sin documento producido y
        # el plazo vence solo: a día de hoy son 40 días hábiles sobre 30 de plazo.
        # Tampoco se crea el ANALIZAR: dar por buena la conformidad tácita (caso A
        # de ADR-011 §6) es justo la decisión que este expediente deja pendiente.
        print("CONSULTA_SEPARATA Ayto. Jerez: sin respuesta — plazo vencido, "
              "pendiente de analizar el silencio.")

        def _responder_organismo(clave, abrev, margen, resultado_analizar, asunto):
            """Respuesta del organismo dentro de plazo + su ANALIZAR.

            Devuelve (documento de la respuesta, fecha). El sentido del
            diagnóstico se declara aquí: en el ANALIZAR de una separata no hay
            checklist del que derivarlo (ADR-033 §3), lo elige el tramitador.
            """
            tarea_esp = espera_por_clave[clave]
            fecha = _comun.fecha_respuesta_en_plazo(tarea_esp, f'separata {abrev}', margen)
            _fijar_reloj(fecha)

            doc_resp_id = _comun.subir(
                client, exp_id, 'RESPUESTA_ORGANISMO', cat['doc_respuesta_organismo'].id,
                fecha, asunto)
            _editar_conservando_consumidos(
                tarea_esp, [], doc_resp_id, f'cerrar plazo separata {abrev}')

            tarea_an = Tarea.query.get(_comun.check(
                svc.crear_tarea(separata_por_clave[clave], cat['tarea_analizar']),
                f'crear_tarea ANALIZAR separata {abrev}'))
            _editar_conservando_consumidos(
                tarea_an, [doc_resp_id], None, f'vincular consumido ANALIZAR separata {abrev}')
            _comun.producir_diagnostico(client, exp_id, tarea_an.id, f'separata {abrev}',
                                        resultado=resultado_analizar)
            return doc_resp_id, fecha

        def _traslado_al_titular(clave, abrev, doc_respuesta_id, fecha_respuesta):
            """CONSULTA_TRASLADO_TITULAR notificado, con su ESPERAR_PLAZO disparado.

            Devuelve la tarea de espera, que el caller cierra (el titular responde)
            o deja corriendo (sigue pendiente a día de hoy).
            """
            res = svc_consultas.crear_traslado(
                fase_consultas,
                {'organismo_expediente_id': oe_por_clave[clave].id, 'tipo': 'TITULAR'})
            tramite_tr = Tramite.query.get(_comun.check(res, f'crear_traslado titular {abrev}'))

            fecha_traslado = _comun.avanzar_habiles(fecha_respuesta, HABILES_HASTA_TRASLADO)
            _fijar_reloj(fecha_traslado)

            tarea_elab = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_elaborar']),
                f'crear_tarea ELABORAR traslado {abrev}'))
            doc_oficio_id = _comun.subir(
                client, exp_id, 'OFICIO_TRASLADO_RESPUESTA',
                cat['doc_oficio_traslado_respuesta'].id, fecha_traslado,
                f'Traslado al titular de la respuesta de {abrev}')
            _editar_conservando_consumidos(
                tarea_elab, [doc_respuesta_id], doc_oficio_id,
                f'vincular producido ELABORAR traslado {abrev}')

            tarea_notif = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_notificar']),
                f'crear_tarea NOTIFICAR traslado {abrev}'))
            doc_justif_id = _comun.subir(
                client, exp_id, 'JUSTIFICANTE_NOTIFICA', cat['doc_justificante_notifica'].id,
                fecha_traslado, f'Justificante de notificación del traslado ({abrev})')
            _comun.notificar(tarea_notif, doc_oficio_id, doc_justif_id, fecha_traslado,
                             f'traslado {abrev}')

            tarea_esp = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_esperar_plazo']),
                f'crear_tarea ESPERAR_PLAZO traslado {abrev}'))
            # Dispara el plazo de los 15 días del art. 131.3.
            _editar_conservando_consumidos(
                tarea_esp, [doc_oficio_id], None, f'disparar plazo traslado {abrev}')
            return tramite_tr, tarea_esp

        # --- ADIF: ciclo completo, cerrado con condicionados ----------------
        doc_resp_adif_id, fecha_resp_adif = _responder_organismo(
            'adif', 'ADIF', MARGEN_ADIF_HABILES, 'condicionado',
            'Informe de ADIF: favorable con condicionados técnicos para el cruce ferroviario')
        tramite_tr_adif, espera_adif = _traslado_al_titular(
            'adif', 'ADIF', doc_resp_adif_id, fecha_resp_adif)

        fecha_resp_titular = _comun.fecha_respuesta_en_plazo(
            espera_adif, 'traslado ADIF', MARGEN_TITULAR_HABILES)
        _fijar_reloj(fecha_resp_titular)
        doc_resp_titular_id = _comun.subir(
            client, exp_id, 'RESPUESTA_TITULAR', cat['doc_respuesta_titular'].id,
            fecha_resp_titular, 'El titular acepta los condicionados de ADIF')
        _editar_conservando_consumidos(
            espera_adif, [], doc_resp_titular_id, 'cerrar plazo traslado ADIF')

        tarea_an_tr_adif = Tarea.query.get(_comun.check(
            svc.crear_tarea(tramite_tr_adif, cat['tarea_analizar']),
            'crear_tarea ANALIZAR traslado ADIF'))
        _editar_conservando_consumidos(
            tarea_an_tr_adif, [doc_resp_titular_id], None,
            'vincular consumido ANALIZAR traslado ADIF')
        _comun.producir_diagnostico(client, exp_id, tarea_an_tr_adif.id, 'traslado ADIF',
                                    resultado='favorable')
        # Desenlace legal del organismo (ADR-011 §6, caso B): el ciclo se cierra
        # con los condicionados de ADIF incorporados.
        _comun.check(
            svc.editar_organismo(oe_por_clave['adif'], via='consulta',
                                 resultado='cerrado_con_condicionados',
                                 direccion_notificacion_id=organismos['adif'][1],
                                 documento_id=None),
            'editar_organismo ADIF (resultado)')
        print("ADIF: respuesta con condicionados, traslado aceptado por el titular — "
              "organismo cerrado_con_condicionados.")

        # --- Diputación: traslado pendiente de respuesta --------------------
        doc_resp_dip_id, fecha_resp_dip = _responder_organismo(
            'diputacion', 'Dip. Cádiz', MARGEN_DIPUTACION_HABILES, 'desfavorable',
            'Informe de la Diputación Provincial de Cádiz: desfavorable al cruce '
            'de la carretera provincial en el trazado propuesto')
        _traslado_al_titular('diputacion', 'Dip. Cádiz', doc_resp_dip_id, fecha_resp_dip)
        # Su ESPERAR_PLAZO se queda abierto: el titular no ha contestado y el plazo
        # de 15 días hábiles sigue corriendo a fecha de hoy. El organismo se queda
        # sin `resultado` — NULL es "ciclo en curso" (ADR-042, #396).
        print("Dip. Cádiz: informe desfavorable trasladado al titular — "
              "pendiente de respuesta, en plazo.")

        # --- Fin del alcance -------------------------------------------------
        # El reloj vuelve a hoy: este expediente-tipo se lee «a fecha de hoy», y
        # dejarlo congelado en la última fecha del escenario haría que el traslado
        # de la Diputación no se viera correr.
        if efectos_desarrollo:
            reloj_simulado.borrar()

        db.session.expire(fase_consultas)
        print(f"\nExpediente AT-{expediente.numero_at} (id={exp_id}) completado — "
              f"fase CONSULTAS abierta, {len(oe_por_clave)} organismos en tres estados.")
        return expediente.numero_at, exp_id


if __name__ == '__main__':
    numero_at, exp_id = main()
