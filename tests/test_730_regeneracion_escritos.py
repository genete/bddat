"""
Tests #730 — regenerar el escrito de una tarea ELABORAR sustituye el draft
anterior en vez de crear un documento nuevo cada vez.

Parte 1: evaluar_regeneracion() — decisión pura, matriz de 8 casos (issue
#730). Tarea stubeada (reutiliza _tarea_stub/_sin_organismo de
test_665_ruta_esftt) + Documento real transitorio, igual que test_667.

Parte 2: helpers físicos de ejecutar_regeneracion() — apartar el fichero
anterior con timestamp, apartar un fichero ajeno, ruta alternativa,
renombrado en sitio.

Parte 3: ejecutar_regeneracion() de extremo a extremo contra la BD real de
desarrollo (mismo patrón que TestEditarTareaEngancheMovimiento en test_667):
verifica que la fila Documento se reutiliza, nunca se crea una segunda.
"""
import hashlib
import os
import time
from types import SimpleNamespace

import pytest

from app import db
from app.models.documentos import Documento
from app.models.documentos_tarea import DocumentoTarea
from app.models.tareas import Tarea
from app.services.regeneracion_escritos import (
    Evaluacion,
    _apartar_fichero_anterior,
    _renombrar_ajeno_aparte,
    _renombrar_en_sitio,
    _ruta_alternativa,
    ejecutar_regeneracion,
    evaluar_regeneracion,
    localizar_draft_vinculado,
)
from tests.test_665_ruta_esftt import _sin_organismo, _tarea_stub
from tests.test_667_mover_documento_esftt import _ruta_tarea_stub_default


@pytest.fixture
def _fs_tmp(app, tmp_path):
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


TIPO_DOC_ID = 7  # arbitrario, consistente entre documento_existente y la plantilla del test


def _vinculo(documento, rol='CONSUMIDO'):
    return SimpleNamespace(rol=rol, documento=documento)


def _documento_con_fichero(fs_tmp, ruta_rel, contenido, *, tipo_doc_id=TIPO_DOC_ID, con_hash=True):
    """Documento transitorio (sin persistir) con su fichero físico ya en disco."""
    ruta_abs = fs_tmp / ruta_rel
    ruta_abs.parent.mkdir(parents=True, exist_ok=True)
    ruta_abs.write_bytes(contenido)
    doc = Documento(
        expediente_id=1,
        url=ruta_rel.replace(os.sep, '/'),
        tipo_doc_id=tipo_doc_id,
        hash_md5=hashlib.md5(contenido).hexdigest() if con_hash else None,
    )
    doc.id = 999
    return doc


# ---------------------------------------------------------------------------
# Parte 1 — evaluar_regeneracion(): matriz de 8 casos
# ---------------------------------------------------------------------------

