"""
verificar_seed.py — Verifica la estructura de los 11 escenarios del listado inteligente

Comprueba que seed_listado.py ha creado correctamente los datos operativos
para los escenarios T01-T11 de ANALISIS_LISTADO_INTELIGENTE.md §6.

Sirve como test de regresión para cuando exista seguimiento.py:
en ese momento, además de verificar la estructura, se podrá comprobar
que el estado deducido por el servicio coincide con el esperado.

Uso:
    cd /d/BDDAT
    source venv/Scripts/activate
    python scripts/verificar_seed.py

Prerequisito: haber ejecutado seed_listado.py al menos una vez.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

# ---------------------------------------------------------------------------
# Infraestructura de verificación
# ---------------------------------------------------------------------------

_errores = []
_total   = 0
_ok      = 0


def check(descripcion, condicion, detalle=''):
    """Registra un check individual. Imprime OK o FAIL."""
    global _total, _ok
    _total += 1
    if condicion:
        _ok += 1
        print(f'  OK  {descripcion}')
    else:
        _errores.append(descripcion + (f' — {detalle}' if detalle else ''))
        print(f'  FAIL {descripcion}' + (f' — {detalle}' if detalle else ''))


def seccion(titulo):
    print(f'\n[{titulo}]')


# ---------------------------------------------------------------------------
# Consultas auxiliares
# ---------------------------------------------------------------------------

def q(sql, **params):
    return db.session.execute(db.text(sql), params).fetchall()


def q1(sql, **params):
    row = db.session.execute(db.text(sql), params).fetchone()
    return row[0] if row else None


def fases_de_sol(sol_id):
    """Devuelve lista de (tipo_fase_codigo, documento_resultado_id, resultado_fase_codigo).
    f[1] IS NULL → fase no finalizada; f[1] IS NOT NULL → fase finalizada (doc de resultado asignado)."""
    return q("""
        SELECT tf.codigo, f.documento_resultado_id, trf.codigo
        FROM fases f
        JOIN tipos_fases tf ON tf.id = f.tipo_fase_id
        LEFT JOIN tipos_resultados_fases trf ON trf.id = f.resultado_fase_id
        WHERE f.solicitud_id = :sid
        ORDER BY f.id
    """, sid=sol_id)


def tramites_de_fase(fase_codigo, sol_id):
    """Devuelve lista de (tipo_tramite_codigo,) para la fase indicada."""
    return q("""
        SELECT tt.codigo
        FROM tramites tr
        JOIN fases f ON f.id = tr.fase_id
        JOIN tipos_fases tf ON tf.id = f.tipo_fase_id
        JOIN tipos_tramites tt ON tt.id = tr.tipo_tramite_id
        WHERE f.solicitud_id = :sid AND tf.codigo = :fc
        ORDER BY tr.id
    """, sid=sol_id, fc=fase_codigo)


def tareas_de_tramite(tramite_codigo, sol_id):
    """Devuelve lista de (tipo_tarea_codigo, doc_usado_id, doc_producido_id, notas)."""
    return q("""
        SELECT tta.codigo, ta.documento_usado_id, ta.documento_producido_id, ta.notas
        FROM tareas ta
        JOIN tramites tr ON tr.id = ta.tramite_id
        JOIN fases f ON f.id = tr.fase_id
        JOIN tipos_tramites tt ON tt.id = tr.tipo_tramite_id
        JOIN tipos_tareas tta ON tta.id = ta.tipo_tarea_id
        WHERE f.solicitud_id = :sid AND tt.codigo = :tc
        ORDER BY ta.id
    """, sid=sol_id, tc=tramite_codigo)


def sol_de_at(numero_at, tipo_sol_codigo, nth=1):
    """
    Devuelve el id de la N-ésima solicitud del AT con ese tipo.
    nth=1 para la primera, nth=2 para la segunda...
    """
    rows = q("""
        SELECT s.id
        FROM solicitudes s
        JOIN expedientes e ON e.id = s.expediente_id
        JOIN tipos_solicitudes ts ON ts.id = s.tipo_solicitud_id
        WHERE e.numero_at = :nat AND ts.siglas = :ts
        ORDER BY s.id
    """, nat=numero_at, ts=tipo_sol_codigo)
    if len(rows) >= nth:
        return rows[nth - 1][0]
    return None


def n_soles_de_at(numero_at):
    return q1("SELECT COUNT(*) FROM solicitudes s JOIN expedientes e ON e.id=s.expediente_id WHERE e.numero_at=:n", n=numero_at)


# ---------------------------------------------------------------------------
# Verificaciones por escenario
# ---------------------------------------------------------------------------

def verificar_T01():
    seccion('T01 | AT=1001 | SOL=PENDIENTE_ESTUDIO | ANALIZAR con doc_usado, sin doc_producido')
    sid = sol_de_at(1001, 'AAP_AAC')
    check('T01: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    check('T01: exactamente 1 fase', len(fases) == 1, f'hay {len(fases)}')
    check('T01: fase es ANALISIS_SOLICITUD', any(f[0] == 'ANALISIS_SOLICITUD' for f in fases))
    check('T01: fase no finalizada (sin doc_resultado)', all(f[1] is None for f in fases))

    trams = tramites_de_fase('ANALISIS_SOLICITUD', sid)
    check('T01: 1 trámite ANALISIS_DOCUMENTAL', len(trams) == 1 and trams[0][0] == 'ANALISIS_DOCUMENTAL',
          f'trámites: {[t[0] for t in trams]}')

    tareas = tareas_de_tramite('ANALISIS_DOCUMENTAL', sid)
    check('T01: 1 tarea ANALIZAR', len(tareas) == 1 and tareas[0][0] == 'ANALIZAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T01: ANALIZAR con doc_usado presente', tareas[0][1] is not None,
              'doc_usado es NULL')
        check('T01: ANALIZAR sin doc_producido', tareas[0][2] is None,
              f'doc_producido={tareas[0][2]}')


def verificar_T02():
    seccion('T02 | AT=1002 | SOL=PENDIENTE_REDACTAR (REDACTAR sin borrador)')
    sid = sol_de_at(1002, 'AAP_AAC')
    check('T02: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    check('T02: fase ANALISIS_SOLICITUD abierta', any(f[0] == 'ANALISIS_SOLICITUD' and f[1] is None for f in fases))

    trams = tramites_de_fase('ANALISIS_SOLICITUD', sid)
    check('T02: trámite REQUERIMIENTO_SUBSANACION', len(trams) == 1 and trams[0][0] == 'REQUERIMIENTO_SUBSANACION',
          f'trámites: {[t[0] for t in trams]}')

    tareas = tareas_de_tramite('REQUERIMIENTO_SUBSANACION', sid)
    check('T02: tarea REDACTAR', len(tareas) == 1 and tareas[0][0] == 'REDACTAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T02: REDACTAR sin doc_producido', tareas[0][2] is None,
              f'doc_producido={tareas[0][2]}')


def verificar_T03():
    seccion('T03 | AT=1003 | SOL=PENDIENTE_FIRMA (FIRMAR con borrador, sin firmado)')
    sid = sol_de_at(1003, 'AAP_AAC')
    check('T03: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    # Documento borrador en el expediente
    exp_id = q1("SELECT e.id FROM expedientes e WHERE e.numero_at=1003")
    n_docs = q1("SELECT COUNT(*) FROM documentos WHERE expediente_id=:eid", eid=exp_id)
    check('T03: 1 documento (borrador) en expediente', n_docs == 1, f'hay {n_docs}')

    tareas = tareas_de_tramite('REQUERIMIENTO_SUBSANACION', sid)
    check('T03: tarea FIRMAR', len(tareas) == 1 and tareas[0][0] == 'FIRMAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T03: FIRMAR con doc_usado (borrador)', tareas[0][1] is not None,
              'doc_usado es NULL')
        check('T03: FIRMAR sin doc_producido (firmado ausente)', tareas[0][2] is None,
              f'doc_producido={tareas[0][2]}')


def verificar_T04():
    seccion('T04 | AT=1004 | Dos solicitudes activas en el mismo AT')
    n = n_soles_de_at(1004)
    check('T04: exactamente 2 solicitudes en AT=1004', n == 2, f'hay {n}')

    # Sol A: AAP_AAC — PENDIENTE_SUBSANAR + PENDIENTE_PLAZOS
    sid_a = sol_de_at(1004, 'AAP_AAC')
    check('T04a: solicitud AAP_AAC existe', sid_a is not None)
    if sid_a:
        fases_a = fases_de_sol(sid_a)
        codigos_a = [f[0] for f in fases_a]
        check('T04a: fase ANALISIS_SOLICITUD', 'ANALISIS_SOLICITUD' in codigos_a)
        check('T04a: fase CONSULTAS', 'CONSULTAS' in codigos_a)
        check('T04a: ambas fases abiertas', all(f[1] is None for f in fases_a))

        tareas_req = tareas_de_tramite('REQUERIMIENTO_SUBSANACION', sid_a)
        check('T04a: tarea ESPERAR_PLAZO en SOL (subsanar)', len(tareas_req) == 1 and tareas_req[0][0] == 'ESPERAR_PLAZO',
              f'tareas: {[t[0] for t in tareas_req]}')
        if tareas_req:
            check('T04a: notas PLAZO_DIAS=0 en SOL (espera indefinida)', tareas_req[0][3] == 'PLAZO_DIAS=0',
                  f'notas={tareas_req[0][3]!r}')

        tareas_cons = tareas_de_tramite('CONSULTA_SEPARATA', sid_a)
        check('T04a: tarea ESPERAR_PLAZO en CONSULTAS', len(tareas_cons) == 1 and tareas_cons[0][0] == 'ESPERAR_PLAZO',
              f'tareas: {[t[0] for t in tareas_cons]}')
        if tareas_cons:
            check('T04a: notas PLAZO_DIAS=0 en CONSULTAS (espera indefinida)', tareas_cons[0][3] == 'PLAZO_DIAS=0',
                  f'notas={tareas_cons[0][3]!r}')

    # Sol B: AAE_DEFINITIVA — PENDIENTE_ESTUDIO
    sid_b = sol_de_at(1004, 'AAE_DEFINITIVA')
    check('T04b: solicitud AAE_DEFINITIVA existe', sid_b is not None)
    if sid_b:
        tareas_b = tareas_de_tramite('ANALISIS_DOCUMENTAL', sid_b)
        check('T04b: tarea ANALIZAR con doc_usado', len(tareas_b) == 1 and tareas_b[0][0] == 'ANALIZAR',
              f'tareas: {[t[0] for t in tareas_b]}')
        if tareas_b:
            check('T04b: ANALIZAR con doc_usado presente', tareas_b[0][1] is not None,
                  'doc_usado es NULL')


def verificar_T05():
    seccion('T05 | AT=1005 | SOL=FIN, CONSULTAS=PENDIENTE_NOTIFICAR')
    sid = sol_de_at(1005, 'AAP_AAC')
    check('T05: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    fases_dict = {f[0]: f for f in fases}
    check('T05: fase ANALISIS_SOLICITUD finalizada', 'ANALISIS_SOLICITUD' in fases_dict and fases_dict['ANALISIS_SOLICITUD'][1] is not None)
    check('T05: fase CONSULTAS abierta', 'CONSULTAS' in fases_dict and fases_dict['CONSULTAS'][1] is None)

    tareas = tareas_de_tramite('CONSULTA_SEPARATA', sid)
    check('T05: tarea NOTIFICAR en CONSULTAS', len(tareas) == 1 and tareas[0][0] == 'NOTIFICAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T05: NOTIFICAR con doc_usado (firmado)', tareas[0][1] is not None)
        check('T05: NOTIFICAR sin doc_producido (justificante ausente)', tareas[0][2] is None)


def verificar_T06():
    seccion('T06 | AT=1006 | SOL=FIN, CONSULTAS=FIN, MA=PENDIENTE_PLAZOS')
    sid = sol_de_at(1006, 'AAP_AAC')
    check('T06: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    fases_dict = {f[0]: f for f in fases}
    check('T06: ANALISIS_SOLICITUD finalizada', 'ANALISIS_SOLICITUD' in fases_dict and fases_dict['ANALISIS_SOLICITUD'][1] is not None)
    check('T06: CONSULTAS finalizada', 'CONSULTAS' in fases_dict and fases_dict['CONSULTAS'][1] is not None)
    check('T06: COMPATIBILIDAD_AMBIENTAL abierta', 'COMPATIBILIDAD_AMBIENTAL' in fases_dict and fases_dict['COMPATIBILIDAD_AMBIENTAL'][1] is None)

    tareas = tareas_de_tramite('SOLICITUD_COMPATIBILIDAD', sid)
    check('T06: tarea ESPERAR_PLAZO en MA', len(tareas) == 1 and tareas[0][0] == 'ESPERAR_PLAZO',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T06: notas PLAZO_DIAS=0 (espera indefinida)', tareas[0][3] == 'PLAZO_DIAS=0',
              f'notas={tareas[0][3]!r}')


def verificar_T07():
    seccion('T07 | AT=1007 | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PUBLICAR')
    sid = sol_de_at(1007, 'AAP_AAC')
    check('T07: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    fases_dict = {f[0]: f for f in fases}
    for pista in ('ANALISIS_SOLICITUD', 'CONSULTAS', 'COMPATIBILIDAD_AMBIENTAL'):
        check(f'T07: {pista} finalizada', pista in fases_dict and fases_dict[pista][1] is not None)
    check('T07: INFORMACION_PUBLICA abierta', 'INFORMACION_PUBLICA' in fases_dict and fases_dict['INFORMACION_PUBLICA'][1] is None)

    tareas = tareas_de_tramite('ANUNCIO_BOP', sid)
    check('T07: tarea PUBLICAR en IP', len(tareas) == 1 and tareas[0][0] == 'PUBLICAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T07: PUBLICAR con doc_usado (firmado)', tareas[0][1] is not None)
        check('T07: PUBLICAR sin doc_producido (justificante ausente)', tareas[0][2] is None)


def verificar_T08():
    seccion('T08 | AT=1008 | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=PENDIENTE_PLAZOS, RES=PENDIENTE_ESTUDIO')
    sid = sol_de_at(1008, 'AAP_AAC')
    check('T08: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    fases_dict = {f[0]: f for f in fases}
    for pista in ('ANALISIS_SOLICITUD', 'CONSULTAS', 'COMPATIBILIDAD_AMBIENTAL'):
        check(f'T08: {pista} finalizada', pista in fases_dict and fases_dict[pista][1] is not None)
    check('T08: INFORMACION_PUBLICA abierta', 'INFORMACION_PUBLICA' in fases_dict and fases_dict['INFORMACION_PUBLICA'][1] is None)
    check('T08: RESOLUCION abierta', 'RESOLUCION' in fases_dict and fases_dict['RESOLUCION'][1] is None)

    tareas_ip = tareas_de_tramite('ANUNCIO_BOP', sid)
    check('T08: ESPERAR_PLAZO en IP', len(tareas_ip) == 1 and tareas_ip[0][0] == 'ESPERAR_PLAZO',
          f'tareas IP: {[t[0] for t in tareas_ip]}')
    if tareas_ip:
        check('T08: notas PLAZO_DIAS=0 (espera indefinida)', tareas_ip[0][3] == 'PLAZO_DIAS=0',
              f'notas={tareas_ip[0][3]!r}')

    tareas_res = tareas_de_tramite('ELABORACION', sid)
    check('T08: ANALIZAR en RESOLUCION', len(tareas_res) == 1 and tareas_res[0][0] == 'ANALIZAR',
          f'tareas RES: {[t[0] for t in tareas_res]}')
    if tareas_res:
        check('T08: ANALIZAR con doc_usado (resolución con input)', tareas_res[0][1] is not None,
              'doc_usado es NULL')


def verificar_T09():
    seccion('T09 | AT=1009 | SOL=FIN, CONSULTAS=FIN, MA=FIN, IP=FIN, RES=PENDIENTE_NOTIFICAR')
    sid = sol_de_at(1009, 'AAP_AAC')
    check('T09: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    fases_dict = {f[0]: f for f in fases}
    for pista in ('ANALISIS_SOLICITUD', 'CONSULTAS', 'COMPATIBILIDAD_AMBIENTAL', 'INFORMACION_PUBLICA'):
        check(f'T09: {pista} finalizada', pista in fases_dict and fases_dict[pista][1] is not None)
    check('T09: RESOLUCION abierta', 'RESOLUCION' in fases_dict and fases_dict['RESOLUCION'][1] is None)

    tareas = tareas_de_tramite('NOTIFICACION', sid)
    check('T09: tarea NOTIFICAR en RESOLUCION', len(tareas) == 1 and tareas[0][0] == 'NOTIFICAR',
          f'tareas: {[t[0] for t in tareas]}')
    if tareas:
        check('T09: NOTIFICAR con doc_usado (resolución firmada)', tareas[0][1] is not None)
        check('T09: NOTIFICAR sin doc_producido (justificante ausente)', tareas[0][2] is None)


def verificar_T10():
    seccion('T10 | AT=1010 | Todas las pistas FIN (FIN=TRUE)')
    sid = sol_de_at(1010, 'AAP_AAC')
    check('T10: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    pistas_esperadas = {
        'ANALISIS_SOLICITUD', 'CONSULTAS', 'COMPATIBILIDAD_AMBIENTAL',
        'INFORMACION_PUBLICA', 'RESOLUCION',
    }
    codigos = {f[0] for f in fases}
    check('T10: 5 fases presentes', pistas_esperadas == codigos,
          f'hay: {codigos}')
    check('T10: todas las fases finalizadas', all(f[1] is not None for f in fases),
          f'sin doc_resultado: {[f[0] for f in fases if f[1] is None]}')
    check('T10: todas con resultado', all(f[2] is not None for f in fases),
          f'sin resultado: {[f[0] for f in fases if f[2] is None]}')
    check('T10: sin tareas documentales pendientes',
          q1("""SELECT COUNT(*) FROM tareas ta
                JOIN tramites tr ON tr.id = ta.tramite_id
                JOIN fases f ON f.id = tr.fase_id
                JOIN tipos_tareas tt ON tt.id = ta.tipo_tarea_id
                WHERE f.solicitud_id = :s
                AND tt.codigo IN ('INCORPORAR','ANALISIS','REDACTAR','FIRMAR','NOTIFICAR','PUBLICAR')
                AND ta.documento_producido_id IS NULL""", s=sid) == 0)


def verificar_T11():
    seccion('T11 | AT=1011 | SOL=PENDIENTE_TRAMITAR (sin fases)')
    sid = sol_de_at(1011, 'AAP_AAC')
    check('T11: solicitud AAP_AAC existe', sid is not None)
    if not sid:
        return

    fases = fases_de_sol(sid)
    check('T11: 0 fases', len(fases) == 0, f'hay {len(fases)}')

    estado = q1("SELECT estado FROM solicitudes WHERE id=:s", s=sid)
    check('T11: solicitud EN_TRAMITE', estado == 'EN_TRAMITE', f'estado={estado!r}')


# ---------------------------------------------------------------------------
# Sección 2: estados deducidos por seguimiento.py
# ---------------------------------------------------------------------------

from app.services.seguimiento import estado_solicitud, fin_total


# Estados esperados por escenario: {pista: codigo_esperado | None}
# None = N/A (sin fases de ese tipo)
ESPERADOS = {
    # (numero_at, tipo_siglas): {pista: estado_esperado}
    (1001, 'AAP_AAC'):      {'SOL': 'PENDIENTE_ESTUDIO',   'CONSULTAS': None,                'MA': None, 'IP': None, 'RES': None},
    (1002, 'AAP_AAC'):      {'SOL': 'PENDIENTE_REDACTAR',  'CONSULTAS': None,                'MA': None, 'IP': None, 'RES': None},
    (1003, 'AAP_AAC'):      {'SOL': 'PENDIENTE_FIRMA',     'CONSULTAS': None,                'MA': None, 'IP': None, 'RES': None},
    (1004, 'AAP_AAC'):      {'SOL': 'PENDIENTE_SUBSANAR',  'CONSULTAS': 'PENDIENTE_PLAZOS',  'MA': None, 'IP': None, 'RES': None},
    (1004, 'AAE_DEFINITIVA'):{'SOL': 'PENDIENTE_ESTUDIO',  'CONSULTAS': None,                'MA': None, 'IP': None, 'RES': None},
    (1005, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'PENDIENTE_NOTIFICAR','MA': None, 'IP': None, 'RES': None},
    (1006, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'FIN',               'MA': 'PENDIENTE_PLAZOS', 'IP': None, 'RES': None},
    (1007, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'FIN',               'MA': 'FIN', 'IP': 'PENDIENTE_PUBLICAR', 'RES': None},
    (1008, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'FIN',               'MA': 'FIN', 'IP': 'PENDIENTE_PLAZOS', 'RES': 'PENDIENTE_ESTUDIO'},
    (1009, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'FIN',               'MA': 'FIN', 'IP': 'FIN', 'RES': 'PENDIENTE_NOTIFICAR'},
    (1010, 'AAP_AAC'):      {'SOL': 'FIN',                 'CONSULTAS': 'FIN',               'MA': 'FIN', 'IP': 'FIN', 'RES': 'FIN'},
    (1011, 'AAP_AAC'):      {'SOL': 'PENDIENTE_TRAMITAR',  'CONSULTAS': None,                'MA': None, 'IP': None, 'RES': None},
}

FIN_TOTAL_ESPERADO = {
    (1001, 'AAP_AAC'): False,
    (1002, 'AAP_AAC'): False,
    (1003, 'AAP_AAC'): False,
    (1004, 'AAP_AAC'): False,
    (1004, 'AAE_DEFINITIVA'): False,
    (1005, 'AAP_AAC'): False,
    (1006, 'AAP_AAC'): False,
    (1007, 'AAP_AAC'): False,
    (1008, 'AAP_AAC'): False,
    (1009, 'AAP_AAC'): False,
    (1010, 'AAP_AAC'): True,
    (1011, 'AAP_AAC'): False,
}


def verificar_estados():
    seccion('ESTADOS DEDUCIDOS — seguimiento.py')
    for (nat, siglas), esperado in ESPERADOS.items():
        sid = sol_de_at(nat, siglas)
        if sid is None:
            check(f'AT={nat} {siglas}: solicitud encontrada para verificar estados', False)
            continue

        try:
            estados = estado_solicitud(sid)
        except Exception as exc:
            check(f'AT={nat} {siglas}: estado_solicitud sin excepción', False, str(exc))
            continue

        for pista, cod_esperado in esperado.items():
            e = estados.get(pista)
            cod_real = e.codigo if e is not None else None
            check(
                f'AT={nat} {siglas} {pista}: {cod_esperado}',
                cod_real == cod_esperado,
                f'obtenido={cod_real!r}',
            )

        ft_esperado = FIN_TOTAL_ESPERADO[(nat, siglas)]
        ft_real = fin_total(estados)
        check(
            f'AT={nat} {siglas} fin_total={ft_esperado}',
            ft_real == ft_esperado,
            f'obtenido={ft_real}',
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

with app.app_context():
    print('Verificando escenarios seed del listado inteligente...')
    print('(Prerequisito: haber ejecutado scripts/seed_listado.py)')

    verificar_T01()
    verificar_T02()
    verificar_T03()
    verificar_T04()
    verificar_T05()
    verificar_T06()
    verificar_T07()
    verificar_T08()
    verificar_T09()
    verificar_T10()
    verificar_T11()
    verificar_estados()

    print(f'\n{"="*50}')
    print(f'Resultado: {_ok}/{_total} checks pasados')
    if _errores:
        print(f'\nFALLOS ({len(_errores)}):')
        for e in _errores:
            print(f'  - {e}')
        sys.exit(1)
    else:
        print('Todos los checks OK.')
