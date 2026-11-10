"""Tests #652 — reglas del motor que gobiernan la creación de los traslados (ADR-042 §D).

Fallo silencioso que evita: que el motor deje crear —o bloquee— un traslado cuando no
toca, sin que nadie lo vea. Una regla de catálogo con el camino o la variable
equivocados no da error: simplemente no dispara (así estuvo, sin que nadie lo notara,
el aviso de vuelta de #460), y la despensa del organismo ofrecería traslados que no
proceden o los negaría cuando sí.

Entran por donde llega el dato: `crear_traslado`, que es lo que llama la ruta de la
despensa, con el ciclo del organismo montado en BD real (SAVEPOINT de `app_ctx`). Cada
rama de decisión de las dos reglas es un caso:

- traslado al titular: procede ante una respuesta real del organismo, analizada,
  cualquiera que sea su sentido; no procede sin trámites, ante el silencio (un
  certificado de plazo cumplido no es una respuesta) ni con la respuesta sin analizar;
- traslado al organismo: procede si la última respuesta del organismo fue desfavorable
  y el titular contestó, con su respuesta analizada.
"""
import pytest


def _montar(arbol, *, organismo=None, diag_organismo=None, titular=None):
    """Ciclo de un organismo de la fase CONSULTAS.

    organismo:      None (sin trámites), 'real' (RESPUESTA_ORGANISMO) o 'certificado'
                    (CERT_PLAZO_CUMPLIDO: el organismo calló).
    diag_organismo: resultado del diagnóstico de su ANALIZAR, o None si no está hecha.
    titular:        None (sin traslado al titular), 'sin_respuesta', 'sin_analizar'
                    (contestó pero su ANALIZAR no está hecha) o 'analizada'.
    """
    from app import db
    from app.models.entidad import Entidad
    from app.models.organismos_expediente import OrganismoExpediente
    from app.models.tramites_organismos import TramiteOrganismo
    from app.services import mutaciones_arbol as svc

    sol = arbol.solicitud_nueva()
    fase = arbol.fase('CONSULTAS', solicitud=sol)
    entidad = Entidad.query.filter_by(rol_consultado=True).first()
    assert entidad is not None, 'la semilla debe traer una entidad con rol_consultado'
    alta = svc.crear_organismo(fase, entidad, via='consulta')
    assert alta.ok, alta.error
    oe = OrganismoExpediente.query.get(alta.ids[0])

    def ciclo(codigo_tramite, doc_respuesta, diagnostico):
        tramite = arbol.tramite(fase, codigo_tramite)
        db.session.add(TramiteOrganismo(tramite_id=tramite.id, organismo_expediente_id=oe.id))
        espera = arbol.tarea(tramite, 'ESPERAR_PLAZO')
        if doc_respuesta is not None:
            documento = arbol.documento(sol.expediente_id, doc_respuesta, f'652-{tramite.id}')
            arbol.vincular(espera, documento, 'PRODUCIDO')
        analisis = arbol.tarea(tramite, 'ANALIZAR')
        if diagnostico is not None:
            arbol.diagnostico(analisis, diagnostico)
        db.session.flush()

    if organismo == 'real':
        ciclo('CONSULTA_SEPARATA', 'RESPUESTA_ORGANISMO', diag_organismo)
    elif organismo == 'certificado':
        ciclo('CONSULTA_SEPARATA', 'CERT_PLAZO_CUMPLIDO', diag_organismo)

    if titular == 'sin_respuesta':
        ciclo('CONSULTA_TRASLADO_TITULAR', None, None)
    elif titular == 'sin_analizar':
        ciclo('CONSULTA_TRASLADO_TITULAR', 'RESPUESTA_TITULAR', None)
    elif titular == 'analizada':
        ciclo('CONSULTA_TRASLADO_TITULAR', 'RESPUESTA_TITULAR', 'favorable')
    return fase, oe


def _intentar(arbol, tipo, **escenario):
    from app.services.consultas_organismos import crear_traslado
    fase, oe = _montar(arbol, **escenario)
    return crear_traslado(fase, {'organismo_expediente_id': oe.id, 'tipo': tipo})


@pytest.mark.parametrize('escenario, procede', [
    pytest.param({}, False, id='organismo_sin_ningun_tramite'),
    pytest.param({'organismo': 'certificado', 'diag_organismo': 'favorable'}, False,
                 id='organismo_en_silencio_con_certificado'),
    pytest.param({'organismo': 'real', 'diag_organismo': None}, False,
                 id='respuesta_real_sin_analizar'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'favorable'}, True,
                 id='respuesta_favorable_analizada'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'desfavorable'}, True,
                 id='respuesta_desfavorable_analizada'),
])
def test_traslado_al_titular(app_ctx, arbol_esftt, escenario, procede):
    res = _intentar(arbol_esftt, 'TITULAR', **escenario)

    assert res.ok is procede, res.error or (res.bloqueo and res.bloqueo.motivo)
    if not procede:
        assert 'traslado al titular' in res.bloqueo.motivo


@pytest.mark.parametrize('escenario, procede', [
    pytest.param({'organismo': 'real', 'diag_organismo': 'desfavorable'}, False,
                 id='sin_traslado_al_titular'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'desfavorable',
                  'titular': 'sin_respuesta'}, False, id='titular_sin_responder'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'desfavorable',
                  'titular': 'sin_analizar'}, False, id='respuesta_del_titular_sin_analizar'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'favorable',
                  'titular': 'analizada'}, False, id='el_organismo_no_se_opuso'),
    pytest.param({'organismo': 'real', 'diag_organismo': 'desfavorable',
                  'titular': 'analizada'}, True, id='organismo_desfavorable_y_titular_analizada'),
])
def test_traslado_al_organismo(app_ctx, arbol_esftt, escenario, procede):
    res = _intentar(arbol_esftt, 'ORGANISMO', **escenario)

    assert res.ok is procede, res.error or (res.bloqueo and res.bloqueo.motivo)
    if not procede:
        assert 'traslado al organismo' in res.bloqueo.motivo
