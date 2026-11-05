"""
#1009 (ADR-050 §J) — subir una plantilla la sustituye solo si valida; si no, la vigente no cambia.

Fallo silencioso que evita: que un fichero que no pasa la validación del motor (no es un `.odt`,
o tiene Jinja roto) acabe sustituyendo a la plantilla vigente aunque la respuesta sea un error.
El supervisor lee «la plantilla no es válida» y da por hecho que no ha pasado nada, pero la
plantilla ya apunta al fichero malo y cada escrito que se genere desde entonces falla o sale roto
(§J: «si no pasa, no cambia nada»). Basta con que alguien reordene `editar` para guardar antes de
validar. El caso válido es el control: sin él, un `editar` que nunca sustituyera nada pasaría el
test.
"""
import io
import json
import zipfile
from pathlib import Path

import pytest

from app import db

BASES = Path(__file__).resolve().parent.parent / 'app' / 'data' / 'plantillas_base'


def _base(nombre: str) -> bytes:
    return (BASES / nombre).read_bytes()


def _con_bucle_sin_cerrar(datos: bytes) -> bytes:
    """El mismo `.odt` con un `{% for %}` sin su `endfor`: el motor lo rechaza al compilar."""
    salida = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(datos)) as origen, \
            zipfile.ZipFile(salida, 'w', zipfile.ZIP_DEFLATED) as destino:
        for info in origen.infolist():
            contenido = origen.read(info.filename)
            if info.filename == 'content.xml':
                contenido = contenido.replace(
                    b'</office:text>',
                    b'<text:p>{% for m in municipios %}{{ m }}</text:p></office:text>', 1)
            destino.writestr(info, contenido)
    return salida.getvalue()


@pytest.fixture
def plantilla_vigente(app, almacen_tmp):
    """Plantilla activa con la resolución base como fichero, commiteada (las rutas no pasan por
    `app_ctx`, #836), y su limpieza: la plantilla antes que la fila de `ficheros` que referencia."""
    from app.models.plantillas import Plantilla
    from app.models.tipos_documentos import TipoDocumento
    from app.services.almacenamiento import contenido

    with app.app_context():
        tipo = TipoDocumento.query.filter_by(codigo='OTROS').first()
        assert tipo is not None, 'la semilla debe traer el tipo de documento OTROS'
        plantilla = Plantilla(codigo='TEST_1009_SUSTITUCION', nombre='Plantilla de prueba #1009',
                              tipo_documento_id=tipo.id, activo=True)
        contenido.guardar_plantilla(plantilla, io.BytesIO(_base('resolucion_base.odt')),
                                    'resolucion_base.odt')
        db.session.add(plantilla)
        db.session.commit()
        plantilla_id = plantilla.id
    yield plantilla_id
    with app.app_context():
        db.session.rollback()
        Plantilla.query.filter_by(id=plantilla_id).delete()
        db.session.commit()


@pytest.mark.parametrize('nuevo,sustituye', [
    (lambda: _base('carta_base.odt'), True),
    (lambda: b'esto no es un odt', False),
    (lambda: _con_bucle_sin_cerrar(_base('carta_base.odt')), False),
], ids=['valida', 'no_es_un_odt', 'jinja_roto'])
def test_una_plantilla_sustituye_a_la_vigente_solo_si_valida(
        usuario_supervisor, app, plantilla_vigente, nuevo, sustituye):
    from app.models.plantillas import Plantilla
    from app.services.almacenamiento import contenido

    vigente = _base('resolucion_base.odt')
    datos = nuevo()

    r = usuario_supervisor.post(
        f'/plantillas/{plantilla_vigente}/editar',
        data={'fichero': (io.BytesIO(datos), 'subida.odt')},
        content_type='multipart/form-data',
        headers={'X-Requested-With': 'XMLHttpRequest'},
    )

    assert r.status_code == 200
    assert json.loads(r.data)['ok'] is sustituye
    with app.app_context():
        plantilla = db.session.get(Plantilla, plantilla_vigente)
        assert contenido.leer_plantilla(plantilla).datos == (datos if sustituye else vigente)
