"""
Tests para #727 — canonicidad de plantillas .odt (ADR-035 §5).

Los ODT de prueba se fabrican con zipfile, igual que en test_726: montar el
mínimo imprescindible es más barato y estable que depender de ficheros
binarios. Las tres plantillas base reales (carta, resolución, fragmento) se
comprueban aparte, contra disco: son el contrato que este módulo protege.
"""
import os
import zipfile

from app.services.generador_escritos import advertencias_plantilla
from app.services.plantilla_canonica_odt import (
    ESTILOS_CARTA,
    ESTILOS_COMUNES,
    ESTILOS_RESOLUCION,
    comprobar_canonicidad,
    leer_marca,
)

NS_DECL = (
    'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
    'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
    'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
    'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"'
)

CONTENT = (
    f'<?xml version="1.0" encoding="UTF-8"?>'
    f'<office:document-content {NS_DECL}>'
    f'<office:automatic-styles/>'
    f'<office:body><office:text><text:p>Hola</text:p></office:text></office:body>'
    f'</office:document-content>'
)


def _styles(fuente_default='Source Sans Pro', estilos_extra=''):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<office:document-styles {NS_DECL}>'
        f'<office:styles>'
        f'<style:default-style style:family="paragraph">'
        f'<style:text-properties style:font-name="{fuente_default}"/>'
        f'</style:default-style>'
        f'{estilos_extra}'
        f'</office:styles>'
        f'<office:automatic-styles/>'
        f'<office:master-styles/>'
        f'</office:document-styles>'
    )


def _meta(marca=None):
    ud = ''
    if marca:
        for clave, valor in marca.items():
            ud += (f'<meta:user-defined meta:name="BDDAT:{clave}">'
                   f'{valor}</meta:user-defined>')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-meta '
        'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0">'
        f'<office:meta>{ud}</office:meta>'
        '</office:document-meta>'
    )


def _estilo_parrafo(nombre_interno, display_name, fuente=None):
    props = f'<style:text-properties style:font-name="{fuente}"/>' if fuente else ''
    return (f'<style:style style:name="{nombre_interno}" '
            f'style:display-name="{display_name}" style:family="paragraph">'
            f'{props}</style:style>')


def _odt(tmp_path, nombre, fuente_default='Source Sans Pro', estilos_extra='',
        marca=None):
    ruta = tmp_path / nombre
    with zipfile.ZipFile(ruta, 'w') as z:
        z.writestr('mimetype', 'application/vnd.oasis.opendocument.text',
                   compress_type=zipfile.ZIP_STORED)
        z.writestr('content.xml', CONTENT)
        z.writestr('styles.xml', _styles(fuente_default, estilos_extra))
        z.writestr('meta.xml', _meta(marca))
    return str(ruta)


# ----------------------------------------------------------------------
# leer_marca
# ----------------------------------------------------------------------

class TestLeerMarca:
    def test_sin_meta_xml_devuelve_none(self, tmp_path):
        ruta = tmp_path / 'sin_meta.odt'
        with zipfile.ZipFile(ruta, 'w') as z:
            z.writestr('content.xml', CONTENT)

        assert leer_marca(str(ruta)) is None

    def test_sin_claves_bddat_devuelve_none(self, tmp_path):
        ruta = _odt(tmp_path, 'sin_marca.odt')

        assert leer_marca(ruta) is None

    def test_lee_las_claves_bddat_presentes(self, tmp_path):
        ruta = _odt(tmp_path, 'con_marca.odt',
                    marca={'plantilla-base': 'carta', 'version-hoja-estilos': '1.0'})

        marca = leer_marca(ruta)

        assert marca == {'plantilla-base': 'carta', 'version-hoja-estilos': '1.0'}

    def test_fichero_no_valido_devuelve_none(self, tmp_path):
        ruta = tmp_path / 'roto.odt'
        ruta.write_text('esto no es un ZIP')

        assert leer_marca(str(ruta)) is None


# ----------------------------------------------------------------------
# comprobar_canonicidad — fuentes
# ----------------------------------------------------------------------

class TestAvisosDeFuentes:
    def test_fuente_corporativa_sin_avisos(self, tmp_path):
        ruta = _odt(tmp_path, 'ok.odt', fuente_default='Source Sans Pro')

        assert comprobar_canonicidad(ruta) == []

    def test_cambria_se_menciona_explicitamente(self, tmp_path):
        ruta = _odt(tmp_path, 'cambria.odt', fuente_default='Cambria')

        avisos = comprobar_canonicidad(ruta)

        assert any('Cambria' in a for a in avisos)
        assert any('acentos' in a for a in avisos)

    def test_otra_fuente_no_corporativa_avisa_sin_mencionar_cambria(self, tmp_path):
        """Calibri no rompe los acentos (medido en #727), pero tampoco es la
        fuente corporativa: avisa por identidad, no por el defecto del texto."""
        ruta = _odt(tmp_path, 'calibri.odt', fuente_default='Calibri')

        avisos = comprobar_canonicidad(ruta)

        assert any('Calibri' in a for a in avisos)
        assert not any('Cambria' in a for a in avisos)
        assert not any('acentos' in a for a in avisos)

    def test_estilos_de_vineta_no_cuentan_como_fuente_ajena(self, tmp_path):
        extra = _estilo_parrafo('WW_5f_CharLFO1LVL2', 'WW_CharLFO1LVL2', fuente='Wingdings')
        ruta = _odt(tmp_path, 'vineta.odt', estilos_extra=extra)

        assert comprobar_canonicidad(ruta) == []

    def test_estilo_graphics_no_cuenta_como_fuente_ajena(self, tmp_path):
        extra = _estilo_parrafo('Graphics', 'Graphics', fuente='Courier New')
        ruta = _odt(tmp_path, 'graphics.odt', estilos_extra=extra)

        assert comprobar_canonicidad(ruta) == []


