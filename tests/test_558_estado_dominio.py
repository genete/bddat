"""
test_558_estado_dominio.py — Núcleo único de reglas de estado (#558).

Tests unitarios puros: el núcleo es duck-typed (solo lee atributos), así que se
prueba con dobles ligeros sin tocar la BD. Cubre:
  - la regla de hoja estado_tarea para los 4 tipos y sus subestados,
  - las reglas de contenedor (incluido el cierre de fase es_finalizadora-aware),
  - el orden de prioridad canónico y su coherencia con el color.
"""
from types import SimpleNamespace

import app.services.estado_dominio as ed


# ---------------------------------------------------------------------------
# Dobles ligeros
# ---------------------------------------------------------------------------

def _doc(tipo_codigo=None):
    tipo_doc = SimpleNamespace(codigo=tipo_codigo) if tipo_codigo else None
    return SimpleNamespace(tipo_doc=tipo_doc)


def _notif(resultado, numero_intento=1):
    return SimpleNamespace(resultado=resultado, numero_intento=numero_intento)


def _tarea(codigo, *, consumidos=(), producido=None, notificacion=None):
    cons = list(consumidos)
    return SimpleNamespace(
        tipo_tarea=SimpleNamespace(codigo=codigo),
        documentos_consumidos=cons,
        documento_producido=producido,
        notificacion=notificacion,
        ejecutada=producido is not None,
        planificada=(not cons and producido is None),
    )


def _fase(*, planificada=False, pdte_cierre=False, finalizadora=False, resultado_fase_id=None):
    return SimpleNamespace(
        planificada=planificada,
        pdte_cierre=pdte_cierre,
        tipo_fase=SimpleNamespace(es_finalizadora=finalizadora),
        resultado_fase_id=resultado_fase_id,
    )


# ---------------------------------------------------------------------------
# Hoja — ANALIZAR
# ---------------------------------------------------------------------------

def test_analizar_planificada_tramitar():
    assert ed.estado_tarea(_tarea('ANALIZAR')) == 'PENDIENTE_TRAMITAR'

def test_analizar_consumido_estudio():
    assert ed.estado_tarea(_tarea('ANALIZAR', consumidos=[_doc()])) == 'PENDIENTE_ESTUDIO'

def test_analizar_producido_fin():
    assert ed.estado_tarea(_tarea('ANALIZAR', consumidos=[_doc()], producido=_doc())) == 'FIN'


# ---------------------------------------------------------------------------
# Hoja — ELABORAR (REDACTAR / FIRMA)
# ---------------------------------------------------------------------------

def test_elaborar_sin_consumido_tramitar():
    assert ed.estado_tarea(_tarea('ELABORAR')) == 'PENDIENTE_TRAMITAR'

def test_elaborar_sin_borrador_redactar():
    assert ed.estado_tarea(_tarea('ELABORAR', consumidos=[_doc()])) == 'PENDIENTE_REDACTAR'

def test_elaborar_con_borrador_firma():
    t = _tarea('ELABORAR', consumidos=[_doc(), _doc(tipo_codigo='BORRADOR_FIRMA')])
    assert ed.estado_tarea(t) == 'PENDIENTE_FIRMA'

def test_elaborar_producido_fin():
    t = _tarea('ELABORAR', consumidos=[_doc(tipo_codigo='BORRADOR_FIRMA')], producido=_doc())
    assert ed.estado_tarea(t) == 'FIN'


# ---------------------------------------------------------------------------
# Hoja — NOTIFICAR (escalada 🔵 → 🟠 → 🔴 vía Notificacion, anclada a tarea_id — ADR-034)
# ---------------------------------------------------------------------------

def test_notificar_sin_consumido_tramitar():
    assert ed.estado_tarea(_tarea('NOTIFICAR')) == 'PENDIENTE_TRAMITAR'

def test_notificar_sin_resultado_notificar():
    assert ed.estado_tarea(_tarea('NOTIFICAR', consumidos=[_doc()])) == 'PENDIENTE_NOTIFICAR'

