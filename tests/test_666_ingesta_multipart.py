"""
Tests #666 — ingesta multipart al pool de documentos (ADR-032 §4).

Parte 1 (esta sección): saneado de nombre y resolución de nombre único en el
pool — funciones puras / solo filesystem local, sin necesidad de contexto
Flask ni BD (mismo patrón que TestRutaPoolDocumento en test_665_ruta_esftt.py).

Parte 2: test funcional del endpoint de subida, contra la BD real de
desarrollo (mismo patrón que el resto de la suite) — ver fixture autouse de
limpieza más abajo.
"""
import hashlib
import io
import json
import os

import pytest

from app.services.rutas_esftt import _saneado_nombre_pool, nombre_pool_unico


# ---------------------------------------------------------------------------
# _saneado_nombre_pool — solo correctivo, nunca trunca por longitud
# ---------------------------------------------------------------------------

class TestSaneadoNombrePool:

    def test_nombre_normal_pasa_intacto(self):
        assert _saneado_nombre_pool('informe.pdf') == 'informe.pdf'

    def test_preserva_acentos_y_enye(self):
        assert _saneado_nombre_pool('Informe_técnico_ñ.pdf') == 'Informe_técnico_ñ.pdf'

    def test_no_trunca_nombres_largos(self):
        nombre_largo = 'Resolución_Autorización_Administrativa_Previa_' * 5 + '.pdf'
        assert _saneado_nombre_pool(nombre_largo) == nombre_largo

    def test_descarta_componentes_de_ruta_unix(self):
        assert _saneado_nombre_pool('../../etc/passwd') == 'passwd'

    def test_descarta_componentes_de_ruta_windows(self):
        assert _saneado_nombre_pool('..\\..\\Windows\\System32\\evil.exe') == 'evil.exe'

    def test_sustituye_caracteres_invalidos_windows(self):
        assert _saneado_nombre_pool('a:b*c?d"e<f>g|h.txt') == 'a_b_c_d_e_f_g_h.txt'

    def test_recorta_espacios_y_puntos_finales(self):
        assert _saneado_nombre_pool('nombre...   ') == 'nombre'

    def test_fallback_si_queda_vacio(self):
        assert _saneado_nombre_pool('....') == 'documento'

    def test_nombre_reservado_windows_sin_extension(self):
        assert _saneado_nombre_pool('con') == '_con'

    def test_nombre_reservado_windows_con_extension_case_insensitive(self):
        assert _saneado_nombre_pool('Con.TXT') == '_Con.TXT'

    def test_nombre_no_reservado_no_se_toca(self):
        assert _saneado_nombre_pool('conclusiones.pdf') == 'conclusiones.pdf'


# ---------------------------------------------------------------------------
# nombre_pool_unico — prefijo de hash + colisión git-style, sin tocar BD
# ---------------------------------------------------------------------------

class TestNombrePoolUnico:

    def test_directorio_vacio_usa_prefijo_de_8(self, tmp_path):
        hash_md5 = hashlib.md5(b'contenido').hexdigest()
        nombre, ya_existe = nombre_pool_unico(hash_md5, 'informe.pdf', str(tmp_path))
        assert nombre == f'{hash_md5[:8]}_informe.pdf'
        assert ya_existe is False

    def test_sanea_el_nombre_original(self, tmp_path):
        hash_md5 = hashlib.md5(b'contenido').hexdigest()
        nombre, _ = nombre_pool_unico(hash_md5, '../../etc/passwd', str(tmp_path))
        assert nombre == f'{hash_md5[:8]}_passwd'

    def test_colision_prefijo_con_contenido_distinto_extiende_un_caracter(self, tmp_path):
        hash_nuevo = 'deadbeef' + '0' * 24
        existente = tmp_path / f'{hash_nuevo[:8]}_informe.pdf'
        existente.write_bytes(b'contenido distinto')

        nombre, ya_existe = nombre_pool_unico(hash_nuevo, 'informe.pdf', str(tmp_path))

        assert ya_existe is False
        assert nombre == f'{hash_nuevo[:9]}_informe.pdf'

    def test_duplicado_exacto_no_marca_reescritura(self, tmp_path):
        contenido = b'contenido real e identico'
        hash_real = hashlib.md5(contenido).hexdigest()
        ruta = tmp_path / f'{hash_real[:8]}_informe.pdf'
        ruta.write_bytes(contenido)

        nombre, ya_existe = nombre_pool_unico(hash_real, 'informe.pdf', str(tmp_path))

        assert ya_existe is True
        assert nombre == f'{hash_real[:8]}_informe.pdf'

    def test_dos_colisiones_seguidas_extiende_dos_caracteres(self, tmp_path):
        hash_nuevo = 'cafebabe' + '1' * 24
        (tmp_path / f'{hash_nuevo[:8]}_informe.pdf').write_bytes(b'otro contenido A')
        (tmp_path / f'{hash_nuevo[:9]}_informe.pdf').write_bytes(b'otro contenido B')

        nombre, ya_existe = nombre_pool_unico(hash_nuevo, 'informe.pdf', str(tmp_path))

        assert ya_existe is False
        assert nombre == f'{hash_nuevo[:10]}_informe.pdf'


