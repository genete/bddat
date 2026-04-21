"""
seed_listado.py — Escenarios de prueba para el listado inteligente

Crea los 11 escenarios de ANALISIS_LISTADO_INTELIGENTE.md §6.
Re-ejecutable: borra datos operativos previos antes de insertar.
Los IDs de maestros se consultan por código — no hay constantes hardcodeadas.

Uso:
    cd /d/BDDAT
    source venv/Scripts/activate
    python scripts/seed_listado.py

Prerequisito: haber ejecutado scripts/reset_maestros_ftt.py al menos una vez.
"""
import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.entidad import Entidad
from app.models.proyectos import Proyecto
from app.models.expedientes import Expediente
from app.models.solicitudes import Solicitud
from app.models.documentos import Documento
from app.models.fases import Fase
from app.models.tramites import Tramite
from app.models.tareas import Tarea

app = create_app()


# ---------------------------------------------------------------------------
# Fechas de referencia
# ---------------------------------------------------------------------------
FECHA_INI   = date(2025, 7, 1)
FECHA_TRAM  = date(2025, 7, 2)
FECHA_TAREA = date(2025, 7, 3)
FECHA_FIN   = date(2026, 1, 15)


# ---------------------------------------------------------------------------
# Carga de IDs desde BD (por código — inmune a reasignaciones de secuencia)
# ---------------------------------------------------------------------------
def cargar_ids():
    fases = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_fases')).fetchall()}
    tramites = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_tramites')).fetchall()}
    solicitudes = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT siglas, id FROM public.tipos_solicitudes')).fetchall()}
    expedientes = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT tipo, id FROM public.tipos_expedientes')).fetchall()}
    docs = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_documentos')).fetchall()}
    resultados = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_resultados_fases')).fetchall()}
    tareas = {r[0]: r[1] for r in db.session.execute(
        db.text('SELECT codigo, id FROM public.tipos_tareas')).fetchall()}
    return fases, tramites, solicitudes, expedientes, docs, resultados, tareas


# ---------------------------------------------------------------------------
# Helpers
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


