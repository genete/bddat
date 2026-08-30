"""Expediente de prueba reproducible (#814): ANALISIS_DOC_DOS_VUELTAS.

Propósito: testear el trámite ANALISIS_DOCUMENTAL con dos vueltas de
subsanación, respuesta del titular siempre dentro de plazo, sin fase de
Información Pública / Consultas / figura ambiental (AAP+AAC, proyecto
EXENTO de instrumento ambiental).

Alcance: termina con ANALISIS_SOLICITUD completa y pendiente de cierre. No
abre la fase RESOLUCION —cerrar la fase y resolver es tramitación posterior,
y con el invariante de precedencia de #823 abrirla con la fase anterior sin
cerrar pasa a estar prohibido—.

Circuito real — nunca INSERT SQL directo:
    - Alta expediente/proyecto/solicitud: replica el bloque ORM de
      wizard_expediente.py paso3 (mismo contador atómico numero_at).
    - Fase/trámite/tarea: app.services.mutaciones_arbol (pasa por el motor
      de reglas real, motor_reglas.evaluar).
    - Checklist documental y diagnóstico: endpoints del contenedor de ANALIZAR
      (POST .../requisitos-documentales/<id> y POST .../analizar, ADR-033). El
      sentido del diagnóstico NO se declara: se deriva de lo que quede sin casar
      en el checklist, y los ítems no cubiertos se congelan como defectos. Por
      eso las tareas ANALIZAR no vinculan consumidos a mano — los deriva el
      propio casado de requisitos (ADR-033 §1, #677).
    - Documentos: subida multipart real a /expedientes/<id>/documentos/subir
      (banco dummy de tests/fixtures/documentos_dummy/, #814 parte 1),
      incluidos los INTERNO simulados — el pool no distingue cómo entró
      el fichero, solo tipos_documentos.origen clasifica externo/interno.
    - Plazos: reloj de desarrollo (#820), instance/reloj_simulado.txt. Las
      fechas de respuesta del titular se derivan del vencimiento real que
      calcula plazos.obtener_estado_plazo_tarea, nunca de un número de días
      escrito a mano — ver `_fecha_respuesta_en_plazo`, patrón a copiar en los
      siguientes expedientes-tipo.

Reejecutable sin implementar borrado aquí: si ya existe un expediente
marcado con este código, sus observaciones pasan a '[RECICLAR] ...' (solo
un UPDATE de una columna, sin cascadas) y se crea uno nuevo desde cero. El
borrado real de los expedientes en [RECICLAR] es un script aparte,
genérico, que no necesita conocer expedientes-tipo concretos.

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/analisis_doc_dos_vueltas.py
"""
import io
import json
import sys
from datetime import date

sys.path.insert(0, r"D:\BDDAT")

CODIGO = 'ANALISIS_DOC_DOS_VUELTAS'
PROPOSITO = (
    'Expediente para testear el apartado de análisis documental con '
    'respuesta dentro de plazo y dos vueltas.'
)
MARCA = f'[DUMMY:{CODIGO}]'
OBSERVACIONES = f'{MARCA} {PROPOSITO}'

FIXTURES_DIR = r"D:\BDDAT\tests\fixtures\documentos_dummy"
CATALOGO_CSV = r"D:\BDDAT\tests\fixtures\expedientes_dummy\catalogo_expedientes.csv"

FECHA_BASE = date(2026, 9, 1)

# Días hábiles ANTES del vencimiento real en que responde el titular. El margen
# es lo único fijo del escenario: la fecha sale del plazo que diga el catálogo
# (ver `_fecha_respuesta_en_plazo`), no de un número de días escrito a mano.
MARGEN_RESPUESTA_HABILES = 3

from app import create_app, db  # noqa: E402
from app.services.plazos import obtener_estado_plazo_tarea  # noqa: E402

app = create_app()


# ---------------------------------------------------------------------------
# Catálogo — resuelto por clave natural, nunca PK hardcodeado
# ---------------------------------------------------------------------------