# ---------------------------------------------------------------------------
# Endpoint funcional — POST /expedientes/<id>/documentos/subir
#
# Contra la BD real de desarrollo (mismo patrón que el resto de la suite,
# ver conftest._login_as). Los Documento de prueba se marcan con '#666 test'
# en el asunto y se borran en el fixture autouse de abajo. FILESYSTEM_BASE se
# redirige a un directorio temporal (_pool_tmp) para no escribir en el
# servidor de ficheros real de desarrollo.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _limpiar_documentos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.documentos import Documento
        Documento.query.filter(
            Documento.asunto.like('%#666 test%')
        ).delete(synchronize_session=False)
        db.session.commit()


@pytest.fixture
def _pool_tmp(app, tmp_path):
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


class TestEndpointSubirDocumento:

    def test_sube_un_fichero_y_crea_documento(self, usuario_supervisor, expediente_seed, _pool_tmp, app):
        metadatos = [{'tipo_doc_id': 1, 'asunto': '#666 test — sube un fichero', 'prioridad': True}]
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={
                'ficheros': (io.BytesIO(b'contenido de prueba'), 'informe_666.pdf'),
                'metadatos': json.dumps(metadatos),
            },
            content_type='multipart/form-data',
        )
        assert r.status_code == 200
        data = r.get_json()
        assert data['ok'] is True
        assert data['creados'] == 1

        with app.app_context():
            from app.models.documentos import Documento
            doc = Documento.query.filter_by(
                expediente_id=expediente_seed,
                asunto='#666 test — sube un fichero',
            ).first()
            assert doc is not None
            assert doc.hash_md5 == hashlib.md5(b'contenido de prueba').hexdigest()
            assert doc.prioridad == 1
            ruta_fisica = doc.ruta_absoluta()

        assert os.path.isfile(ruta_fisica)
        assert ruta_fisica.endswith('informe_666.pdf')

    def test_sin_ficheros_devuelve_400(self, usuario_supervisor, expediente_seed, _pool_tmp):
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={'metadatos': '[]'},
            content_type='multipart/form-data',
        )
        assert r.status_code == 400
        assert r.get_json()['ok'] is False

    def test_duplicado_exacto_no_reescribe_pero_crea_documento(
        self, usuario_supervisor, expediente_seed, _pool_tmp, app,
    ):
        contenido = b'contenido duplicado #666'
        for i in range(2):
            metadatos = [{'tipo_doc_id': 1, 'asunto': f'#666 test — duplicado {i}'}]
            r = usuario_supervisor.post(
                f'/expedientes/{expediente_seed}/documentos/subir',
                data={
                    'ficheros': (io.BytesIO(contenido), 'duplicado.pdf'),
                    'metadatos': json.dumps(metadatos),
                },
                content_type='multipart/form-data',
            )
            assert r.get_json()['ok'] is True

        with app.app_context():
            from app.models.documentos import Documento
            docs = Documento.query.filter(
                Documento.expediente_id == expediente_seed,
                Documento.asunto.like('#666 test — duplicado%'),
            ).order_by(Documento.id).all()
            assert len(docs) == 2
            # Mismo hash, mismo fichero físico — dos registros distintos, sin bloquear.
            assert docs[0].hash_md5 == docs[1].hash_md5
            assert docs[0].url == docs[1].url