class TestEvaluarRegeneracionMatriz:

    def test_caso_1_sin_draft_sin_colision(self, app_ctx, _fs_tmp):
        tarea = _tarea_stub()
        tarea.vinculos_documento = []
        ruta_destino = str(_fs_tmp / 'AT-5' / 'destino.odt')  # no existe

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'contenido nuevo', nombre_fichero='destino.odt',
            ruta_destino_abs=ruta_destino,
        )

        assert ev.caso == 1
        assert ev.documento_existente is None
        assert ev.requiere_confirmacion is False
        assert ev.colision_nombre is None

    def test_caso_2_sin_draft_con_colision_externa(self, app_ctx, _fs_tmp):
        tarea = _tarea_stub()
        tarea.vinculos_documento = []
        destino = _fs_tmp / 'AT-5'
        destino.mkdir(parents=True)
        (destino / 'destino.odt').write_bytes(b'fichero ajeno, nada que ver con bddat')

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'contenido nuevo', nombre_fichero='destino.odt',
            ruta_destino_abs=str(destino / 'destino.odt'),
        )

        assert ev.caso == 2
        assert ev.requiere_confirmacion is True
        assert ev.colision_nombre == 'destino.odt'

    def test_caso_3_hash_igual_nombre_igual_no_op(self, app_ctx, _fs_tmp):
        contenido = b'el mismo contenido de siempre'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'escrito.odt'), contenido)
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=contenido, nombre_fichero='escrito.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'escrito.odt'),
        )

        assert ev.caso == 3
        assert ev.documento_existente is doc
        assert ev.hash_coincide is True
        assert ev.nombre_coincide is True
        assert ev.requiere_confirmacion is False

    def test_caso_4_hash_igual_nombre_distinto_sin_colision(self, app_ctx, _fs_tmp):
        contenido = b'contenido sin cambios'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'viejo.odt'), contenido)
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=contenido, nombre_fichero='nuevo.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'nuevo.odt'),
        )

        assert ev.caso == 4
        assert ev.hash_coincide is True
        assert ev.nombre_coincide is False
        assert ev.colision_nombre is None
        assert ev.requiere_confirmacion is False

    def test_caso_5_hash_igual_nombre_distinto_con_colision(self, app_ctx, _fs_tmp):
        contenido = b'contenido sin cambios'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'viejo.odt'), contenido)
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]
        (_fs_tmp / 'AT-5' / 'nuevo.odt').write_bytes(b'fichero ajeno')

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=contenido, nombre_fichero='nuevo.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'nuevo.odt'),
        )

        assert ev.caso == 5
        assert ev.colision_nombre == 'nuevo.odt'
        assert ev.requiere_confirmacion is True

    def test_caso_6_hash_distinto_nombre_igual(self, app_ctx, _fs_tmp):
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'escrito.odt'), b'version vieja')
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'version nueva, distinta', nombre_fichero='escrito.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'escrito.odt'),
        )

        assert ev.caso == 6
        assert ev.hash_coincide is False
        assert ev.nombre_coincide is True
        # El ocupante del destino es el propio draft a sustituir: nunca colisión externa.
        assert ev.colision_nombre is None
        assert ev.requiere_confirmacion is True

    def test_caso_7_hash_distinto_nombre_distinto_sin_colision(self, app_ctx, _fs_tmp):
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'viejo.odt'), b'version vieja')
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'version nueva, distinta', nombre_fichero='nuevo.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'nuevo.odt'),
        )

        assert ev.caso == 7
        assert ev.colision_nombre is None
        assert ev.requiere_confirmacion is True

    def test_caso_8_hash_distinto_nombre_distinto_con_colision(self, app_ctx, _fs_tmp):
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'viejo.odt'), b'version vieja')
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]
        (_fs_tmp / 'AT-5' / 'nuevo.odt').write_bytes(b'fichero ajeno')

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'version nueva, distinta', nombre_fichero='nuevo.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'nuevo.odt'),
        )

        assert ev.caso == 8
        assert ev.colision_nombre == 'nuevo.odt'
        assert ev.requiere_confirmacion is True

    def test_documento_sin_hash_previo_se_trata_como_hash_distinto(self, app_ctx, _fs_tmp):
        """Documentos anteriores a que se empezara a guardar hash_md5 (o de
        entrada in situ): nunca "coinciden", nunca no-op silencioso."""
        contenido = b'contenido cualquiera'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'escrito.odt'),
                                     contenido, con_hash=False)
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=contenido, nombre_fichero='escrito.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'escrito.odt'),
        )

        assert ev.caso == 6
        assert ev.hash_coincide is False

    def test_rol_distinto_no_cuenta_como_draft(self, app_ctx, _fs_tmp):
        """Un CONSUMIDO ajeno al escrito (p.ej. BORRADOR_FIRMA subido a mano)
        no debe confundirse con el draft — calificador tipo_doc_id."""
        contenido = b'PDF de firma, no el escrito'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'firma.pdf'),
                                     contenido, tipo_doc_id=TIPO_DOC_ID + 1)
        tarea = _tarea_stub()
        tarea.vinculos_documento = [_vinculo(doc)]

        ev = evaluar_regeneracion(
            tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
            doc_bytes=b'escrito nuevo', nombre_fichero='escrito.odt',
            ruta_destino_abs=str(_fs_tmp / 'AT-5' / 'escrito.odt'),
        )

        assert ev.caso == 1
        assert ev.documento_existente is None


