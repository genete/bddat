"""
Tests #730 — regenerar el escrito de una tarea ELABORAR reutiliza el borrador
anterior en vez de crear un documento nuevo cada vez.

Tras ADR-050 (#1007) hay dos casos —sin borrador, el escrito se sube y se
vincula; con borrador, el mismo contenido no hace nada y el distinto sustituye el
contenido del mismo documento— y un solo test. Lo que puede fallar sin ruido es
la identidad del borrador: que regenerar cree una segunda fila o pise otro
documento de la tarea. Las colisiones de nombre, los renombrados y el apartado
de ficheros eran del modelo de carpetas y salieron con él; las guardas nuevas
(formato, almacén caído, tarea que no es ELABORAR) están en el código y no llevan
test (REGLAS_DESARROLLO, «Guardas»).
"""
import io
import zipfile
from types import SimpleNamespace

from app import db
from app.models.documentos_tarea import DocumentoTarea
from app.models.tipos_documentos import TipoDocumento
from app.models.usuarios import Usuario
from app.services.almacenamiento.contenido import leer
from app.services.regeneracion_escritos import (
    GENERADO, SIN_CAMBIOS, SUSTITUIDO, regenerar_escrito,
)
from tests.conftest import ArbolESFTT, documento_con_contenido_de_prueba


def _odt(texto: str) -> bytes:
    """.odt mínimo (zip con `mimetype` primero) con el texto dado: el formato lo admite `subir`."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text')
        z.writestr('content.xml', f'<root><p>{texto}</p></root>')
    return buffer.getvalue()


def _tipo(codigo: str) -> int:
    tipo = TipoDocumento.query.filter_by(codigo=codigo).first()
    assert tipo is not None, f'la semilla debe traer el tipo de documento {codigo}'
    return tipo.id


def test_regenerar_reutiliza_el_borrador_no_crea_otro(app_ctx, fs_tmp):
    """Fallo silencioso que evita: que regenerar cree una segunda fila (la tarea quedaría con dos
    borradores y el anterior vinculado con contenido desactualizado) o pise otro documento consumido
    de la tarea, sin que nada lo avise."""
    from app.services.reloj_simulado import hoy

    tarea = ArbolESFTT(db).tarea_propia('ELABORAR')
    expediente = tarea.tramite.fase.solicitud.expediente
    tipo_escrito = _tipo('OTROS')
    plantilla = SimpleNamespace(tipo_documento_id=tipo_escrito)
    usuario_id = Usuario.query.first().id

    # Otro consumido de la tarea, también .odt pero de otro tipo: no es el borrador.
    ajeno_bytes = _odt('Otro documento, de otro tipo')
    ajeno = documento_con_contenido_de_prueba(
        'otro_consumido.odt', ajeno_bytes, expediente_id=expediente.id,
        tipo_doc_id=_tipo('BORRADOR_FIRMA'), asunto='ajeno', fecha_administrativa=hoy())
    tarea.vinculos_documento.append(DocumentoTarea(documento_id=ajeno.id, rol='CONSUMIDO'))
    db.session.flush()

    def regenerar(contenido):
        res = regenerar_escrito(
            tarea=tarea, expediente=expediente, plantilla=plantilla, doc_bytes=contenido,
            nombre_fichero='escrito_730.odt', asunto='Plantilla de prueba #730', usuario_id=usuario_id)
        db.session.flush()
        return res

    def borradores():
        return [v for v in tarea.vinculos_documento
                if v.rol == 'CONSUMIDO' and v.documento.tipo_doc_id == tipo_escrito]

    # Sin borrador: se sube y se vincula, y no toca el ajeno.
    v1 = _odt('version 1')
    primera = regenerar(v1)
    doc = primera.documento
    assert primera.resultado == GENERADO
    assert doc.id != ajeno.id
    assert leer(doc).datos == v1
    assert [v.documento_id for v in borradores()] == [doc.id]

    # Mismo contenido: nada.
    igual = regenerar(v1)
    assert igual.resultado == SIN_CAMBIOS and igual.documento.id == doc.id

    # Contenido distinto: se sustituye en el mismo documento, sin segunda fila.
    v2 = _odt('version 2, cambio real')
    nueva = regenerar(v2)
    assert nueva.resultado == SUSTITUIDO and nueva.documento.id == doc.id
    assert leer(doc).datos == v2
    assert [v.documento_id for v in borradores()] == [doc.id]

    # El otro consumido sigue intacto.
    assert leer(ajeno).datos == ajeno_bytes
