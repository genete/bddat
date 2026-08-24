"""
Tests de app/services/nombres_documentos.py (#698).

Usa SimpleNamespace en vez de MagicMock anidado: el servicio navega
tramite.fase.tramites (para contar vueltas) y
tramite.fase.solicitud.expediente.tipo_expediente.tipo (para la
sustitución de renovable) — con SimpleNamespace el test controla
exactamente esa estructura sin sorpresas de auto-mocking.
"""
from types import SimpleNamespace

import pytest

from app.services.nombres_documentos import texto_tramite


def _expediente(tipo='Transporte'):
    return SimpleNamespace(tipo_expediente=SimpleNamespace(tipo=tipo))


def _solicitud(expediente):
    return SimpleNamespace(expediente=expediente)


def _fase(codigo, solicitud):
    fase = SimpleNamespace(tipo_fase=SimpleNamespace(codigo=codigo), solicitud=solicitud, tramites=[])
    return fase


def _tramite(id_, codigo, fase, nombre_en_plantilla=None):
    t = SimpleNamespace(
        id=id_,
        tipo_tramite=SimpleNamespace(codigo=codigo, nombre_en_plantilla=nombre_en_plantilla),
        fase=fase,
    )
    fase.tramites.append(t)
    return t


class TestFallbackSinDatoDeCatalogo:
    def test_sin_nombre_en_plantilla_y_sin_ajuste_devuelve_codigo_crudo(self):
        fase = _fase('CONSULTA_MINISTERIO', _solicitud(_expediente()))
        tramite = _tramite(1, 'SOLICITUD_INFORME', fase, nombre_en_plantilla=None)

        assert texto_tramite(tramite) == 'SOLICITUD_INFORME'

    def test_elaboracion_en_reconocimiento_interesado_no_hereda_resolucion(self):
        """Mismo código de trámite (ELABORACION) que RESOLUCION, pero en fase
        no implementada en esta pasada — sin nombre_en_plantilla propio,
        cae al fallback, no hereda 'Resolución' de la otra fase."""
        fase = _fase('RECONOCIMIENTO_INTERESADO', _solicitud(_expediente()))
        tramite = _tramite(1, 'ELABORACION', fase, nombre_en_plantilla=None)

        assert texto_tramite(tramite) == 'ELABORACION'


class TestCatalogoSinAjuste:
    def test_usa_nombre_en_plantilla_tal_cual(self):
        """Trámite sin ajuste ni sustitución registrados: el dato de
        catálogo se usa directamente (caso general, la mayoría de trámites
        una vez poblados por el issue de seguimiento #809)."""
        fase = _fase('INFORMACION_PUBLICA', _solicitud(_expediente()))
        tramite = _tramite(1, 'ANUNCIO_BOP', fase, nombre_en_plantilla='Anuncio BOP')

        assert texto_tramite(tramite) == 'Anuncio BOP'


class TestAjusteRequerimientoSubsanacion:
    def test_primera_vuelta_usa_el_dato_de_catalogo_tal_cual(self):
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente()))
        _tramite(1, 'ANALISIS_DOCUMENTAL', fase)
        req1 = _tramite(2, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')

        assert texto_tramite(req1) == 'Requerimiento'

    def test_segunda_vuelta_anade_sufijo_al_dato_de_catalogo(self):
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente()))
        _tramite(1, 'ANALISIS_DOCUMENTAL', fase)
        _tramite(2, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')
        req2 = _tramite(3, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')

        assert texto_tramite(req2) == 'Requerimiento 2'

    def test_tercera_vuelta(self):
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente()))
        _tramite(1, 'ANALISIS_DOCUMENTAL', fase)
        _tramite(2, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')
        _tramite(3, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')
        req3 = _tramite(4, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento')

        assert texto_tramite(req3) == 'Requerimiento 3'

    def test_si_el_supervisor_cambia_el_texto_base_el_ajuste_lo_respeta(self):
        """El ajuste combina con lo que haya en catálogo, no con un texto
        hardcodeado — si el supervisor edita el campo, el sufijo de vuelta
        sigue aplicándose sobre el nuevo texto."""
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente()))
        _tramite(1, 'ANALISIS_DOCUMENTAL', fase)
        _tramite(2, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento de Subsanación')
        req2 = _tramite(3, 'REQUERIMIENTO_SUBSANACION', fase, nombre_en_plantilla='Requerimiento de Subsanación')

        assert texto_tramite(req2) == 'Requerimiento de Subsanación 2'


class TestSustitucionComunicacionInicioAdmision:
    def test_renovable_ignora_el_dato_de_catalogo(self):
        """Sustitución: el texto sale por código aunque nombre_en_plantilla
        tenga algo poblado — no es wording, es qué acto es el documento."""
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente('Renovable')))
        tramite = _tramite(1, 'COMUNICACION_INICIO_ADMISION', fase, nombre_en_plantilla='Ignorado')

        assert texto_tramite(tramite) == 'Admisión a Trámite'

    @pytest.mark.parametrize('tipo', ['Transporte', 'Distribución', 'Autoconsumo', 'Convencional'])
    def test_no_renovable(self, tipo):
        fase = _fase('ANALISIS_SOLICITUD', _solicitud(_expediente(tipo)))
        tramite = _tramite(1, 'COMUNICACION_INICIO_ADMISION', fase)

        assert texto_tramite(tramite) == 'Oficio Inicio'


class TestResolucion:
    def test_elaboracion_en_fase_resolucion_usa_dato_de_catalogo(self):
        fase = _fase('RESOLUCION', _solicitud(_expediente()))
        tramite = _tramite(1, 'ELABORACION', fase, nombre_en_plantilla='Resolución')

        assert texto_tramite(tramite) == 'Resolución'
