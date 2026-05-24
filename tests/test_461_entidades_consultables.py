"""Tests #461 — helpers de serialización del endpoint GET /api/entidades/consultables.

Patrón: objetos Python puros (MagicMock), sin BD real ni cliente Flask.
"""
from unittest.mock import MagicMock


def _entidad_stub(id=1, nombre='Ministerio de Industria', nif='S2801047B'):
    e = MagicMock()
    e.id = id
    e.nombre_completo = nombre
    e.nif = nif
    return e


def _dir_stub(id=5, descripcion='Sede Central', dir3='EA0015285',
              sir='E04926801', email='notif@minind.gob.es',
              linea1='Paseo de la Castellana, 160', linea2='28046 Madrid'):
    d = MagicMock()
    d.id = id
    d.descripcion = descripcion
    d.codigo_dir3 = dir3
    d.codigo_sir = sir
    d.email = email
    d.direccion_formateada.return_value = {
        'linea1': linea1,
        'linea2': linea2,
        'provincia': 'MADRID',
    }
    return d


class TestSerializarDirConsultado:

    def test_campos_basicos(self):
        from app.routes.api_entidades import _serializar_dir_consultado
        d = _dir_stub()
        r = _serializar_dir_consultado(d)
        assert r['id'] == 5
        assert r['descripcion'] == 'Sede Central'
        assert r['dir3'] == 'EA0015285'
        assert r['sir'] == 'E04926801'
        assert r['email'] == 'notif@minind.gob.es'
        assert r['direccion'] == 'Paseo de la Castellana, 160 — 28046 Madrid'

    def test_dir3_null(self):
        from app.routes.api_entidades import _serializar_dir_consultado
        d = _dir_stub(dir3=None)
        assert _serializar_dir_consultado(d)['dir3'] is None

    def test_sin_linea2(self):
        from app.routes.api_entidades import _serializar_dir_consultado
        d = _dir_stub(linea2='')
        assert _serializar_dir_consultado(d)['direccion'] == 'Paseo de la Castellana, 160'

    def test_sin_ninguna_linea(self):
        from app.routes.api_entidades import _serializar_dir_consultado
        d = _dir_stub(linea1='', linea2='')
        assert _serializar_dir_consultado(d)['direccion'] is None


class TestSerializarConsultable:

    def test_entidad_con_una_direccion(self):
        from app.routes.api_entidades import _serializar_consultable
        e = _entidad_stub()
        r = _serializar_consultable(e, [_dir_stub()])
        assert r['id'] == 1
        assert r['nombre'] == 'Ministerio de Industria'
        assert r['nif'] == 'S2801047B'
        assert len(r['direcciones_consultado']) == 1
        assert r['direcciones_consultado'][0]['dir3'] == 'EA0015285'

    def test_entidad_sin_direcciones(self):
        from app.routes.api_entidades import _serializar_consultable
        r = _serializar_consultable(_entidad_stub(), [])
        assert r['direcciones_consultado'] == []

    def test_nif_null(self):
        from app.routes.api_entidades import _serializar_consultable
        e = _entidad_stub(nif=None)
        assert _serializar_consultable(e, [])['nif'] is None

    def test_multiples_direcciones(self):
        from app.routes.api_entidades import _serializar_consultable
        dirs = [
            _dir_stub(id=5, descripcion='Sede Central'),
            _dir_stub(id=8, descripcion='Delegación Andalucía', dir3='EA0018532'),
        ]
        r = _serializar_consultable(_entidad_stub(), dirs)
        assert len(r['direcciones_consultado']) == 2
        assert r['direcciones_consultado'][1]['dir3'] == 'EA0018532'
