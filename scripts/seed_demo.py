"""
seed_demo.py — Datos de demostración verosímiles para presentación

Crea 7 entidades (empresas reales del sector AT andaluz con nombres ficticios),
una gestoría que representa a varias, y 10 expedientes en distintas fases con
pool de documentos con nombres realistas.

Re-ejecutable: borra datos operativos previos (NO toca usuarios ni maestros).
URLs de documentos son rutas ficticias — no hay ficheros reales.

Uso:
    cd /d/BDDAT
    venv/Scripts/python.exe scripts/seed_demo.py
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.entidad import Entidad
from app.models.autorizados_titular import AutorizadoTitular
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.documentos import Documento
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea

app = create_app()


# ---------------------------------------------------------------------------
# IDs de municipios fijos (de la BD de maestros)
# ---------------------------------------------------------------------------
MUN_SEVILLA  = 774
MUN_MALAGA   = 643
MUN_CORDOBA  = 169
MUN_HUELVA   = 440
MUN_CADIZ    = 116


# ---------------------------------------------------------------------------
# Carga de IDs desde BD (por código — inmune a reasignaciones de secuencia)
# ---------------------------------------------------------------------------
def cargar_ids():
    fases      = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_fases')).fetchall()}
    tramites   = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_tramites')).fetchall()}
    solicitudes = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT siglas, id FROM public.tipos_solicitudes')).fetchall()}
    expedientes = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT tipo, id FROM public.tipos_expedientes')).fetchall()}
    docs       = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_documentos')).fetchall()}
    resultados = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_resultados_fases')).fetchall()}
    tareas     = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_tareas')).fetchall()}
    return fases, tramites, solicitudes, expedientes, docs, resultados, tareas


# ---------------------------------------------------------------------------
# Limpiar datos operativos (NO toca usuarios ni maestros)
# ---------------------------------------------------------------------------
def limpiar():
    db.session.execute(db.text(
        'TRUNCATE TABLE tareas, tramites, fases, documentos,'
        ' historico_titulares_expediente, solicitudes, expedientes,'
        ' municipios_proyecto, documentos_proyecto, proyectos,'
        ' autorizados_titular, direcciones_notificacion, entidades'
        ' RESTART IDENTITY CASCADE'
    ))
    db.session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def crear_exp(numero_at, entidad, tipo_exp_id, titulo, descripcion,
              emplazamiento, fecha=date(2024, 1, 1)):
    p = Proyecto(
        titulo=titulo,
        descripcion=descripcion,
        fecha=fecha,
        finalidad='Instalación de alta tensión en Andalucía',
        emplazamiento=emplazamiento,
        es_modificacion=False,
    )
    db.session.add(p)
    db.session.flush()
    exp = Expediente(
        numero_at=numero_at,
        tipo_expediente_id=tipo_exp_id,
        proyecto_id=p.id,
        titular_id=entidad.id,
        heredado=False,
    )
    db.session.add(exp)
    db.session.flush()
    return exp


def crear_sol(exp, tipo_sol_id, entidad, fecha):
    s = Solicitud(
        expediente_id=exp.id,
        entidad_id=entidad.id,
        tipo_solicitud_id=tipo_sol_id,
        fecha_solicitud=fecha,
        estado='EN_TRAMITE',
    )
    db.session.add(s)
    db.session.flush()
    return s


def crear_doc(exp, url, tipo_doc_id, asunto, fecha_adm=None):
    d = Documento(
        expediente_id=exp.id,
        tipo_doc_id=tipo_doc_id,
        url=url,
        asunto=asunto,
        fecha_administrativa=fecha_adm,
    )
    db.session.add(d)
    db.session.flush()
    return d


def crear_fase(sol, tipo_fase_id, fecha_ini, fin=None, resultado_id=None):
    f = Fase(
        solicitud_id=sol.id,
        tipo_fase_id=tipo_fase_id,
        fecha_inicio=fecha_ini,
        fecha_fin=fin,
        resultado_fase_id=resultado_id,
    )
    db.session.add(f)
    db.session.flush()
    return f


def crear_tramite(fase, tipo_tramite_id, fecha_ini):
    t = Tramite(
        fase_id=fase.id,
        tipo_tramite_id=tipo_tramite_id,
        fecha_inicio=fecha_ini,
    )
    db.session.add(t)
    db.session.flush()
    return t


def crear_tarea(tramite, tipo_tarea_id, fecha_ini,
                doc_usado=None, doc_producido=None, notas=None):
    t = Tarea(
        tramite_id=tramite.id,
        tipo_tarea_id=tipo_tarea_id,
        fecha_inicio=fecha_ini,
        documento_usado_id=doc_usado.id if doc_usado else None,
        documento_producido_id=doc_producido.id if doc_producido else None,
        notas=notas,
    )
    db.session.add(t)
    db.session.flush()
    return t


def fase_fin(sol, tipo_fase_id, fecha_ini, fecha_fin, resultado_id):
    return crear_fase(sol, tipo_fase_id, fecha_ini, fin=fecha_fin,
                      resultado_id=resultado_id)


def autorizar(titular, gestor):
    a = AutorizadoTitular(
        titular_entidad_id=titular.id,
        autorizado_entidad_id=gestor.id,
        activo=True,
        observaciones='Poder notarial general para tramitación de instalaciones AT',
    )
    db.session.add(a)
    db.session.flush()


# ---------------------------------------------------------------------------
# Ejecución principal
# ---------------------------------------------------------------------------
with app.app_context():
    print('Cargando IDs de maestros...')
    TF, TT, TS, TE, TDOC, TRES, TTAREA = cargar_ids()

    # --- Atajos tipos_fases ---
    TF_SOL  = TF['ANALISIS_SOLICITUD']
    TF_CONS = TF['CONSULTAS']
    TF_MA   = TF['COMPATIBILIDAD_AMBIENTAL']
    TF_IP   = TF['INFORMACION_PUBLICA']
    TF_RES  = TF['RESOLUCION']

    # --- Atajos tipos_tramites ---
    TT_ANAL  = TT['ANALISIS_DOCUMENTAL']
    TT_REQ   = TT['REQUERIMIENTO_SUBSANACION']
    TT_SEP   = TT['CONSULTA_SEPARATA']
    TT_COMP  = TT['SOLICITUD_COMPATIBILIDAD']
    TT_BOP   = TT['ANUNCIO_BOP']
    TT_ELAB  = TT['ELABORACION']
    TT_NOTIF = TT['NOTIFICACION']

    # --- Atajos tipos_solicitudes ---
    TS_AAP_AAC     = TS['AAP_AAC']
    TS_AAP_AAC_DUP = TS['AAP_AAC_DUP_AAE_DEFINITIVA']
    TS_AAE_DEF     = TS['AAE_DEFINITIVA']
    TS_AAT         = TS['AAT']
    TS_RAIPEE      = TS['AAP_AAC_RAIPEE_PREVIA_RADNE_INTERESADO']

    # --- Atajos tipos_expedientes ---
    TE_DIST   = TE['Distribución']
    TE_CEDIDA = TE['Distribución cedida']
    TE_RENOV  = TE['Renovable']
    TE_AUTO   = TE['Autoconsumo']

    # --- Atajos documentos ---
    TDOC_OTROS   = TDOC['OTROS']
    TDOC_DR      = TDOC.get('DR_NO_DUP', TDOC['OTROS'])

    # --- Atajos resultados ---
    TRES_FAV = TRES.get('FAVORABLE', next(iter(TRES.values())))

    # --- Atajos tareas ---
    TAREA_ANAL = TTAREA['ANALIZAR']
    TAREA_RED  = TTAREA['REDACTAR']
    TAREA_FIR  = TTAREA['FIRMAR']
    TAREA_NOT  = TTAREA['NOTIFICAR']
    TAREA_PUB  = TTAREA['PUBLICAR']
    TAREA_ESP  = TTAREA['ESPERAR_PLAZO']

    print('Limpiando datos operativos previos...')
    limpiar()

    # =========================================================================
    # ENTIDADES
    # =========================================================================
    print('Creando entidades...')

    # Grandes distribuidoras
    endesa = Entidad(
        nif='A28023430',
        nombre_completo='Endesa Distribución Eléctrica S.L.U.',
        rol_titular=True, rol_consultado=True, activo=True,
        tipo_titular='GRAN_DISTRIBUIDORA',
        email='at.andalucia@endesa.es',
        telefono='954 000 100',
        direccion='Avenida de la Borbolla, 5',
        codigo_postal='41004',
        municipio_id=MUN_SEVILLA,
    )
    sevillana = Entidad(
        nif='A41000111',
        nombre_completo='Sevillana-Endesa Redes Eléctricas S.A.',
        rol_titular=True, rol_consultado=True, activo=True,
        tipo_titular='GRAN_DISTRIBUIDORA',
        email='redes@sevillana-endesa.es',
        telefono='954 000 200',
        direccion='Calle Miraflores, 12',
        codigo_postal='41008',
        municipio_id=MUN_SEVILLA,
    )

    # Promotores renovables
    solarsur = Entidad(
        nif='B41987654',
        nombre_completo='SolarSur Energías Renovables S.L.',
        rol_titular=True, activo=True,
        tipo_titular='PROMOTOR',
        email='proyectos@solarsur.es',
        telefono='955 321 400',
        direccion='Parque Tecnológico Cartuja, Edificio CETA, Módulo 3',
        codigo_postal='41092',
        municipio_id=MUN_SEVILLA,
    )
    eolica = Entidad(
        nif='A14567890',
        nombre_completo='Parque Eólico Sierra Morena S.A.',
        rol_titular=True, activo=True,
        tipo_titular='PROMOTOR',
        email='tramitacion@eolicasierramorena.es',
        telefono='957 100 200',
        direccion='Ronda de los Tejares, 3, 4.ª planta',
        codigo_postal='14001',
        municipio_id=MUN_CORDOBA,
    )
    energiaverde = Entidad(
        nif='B04112233',
        nombre_completo='Energía Verde Almería S.L.',
        rol_titular=True, activo=True,
        tipo_titular='PROMOTOR',
        email='autorizaciones@energiaverde-almeria.es',
        telefono='950 456 789',
        direccion_fallback='Calle Reyes Católicos, 18, 2.º B — 04001 Almería',
    )

    # Autoconsumo industrial
    metalicas = Entidad(
        nif='B11223344',
        nombre_completo='Industrias Metálicas Gaditanas S.L.',
        rol_titular=True, activo=True,
        tipo_titular='OTRO',
        email='instalaciones@imgaditanas.es',
        telefono='956 234 567',
        direccion='Polígono Industrial El Portal, Nave 14',
        codigo_postal='11405',
        municipio_id=MUN_CADIZ,
    )

    # Gestoría representante (representa a solarsur, eolica y energiaverde)
    gestora = Entidad(
        nif='B41555666',
        nombre_completo='Gestión Energética Andaluza S.L.',
        rol_titular=True, activo=True,
        tipo_titular='OTRO',
        email='at@gea-tramitacion.es',
        telefono='954 777 888',
        direccion='Calle Rioja, 8, 3.º izqda.',
        codigo_postal='41001',
        municipio_id=MUN_SEVILLA,
        notas='Gestoría especializada en tramitación AT. Representa a promotores renovables.',
    )

    db.session.add_all([endesa, sevillana, solarsur, eolica,
                        energiaverde, metalicas, gestora])
    db.session.flush()

    # Autorizaciones: gestora representa a tres promotores
    autorizar(solarsur,    gestora)
    autorizar(eolica,      gestora)
    autorizar(energiaverde, gestora)
    print('  Autorizaciones: GEA representa a SolarSur, Eólica Sierra Morena y Energía Verde Almería')

    # =========================================================================
    # EXPEDIENTES
    # =========================================================================

    # ------------------------------------------------------------------
    # AT-2001 | Renovable | SolarSur (via GEA) | AAP+AAC
    # Fase: Análisis Solicitud — Pendiente redactar requerimiento
    # ------------------------------------------------------------------
    exp01 = crear_exp(
        2001, solarsur, TE_RENOV,
        titulo='Planta Fotovoltaica "Las Marismas" — 49,9 MW',
        descripcion='Instalación fotovoltaica de 49,9 MW con línea de evacuación 66 kV',
        emplazamiento='T.M. de Lebrija (Sevilla)',
        fecha=date(2024, 9, 15),
    )
    sol01_entrada = crear_doc(exp01,
        'expedientes/AT-2001/entrada/2024-09-15_Solicitud_AAP_AAC.pdf',
        TDOC_OTROS, 'Solicitud de AAP y AAC', date(2024, 9, 15))
    sol01_mem = crear_doc(exp01,
        'expedientes/AT-2001/entrada/2024-09-15_Memoria_descriptiva.pdf',
        TDOC_OTROS, 'Memoria descriptiva del proyecto', date(2024, 9, 15))
    sol01_planos = crear_doc(exp01,
        'expedientes/AT-2001/entrada/2024-09-15_Planos_general_y_parcelas.pdf',
        TDOC_OTROS, 'Planos — situación general y parcelas afectadas', date(2024, 9, 15))
    sol01 = crear_sol(exp01, TS_AAP_AAC, gestora, date(2024, 9, 15))
    f01 = crear_fase(sol01, TF_SOL, date(2024, 9, 18))
    t01 = crear_tramite(f01, TT_ANAL, date(2024, 9, 18))
    crear_tarea(t01, TAREA_ANAL, date(2024, 9, 18), doc_usado=sol01_entrada)
    t01b = crear_tramite(f01, TT_REQ, date(2024, 10, 14))
    crear_tarea(t01b, TAREA_RED, date(2024, 10, 14), doc_usado=sol01_mem)
    print('AT-2001 OK — Renovable, AAP+AAC, fase SOL pendiente redactar req.')

    # ------------------------------------------------------------------
    # AT-2002 | Renovable | SolarSur (via GEA) | AAP+AAC
    # Fases: SOL=FIN, CONSULTAS pendiente notificar separata
    # ------------------------------------------------------------------
    exp02 = crear_exp(
        2002, solarsur, TE_RENOV,
        titulo='Planta Fotovoltaica "Cerro Blanco" — 49,5 MW',
        descripcion='Instalación FV 49,5 MW con subestación de maniobra 132 kV',
        emplazamiento='T.M. de Utrera (Sevilla)',
        fecha=date(2024, 3, 10),
    )
    sol02_sol = crear_doc(exp02,
        'expedientes/AT-2002/entrada/2024-03-10_Solicitud_AAP_AAC.pdf',
        TDOC_OTROS, 'Solicitud de AAP y AAC', date(2024, 3, 10))
    sol02_sub = crear_doc(exp02,
        'expedientes/AT-2002/salida/2024-04-22_Requerimiento_subsanacion.pdf',
        TDOC_OTROS, 'Requerimiento de subsanación — documentación técnica incompleta', date(2024, 4, 22))
    sol02_subsanada = crear_doc(exp02,
        'expedientes/AT-2002/entrada/2024-05-30_Documentacion_subsanada.pdf',
        TDOC_OTROS, 'Documentación subsanada', date(2024, 5, 30))
    sol02_sep = crear_doc(exp02,
        'expedientes/AT-2002/salida/2024-07-08_Separata_consultas.pdf',
        TDOC_OTROS, 'Separata para organismos consultados', date(2024, 7, 8))
    sol02 = crear_sol(exp02, TS_AAP_AAC, gestora, date(2024, 3, 10))
    fase_fin(sol02, TF_SOL, date(2024, 3, 12), date(2024, 6, 20), TRES_FAV)
    f02_cons = crear_fase(sol02, TF_CONS, date(2024, 7, 8))
    t02_sep = crear_tramite(f02_cons, TT_SEP, date(2024, 7, 8))
    crear_tarea(t02_sep, TAREA_NOT, date(2024, 7, 8), doc_usado=sol02_sep)
    print('AT-2002 OK — Renovable, AAP+AAC, SOL=FIN, CONSULTAS pendiente notificar')

    # ------------------------------------------------------------------
    # AT-2003 | Renovable | Parque Eólico (via GEA) | AAP+AAC+DUP+AAE
    # Fases: SOL=FIN, CONSULTAS=FIN, MA=FIN, IP pendiente publicar BOP
    # ------------------------------------------------------------------
    exp03 = crear_exp(
        2003, eolica, TE_RENOV,
        titulo='Parque Eólico "Sierra Bermeja" — 48 MW',
        descripcion='Parque eólico 48 MW, 12 aerogeneradores, línea de evacuación 132 kV',
        emplazamiento='T.M. de Montoro y Adamuz (Córdoba)',
        fecha=date(2023, 6, 1),
    )
    sol03_dr = crear_doc(exp03,
        'expedientes/AT-2003/entrada/2024-03-01_Declaracion_responsable_no_duplicidad.pdf',
        TDOC_DR, 'Declaración responsable de no duplicidad de expedientes', date(2024, 3, 1))
    sol03_anuncio = crear_doc(exp03,
        'expedientes/AT-2003/salida/2024-08-15_Anuncio_informacion_publica_BOP.pdf',
        TDOC_OTROS, 'Anuncio para publicación en BOP — Información Pública', date(2024, 8, 15))
    sol03 = crear_sol(exp03, TS_AAP_AAC_DUP, gestora, date(2023, 6, 1))
    fase_fin(sol03, TF_SOL,  date(2023, 6, 5),  date(2023, 9, 10), TRES_FAV)
    fase_fin(sol03, TF_CONS, date(2023, 9, 12), date(2024, 1, 20), TRES_FAV)
    fase_fin(sol03, TF_MA,   date(2024, 1, 22), date(2024, 7, 30), TRES_FAV)
    f03_ip = crear_fase(sol03, TF_IP, date(2024, 8, 15))
    t03_bop = crear_tramite(f03_ip, TT_BOP, date(2024, 8, 15))
    crear_tarea(t03_bop, TAREA_PUB, date(2024, 8, 15), doc_usado=sol03_anuncio)
    print('AT-2003 OK — Eólico, AAP+AAC+DUP+AAE, IP pendiente publicar BOP')

    # ------------------------------------------------------------------
    # AT-2004 | Renovable | Parque Eólico (via GEA) | AAP+AAC+DUP+AAE
    # Fases: SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=FIN, RES pendiente notificar
    # ------------------------------------------------------------------
    exp04 = crear_exp(
        2004, eolica, TE_RENOV,
        titulo='Parque Eólico "Los Pedroches" — 36 MW',
        descripcion='Parque eólico 36 MW, 9 aerogeneradores 4 MW, SET colectora',
        emplazamiento='T.M. de Pozoblanco (Córdoba)',
        fecha=date(2022, 11, 7),
    )
    sol04_res = crear_doc(exp04,
        'expedientes/AT-2004/salida/2024-09-20_Resolucion_AAP_firmada.pdf',
        TDOC_OTROS, 'Resolución AAP — firmada y sellada', date(2024, 9, 20))
    sol04 = crear_sol(exp04, TS_AAP_AAC_DUP, gestora, date(2022, 11, 7))
    fase_fin(sol04, TF_SOL,  date(2022, 11, 9),  date(2023, 2, 28), TRES_FAV)
    fase_fin(sol04, TF_CONS, date(2023, 3, 1),   date(2023, 7, 15), TRES_FAV)
    fase_fin(sol04, TF_MA,   date(2023, 7, 17),  date(2024, 2, 10), TRES_FAV)
    fase_fin(sol04, TF_IP,   date(2024, 2, 12),  date(2024, 8, 30), TRES_FAV)
    f04_res = crear_fase(sol04, TF_RES, date(2024, 9, 2))
    t04_not = crear_tramite(f04_res, TT_NOTIF, date(2024, 9, 20))
    crear_tarea(t04_not, TAREA_NOT, date(2024, 9, 20), doc_usado=sol04_res)
    print('AT-2004 OK — Eólico, AAP+AAC+DUP+AAE, RES pendiente notificar resolución')

    # ------------------------------------------------------------------
    # AT-2005 | Distribución | Endesa | AAP+AAC
    # Fases: SOL=FIN, CONSULTAS=FIN, MA pendiente plazo respuesta
    # ------------------------------------------------------------------
    exp05 = crear_exp(
        2005, endesa, TE_DIST,
        titulo='Línea 132 kV "Alcalá – La Rinconada" y SET asociada',
        descripcion='Nueva línea subterránea 132 kV y subestación transformadora 132/20 kV',
        emplazamiento='T.M. de Alcalá de Guadaíra y La Rinconada (Sevilla)',
        fecha=date(2024, 2, 5),
    )
    sol05_sol = crear_doc(exp05,
        'expedientes/AT-2005/entrada/2024-02-05_Solicitud_AAP_AAC.pdf',
        TDOC_OTROS, 'Solicitud de AAP y AAC', date(2024, 2, 5))
    sol05_comp = crear_doc(exp05,
        'expedientes/AT-2005/salida/2024-07-12_Solicitud_compatibilidad_ambiental.pdf',
        TDOC_OTROS, 'Solicitud de Compatibilidad Ambiental al órgano ambiental', date(2024, 7, 12))
    sol05 = crear_sol(exp05, TS_AAP_AAC, endesa, date(2024, 2, 5))
    fase_fin(sol05, TF_SOL,  date(2024, 2, 6),  date(2024, 5, 20), TRES_FAV)
    fase_fin(sol05, TF_CONS, date(2024, 5, 21), date(2024, 7, 10), TRES_FAV)
    f05_ma = crear_fase(sol05, TF_MA, date(2024, 7, 12))
    t05_comp = crear_tramite(f05_ma, TT_COMP, date(2024, 7, 12))
    crear_tarea(t05_comp, TAREA_ESP, date(2024, 7, 12),
                doc_usado=sol05_comp, notas='PLAZO_DIAS=30')
    print('AT-2005 OK — Distribución Endesa, AAP+AAC, MA pendiente plazo')

    # ------------------------------------------------------------------
    # AT-2006 | Distribución | Endesa | AAE Definitiva
    # Fase: SOL pendiente estudio (nuevo expediente)
    # ------------------------------------------------------------------
    exp06 = crear_exp(
        2006, endesa, TE_DIST,
        titulo='SET "Nueva Palmera" 66/20 kV — Autorización de Explotación',
        descripcion='Autorización de explotación definitiva de la SET construida al amparo de AT-1897',
        emplazamiento='T.M. de Palma del Río (Córdoba)',
        fecha=date(2024, 10, 3),
    )
    sol06_acta = crear_doc(exp06,
        'expedientes/AT-2006/entrada/2024-10-03_Solicitud_AAE.pdf',
        TDOC_OTROS, 'Solicitud de Autorización de Explotación Definitiva', date(2024, 10, 3))
    sol06_insp = crear_doc(exp06,
        'expedientes/AT-2006/entrada/2024-10-03_Acta_inspeccion_previa.pdf',
        TDOC_OTROS, 'Acta de inspección previa favorable', date(2024, 10, 3))
    sol06 = crear_sol(exp06, TS_AAE_DEF, endesa, date(2024, 10, 3))
    f06 = crear_fase(sol06, TF_SOL, date(2024, 10, 7))
    t06 = crear_tramite(f06, TT_ANAL, date(2024, 10, 7))
    crear_tarea(t06, TAREA_ANAL, date(2024, 10, 7), doc_usado=sol06_acta)
    print('AT-2006 OK — Distribución Endesa, AAE Definitiva, fase SOL pendiente estudio')

    # ------------------------------------------------------------------
    # AT-2007 | Distribución cedida | Sevillana | AAC
    # Fase: SOL — pendiente firma requerimiento
    # ------------------------------------------------------------------
    exp07 = crear_exp(
        2007, sevillana, TE_CEDIDA,
        titulo='Red MT 20 kV "Urbanización Los Naranjos" — Distribución Cedida',
        descripcion='Cesión de red de distribución 20 kV de urbanizador a empresa distribuidora',
        emplazamiento='T.M. de Mairena del Aljarafe (Sevilla)',
        fecha=date(2024, 8, 19),
    )
    sol07_sol = crear_doc(exp07,
        'expedientes/AT-2007/entrada/2024-08-19_Solicitud_AAC_distribucion_cedida.pdf',
        TDOC_OTROS, 'Solicitud de AAC — instalación de distribución cedida', date(2024, 8, 19))
    sol07_req = crear_doc(exp07,
        'expedientes/AT-2007/salida/2024-09-30_Requerimiento_documentacion_tecnica.pdf',
        TDOC_OTROS, 'Requerimiento de documentación técnica complementaria', date(2024, 9, 30))
    sol07 = crear_sol(exp07, TS_AAP_AAC, sevillana, date(2024, 8, 19))
    f07 = crear_fase(sol07, TF_SOL, date(2024, 8, 21))
    t07a = crear_tramite(f07, TT_ANAL, date(2024, 8, 21))
    crear_tarea(t07a, TAREA_ANAL, date(2024, 8, 21), doc_usado=sol07_sol)
    t07b = crear_tramite(f07, TT_REQ, date(2024, 9, 30))
    crear_tarea(t07b, TAREA_FIR, date(2024, 9, 30), doc_usado=sol07_req)
    print('AT-2007 OK — Distribución cedida Sevillana, AAC, SOL pendiente firma req.')

    # ------------------------------------------------------------------
    # AT-2008 | Autoconsumo | Industrias Metálicas | AAP+AAC+RAIPEE+RADNE
    # Fase: SOL pendiente tramitar (recién registrado, sin fases)
    # ------------------------------------------------------------------
    exp08 = crear_exp(
        2008, metalicas, TE_AUTO,
        titulo='Instalación Autoconsumo Industrial 998 kWp — Polígono El Portal',
        descripcion='Sistema de autoconsumo fotovoltaico 998 kWp sobre cubierta industrial',
        emplazamiento='T.M. de El Puerto de Santa María (Cádiz)',
        fecha=date(2024, 11, 4),
    )
    sol08_sol = crear_doc(exp08,
        'expedientes/AT-2008/entrada/2024-11-04_Solicitud_AAP_AAC_RAIPEE_RADNE.pdf',
        TDOC_OTROS, 'Solicitud conjunta AAP+AAC+RAIPEE+RADNE', date(2024, 11, 4))
    sol08_mem = crear_doc(exp08,
        'expedientes/AT-2008/entrada/2024-11-04_Memoria_tecnica_autoconsumo.pdf',
        TDOC_OTROS, 'Memoria técnica de la instalación de autoconsumo', date(2024, 11, 4))
    crear_sol(exp08, TS_RAIPEE, metalicas, date(2024, 11, 4))
    print('AT-2008 OK — Autoconsumo Industrias Metálicas, sin fases (recién registrado)')

    # ------------------------------------------------------------------
    # AT-2009 | Renovable | Energía Verde Almería (via GEA) | AAP+AAC
    # Dos solicitudes activas: AAP+AAC en consultas + AAE_DEF recién entrada
    # ------------------------------------------------------------------
    exp09 = crear_exp(
        2009, energiaverde, TE_RENOV,
        titulo='Planta Fotovoltaica "Levante I" — 49,9 MW',
        descripcion='Planta FV 49,9 MW en Almería, línea de evacuación 66 kV soterrada',
        emplazamiento='T.M. de Tabernas (Almería)',
        fecha=date(2023, 3, 14),
    )
    # Solicitud principal AAP+AAC — en fase consultas
    sol09a_sep = crear_doc(exp09,
        'expedientes/AT-2009/salida/2023-09-10_Separata_organismos_consulta.pdf',
        TDOC_OTROS, 'Separata enviada a organismos afectados', date(2023, 9, 10))
    sol09a_resp = crear_doc(exp09,
        'expedientes/AT-2009/entrada/2024-02-15_Respuestas_organismos_consulta.pdf',
        TDOC_OTROS, 'Respuestas recibidas de organismos consultados', date(2024, 2, 15))
    sol09a = crear_sol(exp09, TS_AAP_AAC, gestora, date(2023, 3, 14))
    fase_fin(sol09a, TF_SOL, date(2023, 3, 16), date(2023, 8, 20), TRES_FAV)
    f09a_cons = crear_fase(sol09a, TF_CONS, date(2023, 9, 10))
    t09a_sep = crear_tramite(f09a_cons, TT_SEP, date(2023, 9, 10))
    crear_tarea(t09a_sep, TAREA_ESP, date(2023, 9, 10),
                doc_usado=sol09a_sep, notas='PLAZO_DIAS=0')
    # Segunda solicitud AAE_DEF — recién registrada
    sol09b_sol = crear_doc(exp09,
        'expedientes/AT-2009/entrada/2024-10-28_Solicitud_AAE_definitiva.pdf',
        TDOC_OTROS, 'Solicitud de AAE Definitiva', date(2024, 10, 28))
    sol09b = crear_sol(exp09, TS_AAE_DEF, gestora, date(2024, 10, 28))
    f09b = crear_fase(sol09b, TF_SOL, date(2024, 10, 30))
    t09b = crear_tramite(f09b, TT_ANAL, date(2024, 10, 30))
    crear_tarea(t09b, TAREA_ANAL, date(2024, 10, 30), doc_usado=sol09b_sol)
    print('AT-2009 OK — Renovable Almería (GEA), dos solicitudes activas')

    # ------------------------------------------------------------------
    # AT-2010 | Distribución | Endesa | AAT (Transmisión de Titularidad)
    # Solicitud resuelta completamente — FIN=TRUE
    # ------------------------------------------------------------------
    exp10 = crear_exp(
        2010, endesa, TE_DIST,
        titulo='Transmisión de Titularidad SET "Aljarafe" 132/20 kV',
        descripcion='Cambio de titularidad de instalaciones de distribución tras fusión empresarial',
        emplazamiento='T.M. de Bormujos (Sevilla)',
        fecha=date(2023, 1, 10),
    )
    sol10_sol = crear_doc(exp10,
        'expedientes/AT-2010/entrada/2023-01-10_Solicitud_AAT.pdf',
        TDOC_OTROS, 'Solicitud de Autorización de Transmisión de Titularidad', date(2023, 1, 10))
    sol10_res = crear_doc(exp10,
        'expedientes/AT-2010/salida/2023-04-18_Resolucion_AAT_firmada.pdf',
        TDOC_OTROS, 'Resolución AAT — favorable y notificada', date(2023, 4, 18))
    sol10 = crear_sol(exp10, TS_AAT, endesa, date(2023, 1, 10))
    fase_fin(sol10, TF_SOL, date(2023, 1, 12), date(2023, 4, 18), TRES_FAV)
    fase_fin(sol10, TF_RES, date(2023, 4, 18), date(2023, 4, 25), TRES_FAV)
    print('AT-2010 OK — Distribución Endesa, AAT, expediente completamente resuelto')

    db.session.commit()

    # Resumen
    from sqlalchemy import text
    r = db.session.execute(text(
        "SELECT 'expedientes'  t, COUNT(*) n FROM expedientes"
        " UNION ALL SELECT 'solicitudes',   COUNT(*) FROM solicitudes"
        " UNION ALL SELECT 'entidades',     COUNT(*) FROM entidades"
        " UNION ALL SELECT 'autorizados',   COUNT(*) FROM autorizados_titular"
        " UNION ALL SELECT 'documentos',    COUNT(*) FROM documentos"
        " UNION ALL SELECT 'fases',         COUNT(*) FROM fases"
        " UNION ALL SELECT 'tramites',      COUNT(*) FROM tramites"
        " UNION ALL SELECT 'tareas',        COUNT(*) FROM tareas"
    )).fetchall()
    print('\nResumen BD tras seed:')
    for row in r:
        print(f'  {row[0]:15s}: {row[1]}')
    print('\nSeed demo completado correctamente.')
