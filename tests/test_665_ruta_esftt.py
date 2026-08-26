"""
Tests #665 — cálculo de rutas ESFTT (Expediente-Solicitud-Fase-Trámite-Tarea) y
carpeta pool/ (ADR-032 §4).

Fase/trámite/solicitud/expediente se representan con stubs (SimpleNamespace) para
no depender de la BD real, siguiendo el patrón de test_365_bddat_uri.py y
test_420_documentos_tarea.py. Tarea y Documento se stubean con
MagicMock(spec=...) — spec hace que isinstance() los reconozca como su clase real
(necesario para el dispatch de ruta_esftt_documento()) sin disparar la
instrumentación de relaciones de SQLAlchemy (backrefs) que exigiría instancias
mapeadas reales en ambos extremos de cada relación.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.documentos import Documento
from app.models.tareas import Tarea
from app.services.rutas_esftt import ruta_esftt_documento, ruta_pool_documento


def _tarea_stub(
    *,
    tarea_id=201,
    codigo_tarea='ANALIZAR',
    tramite_id=78,
    codigo_tramite='ANALISIS_DOCUMENTAL',
    fase_id=34,
    codigo_fase='ANALISIS_SOLICITUD',
    solicitud_id=12,
    siglas='AAP',
    numero_at=5,
):
    """Tarea real con la cadena tramite→fase→solicitud→expediente stubeada."""
    expediente = SimpleNamespace(numero_at=numero_at)
    solicitud = SimpleNamespace(
        id=solicitud_id,
        tipo_solicitud=SimpleNamespace(siglas=siglas),
        expediente=expediente,
    )
    fase = SimpleNamespace(
        id=fase_id,
        tipo_fase=SimpleNamespace(codigo=codigo_fase),
        solicitud=solicitud,
    )
    tramite = SimpleNamespace(
        id=tramite_id,
        tipo_tramite=SimpleNamespace(codigo=codigo_tramite),
        fase=fase,
    )

    tarea = MagicMock(spec=Tarea)
    tarea.id = tarea_id
    tarea.tramite = tramite
    tarea.tipo_tarea = SimpleNamespace(codigo=codigo_tarea)
    return tarea


def _sin_organismo():
    """Patchea TramiteOrganismo para que ningún trámite tenga organismo asociado."""
    mock_cls = MagicMock()
    mock_cls.query.filter_by.return_value.first.return_value = None
    return patch('app.models.tramites_organismos.TramiteOrganismo', mock_cls)


def _con_organismo(organismo_expediente_id, entidad, vinculo_id=None):
    """Patchea TramiteOrganismo para devolver un vínculo con el organismo_expediente_id dado.

    vinculo_id (id de la fila TramiteOrganismo) es distinto por defecto del
    organismo_expediente_id — deja claro en los tests que el segmento se numera por
    organismo_expediente_id, no por el id del vínculo (#396 bloque 7)."""
    if vinculo_id is None:
        vinculo_id = organismo_expediente_id + 1000
    vinculo = SimpleNamespace(
        id=vinculo_id,
        organismo_expediente_id=organismo_expediente_id,
        organismo_expediente=SimpleNamespace(organismo=entidad),
    )
    mock_cls = MagicMock()
    mock_cls.query.filter_by.return_value.first.return_value = vinculo
    return patch('app.models.tramites_organismos.TramiteOrganismo', mock_cls)


# ---------------------------------------------------------------------------
# ruta_esftt_documento(Tarea) — caso simple, sin organismo ni repetición
# ---------------------------------------------------------------------------

class TestRutaDesdeTareaSimple:

    def test_ruta_completa_sin_organismo(self):
        tarea = _tarea_stub()
        with _sin_organismo():
            resultado = ruta_esftt_documento(tarea)
        assert resultado == (
            'AT-5/000012_AAP/000034_ANALISIS_SOLICITUD/'
            '000078_ANALISIS_DOCUMENTAL/000201_ANALIZAR'
        )

    def test_padding_a_seis_digitos(self):
        tarea = _tarea_stub(tarea_id=7, tramite_id=3, fase_id=1, solicitud_id=42)
        with _sin_organismo():
            resultado = ruta_esftt_documento(tarea)
        assert '000042_AAP' in resultado
        assert '000001_ANALISIS_SOLICITUD' in resultado
        assert '000003_ANALISIS_DOCUMENTAL' in resultado
        assert '000007_ANALIZAR' in resultado

    def test_tipo_no_admitido_lanza_type_error(self):
        with pytest.raises(TypeError, match='espera Documento o Tarea'):
            ruta_esftt_documento(object())


# ---------------------------------------------------------------------------
# Segmento organismo — trámites CONSULTA_* ligados a TramiteOrganismo
# ---------------------------------------------------------------------------

class TestSegmentoOrganismo:

    def test_inserta_segmento_con_abrev(self):
        tarea = _tarea_stub(codigo_tramite='CONSULTA_SEPARATA')
        entidad = SimpleNamespace(abrev='CHMS', nombre_completo='Confederación Hidrográfica')
        with _con_organismo(9, entidad):
            resultado = ruta_esftt_documento(tarea)
        assert resultado == (
            'AT-5/000012_AAP/000034_ANALISIS_SOLICITUD/000009_CHMS/'
            '000078_CONSULTA_SEPARATA/000201_ANALIZAR'
        )

    def test_fallback_a_nombre_completo_saneado_si_abrev_vacio(self):
        tarea = _tarea_stub(codigo_tramite='CONSULTA_SEPARATA')
        entidad = SimpleNamespace(
            abrev=None,
            nombre_completo='Organismo/Con:Caracteres*Invalidos Y Un Nombre Muy Largo',
        )
        with _con_organismo(9, entidad):
            resultado = ruta_esftt_documento(tarea)
        segmentos = resultado.split('/')
        # El segmento organismo es el 4º (índice 3): AT-N / solicitud / fase / organismo / ...
        segmento_organismo = segmentos[3]
        assert segmento_organismo.startswith('000009_')
        texto = segmento_organismo.split('_', 1)[1]
        assert '/' not in texto and ':' not in texto and '*' not in texto
        assert len(texto) <= 30

    def test_sin_tramite_organismo_no_inserta_segmento(self):
        tarea = _tarea_stub()
        with _sin_organismo():
            resultado = ruta_esftt_documento(tarea)
        assert len(resultado.split('/')) == 5  # AT-N/solicitud/fase/tramite/tarea

    def test_mismo_organismo_distintos_vinculos_misma_carpeta(self):
        """#396 bloque 7 — dos trámites del mismo organismo (mismo organismo_expediente_id,
        distinto id de fila TramiteOrganismo) deben compartir carpeta de organismo."""
        entidad = SimpleNamespace(abrev='CHMS', nombre_completo='Confederación Hidrográfica')
        tarea_traslado = _tarea_stub(tramite_id=78, codigo_tramite='CONSULTA_TRASLADO_ORGANISMO')
        tarea_separata = _tarea_stub(tramite_id=79, codigo_tramite='CONSULTA_SEPARATA')

        with _con_organismo(9, entidad, vinculo_id=101):
            ruta_traslado = ruta_esftt_documento(tarea_traslado)
        with _con_organismo(9, entidad, vinculo_id=205):
            ruta_separata = ruta_esftt_documento(tarea_separata)

        segmento_organismo_traslado = ruta_traslado.split('/')[3]
        segmento_organismo_separata = ruta_separata.split('/')[3]
        assert segmento_organismo_traslado == segmento_organismo_separata == '000009_CHMS'


# ---------------------------------------------------------------------------
# ruta_esftt_documento(Documento) — resuelve por primera vinculación
# ---------------------------------------------------------------------------

class TestRutaDesdeDocumento:

    def test_resuelve_por_menor_id_de_vinculo(self):
        tarea_a = _tarea_stub(tarea_id=1, codigo_tarea='ELABORAR')
        tarea_b = _tarea_stub(tarea_id=2, codigo_tarea='NOTIFICAR')

        doc = MagicMock(spec=Documento)
        doc.id = 55
        doc.vinculos_tarea = [
            SimpleNamespace(id=10, tarea=tarea_b),
            SimpleNamespace(id=3, tarea=tarea_a),
        ]

        with _sin_organismo():
            resultado = ruta_esftt_documento(doc)

        assert resultado.endswith('_ELABORAR')

    def test_documento_sin_vinculos_lanza_value_error(self):
        doc = MagicMock(spec=Documento)
        doc.id = 99
        doc.vinculos_tarea = []
        with pytest.raises(ValueError, match='no tiene ninguna tarea vinculada'):
            ruta_esftt_documento(doc)


# ---------------------------------------------------------------------------
# ruta_pool_documento(expediente) — ruta absoluta + makedirs (ADR-032 §1)
# ---------------------------------------------------------------------------

class TestRutaPoolDocumento:

    def test_devuelve_ruta_absoluta_y_crea_directorio(self, tmp_path, app):
        import os
        expediente = SimpleNamespace(numero_at=9)
        base_original = app.config.get('FILESYSTEM_BASE')
        app.config['FILESYSTEM_BASE'] = str(tmp_path)
        try:
            with app.app_context():
                resultado = ruta_pool_documento(expediente)
            esperado = os.path.normpath(os.path.join(str(tmp_path), 'AT-9', 'pool'))
            assert resultado == esperado
            assert os.path.isdir(esperado)
        finally:
            app.config['FILESYSTEM_BASE'] = base_original

    def test_sin_filesystem_base_lanza_runtime_error(self, app):
        expediente = SimpleNamespace(numero_at=9)
        base_original = app.config.get('FILESYSTEM_BASE')
        app.config['FILESYSTEM_BASE'] = ''
        try:
            with app.app_context():
                with pytest.raises(RuntimeError, match='FILESYSTEM_BASE'):
                    ruta_pool_documento(expediente)
        finally:
            app.config['FILESYSTEM_BASE'] = base_original
