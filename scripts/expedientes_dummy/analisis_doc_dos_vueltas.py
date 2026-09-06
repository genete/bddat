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
    - Alta expediente/proyecto/solicitud: `app.services.alta_expediente`, el mismo
      servicio que usa el formulario de alta (#428). Antes replicaba a mano el
      bloque ORM del wizard, y la copia se quedó atrás: ninguna de las dos escribía
      el ancla documental de la solicitud, así que el expediente-tipo nacía con el
      plazo del art. 128 en SIN_PLAZO. El escrito de solicitud entra ahora con el
      alta, y es el mismo documento que después cubre su requisito en el checklist.
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
      escrito a mano — ver `_comun.fecha_respuesta_en_plazo`, patrón compartido
      por todos los expedientes-tipo.
    - Calendario: ninguna fecha absoluta. El escenario se ancla en hoy menos lo
      que dura (`_fecha_base`) y termina en el pasado reciente, así que ninguno
      de sus documentos nace con fecha futura —que desde #824 es un invariante
      del modelo, no una convención— y el expediente-tipo no envejece.

Reejecutable sin implementar borrado aquí: si ya existe un expediente
marcado con este código, sus observaciones pasan a '[RECICLAR] ...' (solo
un UPDATE de una columna, sin cascadas) y se crea uno nuevo desde cero. El
borrado real de los expedientes en [RECICLAR] es un script aparte,
genérico, que no necesita conocer expedientes-tipo concretos.

Uso:
    venv/Scripts/python.exe scripts/expedientes_dummy/analisis_doc_dos_vueltas.py
"""
import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

CODIGO = 'ANALISIS_DOC_DOS_VUELTAS'
PROPOSITO = (
    'Expediente para testear el apartado de análisis documental con '
    'respuesta dentro de plazo y dos vueltas.'
)
MARCA = f'[DUMMY:{CODIGO}]'
OBSERVACIONES = f'{MARCA} {PROPOSITO}'

# Días naturales que dura el escenario completo: dos vueltas de requerimiento
# (10 días hábiles de plazo, respondidas 3 hábiles antes de vencer) son unos 20,
# y el resto es holgura para tramos con muchos festivos. Solo tiene que ser
# suficiente: sobrar unos días acerca o aleja el expediente en el calendario,
# quedarse corto lo empujaría más allá de hoy.
DIAS_ESCENARIO = 45


def _fecha_base() -> date:
    """Ancla del escenario: hoy menos lo que dura, para que el expediente termine
    en el pasado reciente y ninguna de sus fechas nazca futura (#824).

    De `date.today()` y no de `reloj_simulado.hoy()` a propósito: el reloj casi
    siempre viene de la ejecución anterior de este mismo script —lo deja fijado
    en la última fecha del expediente—, así que anclarse a él congelaría el
    expediente-tipo en el calendario del día en que se generó por primera vez.
    """
    return date.today() - timedelta(days=DIAS_ESCENARIO)


FECHA_BASE = _fecha_base()

# Días hábiles ANTES del vencimiento real en que responde el titular. El margen
# es lo único fijo del escenario: la fecha sale del plazo que diga el catálogo
# (ver `_comun.fecha_respuesta_en_plazo`), no de un número de días escrito a mano.
MARGEN_RESPUESTA_HABILES = 3

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
        'municipio': Municipio.query.filter_by(nombre='Mairena del Aljarafe').first(),

        'fase_analisis_solicitud': _fase('ANALISIS_SOLICITUD'),

        'tramite_analisis_documental': _tramite('ANALISIS_DOCUMENTAL'),
        'tramite_requerimiento': _tramite('REQUERIMIENTO_SUBSANACION'),
        'tramite_comunicacion_admision': _tramite('COMUNICACION_INICIO_ADMISION'),

        'tarea_analizar': _tarea('ANALIZAR'),
        'tarea_elaborar': _tarea('ELABORAR'),
        'tarea_notificar': _tarea('NOTIFICAR'),
        'tarea_esperar_plazo': _tarea('ESPERAR_PLAZO'),

        # Ya no se usa para subir nada —lo resuelve `alta_expediente` por código—,
        # pero se conserva en la comprobación: si falta del catálogo, es preferible
        # abortar aquí, con la lista de faltantes, que a mitad del alta.
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
    _comun.abortar_si_catalogo_incompleto(cat)
    return cat


# ---------------------------------------------------------------------------
# Alta expediente/proyecto/solicitud — por el servicio real (#428)
# ---------------------------------------------------------------------------

def _crear_expediente(cat):
    """Alta completa por `alta_expediente()`, la misma vía que el formulario.

    Devuelve el `ResultadoAlta`, que trae ya el escrito de solicitud creado: no hay
    que subirlo después, y es ese documento el que luego cubre el requisito
    MODELO_SOLICITUD del checklist documental.
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
        titulo='Línea subterránea 20 kV Ronda Sur — CT asociado',
        descripcion=(
            'Nueva línea subterránea de distribución 20 kV y centro de '
            'transformación asociado, íntegramente en suelo urbano.'
        ),
        finalidad='Distribución de energía eléctrica en baja/media tensión',
        emplazamiento='T.M. de Mairena del Aljarafe (Sevilla)',
        fecha_proyecto=FECHA_BASE,
        ia_id=cat['ia_exento'].id,
        municipios_ids=[cat['municipio'].id],
        titular_id=cat['entidad'].id,
        tipo_solicitud_id=cat['tipo_solicitud'].id,
        solicitante_id=cat['entidad'].id,
        observaciones=OBSERVACIONES,
        # Campos técnicos del proyecto que el formulario no pide pero este
        # escenario sí fija: sin línea aérea y en suelo urbano es lo que lo deja
        # EXENTO de instrumento ambiental.
        proyecto_extra={
            'es_modificacion': False,
            'sin_linea_aerea': True,
            'max_tension_nominal_kv': 20,
            'solo_suelo_urbano_urbanizable': True,
        },
        documento=DocumentoSolicitud(
            contenido=contenido,
            nombre_original='modelo_solicitud.pdf',
            fecha_registro=FECHA_BASE,
        ),
    ))

    print(f"Expediente AT-{resultado.numero_at} creado "
          f"(id={resultado.expediente.id}, solicitud={resultado.solicitud.id}, "
          f"escrito de solicitud={resultado.documento.id}).")
    return resultado