def _cargar_catalogo():
    from app.models.tipos_expedientes import TipoExpediente
    from app.models.tipos_solicitudes import TipoSolicitud
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.models.tipos_tareas import TipoTarea
    from app.models.tipos_documentos import TipoDocumento
    from app.models.tipos_ia import TipoIA
    from app.models.entidad import Entidad
    from app.models.usuarios import Usuario
    from app.models.municipios import Municipio

    def _fase(codigo):
        return TipoFase.query.filter_by(codigo=codigo).first()

    def _tramite(codigo):
        return TipoTramite.query.filter_by(codigo=codigo).first()

    def _tarea(codigo):
        return TipoTarea.query.filter_by(codigo=codigo).first()

    def _doc(codigo):
        return TipoDocumento.query.filter_by(codigo=codigo).first()

    cat = {
        'tipo_expediente': TipoExpediente.query.filter_by(tipo='Distribución').first(),
        'tipo_solicitud': TipoSolicitud.query.filter_by(siglas='AAP+AAC').first(),
        'ia_exento': TipoIA.query.filter_by(siglas='EXENTO').first(),
        'entidad': Entidad.query.filter_by(nif='A28023430').first(),
        'usuario': Usuario.query.filter_by(siglas='CLG').first(),
        'municipio': Municipio.query.filter_by(nombre='Mairena del Aljarafe').first(),

        'fase_analisis_solicitud': _fase('ANALISIS_SOLICITUD'),

        'tramite_analisis_documental': _tramite('ANALISIS_DOCUMENTAL'),
        'tramite_requerimiento': _tramite('REQUERIMIENTO_SUBSANACION'),
        'tramite_comunicacion_admision': _tramite('COMUNICACION_INICIO_ADMISION'),

        'tarea_analizar': _tarea('ANALIZAR'),
        'tarea_elaborar': _tarea('ELABORAR'),
        'tarea_notificar': _tarea('NOTIFICAR'),
        'tarea_esperar_plazo': _tarea('ESPERAR_PLAZO'),

        'doc_modelo_solicitud': _doc('MODELO_SOLICITUD'),
        'doc_proyecto': _doc('DOC_PROYECTO'),
        # Anexos que el titular aporta en las vueltas de subsanación: cada uno
        # cubre un requisito del checklist documental (#495). La clave sigue el
        # patrón doc_<codigo en minúsculas> — `aportes_por_vuelta` la compone así.
        'doc_nif_titular': _doc('NIF_TITULAR'),
        'doc_escrituras_sociedad': _doc('ESCRITURAS_SOCIEDAD'),
        'doc_poder_representacion': _doc('PODER_REPRESENTACION'),
        'doc_modelo_046': _doc('MODELO_046'),
        'doc_modelo_909': _doc('MODELO_909'),
        'doc_oficio_requerimiento': _doc('OFICIO_REQUERIMIENTO'),
        'doc_subsanacion': _doc('SUBSANACION'),
        'doc_oficio_inicio_admision': _doc('OFICIO_INICIO_ADMISION'),
        'doc_justificante_pago_tasa': _doc('JUSTIFICANTE_PAGO_TASA'),
        'doc_justificante_notifica': _doc('JUSTIFICANTE_NOTIFICA'),
    }
    faltantes = [k for k, v in cat.items() if v is None]
    if faltantes:
        print(f"ABORTADO: catálogo incompleto, faltan: {faltantes}")
        sys.exit(1)
    return cat


# ---------------------------------------------------------------------------
# Reciclaje del expediente anterior (marca, sin borrado)
# ---------------------------------------------------------------------------

def _reciclar_si_existe():
    from app.models.solicitudes import Solicitud
    anterior = Solicitud.query.filter(Solicitud.observaciones.like(f'{MARCA}%')).first()
    if anterior is None:
        print("No hay expediente previo con esta marca — se crea desde cero.")
        return
    numero_at = anterior.expediente.numero_at
    anterior.observaciones = f'[RECICLAR] {anterior.observaciones}'
    db.session.commit()
    print(f"Expediente previo AT-{numero_at} marcado [RECICLAR] (sin borrar).")


# ---------------------------------------------------------------------------
# Alta expediente/proyecto/solicitud — replica wizard_expediente.py paso3
# ---------------------------------------------------------------------------