# ---------------------------------------------------------------------------
# Parte 2 — helpers físicos
# ---------------------------------------------------------------------------

class TestHelpersFisicos:

    def test_apartar_fichero_anterior_deja_sufijo_timestamp_y_libera_el_nombre(self, app_ctx, _fs_tmp):
        contenido = b'borrador anterior'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'escrito.odt'), contenido)
        origen = _fs_tmp / 'AT-5' / 'escrito.odt'

        _apartar_fichero_anterior(doc)

        assert not origen.exists()
        restantes = list((_fs_tmp / 'AT-5').iterdir())
        assert len(restantes) == 1
        assert restantes[0].name.startswith('escrito_')
        assert restantes[0].read_bytes() == contenido

    def test_apartar_fichero_anterior_no_falla_si_ya_no_existe(self, app_ctx, _fs_tmp):
        doc = Documento(expediente_id=1, url='AT-5/no_existe.odt')
        doc.id = 1
        _apartar_fichero_anterior(doc)  # no debe lanzar

    def test_renombrar_ajeno_aparte(self, app_ctx, _fs_tmp):
        (_fs_tmp / 'AT-5').mkdir(parents=True)
        ocupado = _fs_tmp / 'AT-5' / 'escrito.odt'
        ocupado.write_bytes(b'fichero ajeno')

        _renombrar_ajeno_aparte(str(ocupado))

        assert not ocupado.exists()
        restantes = list((_fs_tmp / 'AT-5').iterdir())
        assert len(restantes) == 1
        assert '_ajeno_' in restantes[0].name
        assert restantes[0].read_bytes() == b'fichero ajeno'

    def test_ruta_alternativa_evita_colision(self, app_ctx, _fs_tmp):
        (_fs_tmp / 'AT-5').mkdir(parents=True)
        (_fs_tmp / 'AT-5' / 'escrito.odt').write_bytes(b'x')
        (_fs_tmp / 'AT-5' / 'escrito_2.odt').write_bytes(b'x')

        alternativa = _ruta_alternativa(str(_fs_tmp / 'AT-5' / 'escrito.odt'))

        assert alternativa == str(_fs_tmp / 'AT-5' / 'escrito_3.odt')

    def test_renombrar_en_sitio_mueve_y_actualiza_url(self, app_ctx, _fs_tmp):
        contenido = b'mismo contenido, solo cambia el nombre'
        doc = _documento_con_fichero(_fs_tmp, os.path.join('AT-5', 'viejo.odt'), contenido)
        nuevo_destino = _fs_tmp / 'AT-5' / 'nuevo.odt'

        _renombrar_en_sitio(doc, str(nuevo_destino), str(_fs_tmp))

        assert not (_fs_tmp / 'AT-5' / 'viejo.odt').exists()
        assert nuevo_destino.read_bytes() == contenido
        assert doc.url == 'AT-5/nuevo.odt'


# ---------------------------------------------------------------------------
# Parte 3 — ejecutar_regeneracion() de extremo a extremo (BD real, #667 style)
# ---------------------------------------------------------------------------

def _tarea_real_sin_vinculos(app_ctx):
    tarea = Tarea.query.filter(~Tarea.vinculos_documento.any()).first()
    if tarea is None:
        pytest.skip('No hay tareas sin vínculos documentales en la BD de desarrollo')
    return tarea


