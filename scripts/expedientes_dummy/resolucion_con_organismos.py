"""Expediente de prueba reproducible (#971): RESOLUCION_CON_ORGANISMOS.

Propósito: ningún expediente-tipo de esta carpeta llegaba a la resolución —el de
consultas (`CONSULTAS_VARIOS_ESTADOS`, #862) se queda con `CONSULTAS` abierta a
propósito, los otros dos no pasan de `ANALISIS_SOLICITUD`—, así que no había
dónde probar por el circuito real lo que trajo N5 (#967/#968): la notificación
de la resolución a varios destinatarios, el botón «añadir los que faltan» y el
trámite que no termina mientras falte alguien. Este expediente-tipo recorre la
solicitud hasta **cerrar la fase de resolución**.

Va en la cadena de ADR-049 entre #968 (N5a-2) y #969 (N5a-3): antes de #968 no
existían el botón ni las fuentes; #969 lo usará para comprobar que solo la
notificación al solicitante cumple el plazo del acto.

Escenario: mismo perfil que `CONSULTAS_VARIOS_ESTADOS` y
`REFORMADO_ANALISIS_Y_CONSULTAS` (línea aérea 66 kV en Jerez de la Frontera,
AAP+AAC, exenta de instrumento ambiental) para que el foco quede en la mecánica
de N5, no en variedad administrativa. A diferencia de aquel, aquí las tres
consultas se cierran de verdad:

    Ayuntamiento   silencio, vencido y sin ANALIZAR — conformidad tácita
                   reconocida a mano (Caso A de ADR-011 §6). Sin vía limpia en
                   el catálogo actual: cerrar la fase exige forzar el escape
                   de `editar_fase` (ver #982, detectado al escribir este
                   expediente-tipo; #971 sigue adelante con él, decisión de
                   Carlos).
    ADIF           responde con condicionados dentro de plazo; traslado
                   notificado y aceptado por el titular — cerrado_con_condicionados.
    Diputación     responde favorable dentro de plazo; traslado notificado y
                   aceptado por el titular — cerrado_favorable.

El solicitante actúa **representado** (`solicitudes.representante_entidad_id`,
#967): todo lo que se le notifica —la comunicación de inicio y la resolución—
va a su representante, en su nombre.

Alcance: `ANALISIS_SOLICITUD` y `CONSULTAS` se cierran (`editar_fase`).
`CERT_FIN_INSTRUCCION` se consolida. Se abre `RESOLUCION`: `ELABORACION`
produce la resolución; `NOTIFICACION` se puebla con el botón «añadir las
notificaciones que faltan» (una para el solicitante —a su representante— y una
por cada organismo consultado, sin excluir al del silencio: los tres tienen
fila en `organismos_expediente`) y se cierra cada una con su justificante;
`CERT_CUMPLIMIENTO_FASE` y `CERT_CIERRE_FASE` (con la frase de confirmación)
cierran la fase y resuelven la solicitud.

Circuito real — nunca INSERT SQL directo (ver README.md de esta carpeta):
    - Alta expediente/proyecto/solicitud: `app.services.alta_expediente`.
    - Representante: `mutaciones_arbol.editar_solicitud` (#967, ADR-051 §K).
    - Fase/trámite/tarea y organismos: `app.services.mutaciones_arbol`.
    - Separatas y traslados: `app.services.consultas_organismos`.
    - Cierre de fase: `mutaciones_arbol.editar_fase`.
    - Fin de instrucción y certificados de fase: `cert_fin_instruccion`,
      `cert_cumplimiento_fase`, `cert_cierre_fase` — funciones de servicio
      puras, llamadas directamente (no hay ruta HTTP más simple que el import).
    - Checklist y diagnósticos: endpoints del contenedor de ANALIZAR (ADR-033).

Calendario: ninguna fecha absoluta, todo cuelga de `hoy` hacia atrás igual que
`CONSULTAS_VARIOS_ESTADOS` — ver ese módulo para el porqué del patrón. A
diferencia de aquel, aquí el escenario no se detiene al vencer el plazo del
Ayuntamiento: sigue hacia delante (cierre de fases, resolución, notificaciones,
certificados) con margen de sobra antes de `hoy`. Al terminar, el reloj de
desarrollo se borra: la resolución queda notificada y cerrada «a fecha de hoy».

Reejecutable sin implementar borrado aquí: igual que los demás expedientes-tipo
de esta carpeta (ver README.md).

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/resolucion_con_organismos.py
"""
import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

