"""
Tests #365 — URI bddat:// y helper resolver_url() en Documento (ADR-006).

Verifica sin tocar SQLAlchemy ni BD:
- Validación de esquemas en Documento.url
- fecha_administrativa es independiente del esquema de url (#574)
- resolver_url(): despacho correcto por esquema
- _resolver_bddat(): parseo de URI y retorno de dict completo

Los métodos se invocan como funciones no enlazadas sobre stubs planos,
siguiendo el mismo patrón que test_420_documentos_tarea.py.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.models.documentos import Documento

# Funciones no enlazadas — evitan los descriptores SQLAlchemy
_validar_url = Documento._validar_url
_resolver_url = Documento.resolver_url
_resolver_bddat = Documento._resolver_bddat


class _StubDoc:
    """Stub mínimo de Documento — atributos planos, sin ORM."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def resolver_url(self):
        return _resolver_url(self)

    def _resolver_bddat(self, url):
        return _resolver_bddat(self, url)


# ---------------------------------------------------------------------------
# Validación de esquemas (@validates)
# ---------------------------------------------------------------------------

class TestValidarUrl:

    def test_ruta_local_admitida(self):
        stub = _StubDoc(fecha_administrativa=None)
        resultado = _validar_url(stub, 'url', '/var/datos/expediente/doc.pdf')
        assert resultado == '/var/datos/expediente/doc.pdf'

    def test_http_admitido(self):
        stub = _StubDoc(fecha_administrativa=None)
        resultado = _validar_url(stub, 'url', 'http://example.com/doc.pdf')
        assert resultado == 'http://example.com/doc.pdf'

    def test_https_admitido(self):
        stub = _StubDoc(fecha_administrativa=None)
        resultado = _validar_url(stub, 'url', 'https://example.com/doc.pdf')
        assert resultado == 'https://example.com/doc.pdf'

    def test_bddat_admitido(self):
        stub = _StubDoc(fecha_administrativa=None)
        resultado = _validar_url(stub, 'url', 'bddat://diagnosticos/42')
        assert resultado == 'bddat://diagnosticos/42'

    def test_esquema_desconocido_rechazado(self):
        stub = _StubDoc(fecha_administrativa=None)
        with pytest.raises(ValueError, match='Esquema de URL no admitido'):
            _validar_url(stub, 'url', 'ftp://servidor/doc.pdf')

    def test_none_admitido(self):
        stub = _StubDoc(fecha_administrativa=None)
        assert _validar_url(stub, 'url', None) is None


# ---------------------------------------------------------------------------
# fecha_administrativa es independiente del esquema de url (#574)
# ---------------------------------------------------------------------------

class TestFechaAdministrativaBddat:

    def test_bddat_no_toca_fecha_administrativa(self):
        stub = _StubDoc(fecha_administrativa='2026-01-01')
        _validar_url(stub, 'url', 'bddat://diagnosticos/1')
        assert stub.fecha_administrativa == '2026-01-01'

    def test_ruta_local_no_toca_fecha_administrativa(self):
        stub = _StubDoc(fecha_administrativa='2026-01-01')
        _validar_url(stub, 'url', '/ruta/al/fichero.pdf')
        assert stub.fecha_administrativa == '2026-01-01'

    def test_http_no_toca_fecha_administrativa(self):
        stub = _StubDoc(fecha_administrativa='2026-01-01')
        _validar_url(stub, 'url', 'https://example.com/doc.pdf')
        assert stub.fecha_administrativa == '2026-01-01'


# ---------------------------------------------------------------------------
# resolver_url(): despacho por esquema
# ---------------------------------------------------------------------------

class TestResolverUrl:

    def test_ruta_local_abre_fichero(self, tmp_path):
        fichero = tmp_path / 'doc.pdf'
        fichero.write_bytes(b'%PDF')
        stub = _StubDoc(url=str(fichero))
        resultado = _resolver_url(stub)
        assert hasattr(resultado, 'read')
        resultado.close()

    def test_http_llama_urllib_urlopen(self):
        stub = _StubDoc(url='https://example.com/doc.pdf')
        mock_response = MagicMock()
        with patch('urllib.request.urlopen', return_value=mock_response) as mock_open:
            resultado = _resolver_url(stub)
        mock_open.assert_called_once_with('https://example.com/doc.pdf')
        assert resultado is mock_response

    def test_bddat_delega_a_resolver_bddat(self):
        stub = _StubDoc(url='bddat://diagnosticos/7')
        dict_esperado = {'id': 7, 'documento_id': 3, 'resultado': 'favorable', 'defectos': []}
        with patch.object(stub, '_resolver_bddat', return_value=dict_esperado) as mock_res:
            resultado = _resolver_url(stub)
        mock_res.assert_called_once_with('bddat://diagnosticos/7')
        assert resultado is dict_esperado


# ---------------------------------------------------------------------------
# _resolver_bddat(): parseo de URI y retorno de dict
# ---------------------------------------------------------------------------

class TestResolverBddat:

    def _diag_stub(self, id, documento_id, resultado, defectos):
        d = MagicMock()
        d.id = id
        d.documento_id = documento_id
        d.resultado = resultado
        d.defectos = defectos
        return d

    def _mock_diagnostico_class(self, diag_stub):
        """Mock de la clase Diagnostico con query.get() ya configurado."""
        mock_cls = MagicMock()
        mock_cls.query.get.return_value = diag_stub
        return mock_cls

    def test_diagnostico_devuelve_dict_completo(self):
        stub = _StubDoc()
        diag = self._diag_stub(7, 3, 'favorable', [{'tipo': 'FALTA_FIRMA'}])
        with patch('app.models.diagnosticos.Diagnostico', self._mock_diagnostico_class(diag)):
            resultado = _resolver_bddat(stub, 'bddat://diagnosticos/7')
        assert resultado == {
            'id': 7,
            'documento_id': 3,
            'resultado': 'favorable',
            'defectos': [{'tipo': 'FALTA_FIRMA'}],
        }

    def test_diagnostico_defectos_none_devuelve_lista_vacia(self):
        stub = _StubDoc()
        diag = self._diag_stub(1, 1, 'condicionado', None)
        with patch('app.models.diagnosticos.Diagnostico', self._mock_diagnostico_class(diag)):
            resultado = _resolver_bddat(stub, 'bddat://diagnosticos/1')
        assert resultado['defectos'] == []

    def test_diagnostico_no_encontrado_lanza_lookup_error(self):
        stub = _StubDoc()
        mock_cls = MagicMock()
        mock_cls.query.get.return_value = None
        with patch('app.models.diagnosticos.Diagnostico', mock_cls):
            with pytest.raises(LookupError, match='no encontrado'):
                _resolver_bddat(stub, 'bddat://diagnosticos/99')

    def test_recurso_desconocido_lanza_not_implemented(self):
        stub = _StubDoc()
        with pytest.raises(NotImplementedError, match='no implementado'):
            _resolver_bddat(stub, 'bddat://recurso_futuro/1')

    def test_uri_malformada_sin_id_lanza_value_error(self):
        stub = _StubDoc()
        with pytest.raises(ValueError, match='malformada'):
            _resolver_bddat(stub, 'bddat://diagnosticos')

    def test_id_no_numerico_lanza_value_error(self):
        stub = _StubDoc()
        with pytest.raises(ValueError, match='no numérico'):
            _resolver_bddat(stub, 'bddat://diagnosticos/abc')