def _crear_expediente(cat):
    from app.models.proyectos import Proyecto
    from app.models.municipios_proyecto import MunicipioProyecto
    from app.models.expedientes import Expediente
    from app.models.solicitudes import Solicitud

    proyecto = Proyecto(
        titulo='Línea subterránea 20 kV Ronda Sur — CT asociado',
        descripcion=(
            'Nueva línea subterránea de distribución 20 kV y centro de '
            'transformación asociado, íntegramente en suelo urbano.'
        ),
        fecha=FECHA_BASE,
        finalidad='Distribución de energía eléctrica en baja/media tensión',
        emplazamiento='T.M. de Mairena del Aljarafe (Sevilla)',
        ia_id=cat['ia_exento'].id,
        es_modificacion=False,
        sin_linea_aerea=True,
        max_tension_nominal_kv=20,
        solo_suelo_urbano_urbanizable=True,
    )
    db.session.add(proyecto)
    db.session.flush()

    db.session.add(MunicipioProyecto(municipio_id=cat['municipio'].id, proyecto_id=proyecto.id))

    numero_at = db.session.execute(
        db.text("UPDATE public.contador_numero_at SET valor = valor + 1 RETURNING valor")
    ).scalar()

    expediente = Expediente(
        numero_at=numero_at,
        responsable_id=cat['usuario'].id,
        tipo_expediente_id=cat['tipo_expediente'].id,
        heredado=False,
        proyecto_id=proyecto.id,
        titular_id=cat['entidad'].id,
    )
    db.session.add(expediente)
    db.session.flush()

    solicitud = Solicitud(
        expediente_id=expediente.id,
        entidad_id=cat['entidad'].id,
        tipo_solicitud_id=cat['tipo_solicitud'].id,
        observaciones=OBSERVACIONES,
    )
    db.session.add(solicitud)
    db.session.commit()

    print(f"Expediente AT-{numero_at} creado (id={expediente.id}, solicitud={solicitud.id}).")
    return expediente, solicitud


# ---------------------------------------------------------------------------
# Subida de documentos dummy (multipart real, ADR-032)
# ---------------------------------------------------------------------------

def _subir(client, expediente_id, codigo_tipo_doc, tipo_doc_id, fecha_admin, asunto):
    ruta = f"{FIXTURES_DIR}\\{codigo_tipo_doc.lower()}.pdf"
    with open(ruta, 'rb') as f:
        contenido = f.read()
    r = client.post(
        f'/expedientes/{expediente_id}/documentos/subir',
        data={
            'ficheros': (io.BytesIO(contenido), f'{codigo_tipo_doc.lower()}.pdf'),
            'metadatos': json.dumps([{
                'tipo_doc_id': tipo_doc_id,
                'fecha_administrativa': fecha_admin.isoformat(),
                'asunto': asunto,
                'prioridad': False,
            }]),
        },
        content_type='multipart/form-data',
    )
    body = r.get_json()
    if not body or not body.get('ok'):
        print(f"ABORTADO: fallo al subir {codigo_tipo_doc}: {body}")
        sys.exit(1)
    return body['documentos'][0]['id']


# ---------------------------------------------------------------------------
# Helpers de mutación con comprobación de bloqueo
# ---------------------------------------------------------------------------

def _cubrir_requisito_tasa(solicitud, doc_tasa_id):
    """Vincula el justificante de pago al requisito documental de la tasa
    (art. 45.1 Ley 10/2021) — bloquea cualquier fase tras ANALISIS_SOLICITUD
    si no está cubierto (variable de motor 'tasa_impagada', calculado.py:287).
    Replica app/routes/api_expedientes.py:vincular_requisito_documental (ahí
    la ruta exige un tarea_id de contexto que aquí no aplica — es un simple
    upsert de DocumentoRequisito, sin motor de por medio)."""
    from app.models.requisitos_documentales import RequisitoDocumental, DocumentoRequisito
    from app.models.tipos_documentos import TipoDocumento

    requisito = (
        RequisitoDocumental.query
        .join(TipoDocumento)
        .filter(TipoDocumento.codigo == 'JUSTIFICANTE_PAGO_TASA',
                RequisitoDocumental.activo.is_(True))
        .first()
    )
    if requisito is None:
        print("ABORTADO: no hay RequisitoDocumental activo para JUSTIFICANTE_PAGO_TASA")
        sys.exit(1)
    db.session.add(DocumentoRequisito(
        requisito_id=requisito.id, solicitud_id=solicitud.id, documento_id=doc_tasa_id,
    ))
    db.session.commit()
    print("Requisito de pago de tasa cubierto.")


