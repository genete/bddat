"""Tests #1097 — el diagnóstico de la `ANALIZAR` cierra al organismo (ADR-011 §6).

Fallo silencioso que evita: que el resultado de un organismo (`organismos_expediente.resultado`)
no corresponda a lo que dicen sus diagnósticos. Lo lee el motor para dejar abrir —o bloquear— la
`RESOLUCION` y no da ningún error si está mal: un organismo que sigue cerrado tras deshacer su
diagnóstico, o que figura en `audiencia_previa` con otra vuelta en marcha, abre la resolución con
un ciclo vivo; y una oposición ya resuelta que bloquea el cierre de CONSULTAS, o un organismo de
otra solicitud que bloquea esta, se pagan en cada expediente con más de una ronda o solicitud.

Entran por donde llega el dato (`crear_diagnostico`, `revertir_diagnostico`, `crear_traslado`),
con el ciclo montado en BD real (SAVEPOINT de `app_ctx`). Un test por rama de decisión.
"""
import pytest


def _entidad_consultada(n):
    from app.models.entidad import Entidad
    entidad = Entidad.query.order_by(Entidad.id).offset(n).first()
    assert entidad is not None, 'la semilla debe traer al menos dos entidades'
    return entidad


def _organismo(fase, n=0):
    from app import db
    from app.models.organismos_expediente import OrganismoExpediente
    oe = OrganismoExpediente(expediente_id=fase.solicitud.expediente_id, fase_id=fase.id,
                             organismo_id=_entidad_consultada(n).id, via='consulta')
    db.session.add(oe)
    db.session.flush()
    return oe


def _vuelta(arbol, fase, oe, codigo_tramite, doc_espera, resultado, sentido=None):
    """Un trámite del ciclo del organismo, con su respuesta (o certificado) y su diagnóstico
    producido por `crear_diagnostico`, que es por donde entra el dato. Devuelve la ANALIZAR."""
    from app import db
    from app.models.tramites_organismos import TramiteOrganismo
    from app.services.diagnosticos import crear_diagnostico

    tramite = arbol.tramite(fase, codigo_tramite)
    db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
    espera = arbol.tarea(tramite, 'ESPERAR_PLAZO')
    documento = arbol.documento(fase.solicitud.expediente_id, doc_espera, f'1097-{tramite.id}')
    arbol.vincular(espera, documento, 'PRODUCIDO')
    analisis = arbol.tarea(tramite, 'ANALIZAR')
    db.session.flush()
    crear_diagnostico(analisis, resultado, [], sentido=sentido)
    return analisis


def _resultado(oe):
    from app import db
    db.session.flush()
    db.session.refresh(oe)
    return oe.resultado


# (codigo_tramite, documento de la espera, diagnóstico, sentido)
_SEPARATA_SILENCIO = ('CONSULTA_SEPARATA', 'CERT_PLAZO_CUMPLIDO', 'favorable', None)
_RESPUESTA_FAVORABLE = ('CONSULTA_SEPARATA', 'RESPUESTA_ORGANISMO', 'favorable', None)
_RESPUESTA_CONDICIONADO = ('CONSULTA_SEPARATA', 'RESPUESTA_ORGANISMO', 'condicionado', None)
_OPOSICION = ('CONSULTA_SEPARATA', 'RESPUESTA_ORGANISMO', 'desfavorable', 'oposicion')
_TITULAR_CONFORME = ('CONSULTA_TRASLADO_TITULAR', 'RESPUESTA_TITULAR', 'favorable', None)
_TITULAR_CON_REPAROS = ('CONSULTA_TRASLADO_TITULAR', 'RESPUESTA_TITULAR', 'desfavorable', None)
_ORGANISMO_RECTIFICA = ('CONSULTA_TRASLADO_ORGANISMO', 'RESPUESTA_ORGANISMO', 'favorable', None)