def test_notificar_envio_registrado_sin_resultado():
    # Camino A ("Registrar envío"): fila creada, resultado aún None.
    t = _tarea('NOTIFICAR', consumidos=[_doc()], notificacion=_notif(None))
    assert ed.estado_tarea(t) == 'PENDIENTE_RESULTADO_NOTIFICACION'

def test_notificar_correcta_fin():
    t = _tarea('NOTIFICAR', consumidos=[_doc()], producido=_doc(), notificacion=_notif('CORRECTA'))
    assert ed.estado_tarea(t) == 'FIN'

def test_notificar_incorrecta_1_fallida():
    t = _tarea('NOTIFICAR', consumidos=[_doc()], producido=_doc(), notificacion=_notif('INCORRECTA', 1))
    assert ed.estado_tarea(t) == 'NOTIFICACION_FALLIDA'

def test_notificar_incorrecta_2_agotada():
    t = _tarea('NOTIFICAR', consumidos=[_doc()], producido=_doc(), notificacion=_notif('INCORRECTA', 2))
    assert ed.estado_tarea(t) == 'NOTIFICACION_AGOTADA'


# ---------------------------------------------------------------------------
# Hoja — ESPERAR_PLAZO (mapea el estado de plazo ya resuelto por la proyección)
# ---------------------------------------------------------------------------

def test_esperar_plazo_sin_plazo_tramitar():
    t = _tarea('ESPERAR_PLAZO', consumidos=[_doc()])
    assert ed.estado_tarea(t, plazo=None) == 'PENDIENTE_TRAMITAR'
    assert ed.estado_tarea(t, plazo={'estado': 'SIN_PLAZO'}) == 'PENDIENTE_TRAMITAR'

def test_esperar_plazo_en_plazo_plazos():
    t = _tarea('ESPERAR_PLAZO', consumidos=[_doc()])
    assert ed.estado_tarea(t, plazo={'estado': 'EN_PLAZO'}) == 'PENDIENTE_PLAZOS'

def test_esperar_plazo_vencido_estudio():
    t = _tarea('ESPERAR_PLAZO', consumidos=[_doc()])
    assert ed.estado_tarea(t, plazo={'estado': 'VENCIDO'}) == 'PENDIENTE_ESTUDIO'


# ---------------------------------------------------------------------------
# Contenedor — TRÁMITE
# ---------------------------------------------------------------------------

def test_tramite_planificado_tramitar():
    assert ed.estado_tramite(SimpleNamespace(tareas=[]), []) == ('PENDIENTE_TRAMITAR', True)

def test_tramite_agrega_mayor_prioridad():
    estados = ['PENDIENTE_NOTIFICAR', 'PENDIENTE_REDACTAR', 'FIN']
    assert ed.estado_tramite(SimpleNamespace(tareas=[1, 2, 3]), estados) == ('PENDIENTE_REDACTAR', False)


# ---------------------------------------------------------------------------
# Contenedor — FASE (cierre es_finalizadora-aware, el fix de #558)
# ---------------------------------------------------------------------------

def test_fase_planificada_tramitar():
    assert ed.estado_fase(_fase(planificada=True), []) == ('PENDIENTE_TRAMITAR', True)

def test_fase_finalizadora_sin_resultado_estudio():
    f = _fase(pdte_cierre=True, finalizadora=True, resultado_fase_id=None)
    assert ed.estado_fase(f, []) == ('PENDIENTE_ESTUDIO', True)

def test_fase_finalizadora_con_resultado_cerrar():
    f = _fase(pdte_cierre=True, finalizadora=True, resultado_fase_id=5)
    assert ed.estado_fase(f, []) == ('PENDIENTE_CERRAR', True)

def test_fase_intermedia_pdte_cierre_cerrar():
    # El fix: una intermedia (resultado_fase_id siempre NULL) va a CERRAR, no a ESTUDIO.
    f = _fase(pdte_cierre=True, finalizadora=False, resultado_fase_id=None)
    assert ed.estado_fase(f, []) == ('PENDIENTE_CERRAR', True)

def test_fase_en_curso_agrega():
    f = _fase()
    assert ed.estado_fase(f, ['PENDIENTE_CERRAR', 'PENDIENTE_NOTIFICAR']) == ('PENDIENTE_CERRAR', False)