def _actualizar_catalogo(numero_at):
    """Reescribe (o añade) la fila de este expediente-tipo en el catálogo
    compartido. El CSV describe para qué sirve el expediente, no lo que
    generó — el expediente siempre se recrea, así que el numero_at es el
    único dato que cambia entre ejecuciones."""
    import csv
    import os

    columnas = ['codigo', 'proposito', 'numero_at_actual', 'fecha_ultima_generacion']
    filas = []
    if os.path.isfile(CATALOGO_CSV):
        with open(CATALOGO_CSV, encoding='utf-8') as f:
            filas = [f for f in csv.DictReader(f) if f['codigo'] != CODIGO]

    filas.append({
        'codigo': CODIGO,
        'proposito': PROPOSITO,
        'numero_at_actual': str(numero_at),
        'fecha_ultima_generacion': date.today().isoformat(),
    })
    filas.sort(key=lambda f: f['codigo'])

    os.makedirs(os.path.dirname(CATALOGO_CSV), exist_ok=True)
    with open(CATALOGO_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)
    print(f"Catálogo de expedientes-tipo actualizado: {CATALOGO_CSV}")


def _requisito_id(codigo_tipo_doc: int) -> int:
    """`RequisitoDocumental.id` activo para un código de tipo de documento."""
    from app.models.requisitos_documentales import RequisitoDocumental
    from app.models.tipos_documentos import TipoDocumento

    req = (
        RequisitoDocumental.query
        .join(TipoDocumento)
        .filter(TipoDocumento.codigo == codigo_tipo_doc,
                RequisitoDocumental.activo.is_(True))
        .first()
    )
    if req is None:
        print(f"ABORTADO: no hay RequisitoDocumental activo para {codigo_tipo_doc}")
        sys.exit(1)
    return req.id


def _casar_requisitos(client, exp_id, tarea_analizar_id, pares, etiqueta):
    """Casa documentos del pool con sus requisitos documentales por el circuito
    real (`POST .../requisitos-documentales/<id>`, #495).

    `pares`: [(codigo_tipo_doc, documento_id), ...].

    Esto es lo que alimenta el checklist del contenedor de ANALIZAR: lo que
    quede sin casar se convierte en defecto documental del diagnóstico
    (`consolidar_defectos`), y el resultado se deriva de ahí. Casar también
    deriva los vínculos CONSUMIDO de la tarea (ADR-033 §1, #677) — por eso el
    script NO los vincula a mano en las tareas ANALIZAR extendidas: la
    sincronización liberaría cualquier consumido que no venga de un requisito.
    """
    for codigo, doc_id in pares:
        r = client.post(
            f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_analizar_id}'
            f'/requisitos-documentales/{_requisito_id(codigo)}',
            json={'documento_id': doc_id},
        )
        body = r.get_json() or {}
        if not body.get('ok'):
            print(f"ABORTADO al casar {codigo} en {etiqueta}: {body}")
            sys.exit(1)
    print(f"  checklist {etiqueta}: casados {', '.join(c for c, _ in pares)}.")


def _producir_diagnostico(client, exp_id, tarea_analizar_id, etiqueta):
    """Produce el diagnóstico por el circuito real (`POST .../analizar`, ADR-033).

    No manda `resultado`: en ANALIZAR extendido (ANALISIS_DOCUMENTAL y
    REQUERIMIENTO_SUBSANACION) el sentido no se elige, se deriva del borrador
    consolidado —favorable si no queda ningún defecto, desfavorable si queda
    alguno— y el endpoint ignora lo que mande el cliente. Los ítems no cubiertos
    del checklist quedan congelados en `Diagnostico.defectos` con su cita
    normativa y su `requisito_id` (#724).

    Devuelve el `documento_id` del diagnóstico, que el ELABORAR del requerimiento
    siguiente consume.
    """
    r = client.post(f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_analizar_id}/analizar',
                    json={})
    body = r.get_json() or {}
    if not body.get('ok'):
        print(f"ABORTADO al producir el diagnóstico de {etiqueta}: {body}")
        sys.exit(1)

    doc_id = body['documento']['id']
    from app.models.documentos import Documento
    diag = Documento.query.get(doc_id).diagnostico
    print(f"  diagnóstico {etiqueta}: {diag.resultado} "
          f"({len(diag.defectos or [])} defecto(s) congelado(s)).")
    return doc_id


def _check(res, etiqueta):
    if not res.ok:
        motivo = res.bloqueo.motivo or res.bloqueo.norma_compilada if res.bloqueo else res.error
        print(f"ABORTADO en {etiqueta}: {motivo}")
        sys.exit(1)
    return res.ids[0] if res.ids else None


def _inhabiles_entre(desde: date, hasta: date) -> frozenset:
    """Días inhábiles de BD en el intervalo, para el cómputo local del script."""
    filas = db.session.execute(db.text(
        "SELECT fecha FROM dias_inhabiles WHERE fecha >= :ini AND fecha <= :fin"
    ), {'ini': desde, 'fin': hasta}).fetchall()
    return frozenset(r[0] for r in filas)


