"""
Tests para #732 — el motor ODT contra un fichero real de LibreOffice.

Los 31 tests de `test_726_renderizador_odt.py` fabrican sus .odt con zipfile:
fijan bien la lógica del motor, pero el XML lo escribe el propio test, así
que ninguno mira un fichero que haya pasado de verdad por LibreOffice. Este
módulo cierra ese punto ciego contra `tests/fixtures/plantilla_732.odt` y
`tests/fixtures/Fundamentos732.odt`, fabricados por
`scripts/fabricar_fixture_odt_732.py` a partir de la plantilla base canónica
de #727 (carta_base.odt) con un pase final por LibreOffice real — es el que
se pondría rojo si Writer cambiase su forma de envolver el contenido.

`_generador()` lee el `meta:generator` del fixture y lo añade a cada mensaje
de fallo: si algún día una versión nueva de LibreOffice rompe algo aquí, ese
dato ahorra la mitad del diagnóstico.
"""
import io
import os
import subprocess
import zipfile

import pytest
from lxml import etree

from app.services.generador_escritos_odt import generar_escrito_odt
from app.services.plantilla_canonica_odt import comprobar_canonicidad

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
RUTA_PLANTILLA = os.path.join(FIXTURES_DIR, 'plantilla_732.odt')
RUTA_FRAGMENTO = os.path.join(FIXTURES_DIR, 'Fundamentos732.odt')

CONTEXTO = {
    'numero_at': 'AT-1234',
    'organo': 'Delegación Territorial de Cádiz',
    'sede': {'direccion': 'Plaza de España, 19, Cádiz'},
    'titular': 'Pérez & Hijos S.L.',
    'municipios': ['Cádiz', 'Jerez', 'Rota'],
}
CODIGO_SEGUIMIENTO = 'BDDAT|AT-1234|T99'

Q_META = '{urn:oasis:names:tc:opendocument:xmlns:meta:1.0}'
Q_OFFICE = '{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')


def _generador(ruta: str) -> str:
    """`meta:generator` del .odt, para incluirlo en mensajes de fallo."""
    with zipfile.ZipFile(ruta) as z:
        meta = etree.fromstring(z.read('meta.xml'))
    gen = meta.find(f'{Q_OFFICE}meta/{Q_META}generator')
    return gen.text if gen is not None else '(sin meta:generator)'