CODIGO = 'RESOLUCION_CON_ORGANISMOS'
PROPOSITO = (
    'Expediente que llega hasta cerrar la fase RESOLUCION: consultas todas '
    'cerradas (favorable, condicionado con traslado aceptado, y silencio '
    'reconocido), resolución notificada al solicitante representado y a los '
    'tres organismos consultados, con sus certificados de cumplimiento y '
    'cierre de fase.'
)
MARCA = f'[DUMMY:{CODIGO}]'
OBSERVACIONES = f'{MARCA} {PROPOSITO}'

# Ancla del escenario: hoy es el día hábil nº 60 desde que se notificaron las
# separatas — igual que en CONSULTAS_VARIOS_ESTADOS, pero con más margen: aquí
# el escenario sigue después de que venza el plazo del Ayuntamiento (30 días
# hábiles, art. 131.1) hasta cerrar la resolución, y necesita sitio para ello.
HABILES_DESDE_NOTIFICACION_SEPARATAS = 60

# Días naturales entre el alta y la notificación de las separatas: lo que dura
# la fase de análisis documental sin subsanaciones, la comunicación de inicio
# y su cierre, más el paso a consultas. Holgado a propósito.
DIAS_ANALISIS_PREVIO = 15

# Días hábiles ANTES del vencimiento real en que responde cada organismo (ver
# `_comun.fecha_respuesta_en_plazo`). Iguales y generosos para que, tras el
# traslado y su aceptación, quede margen de sobra hasta `hoy` para cerrar
# CONSULTAS, consolidar la instrucción, elaborar y notificar la resolución, y
# emitir los dos certificados de fase.
MARGEN_ADIF_HABILES = 25
MARGEN_DIPUTACION_HABILES = 25
MARGEN_TITULAR_HABILES = 5

# Días hábiles entre recibir la respuesta de un organismo y notificar el
# traslado al titular: el tiempo de leerla y redactar el oficio.
HABILES_HASTA_TRASLADO = 2

# Organismos consultados — mismo trío que CONSULTAS_VARIOS_ESTADOS (#862), con
# desenlaces distintos: aquí los tres cierran.
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

# El representante del solicitante (#967, ADR-051 §K). Entidad de contacto
# ficticia, dominio .example. `rol_titular` porque el alta de /entidades/nueva
# exige al menos un rol y no hay uno propio para "representante" —es un vínculo
# relacional (`solicitudes.representante_entidad_id`), no un rol de catálogo—;
# mismo criterio que usan los tests (`_entidad()` en test_968).
REPRESENTANTE = {
    'nombre_completo': 'Gestoría Administrativa Guadalcacín S.L.',
    'nif': 'B11223344',
    'email': 'gestion@gestoriaguadalcacin.example',
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
    from app.models.tipos_resultados_fases import TipoResultadoFase

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
        'resultado_favorable': TipoResultadoFase.query.filter_by(codigo='FAVORABLE').first(),

        'fase_analisis_solicitud': _fase('ANALISIS_SOLICITUD'),
        'fase_consultas': _fase('CONSULTAS'),
        'fase_resolucion': _fase('RESOLUCION'),

        'tramite_analisis_documental': _tramite('ANALISIS_DOCUMENTAL'),
        'tramite_comunicacion_admision': _tramite('COMUNICACION_INICIO_ADMISION'),
        'tramite_elaboracion': _tramite('ELABORACION'),
        'tramite_notificacion': _tramite('NOTIFICACION'),
        # Los tres trámites de consulta no se crean por despensa: salen de
        # `enviar_consultas` y `crear_traslado`. Se comprueban aquí para
        # abortar con la lista de faltantes si el catálogo está a medias.
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
        # Canal entre administraciones: las separatas y los traslados a
        # organismo, y sus notificaciones de la resolución, van por SIR.
        'doc_justificante_sir': _doc('JUSTIFICANTE_SIR'),

        'doc_separata': _doc('DOC_SEPARATA'),
        'doc_oficio_separata': _doc('OFICIO_SEPARATA'),
        'doc_respuesta_organismo': _doc('RESPUESTA_ORGANISMO'),
        'doc_oficio_traslado_respuesta': _doc('OFICIO_TRASLADO_RESPUESTA'),
        'doc_respuesta_titular': _doc('RESPUESTA_TITULAR'),

        'doc_resolucion': _doc('RESOLUCION'),
    }
    _comun.abortar_si_catalogo_incompleto(cat)
    return cat