def _avanzar_habiles(fecha_ini: date, n: int) -> date:
    """Replica _sumar_dias_habiles de scripts/reloj_dev.py usando db.session
    (ya en contexto Flask aquí, evita duplicar la conexión psycopg2 aparte)."""
    from datetime import timedelta
    inhabiles = _inhabiles_entre(fecha_ini, fecha_ini + timedelta(days=n * 3 + 15))

    cursor = fecha_ini
    dias = 0
    while dias < n:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in inhabiles:
            dias += 1
    return cursor


def _retroceder_habiles(fecha_fin: date, n: int) -> date:
    """Inverso de `_avanzar_habiles`: n días hábiles hacia atrás desde `fecha_fin`."""
    from datetime import timedelta
    inhabiles = _inhabiles_entre(fecha_fin - timedelta(days=n * 3 + 15), fecha_fin)

    cursor = fecha_fin
    dias = 0
    while dias < n:
        cursor -= timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in inhabiles:
            dias += 1
    return cursor


def _fecha_respuesta_en_plazo(tarea_espera, etiqueta: str) -> date:
    """Fecha en la que responde el titular, derivada del plazo REAL de la tarea.

    PATRÓN para los expedientes-tipo (copiar esto, no un número de días): la
    fecha se calcula desde el vencimiento que devuelve el propio servicio de
    plazos para esta ESPERAR_PLAZO —la entrada de `catalogo_plazos` que le
    corresponde por camino y condiciones, con su valor y su unidad— retrocediendo
    `MARGEN_RESPUESTA_HABILES`. Un "+7 días hábiles" fijo diría "dentro de plazo"
    solo por casualidad: si mañana esa entrada pasa de 10 días hábiles a 5, o a
    meses, el escenario dejaría de ser el que dice ser sin que nada avise.

    Llamar DESPUÉS de vincular el documento CONSUMIDO que dispara el plazo; sin
    disparo el servicio devuelve SIN_PLAZO y aquí se aborta en vez de inventar
    una fecha. Para el escenario inverso (responde fuera de plazo) basta avanzar
    desde `fecha_limite` en lugar de retroceder.
    """
    estado = obtener_estado_plazo_tarea(tarea_espera)
    if estado.fecha_limite is None:
        print(f"ABORTADO: la ESPERAR_PLAZO de {etiqueta} no tiene plazo aplicable en "
              f"catálogo (estado {estado.estado}); no se puede situar la respuesta.")
        sys.exit(1)

    fecha = _retroceder_habiles(estado.fecha_limite, MARGEN_RESPUESTA_HABILES)
    if estado.fecha_disparo and fecha <= estado.fecha_disparo:
        # Plazo más corto que el margen: la respuesta va al día hábil siguiente
        # al disparo, que sigue estando dentro de plazo.
        fecha = _avanzar_habiles(estado.fecha_disparo, 1)
    print(f"  plazo {etiqueta}: {estado.plazo_valor} {estado.plazo_unidad} "
          f"({estado.norma_origen}) — disparo {estado.fecha_disparo}, "
          f"vence {estado.fecha_limite}, responde {fecha}.")
    return fecha