# ---------------------------------------------------------------------------
# Contenedor — SOLICITUD / EXPEDIENTE
# ---------------------------------------------------------------------------

def test_solicitud_sin_fases_tramitar():
    assert ed.estado_solicitud(SimpleNamespace(fases=[], estado='EN_TRAMITE'), []) == ('PENDIENTE_TRAMITAR', True)

def test_solicitud_no_en_tramite_fin():
    assert ed.estado_solicitud(SimpleNamespace(fases=[1], estado='RESUELTA'), ['FIN']) == ('FIN', False)

def test_solicitud_todo_fin_pero_en_tramite_cerrar():
    sol = SimpleNamespace(fases=[1, 2], estado='EN_TRAMITE')
    assert ed.estado_solicitud(sol, ['FIN', 'FIN']) == ('PENDIENTE_CERRAR', True)

def test_solicitud_en_tramite_agrega():
    sol = SimpleNamespace(fases=[1, 2], estado='EN_TRAMITE')
    assert ed.estado_solicitud(sol, ['FIN', 'PENDIENTE_FIRMA']) == ('PENDIENTE_FIRMA', False)

def test_expediente_sin_solicitudes_tramitar():
    assert ed.estado_expediente(SimpleNamespace(), []) == ('PENDIENTE_TRAMITAR', True)

def test_expediente_agrega():
    assert ed.estado_expediente(SimpleNamespace(), ['FIN', 'PENDIENTE_CERRAR']) == ('PENDIENTE_CERRAR', False)


# ---------------------------------------------------------------------------
# Orden canónico y coherencia color↔prioridad
# ---------------------------------------------------------------------------

def test_mayor_prioridad_lista_vacia_fin():
    assert ed.mayor_prioridad([]) == 'FIN'

def test_orden_naranja_gana_a_azul():
    # Inversión decidida en #558: 🟠 (gestión nuestra) más urgente que 🔵 (espera externa).
    assert ed.mayor_prioridad(['PENDIENTE_NOTIFICAR', 'PENDIENTE_CERRAR']) == 'PENDIENTE_CERRAR'
    assert ed.mayor_prioridad(['PENDIENTE_NOTIFICAR', 'NOTIFICACION_FALLIDA']) == 'NOTIFICACION_FALLIDA'

def test_orden_naranja_gana_a_amarillo():
    assert ed.mayor_prioridad(['PENDIENTE_FIRMA', 'PENDIENTE_CERRAR']) == 'PENDIENTE_CERRAR'

def test_orden_agotada_gana_a_naranja():
    assert ed.mayor_prioridad(['PENDIENTE_CERRAR', 'NOTIFICACION_AGOTADA']) == 'NOTIFICACION_AGOTADA'

def test_orden_tramitar_gana_a_todo():
    todos = list(ed.PRIORIDAD)
    assert ed.mayor_prioridad(todos) == 'PENDIENTE_TRAMITAR'

def test_color_mapea_segun_banda():
    assert ed.color('NOTIFICACION_AGOTADA') == 'rojo'
    assert ed.color('PENDIENTE_CERRAR') == 'naranja'
    assert ed.color('PENDIENTE_FIRMA') == 'amarillo'
    assert ed.color('PENDIENTE_NOTIFICAR') == 'azul'
    assert ed.color('PENDIENTE_PLAZOS') == 'gris'
    assert ed.color('FIN') == 'verde'
    assert ed.color('DESCONOCIDO') == 'gris'

def test_coherencia_color_monotono_con_prioridad():
    # La prioridad es monótona con la banda de color (sin inversiones): ordenando los
    # estados por prioridad, el índice de banda nunca retrocede.
    banda = {'rojo': 0, 'naranja': 1, 'amarillo': 2, 'azul': 3, 'gris': 4, 'verde': 5}
    por_prioridad = sorted(ed.PRIORIDAD, key=ed.PRIORIDAD.get)
    indices = [banda[ed.color(e)] for e in por_prioridad]
    assert indices == sorted(indices)