# ---------------------------------------------------------------------------
# Organismos y representante: catálogo de entidades, no datos del expediente
# ---------------------------------------------------------------------------

def _asegurar_organismos(client):
    """Da de alta en el catálogo las entidades consultadas que falten, con su
    dirección de notificación, por las rutas reales de `/entidades`.

    Idempotente por NIF. Devuelve {clave: (Entidad, direccion_notificacion_id)}.
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


def _asegurar_representante(client):
    """El representante del solicitante (#967), dado de alta si falta.
    Idempotente por NIF. Devuelve la `Entidad`."""
    from app.models.entidad import Entidad

    entidad = Entidad.query.filter_by(nif=REPRESENTANTE['nif']).first()
    if entidad is not None:
        return entidad

    r = client.post('/entidades/nueva', data={
        'nombre_completo': REPRESENTANTE['nombre_completo'],
        'nif': REPRESENTANTE['nif'],
        'rol_titular': 'on',
        'email': REPRESENTANTE['email'],
        'activo': 'on',
        'notas': f'Representante del solicitante en el expediente-tipo {CODIGO}.',
    }, follow_redirects=True)
    entidad = Entidad.query.filter_by(nif=REPRESENTANTE['nif']).first()
    if entidad is None:
        print(f"ABORTADO: no se pudo dar de alta al representante "
              f"{REPRESENTANTE['nombre_completo']} (HTTP {r.status_code})")
        sys.exit(1)
    print(f"  representante creado: {entidad.nombre_completo} ({entidad.nif}).")
    return entidad


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
        titulo='Línea aérea 66 kV SE Guadalcacín — SE Cartuja (resolución)',
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
    """`editar_tarea` tratando CONSUMIDO como conjunto completo (no aditivo) —
    ver `_comun.notificar` y el hallazgo de #825 que explica por qué."""
    from app.services import mutaciones_arbol as svc

    previos = [d.id for d in tarea.documentos_consumidos]
    ids = list(dict.fromkeys(previos + list(nuevos_ids)))
    return _comun.check(
        svc.editar_tarea(tarea, documentos_consumidos_ids=ids,
                         documento_producido_id=producido_id, notas=None),
        etiqueta)


def main(app=None, *, efectos_desarrollo=True):
    """Construye el expediente-tipo sobre la app que se le pase.

    `efectos_desarrollo=False` es como lo invoca la semilla de la base de
    tests (#849): deja fuera lo que solo tiene sentido en la máquina de
    desarrollo (mover el reloj simulado). El escenario que se construye es
    el mismo.
    """
    from flask_login import login_user
    from app.services import mutaciones_arbol as svc
    from app.services import consultas_organismos as svc_consultas
    from app.services import cert_fin_instruccion, cert_cumplimiento_fase, cert_cierre_fase
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
        representante = _asegurar_representante(client)

        # --- Calendario, derivado del ancla ---------------------------------
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

        # Representante (#967, ADR-051 §K): antes de crear cualquier NOTIFICAR
        # de fuente SOLICITANTE, para que nazca ya dirigida a él.
        _comun.check(
            svc.editar_solicitud(solicitud, observaciones=solicitud.observaciones,
                                 representante_entidad_id=representante.id),
            'fijar representante de la solicitud')

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

        # --- Fase ANALISIS_SOLICITUD, sin defectos, y cierre ----------------
        fase_id = _comun.check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                               'crear_fase ANALISIS_SOLICITUD')
        fase_analisis = Fase.query.get(fase_id)

        tramite_ad_id = _comun.check(
            svc.crear_tramite(fase_analisis, cat['tramite_analisis_documental']),
            'crear_tramite ANALISIS_DOCUMENTAL')
        tramite_ad = Tramite.query.get(tramite_ad_id)

        tarea_analizar_id = _comun.check(
            svc.crear_tarea(tramite_ad, cat['tarea_analizar']), 'crear_tarea ANALIZAR')

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
            fecha_admision, 'Justificante de notificación de la comunicación de inicio al representante')
        _comun.notificar(Tarea.query.get(tarea_com_notif_id), doc_admision_id,
                         doc_justif_admision_id, fecha_admision, 'admisión (al representante)')
        print("COMUNICACION_INICIO_ADMISION: elaborada y notificada al representante.")

        _comun.check(
            svc.editar_fase(fase_analisis, resultado_fase_id=cat['resultado_favorable'].id,
                            documento_resultado_id=doc_diagnostico_id, observaciones=None),
            'cerrar fase ANALISIS_SOLICITUD')
        print("ANALISIS_SOLICITUD: cerrada.")

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
            _editar_conservando_consumidos(
                tarea_esp, [doc_oficio_id], None,
                f'disparar plazo separata {abrev}')
            espera_por_clave[clave] = tarea_esp
            print(f"CONSULTA_SEPARATA {abrev}: elaborada, notificada por SIR y en espera.")

        # --- Ayuntamiento: silencio, conformidad tácita (Caso A ADR-011 §6) -
        # Ni ANALIZAR ni traslado: es justo lo que el caso A no lleva. Su
        # ESPERAR_PLAZO se queda sin documento producido y el plazo vence
        # solo. Sin vía limpia de cierre en el catálogo actual (#982): la
        # consulta se da por buena a mano y el cierre de CONSULTAS más abajo
        # necesita forzar el escape.
        _comun.check(
            svc.editar_organismo(oe_por_clave['ayuntamiento'], via='consulta',
                                 resultado='cerrado_favorable',
                                 direccion_notificacion_id=organismos['ayuntamiento'][1],
                                 documento_id=None),
            'editar_organismo Ayto. Jerez (conformidad tácita)')
        print("CONSULTA_SEPARATA Ayto. Jerez: sin respuesta, plazo vencido — "
              "conformidad tácita reconocida (Caso A, ADR-011 §6).")

        def _responder_organismo(clave, abrev, margen, resultado_analizar, asunto):
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
                fecha_traslado, f'Justificante de notificación del traslado ({abrev}) al representante')
            _comun.notificar(tarea_notif, doc_oficio_id, doc_justif_id, fecha_traslado,
                             f'traslado {abrev}')

            tarea_esp = Tarea.query.get(_comun.check(
                svc.crear_tarea(tramite_tr, cat['tarea_esperar_plazo']),
                f'crear_tarea ESPERAR_PLAZO traslado {abrev}'))
            _editar_conservando_consumidos(
                tarea_esp, [doc_oficio_id], None, f'disparar plazo traslado {abrev}')
            return tramite_tr, tarea_esp

        def _titular_acepta(tarea_esp, abrev, margen):
            fecha = _comun.fecha_respuesta_en_plazo(tarea_esp, f'traslado {abrev}', margen)
            _fijar_reloj(fecha)
            doc_resp_titular_id = _comun.subir(
                client, exp_id, 'RESPUESTA_TITULAR', cat['doc_respuesta_titular'].id,
                fecha, f'El representante acepta la respuesta de {abrev}')
            _editar_conservando_consumidos(
                tarea_esp, [], doc_resp_titular_id, f'cerrar plazo traslado {abrev}')

            tarea_an_tr = Tarea.query.get(_comun.check(
                svc.crear_tarea(tarea_esp.tramite, cat['tarea_analizar']),
                f'crear_tarea ANALIZAR traslado {abrev}'))
            _editar_conservando_consumidos(
                tarea_an_tr, [doc_resp_titular_id], None,
                f'vincular consumido ANALIZAR traslado {abrev}')
            _comun.producir_diagnostico(client, exp_id, tarea_an_tr.id, f'traslado {abrev}',
                                        resultado='favorable')
            return fecha

        # --- ADIF: respuesta con condicionados, ciclo cerrado ---------------
        doc_resp_adif_id, fecha_resp_adif = _responder_organismo(
            'adif', 'ADIF', MARGEN_ADIF_HABILES, 'condicionado',
            'Informe de ADIF: favorable con condicionados técnicos para el cruce ferroviario')
        tramite_tr_adif, espera_adif = _traslado_al_titular(
            'adif', 'ADIF', doc_resp_adif_id, fecha_resp_adif)
        fecha_titular_adif = _titular_acepta(espera_adif, 'ADIF', MARGEN_TITULAR_HABILES)
        _comun.check(
            svc.editar_organismo(oe_por_clave['adif'], via='consulta',
                                 resultado='cerrado_con_condicionados',
                                 direccion_notificacion_id=organismos['adif'][1],
                                 documento_id=None),
            'editar_organismo ADIF (resultado)')
        print("ADIF: respuesta con condicionados, traslado aceptado por el representante — "
              "organismo cerrado_con_condicionados.")

        # --- Diputación: respuesta favorable, ciclo cerrado ------------------
        doc_resp_dip_id, fecha_resp_dip = _responder_organismo(
            'diputacion', 'Dip. Cádiz', MARGEN_DIPUTACION_HABILES, 'favorable',
            'Informe de la Diputación Provincial de Cádiz: favorable al cruce de la '
            'carretera provincial en el trazado propuesto')
        tramite_tr_dip, espera_dip = _traslado_al_titular(
            'diputacion', 'Dip. Cádiz', doc_resp_dip_id, fecha_resp_dip)
        fecha_titular_dip = _titular_acepta(espera_dip, 'Dip. Cádiz', MARGEN_TITULAR_HABILES)
        _comun.check(
            svc.editar_organismo(oe_por_clave['diputacion'], via='consulta',
                                 resultado='cerrado_favorable',
                                 direccion_notificacion_id=organismos['diputacion'][1],
                                 documento_id=None),
            'editar_organismo Dip. Cádiz (resultado)')
        print("Dip. Cádiz: respuesta favorable, traslado aceptado por el representante — "
              "organismo cerrado_favorable.")

        # --- Cierre de CONSULTAS: escape por el silencio del Ayuntamiento ---
        fecha_actual = max(fecha_titular_adif, fecha_titular_dip)
        fecha_actual = _comun.avanzar_habiles(fecha_actual, 1)
        _fijar_reloj(fecha_actual)
        _comun.check(
            svc.editar_fase(
                fase_consultas, resultado_fase_id=cat['resultado_favorable'].id,
                documento_resultado_id=doc_resp_adif_id, observaciones=None,
                justificacion=(
                    'Ayuntamiento de Jerez de la Frontera: conformidad tácita por '
                    'silencio (ADR-011 §6, Caso A). Sin CERT_PLAZO_CUMPLIDO '
                    'catalogado para CONSULTA_SEPARATA — ver #982.'
                )),
            'cerrar fase CONSULTAS (escape: silencio Ayuntamiento)')
        print("CONSULTAS: cerrada (con el escape del Ayuntamiento en bitácora).")

        # --- Fin de instrucción ----------------------------------------------
        fecha_actual = _comun.avanzar_habiles(fecha_actual, 1)
        _fijar_reloj(fecha_actual)
        res_fin = cert_fin_instruccion.consolidar(solicitud)
        if not res_fin.consolidado:
            pendientes = [b.pendiente for b in res_fin.informe.pendientes]
            print(f"ABORTADO: CERT_FIN_INSTRUCCION no se consolidó: "
                  f"{res_fin.error or pendientes}")
            sys.exit(1)
        doc_fin_instruccion_id = res_fin.documento_id
        print(f"CERT_FIN_INSTRUCCION consolidado (documento={doc_fin_instruccion_id}).")

        # --- Fase RESOLUCION: elaboración -------------------------------------
        fase_resolucion_id = _comun.check(
            svc.crear_fase(solicitud, cat['fase_resolucion']), 'crear_fase RESOLUCION')
        fase_resolucion = Fase.query.get(fase_resolucion_id)
        # Resultado fijado ya (D3 de cert_cierre_fase): el cierre real de la
        # fase lo hace CERT_CIERRE_FASE más abajo, no este editar_fase — aquí
        # solo se deja constancia del resultado, sin tocar documento_resultado_id.
        _comun.check(
            svc.editar_fase(fase_resolucion, resultado_fase_id=cat['resultado_favorable'].id,
                            documento_resultado_id=None, observaciones=None),
            'fijar resultado de RESOLUCION')

        fecha_actual = _comun.avanzar_habiles(fecha_actual, 2)
        _fijar_reloj(fecha_actual)

        tramite_elab_id = _comun.check(
            svc.crear_tramite(fase_resolucion, cat['tramite_elaboracion']),
            'crear_tramite ELABORACION')
        tramite_elab = Tramite.query.get(tramite_elab_id)
        tarea_elab_res_id = _comun.check(
            svc.crear_tarea(tramite_elab, cat['tarea_elaborar']), 'crear_tarea ELABORAR resolucion')
        doc_resolucion_id = _comun.subir(
            client, exp_id, 'RESOLUCION', cat['doc_resolucion'].id, fecha_actual,
            'Resolución de autorización administrativa previa y de construcción (AAP+AAC)')
        _editar_conservando_consumidos(
            Tarea.query.get(tarea_elab_res_id), [doc_fin_instruccion_id], doc_resolucion_id,
            'vincular producido ELABORAR resolucion')
        print("RESOLUCION › ELABORACION: resolución elaborada.")

        # --- Fase RESOLUCION: notificación a solicitante y organismos --------
        fecha_actual = _comun.avanzar_habiles(fecha_actual, 2)
        _fijar_reloj(fecha_actual)

        tramite_notif_id = _comun.check(
            svc.crear_tramite(fase_resolucion, cat['tramite_notificacion']),
            'crear_tramite NOTIFICACION')
        tramite_notif = Tramite.query.get(tramite_notif_id)

        # El botón «añadir las notificaciones que faltan» (#968, ADR-051 §D):
        # una NOTIFICAR por SOLICITANTE (al representante, ya fijado arriba) y
        # una por cada organismo de ORGANISMOS_CONSULTADOS — los tres, sin
        # excluir al Ayuntamiento del silencio: tiene fila en
        # `organismos_expediente` igual que los otros dos.
        res_boton = svc.anadir_notificaciones_que_faltan(tramite_notif)
        if not res_boton.ok:
            motivo = res_boton.bloqueo.motivo if res_boton.bloqueo else res_boton.error
            print(f"ABORTADO en anadir_notificaciones_que_faltan: {motivo}")
            sys.exit(1)
        print(f"NOTIFICACION: el botón creó {len(res_boton.creadas)} notificaciones "
              f"({', '.join(str(i) for i in res_boton.creadas)}).")

        from app.models.entidad import Entidad

        for tarea_id in res_boton.creadas:
            tarea = Tarea.query.get(tarea_id)
            fuente = tarea.notificacion.fuente
            if fuente == 'SOLICITANTE':
                doc_justif_id = _comun.subir(
                    client, exp_id, 'JUSTIFICANTE_NOTIFICA', cat['doc_justificante_notifica'].id,
                    fecha_actual, 'Justificante de notificación de la resolución al representante')
                _comun.notificar(tarea, doc_resolucion_id, doc_justif_id, fecha_actual,
                                 'resolución al solicitante (representado)')
            elif fuente == 'ORGANISMOS_CONSULTADOS':
                org = Entidad.query.get(tarea.notificacion.entidad_id)
                doc_justif_id = _comun.subir(
                    client, exp_id, 'JUSTIFICANTE_SIR', cat['doc_justificante_sir'].id,
                    fecha_actual, f'Justificante SIR de notificación de la resolución a '
                                  f'{org.nombre_completo if org else tarea.notificacion.entidad_id}')
                _comun.notificar(tarea, doc_resolucion_id, doc_justif_id, fecha_actual,
                                 f'resolución a {org.nombre_completo if org else "organismo"}',
                                 canal='SIR')
            else:
                print(f"ABORTADO: NOTIFICAR {tarea_id} con fuente {fuente!r} sin regla en "
                      f"este expediente-tipo.")
                sys.exit(1)
        print("NOTIFICACION: todas las notificaciones creadas por el botón, cerradas.")

        # --- Certificados de fase: cumplimiento y cierre ----------------------
        fecha_actual = _comun.avanzar_habiles(fecha_actual, 1)
        _fijar_reloj(fecha_actual)

        res_cumplimiento = cert_cumplimiento_fase.emitir(fase_resolucion)
        if not res_cumplimiento.emitido:
            print(f"ABORTADO: CERT_CUMPLIMIENTO_FASE no se emitió: "
                  f"{res_cumplimiento.error or res_cumplimiento.revision.falta}")
            sys.exit(1)
        print(f"CERT_CUMPLIMIENTO_FASE emitido (documento={res_cumplimiento.documento_id}).")

        res_cierre = cert_cierre_fase.emitir(fase_resolucion, confirmacion='cerrar finalizadora')
        if not res_cierre.emitido:
            pendientes = [b.pendiente for b in res_cierre.informe.pendientes]
            print(f"ABORTADO: CERT_CIERRE_FASE no se emitió: {res_cierre.error or pendientes}")
            sys.exit(1)
        print(f"CERT_CIERRE_FASE emitido (documento={res_cierre.documento_id}) — "
              f"RESOLUCION cerrada, solicitud resuelta.")

        # --- Fin del alcance ---------------------------------------------------
        if efectos_desarrollo:
            reloj_simulado.borrar()

        db.session.expire(fase_resolucion)
        print(f"\nExpediente AT-{expediente.numero_at} (id={exp_id}) completado — "
              f"RESOLUCION cerrada con {len(oe_por_clave)} organismos notificados.")
        return expediente.numero_at, exp_id


if __name__ == '__main__':
    numero_at, exp_id = main()