def main():
    from flask_login import login_user
    from app.services import mutaciones_arbol as svc
    from app.services import reloj_simulado
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea
    from app.models.notificaciones import Notificacion

    def _notificar(tarea_notif, doc_consumido_id, doc_justificante_id, fecha, etiqueta):
        """Cierra NOTIFICAR de verdad — vincula el justificante como PRODUCIDO
        y registra la Notificacion (ADR-034) con resultado CORRECTA.

        El hook automático (_hook_657_notificar_resultado, mutaciones_arbol.py)
        no basta aquí: solo actúa sobre justificantes NOTIFICA parseables de
        verdad (parsear_documento_notifica). Un PDF dummy nunca lo es, así que
        replica a mano el "Registrar puesta a disposición" + "Registrar
        notificación" manuales (api_expedientes.py POST+PATCH
        /nodo/tarea/<id>/notificar) — sin esto la tarea queda en
        PENDIENTE_NOTIFICAR (#814, hallazgo de revisión) y nada en el motor
        actual lo impide (ver nota HUECO_NOTIFICAR_SIN_RESOLVER más abajo)."""
        _check(svc.editar_tarea(tarea_notif, documentos_consumidos_ids=[doc_consumido_id],
                                 documento_producido_id=doc_justificante_id, notas=None),
               f'vincular producido NOTIFICAR {etiqueta}')
        notif = Notificacion.query.filter_by(tarea_id=tarea_notif.id).first()
        if notif is None:
            notif = Notificacion(tarea_id=tarea_notif.id)
            db.session.add(notif)
        notif.documento_id = doc_justificante_id
        notif.canal = 'NOTIFICA'
        notif.fecha_puesta_disposicion = fecha
        notif.resultado = 'CORRECTA'
        notif.fecha_resultado = fecha
        notif.numero_intento = 1
        db.session.commit()

    with app.test_request_context():
        cat = _cargar_catalogo()
        _reciclar_si_existe()
        reloj_simulado.fijar(FECHA_BASE)

        login_user(cat['usuario'])

        client = app.test_client()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(cat['usuario'].id)
            sess['_fresh'] = True
            rol = cat['usuario'].roles[0] if cat['usuario'].roles else None
            if rol:
                sess['rol_activo_id'] = rol.id
                sess['rol_activo_nombre'] = rol.nombre

        expediente, solicitud = _crear_expediente(cat)
        exp_id = expediente.id

        doc_solicitud_id = _subir(client, exp_id, 'MODELO_SOLICITUD',
                                   cat['doc_modelo_solicitud'].id, FECHA_BASE,
                                   'Solicitud de AAP+AAC')
        doc_proyecto_id = _subir(client, exp_id, 'DOC_PROYECTO',
                                  cat['doc_proyecto'].id, FECHA_BASE,
                                  'Proyecto técnico')
        doc_tasa_id = _subir(client, exp_id, 'JUSTIFICANTE_PAGO_TASA',
                              cat['doc_justificante_pago_tasa'].id, FECHA_BASE,
                              'Justificante de pago de la tasa')
        _cubrir_requisito_tasa(solicitud, doc_tasa_id)

        # --- Fase ANALISIS_SOLICITUD ---------------------------------------
        fase_id = _check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                          'crear_fase ANALISIS_SOLICITUD')
        fase = Fase.query.get(fase_id)

        tramite_ad_id = _check(svc.crear_tramite(fase, cat['tramite_analisis_documental']),
                                'crear_tramite ANALISIS_DOCUMENTAL')
        tramite_ad = Tramite.query.get(tramite_ad_id)

        tarea_analizar0_id = _check(svc.crear_tarea(tramite_ad, cat['tarea_analizar']),
                                     'crear_tarea ANALIZAR inicial')
        # Lo presentado con la solicitud. El resto de requisitos aplicables queda
        # sin casar → son los defectos del primer diagnóstico. La tasa se vuelve a
        # casar aquí aunque ya lo estuviera (`_cubrir_requisito_tasa`, upsert
        # idempotente): es esta llamada la que deriva su vínculo CONSUMIDO.
        _casar_requisitos(client, exp_id, tarea_analizar0_id, [
            ('MODELO_SOLICITUD', doc_solicitud_id),
            ('DOC_PROYECTO', doc_proyecto_id),
            ('JUSTIFICANTE_PAGO_TASA', doc_tasa_id),
        ], 'presentación')
        doc_diagnostico_id = _producir_diagnostico(client, exp_id, tarea_analizar0_id,
                                                    'ANALISIS_DOCUMENTAL')

        # --- Dos vueltas de REQUERIMIENTO_SUBSANACION -----------------------
        # Qué aporta el titular en cada vuelta: la 1ª deja el checklist aún
        # incompleto (segundo requerimiento), la 2ª lo completa (favorable).
        # El sentido del diagnóstico NO se declara aquí — lo deriva el motor de
        # lo que quede sin casar.
        aportes_por_vuelta = [
            [('NIF_TITULAR', 'NIF del titular'),
             ('ESCRITURAS_SOCIEDAD', 'Escritura de constitución de la sociedad'),
             ('PODER_REPRESENTACION', 'Poder de representación')],
            [('MODELO_046', 'Modelo 046 de autoliquidación de tasa'),
             ('MODELO_909', 'Modelo 909 carta de pago')],
        ]
        fecha_actual = FECHA_BASE

        for vuelta in (1, 2):
            tramite_req_id = _check(svc.crear_tramite(fase, cat['tramite_requerimiento']),
                                     f'crear_tramite REQUERIMIENTO_SUBSANACION #{vuelta}')
            tramite_req = Tramite.query.get(tramite_req_id)

            tarea_elab_id = _check(svc.crear_tarea(tramite_req, cat['tarea_elaborar']),
                                    f'crear_tarea ELABORAR #{vuelta}')
            tarea_elab = Tarea.query.get(tarea_elab_id)
            doc_oficio_id = _subir(client, exp_id, 'OFICIO_REQUERIMIENTO',
                                    cat['doc_oficio_requerimiento'].id, fecha_actual,
                                    f'Requerimiento de subsanación #{vuelta}')
            # ELABORAR consume el diagnóstico que motiva este requerimiento.
            _check(svc.editar_tarea(tarea_elab, documentos_consumidos_ids=[doc_diagnostico_id],
                                     documento_producido_id=doc_oficio_id, notas=None),
                   f'vincular producido ELABORAR #{vuelta}')

            tarea_notif_id = _check(svc.crear_tarea(tramite_req, cat['tarea_notificar']),
                                     f'crear_tarea NOTIFICAR #{vuelta}')
            tarea_notif = Tarea.query.get(tarea_notif_id)
            doc_justif_id = _subir(client, exp_id, 'JUSTIFICANTE_NOTIFICA',
                                    cat['doc_justificante_notifica'].id, fecha_actual,
                                    f'Justificante de notificación del requerimiento #{vuelta}')
            _notificar(tarea_notif, doc_oficio_id, doc_justif_id, fecha_actual, f'req.#{vuelta}')

            tarea_esp_id = _check(svc.crear_tarea(tramite_req, cat['tarea_esperar_plazo']),
                                   f'crear_tarea ESPERAR_PLAZO #{vuelta}')
            tarea_esp = Tarea.query.get(tarea_esp_id)
            # Dispara el plazo: CONSUMIDO = oficio ya notificado (catalogo_plazos id=5).
            _check(svc.editar_tarea(tarea_esp, documentos_consumidos_ids=[doc_oficio_id],
                                     documento_producido_id=None, notas=None),
                   f'disparar plazo ESPERAR_PLAZO #{vuelta}')

            # Fecha derivada del plazo real de la tarea, no de un número fijo.
            fecha_actual = _fecha_respuesta_en_plazo(tarea_esp, f'req.#{vuelta}')
            reloj_simulado.fijar(fecha_actual)

            doc_subsanacion_id = _subir(client, exp_id, 'SUBSANACION',
                                         cat['doc_subsanacion'].id, fecha_actual,
                                         f'Respuesta a requerimiento #{vuelta}')
            # Cierra el plazo dentro de término: PRODUCIDO = respuesta del titular.
            _check(svc.editar_tarea(tarea_esp, documentos_consumidos_ids=[doc_oficio_id],
                                     documento_producido_id=doc_subsanacion_id, notas=None),
                   f'cerrar plazo ESPERAR_PLAZO #{vuelta}')

            # Anexos que acompañan al escrito de subsanación: son los que casan
            # con los requisitos que faltaban.
            aportados = []
            for codigo, asunto in aportes_por_vuelta[vuelta - 1]:
                doc_anexo_id = _subir(client, exp_id, codigo, cat[f'doc_{codigo.lower()}'].id,
                                       fecha_actual, f'{asunto} (subsanación #{vuelta})')
                aportados.append((codigo, doc_anexo_id))

            tarea_analizar_id = _check(svc.crear_tarea(tramite_req, cat['tarea_analizar']),
                                        f'crear_tarea ANALIZAR #{vuelta}')
            # Sin vincular consumidos a mano: los deriva el casado de requisitos.
            _casar_requisitos(client, exp_id, tarea_analizar_id, aportados,
                              f'subsanación #{vuelta}')
            doc_diagnostico_id = _producir_diagnostico(client, exp_id, tarea_analizar_id,
                                                        f'REQUERIMIENTO_SUBSANACION #{vuelta}')
            print(f"REQUERIMIENTO_SUBSANACION #{vuelta}: respuesta dentro de plazo.")

        # --- COMUNICACION_INICIO_ADMISION -----------------------------------
        tramite_com_id = _check(svc.crear_tramite(fase, cat['tramite_comunicacion_admision']),
                                 'crear_tramite COMUNICACION_INICIO_ADMISION')
        tramite_com = Tramite.query.get(tramite_com_id)

        tarea_com_elab_id = _check(svc.crear_tarea(tramite_com, cat['tarea_elaborar']),
                                    'crear_tarea ELABORAR admision')
        tarea_com_elab = Tarea.query.get(tarea_com_elab_id)
        # El hook automático de #776 ya vinculó aquí, al crear la tarea, el documento
        # que dispara el plazo del art. 21.4 (documento_disparo_comunicacion_admision,
        # #825). Hay que conservarlo: editar_tarea trata documentos_consumidos_ids como
        # el conjunto CONSUMIDO deseado completo (no aditivo) — si no se repite aquí,
        # se libera y el plazo de esta tarea queda SIN_PLAZO (hallazgo #825).
        ids_consumidos_previos = [d.id for d in tarea_com_elab.documentos_consumidos]
        doc_admision_id = _subir(client, exp_id, 'OFICIO_INICIO_ADMISION',
                                  cat['doc_oficio_inicio_admision'].id, fecha_actual,
                                  'Comunicación de inicio y admisión a trámite')
        # ELABORAR consume el diagnóstico favorable que habilita la admisión, además
        # del documento de disparo del plazo que ya trae de la línea anterior.
        _check(svc.editar_tarea(
            tarea_com_elab,
            documentos_consumidos_ids=list(dict.fromkeys(ids_consumidos_previos + [doc_diagnostico_id])),
            documento_producido_id=doc_admision_id, notas=None),
               'vincular producido ELABORAR admision')

        tarea_com_notif_id = _check(svc.crear_tarea(tramite_com, cat['tarea_notificar']),
                                     'crear_tarea NOTIFICAR admision')
        tarea_com_notif = Tarea.query.get(tarea_com_notif_id)
        doc_justif_admision_id = _subir(client, exp_id, 'JUSTIFICANTE_NOTIFICA',
                                         cat['doc_justificante_notifica'].id, fecha_actual,
                                         'Justificante de notificación de la comunicación de inicio')
        _notificar(tarea_com_notif, doc_admision_id, doc_justif_admision_id, fecha_actual, 'admision')
        print("COMUNICACION_INICIO_ADMISION: elaborada y notificada (Notificacion CORRECTA).")

        # --- Fin del alcance -------------------------------------------------
        # El expediente-tipo acaba aquí: ANALISIS_SOLICITUD queda completa y
        # pendiente de cierre (todos sus trámites finalizados, sin
        # documento_resultado_id). Cerrar la fase y abrir RESOLUCION es
        # tramitación posterior — y abrirla con la fase anterior sin cerrar
        # pasa a estar prohibido con el invariante de precedencia de #823.
        db.session.expire(fase)
        estado_fase = 'pendiente de cierre' if fase.pdte_cierre else 'en curso'
        print(f"Fase ANALISIS_SOLICITUD {estado_fase} — fin del alcance del script.")

        _actualizar_catalogo(expediente.numero_at)

        print(f"\nExpediente AT-{expediente.numero_at} (id={exp_id}) completado.")
        return expediente.numero_at, exp_id


