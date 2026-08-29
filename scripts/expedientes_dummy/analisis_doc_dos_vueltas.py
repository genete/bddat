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
    - Diagnóstico: app.services.diagnosticos.crear_diagnostico.
    - Documentos: subida multipart real a /expedientes/<id>/documentos/subir
      (banco dummy de tests/fixtures/documentos_dummy/, #814 parte 1),
      incluidos los INTERNO simulados — el pool no distingue cómo entró
      el fichero, solo tipos_documentos.origen clasifica externo/interno.
    - Plazos: reloj de desarrollo (#820), instance/reloj_simulado.txt.

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

from app import create_app, db  # noqa: E402

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


def _check(res, etiqueta):
    if not res.ok:
        motivo = res.bloqueo.motivo or res.bloqueo.norma_compilada if res.bloqueo else res.error
        print(f"ABORTADO en {etiqueta}: {motivo}")
        sys.exit(1)
    return res.ids[0] if res.ids else None


def _avanzar_habiles(fecha_ini: date, n: int) -> date:
    """Replica _sumar_dias_habiles de scripts/reloj_dev.py usando db.session
    (ya en contexto Flask aquí, evita duplicar la conexión psycopg2 aparte)."""
    from datetime import timedelta
    margen = n * 3 + 15
    filas = db.session.execute(db.text(
        "SELECT fecha FROM dias_inhabiles WHERE fecha >= :ini AND fecha <= :fin"
    ), {'ini': fecha_ini, 'fin': fecha_ini + timedelta(days=margen)}).fetchall()
    inhabiles = frozenset(r[0] for r in filas)

    cursor = fecha_ini
    dias = 0
    while dias < n:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in inhabiles:
            dias += 1
    return cursor


def main():
    from flask_login import login_user
    from app.services import mutaciones_arbol as svc
    from app.services import diagnosticos as diag_svc
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
        tarea_analizar0 = Tarea.query.get(tarea_analizar0_id)
        _check(svc.editar_tarea(tarea_analizar0,
                                 documentos_consumidos_ids=[doc_solicitud_id, doc_proyecto_id],
                                 documento_producido_id=None, notas=None),
               'vincular consumidos ANALIZAR inicial')
        doc_diagnostico = diag_svc.crear_diagnostico(
            tarea_analizar0, 'desfavorable',
            [{'descripcion': 'Falta memoria técnica ampliada de la línea subterránea'}],
        )
        print("ANALISIS_DOCUMENTAL: diagnóstico inicial desfavorable.")

        # --- Dos vueltas de REQUERIMIENTO_SUBSANACION -----------------------
        defectos_por_vuelta = [
            [{'descripcion': 'Documentación de subsanación incompleta: falta plano actualizado'}],
            [],  # 2ª vuelta: favorable
        ]
        resultado_por_vuelta = ['desfavorable', 'favorable']
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
            _check(svc.editar_tarea(tarea_elab, documentos_consumidos_ids=[doc_diagnostico.id],
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

            fecha_actual = _avanzar_habiles(fecha_actual, 7)
            reloj_simulado.fijar(fecha_actual)

            doc_subsanacion_id = _subir(client, exp_id, 'SUBSANACION',
                                         cat['doc_subsanacion'].id, fecha_actual,
                                         f'Respuesta a requerimiento #{vuelta}')
            # Cierra el plazo dentro de término: PRODUCIDO = respuesta del titular.
            _check(svc.editar_tarea(tarea_esp, documentos_consumidos_ids=[doc_oficio_id],
                                     documento_producido_id=doc_subsanacion_id, notas=None),
                   f'cerrar plazo ESPERAR_PLAZO #{vuelta}')

            tarea_analizar_id = _check(svc.crear_tarea(tramite_req, cat['tarea_analizar']),
                                        f'crear_tarea ANALIZAR #{vuelta}')
            tarea_analizar = Tarea.query.get(tarea_analizar_id)
            _check(svc.editar_tarea(tarea_analizar, documentos_consumidos_ids=[doc_subsanacion_id],
                                     documento_producido_id=None, notas=None),
                   f'vincular consumido ANALIZAR #{vuelta}')
            doc_diagnostico = diag_svc.crear_diagnostico(
                tarea_analizar, resultado_por_vuelta[vuelta - 1], defectos_por_vuelta[vuelta - 1])
            print(f"REQUERIMIENTO_SUBSANACION #{vuelta}: respuesta dentro de plazo, "
                  f"diagnóstico {resultado_por_vuelta[vuelta - 1]}.")

        # --- COMUNICACION_INICIO_ADMISION -----------------------------------
        tramite_com_id = _check(svc.crear_tramite(fase, cat['tramite_comunicacion_admision']),
                                 'crear_tramite COMUNICACION_INICIO_ADMISION')
        tramite_com = Tramite.query.get(tramite_com_id)

        tarea_com_elab_id = _check(svc.crear_tarea(tramite_com, cat['tarea_elaborar']),
                                    'crear_tarea ELABORAR admision')
        tarea_com_elab = Tarea.query.get(tarea_com_elab_id)
        doc_admision_id = _subir(client, exp_id, 'OFICIO_INICIO_ADMISION',
                                  cat['doc_oficio_inicio_admision'].id, fecha_actual,
                                  'Comunicación de inicio y admisión a trámite')
        # ELABORAR consume el diagnóstico favorable que habilita la admisión.
        _check(svc.editar_tarea(tarea_com_elab, documentos_consumidos_ids=[doc_diagnostico.id],
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
