"""
Tests #666 — ingesta multipart al pool de documentos (ADR-032 §4, ADR-050 §C).

Parte 1 (esta sección): saneado del nombre del fichero que llega de fuera —
función pura, sin contexto Flask ni BD. El nombre único con prefijo MD5 del pool
salió con el modelo de rutas (#1007, PR 5): el almacén nombra por SHA-256.

Parte 2: test funcional del endpoint de subida, contra la BD real de
desarrollo (mismo patrón que el resto de la suite) — ver fixture autouse de
limpieza más abajo.
"""
import io
import json

import pytest

from app.services.almacenamiento.nombres import sanear_nombre as _saneado_nombre_pool


# ---------------------------------------------------------------------------
# sanear_nombre — solo correctivo, nunca trunca por longitud
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
# Endpoint funcional — POST /expedientes/<id>/documentos/subir
#
# Contra la BD real de desarrollo (mismo patrón que el resto de la suite,
# ver conftest._login_as). Los Documento de prueba se marcan con '#666 test'
# en el asunto y se borran en el fixture autouse de abajo. El almacén se
# redirige a un directorio temporal (`almacen_tmp`) para no escribir en el
# almacén real de desarrollo.
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


class TestEndpointSubirDocumento:

    def test_sube_un_fichero_y_crea_documento(self, usuario_supervisor, expediente_seed, almacen_tmp, app):
        contenido = b'%PDF-1.4 contenido de prueba #666'
        metadatos = [{'tipo_doc_id': 1, 'asunto': '#666 test — sube un fichero', 'prioridad': True}]
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={
                'ficheros': (io.BytesIO(contenido), 'informe_666.pdf'),
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
            from app.services.almacenamiento.contenido import leer
            doc = Documento.query.filter_by(
                expediente_id=expediente_seed,
                asunto='#666 test — sube un fichero',
            ).first()
            assert doc is not None
            assert doc.prioridad == 1
            assert doc.nombre_fichero == 'informe_666.pdf'
            assert leer(doc).datos == contenido

    def test_sin_ficheros_devuelve_400(self, usuario_supervisor, expediente_seed, almacen_tmp):
        r = usuario_supervisor.post(
            f'/expedientes/{expediente_seed}/documentos/subir',
            data={'metadatos': '[]'},
            content_type='multipart/form-data',
        )
        assert r.status_code == 400
        assert r.get_json()['ok'] is False

    def test_duplicado_exacto_no_reescribe_pero_crea_documento(
        self, usuario_supervisor, expediente_seed, almacen_tmp, app,
    ):
        contenido = b'%PDF-1.4 contenido duplicado #666'
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
            # Mismo contenido guardado una sola vez — dos documentos distintos, sin bloquear.
            assert docs[0].fichero_ref == docs[1].fichero_ref