# ----------------------------------------------------------------------
# comprobar_canonicidad — estilos esperados, según la marca
# ----------------------------------------------------------------------

class TestAvisosDeEstilos:
    def test_sin_marca_no_exige_estilos(self, tmp_path):
        """Sin marca no se sabe de qué base deriva: no se adivina, solo se
        comprueban fuentes."""
        ruta = _odt(tmp_path, 'sin_marca.odt')

        assert comprobar_canonicidad(ruta) == []

    def test_marca_carta_exige_sus_estilos_y_avisa_de_los_que_faltan(self, tmp_path):
        ruta = _odt(tmp_path, 'carta_incompleta.odt',
                    marca={'plantilla-base': 'carta'})

        avisos = comprobar_canonicidad(ruta)

        assert len(avisos) == 1
        assert 'Cabecera - Consejería' in avisos[0]
        assert 'Formulario - Datos' in avisos[0]

    def test_marca_carta_sin_avisos_si_estan_todos_los_estilos(self, tmp_path):
        # style:name no necesita el escapado «_20_» de LibreOffice: es solo su
        # convención interna, no una exigencia de XML/ODF. Aquí basta con que
        # coincida con el display-name, que es lo único que mira la función.
        extra = ''.join(_estilo_parrafo(f'auto{i}', n)
                        for i, n in enumerate(ESTILOS_COMUNES + ESTILOS_CARTA))
        ruta = _odt(tmp_path, 'carta_completa.odt', estilos_extra=extra,
                    marca={'plantilla-base': 'carta'})

        assert comprobar_canonicidad(ruta) == []

    def test_marca_resolucion_no_exige_los_estilos_solo_de_carta(self, tmp_path):
        """Una resolución no lleva tabla de destinatario: no debe avisar por
        no tener Formulario - Datos."""
        extra = ''.join(_estilo_parrafo(f'auto{i}', n)
                        for i, n in enumerate(ESTILOS_COMUNES + ESTILOS_RESOLUCION))
        ruta = _odt(tmp_path, 'resolucion_completa.odt', estilos_extra=extra,
                    marca={'plantilla-base': 'resolucion'})

        assert comprobar_canonicidad(ruta) == []

    def test_marca_desconocida_no_exige_estilos(self, tmp_path):
        ruta = _odt(tmp_path, 'marca_rara.odt',
                    marca={'plantilla-base': 'algo_inventado'})

        assert comprobar_canonicidad(ruta) == []


# ----------------------------------------------------------------------
# Las tres plantillas base reales: el contrato que este módulo protege
# ----------------------------------------------------------------------

RAIZ_BASES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'app', 'data', 'plantillas_base')


class TestPlantillasBaseReales:
    def test_carta_base_sin_avisos(self):
        ruta = os.path.join(RAIZ_BASES, 'carta_base.odt')
        assert comprobar_canonicidad(ruta) == []
        assert leer_marca(ruta)['plantilla-base'] == 'carta'

    def test_resolucion_base_sin_avisos(self):
        ruta = os.path.join(RAIZ_BASES, 'resolucion_base.odt')
        assert comprobar_canonicidad(ruta) == []
        assert leer_marca(ruta)['plantilla-base'] == 'resolucion'

    def test_fragmento_base_sin_avisos(self):
        ruta = os.path.join(RAIZ_BASES, 'fragmento_base.odt')
        assert comprobar_canonicidad(ruta) == []
        assert leer_marca(ruta)['plantilla-base'] == 'fragmento'


# ----------------------------------------------------------------------
# Dispatcher — generador_escritos.advertencias_plantilla
# ----------------------------------------------------------------------

class TestDispatcherAdvertenciasPlantilla:
    def test_docx_no_tiene_avisos_de_canonicidad(self, tmp_path):
        """ADR-035 §5 es concepto propio del motor .odt: el .docx no tiene
        plantilla base, así que no hay nada que comprobar."""
        ruta = tmp_path / 'plantilla.docx'
        ruta.write_bytes(b'PK\x03\x04')  # cabecera ZIP, no hace falta más

        assert advertencias_plantilla(str(ruta)) == []

    def test_odt_delega_en_comprobar_canonicidad(self, tmp_path):
        ruta = _odt(tmp_path, 'cambria.odt', fuente_default='Cambria')

        avisos = advertencias_plantilla(ruta)

        assert any('Cambria' in a for a in avisos)