def _partes(datos: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        return {n: z.read(n).decode('utf-8') for n in z.namelist()
                if n.endswith('.xml')}


@pytest.fixture(scope='module')
def generador():
    return _generador(RUTA_PLANTILLA)


@pytest.fixture(scope='module')
def renderizado():
    """Render único del fixture, reutilizado por todos los tests del módulo."""
    datos = generar_escrito_odt(
        RUTA_PLANTILLA, CONTEXTO,
        codigo_seguimiento=CODIGO_SEGUIMIENTO, fragmentos_dir=FIXTURES_DIR)
    return _partes(datos)


# ----------------------------------------------------------------------
# El fixture es lo que dice ser
# ----------------------------------------------------------------------

class TestFixtureEsRealDeLibreOffice:
    def test_meta_generator_dice_libreoffice(self, generador):
        assert 'LibreOffice' in generador, (
            f'plantilla_732.odt no lleva meta:generator de LibreOffice '
            f'(leído: "{generador}") — no es el fichero real que #732 exige.')

    def test_pasa_la_canonicidad_de_727(self, generador):
        avisos = comprobar_canonicidad(RUTA_PLANTILLA)
        assert avisos == [], (
            f'plantilla_732.odt no pasa la canonicidad de #727: {avisos} '
            f'(generado con {generador})')


# ----------------------------------------------------------------------
# Token en el cuerpo
# ----------------------------------------------------------------------

class TestTokenEnCuerpo:
    def test_sustituye_el_token_del_cuerpo(self, renderizado, generador):
        assert 'Expediente AT-1234.' in renderizado['content.xml'], (
            f'El token del cuerpo no se sustituyó (fixture generado con {generador})')


# ----------------------------------------------------------------------
# Tokens en cabecera y pie — LAS DOS master pages (ADR-035 §3)
# ----------------------------------------------------------------------

class TestTokensEnCabeceraYPie:
    def test_token_de_cabecera_en_ambas_master_pages(self, renderizado, generador):
        """MP0 (páginas siguientes) y MPF0 (primera página) llevan cabecera
        propia; el token debe llegar a las dos."""
        styles = renderizado['styles.xml']
        assert styles.count('Delegación Territorial de Cádiz') == 2, (
            'El token de cabecera no llegó a las dos master pages '
            f'(generado con {generador})')

    def test_token_de_pie_en_ambas_master_pages(self, renderizado, generador):
        """MPF0 ya traía pie; MP0 no lo tenía y se le creó uno en el fixture
        (ADR-035 §3: es justo el caso donde la prueba de concepto perdía
        contenido en la página 1 si solo se miraba una master page)."""
        styles = renderizado['styles.xml']
        assert styles.count('Plaza de España, 19, Cádiz') == 2, (
            'El token de pie no llegó a las dos master pages '
            f'(generado con {generador})')

    def test_codigo_de_seguimiento_en_ambas_master_pages_con_pie(self, renderizado, generador):
        styles = renderizado['styles.xml']
        assert styles.count('CodigoSeguimientoBDDAT') >= 2, (
            'El código de seguimiento no se inyectó en las master pages con pie '
            f'(generado con {generador})')
        assert styles.count(CODIGO_SEGUIMIENTO) >= 2


# ----------------------------------------------------------------------
# Fragmento real
# ----------------------------------------------------------------------

class TestFragmentoReal:
    def test_el_fragmento_se_inserta(self, renderizado, generador):
        content = renderizado['content.xml']
        assert 'Fundamentos de Derecho de la resolución.' in content, (
            f'El fragmento real no se insertó (generado con {generador})')
        assert '{{r' not in content

    def test_el_token_del_fragmento_se_rellena_antes_de_jinja2(self, renderizado, generador):
        """Lo que docxtpl no permite (ADR-035): un fragmento puede traer
        tokens propios y se rellenan."""
        assert 'Alegado por Pérez &amp; Hijos S.L.' in renderizado['content.xml'], (
            f'El token propio del fragmento no se rellenó (generado con {generador})')


# ----------------------------------------------------------------------
# Bucles — tabla y párrafo
# ----------------------------------------------------------------------

class TestBucles:
    def test_bucle_de_fila_repite_los_municipios(self, renderizado, generador):
        content = renderizado['content.xml']
        for municipio in ('Cádiz', 'Jerez', 'Rota'):
            assert municipio in content, (
                f'"{municipio}" no aparece tras el bucle de fila '
                f'(generado con {generador})')
        assert '{%tr' not in content

    def test_bucle_de_parrafo_repite_los_municipios(self, renderizado, generador):
        content = renderizado['content.xml']
        assert 'for m in municipios' not in content, (
            f'La etiqueta {{%p ... %}} deja texto suelto en el documento '
            f'(generado con {generador})')
        assert '{%p' not in content


# ----------------------------------------------------------------------
# Integración con soffice: el .odt generado convertido a PDF real
# ----------------------------------------------------------------------

@pytest.mark.skipif(not os.path.isfile(SOFFICE),
                    reason=f'LibreOffice no encontrado en {SOFFICE}')
class TestIntegracionPdf:
    def test_texto_y_codigo_sobreviven_al_pdf(self, tmp_path, generador):
        pypdf = pytest.importorskip('pypdf')

        datos = generar_escrito_odt(
            RUTA_PLANTILLA, CONTEXTO,
            codigo_seguimiento=CODIGO_SEGUIMIENTO, fragmentos_dir=FIXTURES_DIR)

        odt_generado = tmp_path / 'salida_732.odt'
        odt_generado.write_bytes(datos)

        perfil = 'file:///' + str(tmp_path / 'perfil').replace('\\', '/')
        r = subprocess.run(
            [SOFFICE, f'-env:UserInstallation={perfil}', '--headless',
             '--norestore', '--convert-to', 'pdf', '--outdir', str(tmp_path),
             str(odt_generado)],
            capture_output=True, timeout=300, text=True)
        assert r.returncode == 0, (
            f'soffice no convirtió a PDF: {r.stderr[:500]} '
            f'(fixture generado con {generador})')

        pdf = pypdf.PdfReader(str(tmp_path / 'salida_732.pdf'))
        texto = '\n'.join(p.extract_text() or '' for p in pdf.pages)

        assert 'AT-1234' in texto, (
            f'El número de expediente no llega al texto extraíble del PDF '
            f'(fixture generado con {generador})')
        assert 'Cádiz' in texto, (
            'Los acentos del texto extraíble salen rotos (ADR-035 §5: '
            f'defecto de la fuente Cambria) (fixture generado con {generador})')
        assert CODIGO_SEGUIMIENTO in texto, (
            'El código de seguimiento no sobrevive al pipeline .odt → PDF '
            f'(fixture generado con {generador})')
