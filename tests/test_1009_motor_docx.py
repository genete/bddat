"""
#1009 (ADR-050 §J) — el motor .docx inserta el fragmento que la plantilla cita.

Fallo silencioso que evita: el escrito .docx sale sin el pie de recurso o sin los fundamentos de
derecho, porque docxtpl descarta sin avisar el contenido anidado (la razón de ser de los dos
parches del motor) o porque un cambio de dependencia o de firma lo deja pasar vacío, y nadie lo
nota hasta que se notifica. El motor es el plan ante desastre si los puestos de la Junta pierden
LibreOffice (ADR-050 §J, enmienda del 2026-11-02) y no tenía ningún test que lo ejecutara.
"""
import io

import pytest

from app.services.generador_escritos_docx import generar_escrito_docx


def _docx(texto: str) -> bytes:
    """.docx mínimo, con python-docx, con un único párrafo."""
    from docx import Document
    documento = Document()
    documento.add_paragraph(texto)
    salida = io.BytesIO()
    documento.save(salida)
    return salida.getvalue()


def _texto(datos: bytes) -> str:
    from docx import Document
    return '\n'.join(p.text for p in Document(io.BytesIO(datos)).paragraphs)


def test_el_fragmento_citado_llega_al_escrito():
    plantilla = _docx('Antes {{r Pie }} después')
    pie = _docx('TEXTO DEL PIE DE RECURSO')

    generado = generar_escrito_docx(plantilla, {}, fragmento=lambda nombre: pie)

    assert 'TEXTO DEL PIE DE RECURSO' in _texto(generado)


def test_un_fragmento_que_falta_detiene_la_generacion():
    plantilla = _docx('Antes {{r Pie }} después')

    with pytest.raises(LookupError, match='Pie'):
        generar_escrito_docx(plantilla, {})
