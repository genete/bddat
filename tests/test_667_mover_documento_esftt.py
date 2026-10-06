"""
Tests #667 — mover documento a su carpeta ESFTT al vincularse por primera vez
a una tarea (ADR-032 §3).

Parte 1: mover_a_esftt() / mover_a_pool() — movimiento físico puro. Documento
real transitorio (no persistido — solo hace falta .url/.hash_md5/.id/.expediente
para el cálculo de rutas) y Tarea stubeada, reutilizando los helpers de
test_665_ruta_esftt.py. FILESYSTEM_BASE apunta a tmp_path — nunca toca el
servidor de ficheros real.

La parte 2 —que `editar_tarea()` llamaba a estas funciones al vincular y al
desvincular— se retiró en el corte de ADR-050 (#1007): vincular es solo una fila y
no mueve ningún fichero. Estas funciones y sus tests salen en el PR 5.
"""
import hashlib

import pytest

from app import db
from app.models.documentos import Documento
from app.models.expedientes import Expediente
from app.services.rutas_esftt import mover_a_esftt, mover_a_pool
from tests.test_665_ruta_esftt import _tarea_stub, _sin_organismo


# ---------------------------------------------------------------------------
# Fixture: FILESYSTEM_BASE apuntando a tmp_path (nunca al servidor real)
# ---------------------------------------------------------------------------

@pytest.fixture
def _fs_tmp(app, tmp_path):
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


def _ruta_tarea_stub_default() -> str:
    """Ruta ESFTT que produce _tarea_stub() con sus valores por defecto (ver test_665)."""
    return ('AT-5/000012_AAP/000034_ANALISIS_SOLICITUD/'
            '000078_ANALISIS_DOCUMENTAL/000201_ANALIZAR')


# ---------------------------------------------------------------------------
# mover_a_esftt(documento, tarea)
# ---------------------------------------------------------------------------

