"""
Tests para #182 — código de trazabilidad embebido (composición y extracción).

Lógica pura, sin ODF ni PDF de por medio: eso ya lo prueba
`test_726_renderizador_odt.py` (el gancho de inyección) y
`test_732_fixture_real.py` (supervivencia al pipeline .odt → PDF real). La
clase `TestCicloCompletoConFixtureReal` de aquí abajo es la excepción: cierra
el círculo que R10 investigó (componer → inyectar → PDF real → extraer) con
el algoritmo definitivo, no con un string de prueba arbitrario.
"""
import os
import subprocess

import pytest

from app.services.codigo_seguimiento import componer_codigo, extraer_tarea_id
from app.services.generador_escritos_odt import generar_escrito_odt

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
RUTA_PLANTILLA = os.path.join(FIXTURES_DIR, 'plantilla_732.odt')

SOFFICE = os.environ.get(
    'SOFFICE', r'C:\Program Files\LibreOffice\program\soffice.com')


class TestComponerCodigo:
    def test_formato_bddat_id_letra(self):
        assert componer_codigo(4711) == 'BDDAT-4711-L'

    def test_es_ascii_puro(self):
        codigo = componer_codigo(123456)
        assert codigo.isascii()


class TestExtraerTareaId:
    def test_roundtrip(self):
        for tarea_id in (1, 23, 24, 4711, 999999):
            assert extraer_tarea_id(componer_codigo(tarea_id)) == tarea_id

    def test_codigo_dentro_de_texto_alrededor(self):
        codigo = componer_codigo(4711)
        texto = f'Cabecera\n{codigo}\nPie de página con más texto.'
        assert extraer_tarea_id(texto) == 4711

    def test_ausente_devuelve_none(self):
        assert extraer_tarea_id('Un documento cualquiera sin código.') is None

    def test_texto_vacio_o_none(self):
        assert extraer_tarea_id('') is None
        assert extraer_tarea_id(None) is None

    def test_letra_de_control_alterada_se_rechaza(self):
        """El escenario real del issue: alteración accidental que produce una
        asociación falsa de buena fe. Se detecta y se trata como ausente."""
        codigo_valido = componer_codigo(4711)
        letra_equivocada = 'X' if codigo_valido[-1] != 'X' else 'Y'
        codigo_alterado = codigo_valido[:-1] + letra_equivocada

        assert extraer_tarea_id(codigo_alterado) is None

    def test_id_alterado_sin_recalcular_letra_se_rechaza(self):
        """Cambiar el id (p. ej. edición manual) sin tocar la letra tampoco
        debe colar como código de OTRA tarea válida."""
        codigo = componer_codigo(4711)
        codigo_con_otro_id = codigo.replace('4711', '4712')

        assert extraer_tarea_id(codigo_con_otro_id) is None


# ----------------------------------------------------------------------
# Ciclo completo con el fixture real de #732: componer → inyectar → PDF real
# vía soffice → extraer. Cierra R10 con el algoritmo definitivo.
# ----------------------------------------------------------------------

@pytest.mark.skipif(not os.path.isfile(SOFFICE),
                    reason=f'LibreOffice no encontrado en {SOFFICE}')
class TestCicloCompletoConFixtureReal:
    def test_el_tarea_id_se_recupera_tras_el_pdf_real(self, tmp_path):
        pypdf = pytest.importorskip('pypdf')

        tarea_id = 4711
        codigo = componer_codigo(tarea_id)
        contexto = {
            'numero_at': 'AT-1234',
            'organo': 'Delegación Territorial de Cádiz',
            'sede': {'direccion': 'Plaza de España, 19, Cádiz'},
            'titular': 'Pérez & Hijos S.L.',
            'municipios': ['Cádiz', 'Jerez', 'Rota'],
        }

        datos = generar_escrito_odt(
            RUTA_PLANTILLA, contexto,
            codigo_seguimiento=codigo, fragmentos_dir=FIXTURES_DIR)

        odt_generado = tmp_path / 'salida_182.odt'
        odt_generado.write_bytes(datos)

        perfil = 'file:///' + str(tmp_path / 'perfil').replace('\\', '/')
        r = subprocess.run(
            [SOFFICE, f'-env:UserInstallation={perfil}', '--headless',
             '--norestore', '--convert-to', 'pdf', '--outdir', str(tmp_path),
             str(odt_generado)],
            capture_output=True, timeout=300, text=True)
        assert r.returncode == 0, f'soffice no convirtió a PDF: {r.stderr[:500]}'

        pdf = pypdf.PdfReader(str(tmp_path / 'salida_182.pdf'))
        texto = '\n'.join(p.extract_text() or '' for p in pdf.pages)

        assert extraer_tarea_id(texto) == tarea_id, (
            'El código compuesto por componer_codigo() no se recupera con '
            'extraer_tarea_id() tras el circuito .odt → PDF real')
