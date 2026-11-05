"""
#1009 (ADR-050 §J, bloque 3) — un expediente dummy genera su escrito por la ruta real.

Fallo silencioso que evita: que el escrito de un expediente salga sin los datos del expediente
o sin el fragmento que cita la plantilla, y nada falle. Cada pieza tiene sus tests con datos
sintéticos sueltos (el motor, el contexto base, la regeneración), pero ninguno recorre la cadena
entera con un expediente de verdad: plantilla del almacén → desplegable de la tarea → motor con
el contexto del expediente y su fragmento → documento vinculado → descarga. Un cambio en
cualquier eslabón (el contexto, la inserción de fragmentos, el almacén) puede dejar un escrito
válido pero vacío de datos, y un .odt sin los datos del expediente no da ningún error.

Los valores esperados salen de la BD (el número AT y el titular del expediente), no del motor, y
el texto del fragmento, de `scripts/plantillas_demo.py`.

La plantilla y el fragmento se registran con la misma función que usa la semilla
(`plantillas_demo.registrar`) pero con otro prefijo y en el almacén temporal: leer desde él las
filas de la semilla, cuyo contenido está en el almacén de tests, las marcaría como ausentes (§G)
y quedarían así para el resto de la suite.
"""
import html
import io
import re
import zipfile

import pytest

from app import db
from scripts import plantillas_demo

PREFIJO = 'E2E_'


@pytest.fixture
def plantilla_de_demostracion(app, almacen_tmp):
    """ID de la plantilla `E2E_RESOLUCION` y su fragmento, registrados en el almacén temporal y
    commiteados (las rutas no pasan por `app_ctx`, #836), y su limpieza: las filas antes que la
    fila de `ficheros` que referencian."""
    from app.models.fragmentos import Fragmento
    from app.models.plantillas import Plantilla

    with app.app_context():
        ids = plantillas_demo.registrar(PREFIJO, claves=['RESOLUCION'])
        db.session.commit()
        plantilla_id = ids['RESOLUCION']
    yield plantilla_id
    with app.app_context():
        db.session.rollback()
        Plantilla.query.filter(Plantilla.codigo.like(f'{PREFIJO}%')).delete(
            synchronize_session=False)
        Fragmento.query.filter_by(nombre=plantillas_demo.nombre_fragmento(PREFIJO)).delete()
        db.session.commit()


def test_un_expediente_dummy_genera_su_escrito_por_la_ruta_real(
        usuario_supervisor, app, expediente_seed, elaborar_de_resolucion,
        plantilla_de_demostracion):
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.expedientes import Expediente

    doc_id = None
    try:
        r = usuario_supervisor.get(f'/api/escritos/plantillas?tarea_id={elaborar_de_resolucion}')
        assert r.status_code == 200
        assert plantilla_de_demostracion in [p['id'] for p in r.get_json()['plantillas']]

        r = usuario_supervisor.post('/api/escritos/generar', json={
            'plantilla_id': plantilla_de_demostracion, 'tarea_id': elaborar_de_resolucion})
        assert r.status_code == 200
        generado = r.get_json()
        doc_id = generado.get('doc_id')
        assert generado['resultado'] == 'GENERADO'

        r = usuario_supervisor.get(generado['enlace'])
        assert r.status_code == 200
        with app.app_context():
            expediente = db.session.get(Expediente, expediente_seed)
            numero_at = f'AT-{expediente.numero_at}'
            titular = expediente.titular.nombre_completo
        contenido_xml = zipfile.ZipFile(io.BytesIO(r.data)).read('content.xml').decode('utf-8')
        texto = html.unescape(re.sub(r'<[^>]+>', '', contenido_xml))
        assert numero_at in texto
        assert titular in texto
        assert plantillas_demo.TEXTO_DEL_FRAGMENTO in texto
        assert '{{' not in texto
    finally:
        with app.app_context():
            db.session.rollback()
            if doc_id is not None:
                DocumentoTarea.query.filter_by(documento_id=doc_id).delete()
                Documento.query.filter_by(id=doc_id).delete()
            db.session.commit()