def crear_exp(numero_at, entidad, tipo_exp_id):
    p = Proyecto(
        titulo=f'Proyecto AT{numero_at}',
        descripcion=f'Instalación de prueba escenario AT{numero_at}',
        fecha=date(2025, 1, 1),
        finalidad='Prueba de escenario listado inteligente',
        emplazamiento='Sevilla',
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


def crear_sol(exp, tipo_sol_id, entidad, fecha=None, doc_solicitud=None):
    s = Solicitud(
        expediente_id=exp.id,
        entidad_id=entidad.id,
        tipo_solicitud_id=tipo_sol_id,
        documento_solicitud_id=doc_solicitud.id if doc_solicitud else None,
    )
    db.session.add(s)
    db.session.flush()
    return s


def crear_doc(exp, url, tipo_doc_id, fecha_adm=None):
    d = Documento(
        expediente_id=exp.id,
        tipo_doc_id=tipo_doc_id,
        url=url,
        asunto=url.split('/')[-1],
        fecha_administrativa=fecha_adm,
    )
    db.session.add(d)
    db.session.flush()
    return d


def crear_fase(sol, tipo_fase_id, fin=None, resultado_id=None):
    f = Fase(
        solicitud_id=sol.id,
        tipo_fase_id=tipo_fase_id,
        resultado_fase_id=resultado_id,
    )
    db.session.add(f)
    db.session.flush()
    return f


def crear_tramite(fase, tipo_tramite_id):
    t = Tramite(
        fase_id=fase.id,
        tipo_tramite_id=tipo_tramite_id,
    )
    db.session.add(t)
    db.session.flush()
    return t


def crear_tarea(tramite, tipo_tarea_id, doc_usado=None, doc_producido=None, notas=None):
    t = Tarea(
        tramite_id=tramite.id,
        tipo_tarea_id=tipo_tarea_id,
        documento_usado_id=doc_usado.id if doc_usado else None,
        documento_producido_id=doc_producido.id if doc_producido else None,
        notas=notas,
    )
    db.session.add(t)
    db.session.flush()
    return t


def fase_fin(sol, tipo_fase_id, resultado_id=None):
    return crear_fase(sol, tipo_fase_id, resultado_id=resultado_id)


# ---------------------------------------------------------------------------
# Escenarios
# ---------------------------------------------------------------------------
with app.app_context():
    print('Cargando IDs de maestros desde BD...')
    TF, TT, TS, TE, TDOC, TRES, TTAREA = cargar_ids()

    # Atajos legibles
    TF_SOL  = TF['ANALISIS_SOLICITUD']
    TF_MA   = TF['COMPATIBILIDAD_AMBIENTAL']
    TF_CONS = TF['CONSULTAS']
    TF_IP   = TF['INFORMACION_PUBLICA']
    TF_RES  = TF['RESOLUCION']

    TT_ANAL_DOC = TT['ANALISIS_DOCUMENTAL']
    TT_REQ_SUB  = TT['REQUERIMIENTO_SUBSANACION']
    TT_CONS_SEP = TT['CONSULTA_SEPARATA']
    TT_SOL_COMP = TT['SOLICITUD_COMPATIBILIDAD']
    TT_BOP      = TT['ANUNCIO_BOP']
    TT_ELAB     = TT['ELABORACION']
    TT_NOTIF    = TT['NOTIFICACION']

    TS_AAP_AAC = TS['AAP_AAC']
    TS_AAE_DEF = TS['AAE_DEFINITIVA']

    TE_DIST    = TE['Distribución']

    TDOC_OTROS = TDOC.get('OTROS', next(iter(TDOC.values())))
    TRES_FAV   = TRES.get('FAVORABLE', next(iter(TRES.values())))

    TAREA_ANAL = TTAREA['ANALIZAR']
    TAREA_RED  = TTAREA['REDACTAR']
    TAREA_FIR  = TTAREA['FIRMAR']
    TAREA_NOT  = TTAREA['NOTIFICAR']
    TAREA_PUB  = TTAREA['PUBLICAR']
    TAREA_ESP  = TTAREA['ESPERAR_PLAZO']

    print('Limpiando datos operativos previos...')
    limpiar()

    # Entidades de prueba
    e_dist = Entidad(nombre_completo='Gran Distribuidora Eléctrica S.A.', rol_titular=True, activo=True, tipo_titular='GRAN_DISTRIBUIDORA')
    e_prom = Entidad(nombre_completo='Promotor Solar Sur S.L.', rol_titular=True, activo=True, tipo_titular='PROMOTOR')
    db.session.add_all([e_dist, e_prom])
    db.session.flush()

    # ------------------------------------------------------------------
    # T01 | AAP_AAC | SOL=PENDIENTE_ESTUDIO | ANALIZAR con doc_usado, sin doc_producido
    # ------------------------------------------------------------------
    exp01 = crear_exp(1001, e_dist, TE_DIST)
    sol_recibida01 = crear_doc(exp01, 'seed://sol_recibida_T01', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol01 = crear_sol(exp01, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida01)
    f01 = crear_fase(sol01, TF_SOL)
    t01 = crear_tramite(f01, TT_ANAL_DOC)
    crear_tarea(t01, TAREA_ANAL, doc_usado=sol_recibida01)
    print('T01 OK — SOL=PENDIENTE_ESTUDIO')

    # ------------------------------------------------------------------
    # T02 | AAP_AAC | SOL=PENDIENTE_REDACTAR | REDACTAR con doc_usado, sin doc_producido
    # ------------------------------------------------------------------
    exp02 = crear_exp(1002, e_dist, TE_DIST)
    sol_recibida02 = crear_doc(exp02, 'seed://sol_recibida_T02', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol02 = crear_sol(exp02, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida02)
    f02 = crear_fase(sol02, TF_SOL)
    t02 = crear_tramite(f02, TT_REQ_SUB)
    crear_tarea(t02, TAREA_RED, doc_usado=sol_recibida02)
    print('T02 OK — SOL=PENDIENTE_REDACTAR')

    # ------------------------------------------------------------------
    # T03 | AAP_AAC | SOL=PENDIENTE_FIRMA | FIRMAR con borrador, sin firmado
    # ------------------------------------------------------------------
    exp03 = crear_exp(1003, e_dist, TE_DIST)
    sol_recibida03 = crear_doc(exp03, 'seed://sol_recibida_T03', TDOC_OTROS, fecha_adm=FECHA_INI)
    borrador03 = crear_doc(exp03, 'seed://borrador_T03', TDOC_OTROS)
    sol03 = crear_sol(exp03, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida03)
    f03 = crear_fase(sol03, TF_SOL)
    t03 = crear_tramite(f03, TT_REQ_SUB)
    crear_tarea(t03, TAREA_FIR, doc_usado=borrador03)
    print('T03 OK — SOL=PENDIENTE_FIRMA')

    # ------------------------------------------------------------------
    # T04 | Mismo AT, dos solicitudes activas (indicador visual)
    #      Sol 1 AAP_AAC: SOL=PENDIENTE_SUBSANAR, CONSULTAS=PENDIENTE_PLAZOS
    #      Sol 2 AAE_DEF: SOL=PENDIENTE_ESTUDIO
    # ------------------------------------------------------------------
    exp04 = crear_exp(1004, e_dist, TE_DIST)

    sol_recibida04a = crear_doc(exp04, 'seed://sol_recibida_T04a', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol04a = crear_sol(exp04, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida04a)
    f04a_sol = crear_fase(sol04a, TF_SOL)
    t04a_req = crear_tramite(f04a_sol, TT_REQ_SUB)
    crear_tarea(t04a_req, TAREA_ESP, notas='PLAZO_DIAS=0')
    f04a_cons = crear_fase(sol04a, TF_CONS)
    t04a_sep = crear_tramite(f04a_cons, TT_CONS_SEP)
    crear_tarea(t04a_sep, TAREA_ESP, notas='PLAZO_DIAS=0')

    sol_recibida04b = crear_doc(exp04, 'seed://sol_recibida_T04b', TDOC_OTROS, fecha_adm=date(2025, 8, 1))
    sol04b = crear_sol(exp04, TS_AAE_DEF, e_dist, fecha=date(2025, 8, 1), doc_solicitud=sol_recibida04b)
    f04b_sol = crear_fase(sol04b, TF_SOL)
    t04b = crear_tramite(f04b_sol, TT_ANAL_DOC)
    crear_tarea(t04b, TAREA_ANAL, doc_usado=sol_recibida04b)
    print('T04 OK — dos filas: PENDIENTE_SUBSANAR+PENDIENTE_PLAZOS / PENDIENTE_ESTUDIO')

    # ------------------------------------------------------------------
    # T05 | AAP_AAC | SOL=FIN, CONSULTAS=PENDIENTE_NOTIFICAR
    # ------------------------------------------------------------------
    exp05 = crear_exp(1005, e_dist, TE_DIST)
    sol_recibida05 = crear_doc(exp05, 'seed://sol_recibida_T05', TDOC_OTROS, fecha_adm=FECHA_INI)
    firmado05 = crear_doc(exp05, 'seed://firmado_T05', TDOC_OTROS)
    sol05 = crear_sol(exp05, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida05)
    fase_fin(sol05, TF_SOL, TRES_FAV)
    f05_cons = crear_fase(sol05, TF_CONS)
    t05_sep = crear_tramite(f05_cons, TT_CONS_SEP)
    crear_tarea(t05_sep, TAREA_NOT, doc_usado=firmado05)
    print('T05 OK — SOL=FIN, CONSULTAS=PENDIENTE_NOTIFICAR')

    # ------------------------------------------------------------------
    # T06 | AAP_AAC | SOL=FIN, CONSULTAS=FIN, MA=PENDIENTE_PLAZOS
    # ------------------------------------------------------------------
    exp06 = crear_exp(1006, e_dist, TE_DIST)
    sol_recibida06 = crear_doc(exp06, 'seed://sol_recibida_T06', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol06 = crear_sol(exp06, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida06)
    fase_fin(sol06, TF_SOL, TRES_FAV)
    fase_fin(sol06, TF_CONS, TRES_FAV)
    f06_ma = crear_fase(sol06, TF_MA)
    t06_comp = crear_tramite(f06_ma, TT_SOL_COMP)
    crear_tarea(t06_comp, TAREA_ESP, notas='PLAZO_DIAS=0')
    print('T06 OK — SOL=FIN, CONSULTAS=FIN, MA=PENDIENTE_PLAZOS')

    # ------------------------------------------------------------------
    # T07 | AAP_AAC | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PUBLICAR
    # ------------------------------------------------------------------
    exp07 = crear_exp(1007, e_dist, TE_DIST)
    sol_recibida07 = crear_doc(exp07, 'seed://sol_recibida_T07', TDOC_OTROS, fecha_adm=FECHA_INI)
    firmado07 = crear_doc(exp07, 'seed://firmado_T07', TDOC_OTROS)
    sol07 = crear_sol(exp07, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida07)
    fase_fin(sol07, TF_SOL, TRES_FAV)
    fase_fin(sol07, TF_CONS, TRES_FAV)
    fase_fin(sol07, TF_MA, TRES_FAV)
    f07_ip = crear_fase(sol07, TF_IP)
    t07_bop = crear_tramite(f07_ip, TT_BOP)
    crear_tarea(t07_bop, TAREA_PUB, doc_usado=firmado07)
    print('T07 OK — SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PUBLICAR')

    # ------------------------------------------------------------------
    # T08 | AAP_AAC | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PLAZOS, RES=PENDIENTE_ESTUDIO
    # ------------------------------------------------------------------
    exp08 = crear_exp(1008, e_dist, TE_DIST)
    sol_recibida08_sol = crear_doc(exp08, 'seed://sol_recibida_T08_sol', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol08 = crear_sol(exp08, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida08_sol)
    fase_fin(sol08, TF_SOL, TRES_FAV)
    fase_fin(sol08, TF_CONS, TRES_FAV)
    fase_fin(sol08, TF_MA, TRES_FAV)
    f08_ip = crear_fase(sol08, TF_IP)
    t08_bop = crear_tramite(f08_ip, TT_BOP)
    crear_tarea(t08_bop, TAREA_ESP, notas='PLAZO_DIAS=0')
    sol_recibida08 = crear_doc(exp08, 'seed://sol_recibida_T08', TDOC_OTROS)
    f08_res = crear_fase(sol08, TF_RES)
    t08_elab = crear_tramite(f08_res, TT_ELAB)
    crear_tarea(t08_elab, TAREA_ANAL, doc_usado=sol_recibida08)
    print('T08 OK — SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PLAZOS, RES=PENDIENTE_ESTUDIO')

    # ------------------------------------------------------------------
    # T09 | AAP_AAC | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=FIN, RES=PENDIENTE_NOTIFICAR
    # ------------------------------------------------------------------
    exp09 = crear_exp(1009, e_dist, TE_DIST)
    sol_recibida09 = crear_doc(exp09, 'seed://sol_recibida_T09', TDOC_OTROS, fecha_adm=FECHA_INI)
    firmado09 = crear_doc(exp09, 'seed://firmado_T09', TDOC_OTROS)
    sol09 = crear_sol(exp09, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida09)
    fase_fin(sol09, TF_SOL, TRES_FAV)
    fase_fin(sol09, TF_CONS, TRES_FAV)
    fase_fin(sol09, TF_MA, TRES_FAV)
    fase_fin(sol09, TF_IP, TRES_FAV)
    f09_res = crear_fase(sol09, TF_RES)
    t09_notif = crear_tramite(f09_res, TT_NOTIF)
    crear_tarea(t09_notif, TAREA_NOT, doc_usado=firmado09)
    print('T09 OK — SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=FIN, RES=PENDIENTE_NOTIFICAR')

    # ------------------------------------------------------------------
    # T10 | AAP_AAC | Todas las pistas FIN → FIN=TRUE
    # ------------------------------------------------------------------
    exp10 = crear_exp(1010, e_dist, TE_DIST)
    sol_recibida10 = crear_doc(exp10, 'seed://sol_recibida_T10', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol10 = crear_sol(exp10, TS_AAP_AAC, e_dist, doc_solicitud=sol_recibida10)
    fase_fin(sol10, TF_SOL, TRES_FAV)
    fase_fin(sol10, TF_CONS, TRES_FAV)
    fase_fin(sol10, TF_MA, TRES_FAV)
    fase_fin(sol10, TF_IP, TRES_FAV)
    fase_fin(sol10, TF_RES, TRES_FAV)
    print('T10 OK — Todas las pistas FIN (FIN=TRUE)')

    # ------------------------------------------------------------------
    # T11 | AAP_AAC | SOL=PENDIENTE_TRAMITAR | Sin fases creadas
    # ------------------------------------------------------------------
    exp11 = crear_exp(1011, e_prom, TE_DIST)
    sol_recibida11 = crear_doc(exp11, 'seed://sol_recibida_T11', TDOC_OTROS, fecha_adm=FECHA_INI)
    sol11 = crear_sol(exp11, TS_AAP_AAC, e_prom, doc_solicitud=sol_recibida11)
    print('T11 OK — SOL=PENDIENTE_TRAMITAR (sin fases)')

    db.session.commit()

    from sqlalchemy import text
    r = db.session.execute(text(
        "SELECT 'expedientes' t, COUNT(*) n FROM expedientes"
        " UNION ALL SELECT 'solicitudes', COUNT(*) FROM solicitudes"
        " UNION ALL SELECT 'fases', COUNT(*) FROM fases"
        " UNION ALL SELECT 'tramites', COUNT(*) FROM tramites"
        " UNION ALL SELECT 'tareas', COUNT(*) FROM tareas"
        " UNION ALL SELECT 'documentos', COUNT(*) FROM documentos"
    )).fetchall()
    print('\nResumen BD tras seed:')
    for row in r:
        print(f'  {row[0]:15s}: {row[1]}')
    print('\nSeed completado correctamente.')