@pytest.mark.parametrize('ciclo, esperado', [
    pytest.param([_SEPARATA_SILENCIO], 'cerrado_favorable', id='A_silencio'),
    pytest.param([_RESPUESTA_FAVORABLE], None, id='respuesta_favorable_falta_el_traslado'),
    pytest.param([_RESPUESTA_FAVORABLE, _TITULAR_CONFORME], 'cerrado_favorable',
                 id='B_respuesta_favorable_y_titular_conforme'),
    pytest.param([_RESPUESTA_CONDICIONADO, _TITULAR_CONFORME], 'cerrado_con_condicionados',
                 id='condicionado_y_titular_conforme'),
    pytest.param([_OPOSICION, _TITULAR_CONFORME, _ORGANISMO_RECTIFICA, _TITULAR_CONFORME],
                 'cerrado_favorable', id='C_oposicion_resuelta_en_otra_vuelta'),
    pytest.param([_OPOSICION], 'audiencia_previa', id='desfavorable_sin_otra_vuelta'),
    pytest.param([_OPOSICION, _TITULAR_CONFORME], None, id='falta_el_traslado_al_organismo'),
    pytest.param([_RESPUESTA_FAVORABLE, _TITULAR_CON_REPAROS], None,
                 id='titular_con_reparos_queda_en_curso'),
])
def test_resultado_segun_el_ciclo(app_ctx, arbol_esftt, ciclo, esperado):
    sol = arbol_esftt.solicitud_nueva()
    fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
    oe = _organismo(fase)

    for paso in ciclo:
        _vuelta(arbol_esftt, fase, oe, *paso)

    assert _resultado(oe) == esperado


def test_revertir_el_diagnostico_reabre_al_organismo(app_ctx, arbol_esftt):
    from app.services.diagnosticos import revertir_diagnostico
    sol = arbol_esftt.solicitud_nueva()
    fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
    oe = _organismo(fase)
    analisis = _vuelta(arbol_esftt, fase, oe, *_SEPARATA_SILENCIO)
    assert _resultado(oe) == 'cerrado_favorable'

    revertir_diagnostico(analisis)

    assert _resultado(oe) is None


def test_otra_vuelta_saca_al_organismo_de_audiencia_previa(app_ctx, arbol_esftt):
    from app.services.consultas_organismos import crear_traslado
    sol = arbol_esftt.solicitud_nueva()
    fase = arbol_esftt.fase('CONSULTAS', solicitud=sol)
    oe = _organismo(fase)
    _vuelta(arbol_esftt, fase, oe, *_OPOSICION)
    assert _resultado(oe) == 'audiencia_previa'

    res = crear_traslado(fase, {'organismo_expediente_id': oe.id, 'tipo': 'TITULAR'})
    assert res.ok, res.error or (res.bloqueo and res.bloqueo.motivo)

    assert _resultado(oe) is None


@pytest.mark.parametrize('resultados, terminados', [
    pytest.param(['audiencia_previa', 'cerrado_favorable'], True, id='rondas_todas_terminadas'),
    pytest.param(['cerrado_favorable', None], False, id='en_curso_en_la_ultima_ronda'),
    pytest.param([None, 'cerrado_favorable'], False, id='en_curso_en_una_ronda_anterior'),
])
def test_organismos_todos_terminados_recorre_todas_las_rondas(
        app_ctx, arbol_esftt, resultados, terminados):
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.variables import get_registry
    sol = arbol_esftt.solicitud_nueva()
    for n, resultado in enumerate(resultados):
        _organismo(arbol_esftt.fase('CONSULTAS', solicitud=sol), n=n).resultado = resultado
    db.session.flush()
    db.session.expire_all()

    variable = get_registry()['organismos_todos_terminados']

    assert variable(ExpedienteContext(sol.expediente, objeto=sol)) is terminados


def test_organismos_todos_terminados_no_mira_otras_solicitudes(app_ctx, arbol_esftt):
    from app import db
    from app.services.assembler import ExpedienteContext
    from app.services.variables import get_registry
    sol = arbol_esftt.solicitud_nueva()
    otra = arbol_esftt.solicitud_nueva()   # mismo expediente: la semilla cuelga ambas del primero
    assert otra.expediente_id == sol.expediente_id
    _organismo(arbol_esftt.fase('CONSULTAS', solicitud=otra))   # en curso, de la otra solicitud
    db.session.flush()
    db.session.expire_all()

    variable = get_registry()['organismos_todos_terminados']

    assert variable(ExpedienteContext(sol.expediente, objeto=sol)) is True