class TestMoverAEsftt:

    def test_no_op_si_esquema_bddat(self, app_ctx, _fs_tmp):
        doc = Documento(expediente_id=1, url='bddat://diagnosticos/1')
        tarea = _tarea_stub()
        assert mover_a_esftt(doc, tarea) is False
        assert doc.url == 'bddat://diagnosticos/1'

    def test_no_op_si_esquema_http(self, app_ctx, _fs_tmp):
        doc = Documento(expediente_id=1, url='https://ejemplo.org/x.pdf')
        tarea = _tarea_stub()
        assert mover_a_esftt(doc, tarea) is False

    def test_no_op_si_ya_esta_en_destino(self, app_ctx, _fs_tmp):
        destino_rel = _ruta_tarea_stub_default()
        destino_dir = _fs_tmp / destino_rel
        destino_dir.mkdir(parents=True)
        (destino_dir / 'informe.pdf').write_bytes(b'contenido')

        doc = Documento(expediente_id=1, url=f'{destino_rel}/informe.pdf')
        doc.id = 1
        tarea = _tarea_stub()

        with _sin_organismo():
            resultado = mover_a_esftt(doc, tarea)

        assert resultado is False
        assert doc.url == f'{destino_rel}/informe.pdf'

    def test_mueve_y_recupera_nombre_original_del_pool(self, app_ctx, _fs_tmp):
        contenido = b'contenido real del informe'
        hash_md5 = hashlib.md5(contenido).hexdigest()
        prefijo = hash_md5[:8]

        origen_dir = _fs_tmp / 'AT-5' / 'pool'
        origen_dir.mkdir(parents=True)
        origen = origen_dir / f'{prefijo}_informe.pdf'
        origen.write_bytes(contenido)

        doc = Documento(expediente_id=1, url=f'AT-5/pool/{prefijo}_informe.pdf', hash_md5=hash_md5)
        doc.id = 42
        tarea = _tarea_stub()

        with _sin_organismo():
            resultado = mover_a_esftt(doc, tarea)

        assert resultado is True
        assert doc.url == f'{_ruta_tarea_stub_default()}/informe.pdf'  # prefijo hash despojado
        assert not origen.exists()
        destino = _fs_tmp / doc.url
        assert destino.read_bytes() == contenido

    def test_conserva_nombre_si_documento_sin_hash_registro_in_situ(self, app_ctx, _fs_tmp):
        origen_dir = _fs_tmp / 'cualquier' / 'carpeta' / 'de_red'
        origen_dir.mkdir(parents=True)
        origen = origen_dir / 'Informe Ya Organizado.pdf'
        origen.write_bytes(b'contenido in situ')

        doc = Documento(
            expediente_id=1,
            url='cualquier/carpeta/de_red/Informe Ya Organizado.pdf',
        )  # sin hash_md5: no viene de multipart
        doc.id = 43
        tarea = _tarea_stub()

        with _sin_organismo():
            mover_a_esftt(doc, tarea)

        assert doc.url == f'{_ruta_tarea_stub_default()}/Informe Ya Organizado.pdf'

    def test_colision_de_nombre_en_destino_sufija_con_id_documento(self, app_ctx, _fs_tmp):
        destino_dir = _fs_tmp / _ruta_tarea_stub_default()
        destino_dir.mkdir(parents=True)
        (destino_dir / 'informe.pdf').write_bytes(b'contenido de OTRO documento')

        origen_dir = _fs_tmp / 'AT-5' / 'pool'
        origen_dir.mkdir(parents=True)
        origen = origen_dir / 'aaaaaaaa_informe.pdf'
        origen.write_bytes(b'contenido de ESTE documento')

        doc = Documento(
            expediente_id=1, url='AT-5/pool/aaaaaaaa_informe.pdf', hash_md5='a' * 32,
        )
        doc.id = 77
        tarea = _tarea_stub()

        with _sin_organismo():
            mover_a_esftt(doc, tarea)

        assert doc.url == f'{_ruta_tarea_stub_default()}/informe_77.pdf'
        assert (destino_dir / 'informe.pdf').read_bytes() == b'contenido de OTRO documento'
        assert (destino_dir / 'informe_77.pdf').read_bytes() == b'contenido de ESTE documento'

    def test_fallo_en_commit_no_deja_url_apuntando_a_nada_inexistente(
        self, app_ctx, _fs_tmp, monkeypatch,
    ):
        origen_dir = _fs_tmp / 'AT-5' / 'pool'
        origen_dir.mkdir(parents=True)
        origen = origen_dir / 'aaaaaaaa_informe.pdf'
        origen.write_bytes(b'contenido')

        doc = Documento(expediente_id=1, url='AT-5/pool/aaaaaaaa_informe.pdf', hash_md5='a' * 32)
        doc.id = 88
        tarea = _tarea_stub()

        def _commit_falla():
            raise RuntimeError('fallo simulado en commit (#667)')

        monkeypatch.setattr(db.session, 'commit', _commit_falla)

        with _sin_organismo():
            with pytest.raises(RuntimeError, match='fallo simulado'):
                mover_a_esftt(doc, tarea)

        # El origen sigue intacto: nunca se borra sin un commit exitoso de antes.
        assert origen.exists()
        assert origen.read_bytes() == b'contenido'


# ---------------------------------------------------------------------------
# mover_a_pool(documento)
# ---------------------------------------------------------------------------

class TestMoverAPool:

    def test_no_op_si_esquema_bddat(self, app_ctx, _fs_tmp):
        doc = Documento(expediente_id=1, url='bddat://certificados/1')
        expediente = Expediente(numero_at=5)
        assert mover_a_pool(doc, expediente) is False

    def test_no_op_si_ya_esta_en_pool(self, app_ctx, _fs_tmp):
        pool_dir = _fs_tmp / 'AT-5' / 'pool'
        pool_dir.mkdir(parents=True)
        (pool_dir / 'informe.pdf').write_bytes(b'contenido')

        doc = Documento(expediente_id=1, url='AT-5/pool/informe.pdf')
        doc.id = 1
        expediente = Expediente(numero_at=5)

        assert mover_a_pool(doc, expediente) is False

    def test_mueve_de_carpeta_esftt_a_pool(self, app_ctx, _fs_tmp):
        origen_dir = _fs_tmp / _ruta_tarea_stub_default()
        origen_dir.mkdir(parents=True)
        origen = origen_dir / 'informe.pdf'
        origen.write_bytes(b'contenido huerfano de nuevo')

        doc = Documento(expediente_id=1, url=f'{_ruta_tarea_stub_default()}/informe.pdf')
        doc.id = 99
        expediente = Expediente(numero_at=5)

        resultado = mover_a_pool(doc, expediente)

        assert resultado is True
        assert doc.url == 'AT-5/pool/informe.pdf'
        assert not origen.exists()
        assert (_fs_tmp / 'AT-5' / 'pool' / 'informe.pdf').read_bytes() == b'contenido huerfano de nuevo'

