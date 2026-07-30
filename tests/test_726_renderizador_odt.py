"""
Tests para #726 — motor de render de plantillas .odt (ADR-035).

Los ODT de prueba se fabrican aquí con zipfile: un .odt es un ZIP con XML
dentro, y montar el mínimo imprescindible sale más barato y más estable que
depender de ficheros binarios en el repositorio.

No hay app de Flask ni base de datos en juego: el motor recibe el contexto ya
construido (ADR-035 §6).
"""
import re
import zipfile
from unittest.mock import MagicMock

import pytest

from app.services.generador_escritos import (
    TIPOS_CONTENIDO,
    componer_nombre_documento,
    tipo_contenido_documento,
    validar_plantilla,
)
from app.services.generador_escritos_odt import generar_escrito_odt

# ----------------------------------------------------------------------
# Fabricación de ODT mínimos
# ----------------------------------------------------------------------

NS_DECL = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
    'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
    'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"'
)

CONTENT = (
    f'<?xml version="1.0" encoding="UTF-8"?>'
    f'<office:document-content {NS_DECL}>'
    f'<office:automatic-styles>{{estilos}}</office:automatic-styles>'
    f'<office:body><office:text>{{cuerpo}}</office:text></office:body>'
    f'</office:document-content>'
)

STYLES = (
    f'<?xml version="1.0" encoding="UTF-8"?>'
    f'<office:document-styles {NS_DECL}>'
    f'<office:automatic-styles/>'
    f'<office:master-styles>{{masters}}</office:master-styles>'
    f'</office:document-styles>'
)

# Dos master pages con pie: es el caso que ADR-035 §3 señala como trampa
# (primera página distinta), y donde la prueba de concepto perdía el código.
MASTERS_DOS = (
    '<style:master-page style:name="Standard">'
    '<style:footer><text:p>pie normal</text:p></style:footer>'
    '</style:master-page>'
    '<style:master-page style:name="First_20_Page">'
    '<style:footer><text:p>pie primera</text:p></style:footer>'
    '</style:master-page>'
)


def _odt(tmp_path, nombre, cuerpo, estilos='', masters=MASTERS_DOS):
    """Escribe un .odt mínimo y devuelve su ruta."""
    ruta = tmp_path / nombre
    with zipfile.ZipFile(ruta, 'w') as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text',
                   compress_type=zipfile.ZIP_STORED)
        z.writestr('content.xml', CONTENT.format(cuerpo=cuerpo, estilos=estilos))
        z.writestr('styles.xml', STYLES.format(masters=masters))
    return str(ruta)


def _partes(datos: bytes) -> dict:
    """Descomprime el resultado y devuelve {nombre: texto}."""
    import io
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        return {n: z.read(n).decode('utf-8') for n in z.namelist()
                if n.endswith('.xml')}


# ----------------------------------------------------------------------
# Tokens
# ----------------------------------------------------------------------

