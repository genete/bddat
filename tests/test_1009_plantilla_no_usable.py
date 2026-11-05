"""
#1009 (ADR-050 §J, enmienda del 2026-11-02) — el servidor no genera con una plantilla que el
supervisor ha desactivado.

Fallo silencioso que evita: se genera un escrito con una plantilla que el supervisor pausó por
llevar un error, porque solo el desplegable la ocultaba y `/api/escritos/generar` no miraba
`activo`: quien tuviera su id (una pantalla abierta de antes, una petición a mano) sacaba el
escrito con el texto equivocado y nada lo avisaba.

Regresión de un hueco real: hasta #1009 `generar` y `preview` solo comprobaban que la plantilla
existiera. La guarda vive en el código (`contenido.motivo_no_usable`); este test fija que la ruta
la aplica.
"""
import io
import zipfile

import pytest

from app import db


def _odt_minimo() -> bytes:
    """.odt mínimo (zip con `mimetype` primero): el formato lo admite el módulo de contenido."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
        z.writestr('content.xml', '<root><p>plantilla de prueba #1009</p></root>')
    return buffer.getvalue()


@pytest.fixture
def plantilla_desactivada(app, almacen_tmp):
    """Plantilla con fichero en el almacén y `activo = false`, commiteada (las rutas no pasan por
    `app_ctx`, #836), y su limpieza: la plantilla antes que la fila de `ficheros` que referencia."""
    from app.models.plantillas import Plantilla
    from app.models.tipos_documentos import TipoDocumento
    from app.services.almacenamiento import contenido

    with app.app_context():
        tipo = TipoDocumento.query.filter_by(codigo='OTROS').first()
        assert tipo is not None, 'la semilla debe traer el tipo de documento OTROS'
        plantilla = Plantilla(codigo='TEST_1009_DESACTIVADA', nombre='Plantilla de prueba #1009',
                              tipo_documento_id=tipo.id, activo=False)
        contenido.guardar_plantilla(plantilla, io.BytesIO(_odt_minimo()), 'test_1009.odt')
        db.session.add(plantilla)
        db.session.commit()
        plantilla_id = plantilla.id
    yield plantilla_id
    with app.app_context():
        db.session.rollback()
        Plantilla.query.filter_by(id=plantilla_id).delete()
        db.session.commit()


@pytest.fixture
def elaborar_de_resolucion(app, expediente_seed):
    """ELABORAR de la resolución —un trámite sin destinatario— commiteada, y su limpieza."""
    from app.models.fases import Fase
    from app.models.solicitudes import Solicitud
    from tests.conftest import ArbolESFTT

    with app.app_context():
        solicitud = (Solicitud.query.filter_by(expediente_id=expediente_seed)
                     .order_by(Solicitud.id).first())
        assert solicitud is not None, 'la semilla debe traer una solicitud en el expediente'
        arbol = ArbolESFTT(db)
        fase = arbol.fase('RESOLUCION', solicitud=solicitud)
        tarea = arbol.tarea(arbol.tramite(fase, 'ELABORACION'), 'ELABORAR')
        db.session.commit()
        fase_id, tarea_id = fase.id, tarea.id
    yield tarea_id
    with app.app_context():
        db.session.rollback()
        Fase.query.filter_by(id=fase_id).delete()
        db.session.commit()


def test_generar_rechaza_una_plantilla_desactivada(usuario_supervisor, app, plantilla_desactivada,
                                                   elaborar_de_resolucion):
    from app.models.tareas import Tarea

    r = usuario_supervisor.post('/api/escritos/generar', json={
        'plantilla_id': plantilla_desactivada, 'tarea_id': elaborar_de_resolucion})

    assert r.status_code == 409
    assert 'desactivada' in r.get_json()['error']
    with app.app_context():
        assert db.session.get(Tarea, elaborar_de_resolucion).vinculos_documento == []