def _plantilla_stub(tipo_documento_id):
    return SimpleNamespace(nombre='Plantilla de prueba #730', variante=None,
                           tipo_documento_id=tipo_documento_id)


class TestEjecutarRegeneracionExtremoAExtremo:

    def test_caso_1_alta_crea_documento_y_vincula_consumido(self, app_ctx, fs_tmp):
        tarea = _tarea_real_sin_vinculos(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        plantilla = _plantilla_stub(TIPO_DOC_ID)
        nombre = 'escrito_730.odt'
        ruta = str(fs_tmp / f'AT-{expediente.numero_at}' / nombre)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        doc_bytes = b'primera generacion'

        ev = evaluar_regeneracion(tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
                                  doc_bytes=doc_bytes, nombre_fichero=nombre, ruta_destino_abs=ruta)
        assert ev.caso == 1

        doc = ejecutar_regeneracion(
            tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=doc_bytes,
            nombre_fichero=nombre, ruta_destino_abs=ruta, fs_base=str(fs_tmp),
            rol='CONSUMIDO', asunto='Plantilla de prueba #730', evaluacion=ev,
        )
        db.session.flush()

        assert doc.id is not None
        assert doc.hash_md5 == hashlib.md5(doc_bytes).hexdigest()
        vinculo = next(v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO')
        assert vinculo.documento_id == doc.id

    def test_caso_6_sustitucion_reutiliza_fila_no_crea_una_segunda(self, app_ctx, fs_tmp):
        tarea = _tarea_real_sin_vinculos(app_ctx)
        expediente = tarea.tramite.fase.solicitud.expediente
        plantilla = _plantilla_stub(TIPO_DOC_ID)
        nombre = 'escrito_730.odt'
        ruta = str(fs_tmp / f'AT-{expediente.numero_at}' / nombre)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)

        # Primera generación
        ev1 = evaluar_regeneracion(tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
                                   doc_bytes=b'version 1', nombre_fichero=nombre, ruta_destino_abs=ruta)
        doc1 = ejecutar_regeneracion(
            tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=b'version 1',
            nombre_fichero=nombre, ruta_destino_abs=ruta, fs_base=str(fs_tmp),
            rol='CONSUMIDO', asunto='Plantilla de prueba #730', evaluacion=ev1,
        )
        db.session.flush()
        primer_id = doc1.id

        # mtime del fichero anterior tiene que poder distinguirse del de ahora
        time.sleep(1.1)

        # Segunda generación — mismo nombre, contenido distinto (caso 6)
        ev2 = evaluar_regeneracion(tarea=tarea, rol='CONSUMIDO', tipo_doc_id=TIPO_DOC_ID,
                                   doc_bytes=b'version 2, cambio real', nombre_fichero=nombre,
                                   ruta_destino_abs=ruta)
        assert ev2.caso == 6
        assert ev2.documento_existente.id == primer_id

        doc2 = ejecutar_regeneracion(
            tarea=tarea, expediente=expediente, plantilla=plantilla,
            doc_bytes=b'version 2, cambio real', nombre_fichero=nombre, ruta_destino_abs=ruta,
            fs_base=str(fs_tmp), rol='CONSUMIDO', asunto='Plantilla de prueba #730', evaluacion=ev2,
        )
        db.session.flush()

        # Misma fila reutilizada, no una segunda
        assert doc2.id == primer_id
        vinculos_consumido = [v for v in tarea.vinculos_documento if v.rol == 'CONSUMIDO']
        assert len(vinculos_consumido) == 1

        # El fichero anterior quedó apartado con timestamp, el nuevo ocupa el nombre canónico
        ficheros = os.listdir(os.path.dirname(ruta))
        assert nombre in ficheros
        apartados = [f for f in ficheros if f != nombre]
        assert len(apartados) == 1
        assert apartados[0].startswith('escrito_730_')
        with open(ruta, 'rb') as f:
            assert f.read() == b'version 2, cambio real'