# ---------------------------------------------------------------------------
# HUECO_PRECEDENCIA_AL_CREAR (#814 → implementación en #823, no implementado):
#
# Recorrer este circuito con todos los documentos disponibles de golpe —cosa
# que en la vida real no ocurre: el justificante no existe hasta que llega del
# sistema de notificaciones— destapó que nada comprueba la precedencia al
# crear un nodo del árbol. check_invariante no tiene rama CREAR (solo BORRAR/
# FINALIZAR/MUTAR/REABRIR) y crear_fase/crear_tramite/crear_tarea solo miran
# el sellado de fase cerrada (#720) antes de consultar el motor.
#
# Verificado sobre AT-15 (conservado a propósito en BD de desarrollo): se creó
# ESPERAR_PLAZO con su NOTIFICAR en curso, un 2º REQUERIMIENTO_SUBSANACION con
# el 1º en curso, y la fase RESOLUCION con ANALISIS_SOLICITUD sin finalizar —
# sin usar `justificacion` en ningún punto.
#
# No hace falta ninguna variable de motor nueva: Tramite.finalizado ya devuelve
# False tanto si falta el documento producido como si un NOTIFICAR está
# ejecutado sin resultado CORRECTA, y Fase.finalizada/pdte_cierre hacen lo
# propio un nivel arriba. Análisis y decisiones de diseño: #814, apartado
# HUECO_PRECEDENCIA_AL_CREAR.
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    numero_at, exp_id = main()