def main(app=None, *, efectos_desarrollo=True):
    """Construye el expediente-tipo sobre la app que se le pase.

    `efectos_desarrollo=False` es como lo invoca la semilla de la base de tests
    (#849): deja fuera lo que solo tiene sentido en la máquina de desarrollo —
    fijar el reloj simulado, que escribe en `instance/` y que bajo
    `TestingConfig` (DEBUG=False) el sistema ignora de todas formas—. El
    escenario que se construye es el mismo.
    """
    from flask_login import login_user
    from app.services import mutaciones_arbol as svc
    from app.services import reloj_simulado
    from app.models.fases import Fase
    from app.models.tramites import Tramite
    from app.models.tareas import Tarea

    if app is None:
        app = create_app()

    def _fijar_reloj(fecha):
        if efectos_desarrollo:
            reloj_simulado.fijar(fecha)

    with app.test_request_context():
        cat = _cargar_catalogo()
        _comun.reciclar_si_existe(MARCA)
        _fijar_reloj(FECHA_BASE)

        login_user(cat['usuario'])
        client = _comun.abrir_cliente(app, cat['usuario'])

        alta = _crear_expediente(cat)
        expediente, solicitud = alta.expediente, alta.solicitud
        exp_id = expediente.id

        # El escrito de solicitud no se sube aparte: entró con el alta y es el que
        # ancla la solicitud (#428). El mismo documento cubre luego su requisito en
        # el checklist documental, unas líneas más abajo.
        doc_solicitud_id = alta.documento.id

        doc_proyecto_id = _comun.subir(client, exp_id, 'DOC_PROYECTO',
                                  cat['doc_proyecto'].id, FECHA_BASE,
                                  'Proyecto técnico')
        doc_tasa_id = _comun.subir(client, exp_id, 'JUSTIFICANTE_PAGO_TASA',
                              cat['doc_justificante_pago_tasa'].id, FECHA_BASE,
                              'Justificante de pago de la tasa')
        _comun.cubrir_requisito_tasa(solicitud, doc_tasa_id)

        # --- Fase ANALISIS_SOLICITUD ---------------------------------------
        fase_id = _comun.check(svc.crear_fase(solicitud, cat['fase_analisis_solicitud']),
                          'crear_fase ANALISIS_SOLICITUD')
        fase = Fase.query.get(fase_id)

        tramite_ad_id = _comun.check(svc.crear_tramite(fase, cat['tramite_analisis_documental']),
                                'crear_tramite ANALISIS_DOCUMENTAL')
        tramite_ad = Tramite.query.get(tramite_ad_id)

        tarea_analizar0_id = _comun.check(svc.crear_tarea(tramite_ad, cat['tarea_analizar']),
                                     'crear_tarea ANALIZAR inicial')
        # Lo presentado con la solicitud. El resto de requisitos aplicables queda
        # sin casar → son los defectos del primer diagnóstico. La tasa se vuelve a
        # casar aquí aunque ya lo estuviera (`_cubrir_requisito_tasa`, upsert
        # idempotente): es esta llamada la que deriva su vínculo CONSUMIDO.
        _comun.casar_requisitos(client, exp_id, tarea_analizar0_id, [
            ('MODELO_SOLICITUD', doc_solicitud_id),
            ('DOC_PROYECTO', doc_proyecto_id),
            ('JUSTIFICANTE_PAGO_TASA', doc_tasa_id),
        ], 'presentación')
        doc_diagnostico_id = _comun.producir_diagnostico(client, exp_id, tarea_analizar0_id,
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
            tramite_req_id = _comun.check(svc.crear_tramite(fase, cat['tramite_requerimiento']),
                                     f'crear_tramite REQUERIMIENTO_SUBSANACION #{vuelta}')
            tramite_req = Tramite.query.get(tramite_req_id)

            tarea_elab_id = _comun.check(svc.crear_tarea(tramite_req, cat['tarea_elaborar']),
                                    f'crear_tarea ELABORAR #{vuelta}')
            tarea_elab = Tarea.query.get(tarea_elab_id)
            doc_oficio_id = _comun.subir(client, exp_id, 'OFICIO_REQUERIMIENTO',
                                    cat['doc_oficio_requerimiento'].id, fecha_actual,
                                    f'Requerimiento de subsanación #{vuelta}')
            # ELABORAR consume el diagnóstico que motiva este requerimiento.
            _comun.check(svc.editar_tarea(tarea_elab, documentos_consumidos_ids=[doc_diagnostico_id],
                                     documento_producido_id=doc_oficio_id, notas=None),
                   f'vincular producido ELABORAR #{vuelta}')

            tarea_notif_id = _comun.check(svc.crear_tarea(tramite_req, cat['tarea_notificar']),
                                     f'crear_tarea NOTIFICAR #{vuelta}')
            tarea_notif = Tarea.query.get(tarea_notif_id)
            doc_justif_id = _comun.subir(client, exp_id, 'JUSTIFICANTE_NOTIFICA',
                                    cat['doc_justificante_notifica'].id, fecha_actual,
                                    f'Justificante de notificación del requerimiento #{vuelta}')
            _comun.notificar(tarea_notif, doc_oficio_id, doc_justif_id, fecha_actual, f'req.#{vuelta}')

            tarea_esp_id = _comun.check(svc.crear_tarea(tramite_req, cat['tarea_esperar_plazo']),
                                   f'crear_tarea ESPERAR_PLAZO #{vuelta}')
            tarea_esp = Tarea.query.get(tarea_esp_id)
            # Dispara el plazo: CONSUMIDO = oficio ya notificado (catalogo_plazos id=5).
            _comun.check(svc.editar_tarea(tarea_esp, documentos_consumidos_ids=[doc_oficio_id],
                                     documento_producido_id=None, notas=None),
                   f'disparar plazo ESPERAR_PLAZO #{vuelta}')

            # Fecha derivada del plazo real de la tarea, no de un número fijo.
            fecha_actual = _comun.fecha_respuesta_en_plazo(
                tarea_esp, f'req.#{vuelta}', MARGEN_RESPUESTA_HABILES)
            _fijar_reloj(fecha_actual)

            doc_subsanacion_id = _comun.subir(client, exp_id, 'SUBSANACION',
                                         cat['doc_subsanacion'].id, fecha_actual,
                                         f'Respuesta a requerimiento #{vuelta}')
            # Cierra el plazo dentro de término: PRODUCIDO = respuesta del titular.
            _comun.check(svc.editar_tarea(tarea_esp, documentos_consumidos_ids=[doc_oficio_id],
                                     documento_producido_id=doc_subsanacion_id, notas=None),
                   f'cerrar plazo ESPERAR_PLAZO #{vuelta}')

            # Anexos que acompañan al escrito de subsanación: son los que casan
            # con los requisitos que faltaban.
            aportados = []
            for codigo, asunto in aportes_por_vuelta[vuelta - 1]:
                doc_anexo_id = _comun.subir(client, exp_id, codigo, cat[f'doc_{codigo.lower()}'].id,
                                       fecha_actual, f'{asunto} (subsanación #{vuelta})')
                aportados.append((codigo, doc_anexo_id))

            tarea_analizar_id = _comun.check(svc.crear_tarea(tramite_req, cat['tarea_analizar']),
                                        f'crear_tarea ANALIZAR #{vuelta}')
            # Sin vincular consumidos a mano: los deriva el casado de requisitos.
            _comun.casar_requisitos(client, exp_id, tarea_analizar_id, aportados,
                              f'subsanación #{vuelta}')
            doc_diagnostico_id = _comun.producir_diagnostico(client, exp_id, tarea_analizar_id,
                                                        f'REQUERIMIENTO_SUBSANACION #{vuelta}')
            print(f"REQUERIMIENTO_SUBSANACION #{vuelta}: respuesta dentro de plazo.")

        # --- COMUNICACION_INICIO_ADMISION -----------------------------------
        tramite_com_id = _comun.check(svc.crear_tramite(fase, cat['tramite_comunicacion_admision']),
                                 'crear_tramite COMUNICACION_INICIO_ADMISION')
        tramite_com = Tramite.query.get(tramite_com_id)

        tarea_com_elab_id = _comun.check(svc.crear_tarea(tramite_com, cat['tarea_elaborar']),
                                    'crear_tarea ELABORAR admision')
        tarea_com_elab = Tarea.query.get(tarea_com_elab_id)
        # El hook automático de #776 ya vinculó aquí, al crear la tarea, el documento
        # que dispara el plazo del art. 21.4 (documento_disparo_comunicacion_admision,
        # #825). Hay que conservarlo: editar_tarea trata documentos_consumidos_ids como
        # el conjunto CONSUMIDO deseado completo (no aditivo) — si no se repite aquí,
        # se libera y el plazo de esta tarea queda SIN_PLAZO (hallazgo #825).
        ids_consumidos_previos = [d.id for d in tarea_com_elab.documentos_consumidos]
        doc_admision_id = _comun.subir(client, exp_id, 'OFICIO_INICIO_ADMISION',
                                  cat['doc_oficio_inicio_admision'].id, fecha_actual,
                                  'Comunicación de inicio y admisión a trámite')
        # ELABORAR consume el diagnóstico favorable que habilita la admisión, además
        # del documento de disparo del plazo que ya trae de la línea anterior.
        _comun.check(svc.editar_tarea(
            tarea_com_elab,
            documentos_consumidos_ids=list(dict.fromkeys(ids_consumidos_previos + [doc_diagnostico_id])),
            documento_producido_id=doc_admision_id, notas=None),
               'vincular producido ELABORAR admision')

        tarea_com_notif_id = _comun.check(svc.crear_tarea(tramite_com, cat['tarea_notificar']),
                                     'crear_tarea NOTIFICAR admision')
        tarea_com_notif = Tarea.query.get(tarea_com_notif_id)
        doc_justif_admision_id = _comun.subir(client, exp_id, 'JUSTIFICANTE_NOTIFICA',
                                         cat['doc_justificante_notifica'].id, fecha_actual,
                                         'Justificante de notificación de la comunicación de inicio')
        _comun.notificar(tarea_com_notif, doc_admision_id, doc_justif_admision_id, fecha_actual, 'admision')
        print("COMUNICACION_INICIO_ADMISION: elaborada y notificada (Notificacion CORRECTA).")

        # --- Fin del alcance -------------------------------------------------
        # El expediente-tipo acaba aquí: ANALISIS_SOLICITUD queda completa y
        # pendiente de cierre (todos sus trámites finalizados, sin
        # documento_resultado_id). Cerrar la fase y abrir RESOLUCION es
        # tramitación posterior — y abrirla dejará de ser libre cuando se
        # implemente ADR-043 (#827): no por recuento de fases sin cerrar, sino
        # porque falte el CERT_FIN_INSTRUCCION de la solicitud (art. 82.1 LPACAP).
        db.session.expire(fase)
        estado_fase = 'pendiente de cierre' if fase.pdte_cierre else 'en curso'
        print(f"Fase ANALISIS_SOLICITUD {estado_fase} — fin del alcance del script.")

        print(f"\nExpediente AT-{expediente.numero_at} (id={exp_id}) completado.")
        return expediente.numero_at, exp_id


# ---------------------------------------------------------------------------
# HUECO_PRECEDENCIA_AL_CREAR (#814 → cerrado en #823, salvo la fase finalizadora):
#
# Recorrer este circuito con todos los documentos disponibles de golpe —cosa
# que en la vida real no ocurre: el justificante no existe hasta que llega del
# sistema de notificaciones— destapó que nada comprobaba la precedencia al
# crear un nodo del árbol. Verificado sobre AT-15 (conservado a propósito en BD
# de desarrollo): se creó ESPERAR_PLAZO con su NOTIFICAR en curso, un 2º
# REQUERIMIENTO_SUBSANACION con el 1º en curso, y la fase RESOLUCION con
# ANALISIS_SOLICITUD sin finalizar — sin usar `justificacion` en ningún punto.
#
# Los dos primeros ya no son posibles: check_invariante tiene rama CREAR (#823)
# y ambos checks son puerta cerrada. El orden en que este script construye la
# fase los respeta por construcción —cada ESPERAR_PLAZO se crea después de
# `_comun.notificar()`, y cada vuelta después de cerrar la anterior—, así que sigue
# corriendo sin tocar nada.
#
# El tercero (fase finalizadora) salió de #823: ADR-043 lo reformula como la
# existencia del CERT_FIN_INSTRUCCION de la solicitud, regla de motor con norma
# citable (art. 82.1 LPACAP) más invariante en el emisor del certificado, y se
# implementa en #827. Análisis original: #814, apartado del mismo nombre.
# ---------------------------------------------------------------------------


if __name__ == '__main__':
    numero_at, exp_id = main()