class TestTokens:
    def test_sustituye_tokens_en_cuerpo_y_en_estilos(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt',
                    cuerpo='<text:p>Expediente {{ numero_at }}</text:p>',
                    masters=(
                        '<style:master-page style:name="Standard">'
                        '<style:footer><text:p>{{ organo }}</text:p></style:footer>'
                        '</style:master-page>'
                    ))

        partes = _partes(generar_escrito_odt(
            ruta, {'numero_at': 'AT-1234', 'organo': 'Delegación Territorial'},
            fragmentos_dir=str(tmp_path)))

        assert 'Expediente AT-1234' in partes['content.xml']
        assert 'Delegación Territorial' in partes['styles.xml']

    def test_resuelve_acceso_anidado(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt',
                    cuerpo='<text:p>{{ sede.direccion }}</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {'sede': {'direccion': 'Plaza de España, 19'}},
            fragmentos_dir=str(tmp_path)))

        assert 'Plaza de España, 19' in partes['content.xml']

    def test_token_sin_dato_queda_vacio_y_no_rompe(self, tmp_path):
        """Paridad con el motor .docx: un token no definido se renderiza vacío.

        Importa porque los tokens institucionales (sede, órgano) no existen
        hasta #728 y las plantillas ya los llevan.
        """
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>[{{ inexistente }}]</text:p>')

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        assert '[]' in partes['content.xml']

    def test_escapa_los_valores_con_caracteres_xml(self, tmp_path):
        """Un & o un < en el dato no puede romper el XML del documento."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>{{ titular }}</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {'titular': 'Pérez & Hijos <S.L.>'}, fragmentos_dir=str(tmp_path)))

        assert 'Pérez &amp; Hijos &lt;S.L.&gt;' in partes['content.xml']


class TestTokensPartidos:
    def test_recompone_token_repartido_en_varios_spans(self, tmp_path):
        """Writer parte el token si alguien le cambia el formato a media palabra."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo=(
            '<text:p>{{ nu<text:span text:style-name="T1">mero_</text:span>at }}</text:p>'
        ))

        partes = _partes(generar_escrito_odt(
            ruta, {'numero_at': 'AT-1234'}, fragmentos_dir=str(tmp_path)))

        assert 'AT-1234' in partes['content.xml']

    def test_conserva_el_texto_que_rodea_al_token(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt', cuerpo=(
            '<text:p>Antes {{ nu<text:span>mero_at }} después</text:span></text:p>'
        ))

        partes = _partes(generar_escrito_odt(
            ruta, {'numero_at': 'AT-1234'}, fragmentos_dir=str(tmp_path)))

        assert 'Antes AT-1234 después' in re.sub(r'<[^>]+>', '', partes['content.xml'])

    def test_no_toca_un_parrafo_sin_tokens(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt', cuerpo=(
            '<text:p>Texto <text:span text:style-name="T1">con formato</text:span> mixto</text:p>'
        ))

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        assert '<text:span text:style-name="T1">con formato</text:span>' in partes['content.xml']


# ----------------------------------------------------------------------
# Fragmentos
# ----------------------------------------------------------------------

