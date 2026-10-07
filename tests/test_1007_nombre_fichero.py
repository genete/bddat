"""#1007 (ADR-050 §C) — `documentos.nombre_fichero`: el nombre que se enseña.

Fallo silencioso que evita: el nombre original de un fichero (el que le puso quien lo
subió) se pierde sin error, porque el almacén guarda el contenido por su hash, sin nombre.
"""


def _documento_ingerido(alta_propia, nombre_original):
    """Un documento entrado al pool por la vía real, con su fecha y su tipo."""
    import io

    from app import db
    from app.models.tipos_documentos import TipoDocumento
    from app.services.ingesta_pool import FicheroAIngestar, ingestar_en_pool
    from app.services.reloj_simulado import hoy

    tipo = TipoDocumento.query.filter_by(codigo='MODELO_SOLICITUD').first()
    assert tipo is not None, "la semilla debe traer el TipoDocumento 'MODELO_SOLICITUD'"
    [documento] = ingestar_en_pool(alta_propia.expediente, [FicheroAIngestar(
        io.BytesIO(b'%PDF-1.4 contenido de prueba'), nombre_original,
        tipo_doc_id=tipo.id, fecha_administrativa=hoy())])
    db.session.add(documento)
    db.session.flush()
    return documento


class TestIngesta:

    def test_guarda_el_original_saneado(self, alta_propia):
        """El `?` y el salto de línea no valen en un nombre de fichero de Windows."""
        doc = _documento_ingerido(alta_propia, 'Informe técnico?\n2026.pdf')

        assert doc.nombre_fichero == 'Informe técnico__2026.pdf'
        assert doc.nombre_visible() == 'Informe técnico__2026.pdf'
