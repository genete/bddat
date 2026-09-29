"""
Tests para #300 — _direccion_titular() en ContextoBaseExpediente.

Verifica:
- Uso de la sede de la solicitud del escrito cuando la tiene (#989)
- Sin ella, la ficha de la entidad (ya no la DireccionNotificacion de rol
  TITULAR más reciente, #989)
- Formato dict granular {calle, cp, municipio, provincia}
- None cuando el expediente no tiene titular
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.escritos import ContextoBaseExpediente


def _mock_municipio(nombre, provincia):
    m = MagicMock()
    m.nombre = nombre
    m.provincia = provincia
    return m


def _make_exp(titular=None):
    exp = MagicMock()
    exp.titular = titular
    exp.proyecto = None
    exp.responsable = None
    exp.numero_at = None
    return exp


# ---------------------------------------------------------------------------
# _dir_a_dict (helper estático)
# ---------------------------------------------------------------------------

class TestDirADict:
    def test_campos_estructurados(self):
        src = MagicMock()
        src.direccion_fallback = None
        src.direccion = 'C/ Mayor, 1'
        src.codigo_postal = '18001'
        src.municipio = _mock_municipio('Granada', 'GRANADA')
        src.nif = 'B12345678'
        src.email = 'contacto@empresa.com'

        result = ContextoBaseExpediente._dir_a_dict(src)

        assert result == {
            'calle':     'C/ Mayor, 1',
            'cp':        '18001',
            'municipio': 'Granada',
            'provincia': 'GRANADA',
            'nif':       'B12345678',
            'email':     'contacto@empresa.com',
        }

    def test_fallback_rellena_solo_calle(self):
        src = MagicMock()
        src.direccion_fallback = '23 Penny Lane, London, UK'
        src.nif = None
        src.email = None

        result = ContextoBaseExpediente._dir_a_dict(src)

        assert result['calle'] == '23 Penny Lane, London, UK'
        assert result['cp'] == ''
        assert result['municipio'] == ''
        assert result['provincia'] == ''
        assert result['nif'] == ''
        assert result['email'] == ''

    def test_sin_municipio_devuelve_cadenas_vacias(self):
        src = MagicMock()
        src.direccion_fallback = None
        src.direccion = 'Avda. de la Paz, 3'
        src.codigo_postal = '23700'
        src.municipio = None
        src.nif = None
        src.email = None

        result = ContextoBaseExpediente._dir_a_dict(src)

        assert result['municipio'] == ''
        assert result['provincia'] == ''

    def test_direccion_none_devuelve_cadena_vacia(self):
        src = MagicMock()
        src.direccion_fallback = None
        src.direccion = None
        src.codigo_postal = None
        src.municipio = None
        src.nif = None
        src.email = None

        result = ContextoBaseExpediente._dir_a_dict(src)

        assert result == {'calle': '', 'cp': '', 'municipio': '', 'provincia': '', 'nif': '', 'email': ''}

    def test_nif_y_email_de_notificacion(self):
        src = MagicMock()
        src.direccion_fallback = None
        src.direccion = 'C/ Test, 1'
        src.codigo_postal = '41001'
        src.municipio = _mock_municipio('Sevilla', 'SEVILLA')
        src.nif = 'A41000001'
        src.email = 'notif@iberdrola.es'

        result = ContextoBaseExpediente._dir_a_dict(src)

        assert result['nif'] == 'A41000001'
        assert result['email'] == 'notif@iberdrola.es'

    def test_no_devuelve_repr_de_debug(self):
        """Garantía anti-regresión: nunca debe aparecer '<DireccionNotif' en el resultado."""
        src = MagicMock()
        src.direccion_fallback = None
        src.direccion = 'C/ Test, 1'
        src.codigo_postal = '41001'
        src.municipio = _mock_municipio('Sevilla', 'SEVILLA')
        src.nif = None
        src.email = None

        result = ContextoBaseExpediente._dir_a_dict(src)

        for v in result.values():
            assert '<' not in v


# ---------------------------------------------------------------------------
# _direccion_titular — la sede de la solicitud o la ficha (#989, ADR-051 §K)
# ---------------------------------------------------------------------------

TARGET = 'app.services.escritos.notif_svc.sede_de'


def _solicitud_de(titular):
    sol = MagicMock()
    sol.entidad_id = titular.id
    return sol


class TestDireccionTitular:
    def _titular(self, **kwargs):
        t = MagicMock()
        t.id = 1
        t.direccion_fallback = kwargs.get('fallback')
        t.direccion = kwargs.get('direccion', 'Calle Entidad, 5')
        t.codigo_postal = kwargs.get('cp', '29001')
        t.municipio = kwargs.get('municipio', _mock_municipio('Málaga', 'MÁLAGA'))
        t.nif = kwargs.get('nif', 'B29000001')
        t.email = kwargs.get('email', 'titular@empresa.com')
        return t

    def test_sin_titular_devuelve_none(self):
        exp = _make_exp(titular=None)
        ctx = ContextoBaseExpediente(exp)
        assert ctx._direccion_titular() is None

    def test_usa_la_sede_de_la_solicitud(self):
        dn = MagicMock()
        dn.direccion_fallback = None
        dn.direccion = 'C/ Notificacion, 7'
        dn.codigo_postal = '41002'
        dn.municipio = _mock_municipio('Sevilla', 'SEVILLA')
        dn.nif = None
        dn.email = 'notif@empresa.es'

        titular = self._titular()
        exp = _make_exp(titular=titular)

        with patch(TARGET, return_value=dn):
            result = ContextoBaseExpediente(exp, _solicitud_de(titular))._direccion_titular()

        assert result['calle'] == 'C/ Notificacion, 7'
        assert result['municipio'] == 'Sevilla'
        assert result['nif'] == 'B29000001'          # el de la ficha: una sede no tiene NIF
        assert result['email'] == 'notif@empresa.es'

    def test_sin_sede_la_ficha(self):
        """Sin sede, la ficha: ya no la dirección de rol titular más reciente."""
        titular = self._titular(direccion='Calle Entidad, 5', cp='29001',
                                municipio=_mock_municipio('Málaga', 'MÁLAGA'))
        exp = _make_exp(titular=titular)

        with patch(TARGET, return_value=None):
            result = ContextoBaseExpediente(exp, _solicitud_de(titular))._direccion_titular()

        assert result['calle'] == 'Calle Entidad, 5'
        assert result['provincia'] == 'MÁLAGA'
        assert ContextoBaseExpediente(exp)._direccion_titular()['calle'] == 'Calle Entidad, 5'

    def test_get_contexto_incluye_titular_dir_como_dict(self):
        dn = MagicMock()
        dn.direccion_fallback = None
        dn.direccion = 'C/ Principal, 1'
        dn.codigo_postal = '18001'
        dn.municipio = _mock_municipio('Granada', 'GRANADA')
        dn.nif = None
        dn.email = 'notif@test.com'

        titular = MagicMock()
        titular.id = 42
        titular.nombre_completo = 'Empresa Test SL'
        titular.nif = 'B12345678'

        exp = MagicMock()
        exp.titular = titular
        exp.numero_at = '0001'
        exp.proyecto = None
        exp.responsable = None

        with patch(TARGET, return_value=dn):
            ctx = ContextoBaseExpediente(exp, _solicitud_de(titular)).get_contexto()

        assert isinstance(ctx['titular_dir'], dict)
        assert set(ctx['titular_dir']) == {'calle', 'cp', 'municipio', 'provincia', 'nif', 'email'}
        assert 'titular_direccion' not in ctx

    def test_get_contexto_sin_titular_dir_es_none(self):
        exp = _make_exp(titular=None)
        ctx = ContextoBaseExpediente(exp).get_contexto()
        assert ctx['titular_dir'] is None