class TestFragmentos:
    def _con_fragmento(self, tmp_path, cuerpo_fragmento, estilos=''):
        _odt(tmp_path, 'Fundamentos.odt', cuerpo=cuerpo_fragmento, estilos=estilos)
        return _odt(tmp_path, 'plantilla.odt',
                    cuerpo='<text:p>{{r Fundamentos }}</text:p>'
                           '<text:p>final</text:p>')

    def test_sustituye_el_parrafo_del_marcador_por_los_bloques(self, tmp_path):
        ruta = self._con_fragmento(
            tmp_path, '<text:p>Primero.</text:p><text:p>Segundo.</text:p>')

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        content = partes['content.xml']
        assert 'Primero.' in content and 'Segundo.' in content
        # El marcador no deja rastro y los bloques quedan a nivel de bloque,
        # no anidados dentro de un párrafo contenedor.
        assert '{{r' not in content
        assert '<text:p>Primero.</text:p><text:p>Segundo.</text:p>' in content

    def test_rellena_los_tokens_que_trae_el_fragmento(self, tmp_path):
        """Lo que docxtpl no permite: fragmentos ANTES de Jinja2."""
        ruta = self._con_fragmento(tmp_path, '<text:p>Exp. {{ numero_at }}</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {'numero_at': 'AT-1234'}, fragmentos_dir=str(tmp_path)))

        assert 'Exp. AT-1234' in partes['content.xml']

    def test_renombra_los_estilos_automaticos_del_fragmento(self, tmp_path):
        """LibreOffice llama P1 a un estilo automático en todos los documentos."""
        ruta = self._con_fragmento(
            tmp_path,
            '<text:p text:style-name="P1">Con estilo propio</text:p>',
            estilos='<style:style style:name="P1" style:family="paragraph"/>')

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        content = partes['content.xml']
        assert 'style:name="frgFundamentos_P1"' in content
        assert 'text:style-name="frgFundamentos_P1"' in content

    def test_fragmento_ausente_no_rompe_y_no_deja_el_marcador(self, tmp_path):
        ruta = _odt(tmp_path, 'plantilla.odt',
                    cuerpo='<text:p>{{r NoExiste }}</text:p><text:p>final</text:p>')

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        assert '{{r' not in partes['content.xml']
        assert 'final' in partes['content.xml']


# ----------------------------------------------------------------------
# Bucles de fila
# ----------------------------------------------------------------------

class TestBuclesDeFila:
    TABLA = (
        '<table:table>'
        '<table:table-row><table:table-cell>'
        '<text:p>{%tr for m in municipios %}{{ m }}</text:p>'
        '</table:table-cell></table:table-row>'
        '<table:table-row><table:table-cell>'
        '<text:p>{%tr endfor %}</text:p>'
        '</table:table-cell></table:table-row>'
        '</table:table>'
    )

    def test_repite_la_fila_por_cada_elemento(self, tmp_path):
        """Convención de docxtpl: la etiqueta va delante de su fila, así que se
        repite la fila del `for` y la del `endfor` queda fuera del bucle."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo=self.TABLA)

        partes = _partes(generar_escrito_odt(
            ruta, {'municipios': ['Cádiz', 'Jerez', 'Rota']},
            fragmentos_dir=str(tmp_path)))

        content = partes['content.xml']
        assert content.count('<table:table-row>') == 4   # 3 repetidas + la del endfor
        for municipio in ('Cádiz', 'Jerez', 'Rota'):
            assert municipio in content
        assert '{%tr' not in content

    def test_lista_vacia_deja_la_tabla_sin_filas_de_datos(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt', cuerpo=self.TABLA)

        partes = _partes(generar_escrito_odt(
            ruta, {'municipios': []}, fragmentos_dir=str(tmp_path)))

        assert partes['content.xml'].count('<table:table-row>') == 1


# ----------------------------------------------------------------------
# Código de seguimiento — gancho de #182
# ----------------------------------------------------------------------

class TestCodigoSeguimiento:
    def test_inyecta_en_todas_las_master_pages(self, tmp_path):
        """ADR-035 §3: con primera página distinta hay más de una master page.

        Inyectar en la primera que aparece deja la página 1 sin código, que es
        exactamente lo que le pasó a la prueba de concepto.
        """
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>cuerpo</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {}, codigo_seguimiento='BDDAT|AT-1234|T99',
            fragmentos_dir=str(tmp_path)))

        styles = partes['styles.xml']
        assert styles.count('CodigoSeguimientoBDDAT') == 2
        assert styles.count('BDDAT|AT-1234|T99') == 2

    def test_crea_el_pie_si_la_master_page_no_lo_tiene(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>cuerpo</text:p>',
                    masters='<style:master-page style:name="Standard"/>')

        partes = _partes(generar_escrito_odt(
            ruta, {}, codigo_seguimiento='X-1', fragmentos_dir=str(tmp_path)))

        assert 'CodigoSeguimientoBDDAT' in partes['styles.xml']

    def test_sin_codigo_no_inserta_nada(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>cuerpo</text:p>')

        partes = _partes(generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path)))

        assert 'CodigoSeguimientoBDDAT' not in partes['styles.xml']

    def test_el_codigo_no_se_interpreta_como_plantilla(self, tmp_path):
        """Se inyecta después de Jinja2: un código con llaves es dato, no código."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>cuerpo</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {}, codigo_seguimiento='{{ no_soy_token }}',
            fragmentos_dir=str(tmp_path)))

        assert partes['styles.xml'].count('{{ no_soy_token }}') == 2

    def test_el_marco_declara_la_proteccion_que_sobrevive(self, tmp_path):
        """ADR-035: style:protect es lo único que aguanta abrir y guardar."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>cuerpo</text:p>')

        partes = _partes(generar_escrito_odt(
            ruta, {}, codigo_seguimiento='X-1', fragmentos_dir=str(tmp_path)))

        assert 'style:protect="content position size"' in partes['styles.xml']


# ----------------------------------------------------------------------
# Empaquetado
# ----------------------------------------------------------------------

class TestEmpaquetado:
    def test_mimetype_va_primero_y_sin_comprimir(self, tmp_path):
        """Lo exige ODF: es como se reconoce el formato sin descomprimir."""
        import io
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>x</text:p>')

        datos = generar_escrito_odt(ruta, {}, fragmentos_dir=str(tmp_path))

        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            primero = z.infolist()[0]
            assert primero.filename == 'mimetype'
            assert primero.compress_type == zipfile.ZIP_STORED
            assert z.read('mimetype') == b'application/vnd.oasis.opendocument.text'

    def test_conserva_las_partes_que_no_toca(self, tmp_path):
        import io
        ruta = tmp_path / 'p.odt'
        with zipfile.ZipFile(ruta, 'w') as z:
            z.writestr('mimetype', 'application/vnd.oasis.opendocument.text',
                       compress_type=zipfile.ZIP_STORED)
            z.writestr('content.xml', CONTENT.format(cuerpo='<text:p>x</text:p>',
                                                     estilos=''))
            z.writestr('styles.xml', STYLES.format(masters=MASTERS_DOS))
            z.writestr('Pictures/logo.png', b'\x89PNG-falso')
            z.writestr('meta.xml', '<meta/>')

        datos = generar_escrito_odt(str(ruta), {}, fragmentos_dir=str(tmp_path))

        with zipfile.ZipFile(io.BytesIO(datos)) as z:
            assert z.read('Pictures/logo.png') == b'\x89PNG-falso'
            assert z.read('meta.xml') == b'<meta/>'


# ----------------------------------------------------------------------
# Elección de motor por extensión (ADR-035 §2)
# ----------------------------------------------------------------------

class TestEleccionDeMotor:
    def _plantilla(self, ruta_plantilla, variante=None):
        p = MagicMock()
        p.ruta_plantilla = ruta_plantilla
        p.variante = variante
        return p

    def test_nombre_hereda_la_extension_de_la_plantilla(self):
        tarea = MagicMock()
        tarea.tipo_tarea.nombre_en_plantilla = 'RESOLUCION'
        tarea.tramite = None

        nombre_odt = componer_nombre_documento(tarea, self._plantilla('escritos/r.odt'))
        nombre_docx = componer_nombre_documento(tarea, self._plantilla('escritos/r.docx'))

        assert nombre_odt.endswith('.odt')
        assert nombre_docx.endswith('.docx')

    def test_tipo_contenido_por_extension(self):
        assert tipo_contenido_documento('escrito.odt') == TIPOS_CONTENIDO['.odt']
        assert tipo_contenido_documento('escrito.docx') == TIPOS_CONTENIDO['.docx']
        assert tipo_contenido_documento('escrito.xyz') == 'application/octet-stream'

    def test_validacion_acepta_un_odt_correcto(self, tmp_path):
        ruta = _odt(tmp_path, 'p.odt',
                    cuerpo='<text:p>{{ numero_at }}</text:p>')

        assert validar_plantilla(ruta) is None

    def test_validacion_admite_los_marcadores_de_fragmento(self, tmp_path):
        """{{r Nombre }} no es Jinja2: lo resuelve el motor antes de compilar."""
        ruta = _odt(tmp_path, 'p.odt', cuerpo='<text:p>{{r Fundamentos }}</text:p>')

        assert validar_plantilla(ruta) is None

    def test_validacion_detecta_un_bucle_sin_cerrar(self, tmp_path):
        """Es lo que se le escapa al supervisor y no se ve hasta generar."""
        ruta = _odt(tmp_path, 'p.odt',
                    cuerpo='<text:p>{% for m in municipios %}{{ m }}</text:p>')

        error = validar_plantilla(ruta)

        assert error and 'endfor' in error.lower()

    def test_validacion_rechaza_lo_que_no_es_un_odt(self, tmp_path):
        ruta = tmp_path / 'falso.odt'
        ruta.write_text('esto no es un ZIP')

        assert 'no es un .odt' in validar_plantilla(str(ruta))

    def test_validacion_rechaza_una_extension_sin_motor(self, tmp_path):
        ruta = tmp_path / 'plantilla.rtf'
        ruta.write_text('x')

        assert 'no soportado' in validar_plantilla(str(ruta))

    def test_extension_sin_motor_da_error_explicito(self, tmp_path, monkeypatch):
        from app.services import generador_escritos

        ruta = tmp_path / 'plantilla.rtf'
        ruta.write_text('x')
        monkeypatch.setattr(generador_escritos, '_ruta_plantilla', lambda r: str(ruta))
        monkeypatch.setattr(generador_escritos, 'construir_contexto',
                            lambda *a, **k: {})

        with pytest.raises(ValueError, match='No hay motor'):
            generador_escritos.generar_escrito(
                self._plantilla('plantilla.rtf'), MagicMock(), MagicMock())
