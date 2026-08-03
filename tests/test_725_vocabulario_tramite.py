"""
Tests #725 — vocabulario y cardinalidad de fase→trámite (ADR-037 §B/§C, tarea 8).

Con SQL real (fixture `arbol_esftt`), sin mocks. Generaliza check_orden_tarea
(T→Ta, secuencia) a existencia/cardinalidad en fase→trámite.
"""
import pytest
from flask_login import login_user


def _tipo(modelo, codigo):
    fila = modelo.query.filter_by(codigo=codigo).first()
    if fila is None:
        pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
    return fila


def _usuario():
    from app.models.usuarios import Usuario
    usuario = Usuario.query.first()
    if usuario is None:
        pytest.skip('No hay usuarios en la BD de desarrollo')
    return usuario


class TestCheckVocabularioTramite:
    """Unidad: app/services/vocabulario_esftt.py::check_vocabulario_tramite"""

    def test_fase_sin_vocabulario_no_bloquea(self, app_ctx):
        from app.services.vocabulario_esftt import check_vocabulario_tramite

        fase_stub = type('FaseStub', (), {'tipo_fase_id': -1, 'id': -1})()
        assert check_vocabulario_tramite(fase_stub, tipo_tramite=None) is None

    def test_tramite_del_vocabulario_no_bloquea(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services.vocabulario_esftt import check_vocabulario_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        analisis_documental = _tipo(TipoTramite, 'ANALISIS_DOCUMENTAL')

        assert check_vocabulario_tramite(fase, analisis_documental) is None

    def test_tramite_fuera_de_vocabulario_bloquea_escapable(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services.vocabulario_esftt import check_vocabulario_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        anuncio_boe = _tipo(TipoTramite, 'ANUNCIO_BOE')  # vocabulario de INFORMACION_PUBLICA

        res = check_vocabulario_tramite(fase, anuncio_boe)

        assert res is not None
        assert res.permitido is False
        assert res.puede_escapar is True
        assert 'ANUNCIO_BOE' in res.norma_compilada

    def test_cardinalidad_ilimitada_no_bloquea_con_varios(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services.vocabulario_esftt import check_vocabulario_tramite

        fase = arbol_esftt.fase('CONSULTAS')
        separata = _tipo(TipoTramite, 'CONSULTA_SEPARATA')
        arbol_esftt.tramite(fase, 'CONSULTA_SEPARATA')
        arbol_esftt.tramite(fase, 'CONSULTA_SEPARATA')
        arbol_esftt.tramite(fase, 'CONSULTA_SEPARATA')

        assert check_vocabulario_tramite(fase, separata) is None

    def test_cardinalidad_maxima_alcanzada_bloquea_escapable(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services.vocabulario_esftt import check_vocabulario_tramite

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        analisis_documental = _tipo(TipoTramite, 'ANALISIS_DOCUMENTAL')  # cardinalidad 1
        arbol_esftt.tramite(fase, 'ANALISIS_DOCUMENTAL')

        res = check_vocabulario_tramite(fase, analisis_documental)

        assert res is not None
        assert res.puede_escapar is True


class TestCrearTramiteConVocabulario:
    """Integración: app/services/mutaciones_arbol.py::crear_tramite"""

    def test_crear_tramite_fuera_de_vocabulario_bloquea_sin_justificacion(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        anuncio_boe = _tipo(TipoTramite, 'ANUNCIO_BOE')

        res = svc.crear_tramite(fase, anuncio_boe, justificacion=None)

        assert res.ok is False
        assert res.bloqueo.puede_escapar is True

    def test_crear_tramite_fuera_de_vocabulario_se_fuerza_con_justificacion(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.models.tramites import Tramite
        from app.services import mutaciones_arbol as svc

        usuario = _usuario()
        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        anuncio_boe = _tipo(TipoTramite, 'ANUNCIO_BOE')

        with app_ctx.test_request_context():
            login_user(usuario)
            res = svc.crear_tramite(fase, anuncio_boe, justificacion='Caso especial acordado con el titular')

        assert res.ok is True
        creado = Tramite.query.get(res.ids[0])
        assert creado.tipo_tramite_id == anuncio_boe.id

    def test_crear_tramite_del_vocabulario_no_pide_justificacion(self, arbol_esftt, app_ctx):
        from app.models.tipos_tramites import TipoTramite
        from app.services import mutaciones_arbol as svc

        fase = arbol_esftt.fase('ANALISIS_SOLICITUD')
        comunicacion_inicio = _tipo(TipoTramite, 'COMUNICACION_INICIO')

        res = svc.crear_tramite(fase, comunicacion_inicio, justificacion=None)

        assert res.ok is True
