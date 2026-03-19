"""
limpiar_fragmento.py — Limpia un .docx para usarlo como fragmento de plantilla.

Elimina los elementos que interfieren con docxtpl al copiar/pegar desde otros documentos:
  - Marcadores de revisión (<w:ins>, <w:del>) → acepta todos los cambios
  - Cambios de formato rastreados (<w:rPrChange>, <w:pPrChange>)
  - Comentarios y anotaciones

USO:
    python limpiar_fragmento.py mi_fragmento.docx
    python limpiar_fragmento.py mi_fragmento.docx -o fragmento_limpio.docx
"""

import sys
import shutil
from pathlib import Path
from lxml import etree


W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'

# Etiquetas que se eliminan completamente (con todo su contenido)
ELIMINAR_CON_CONTENIDO = {
    f'{{{W}}}del',           # texto eliminado rastreado
    f'{{{W}}}rPrChange',     # cambio de formato de carácter rastreado
    f'{{{W}}}pPrChange',     # cambio de formato de párrafo rastreado
    f'{{{W}}}sectPrChange',  # cambio de sección rastreado
    f'{{{W}}}tblPrChange',   # cambio de tabla rastreado
    f'{{{W}}}trPrChange',    # cambio de fila rastreado
    f'{{{W}}}tcPrChange',    # cambio de celda rastreado
    f'{{{W}}}commentRangeStart',
    f'{{{W}}}commentRangeEnd',
    f'{{{W}}}commentReference',
    f'{{{W}}}sectPr',        # propiedades de sección — generan saltos al insertar el fragmento
}

# Etiquetas que se "aceptan": se eliminan pero se conserva su contenido hijo
ACEPTAR_INSERCION = {
    f'{{{W}}}ins',           # texto insertado rastreado → se convierte en texto normal
}


def limpiar_elemento(elemento):
    """Recorre el árbol XML y limpia marcadores de revisión."""
    # Primero procesar hijos (en orden inverso para poder modificar mientras iteramos)
    for hijo in list(elemento):
        limpiar_elemento(hijo)

    padre = elemento.getparent()
    if padre is None:
        return

    if elemento.tag in ELIMINAR_CON_CONTENIDO:
        padre.remove(elemento)

    elif elemento.tag in ACEPTAR_INSERCION:
        # Sustituir <w:ins> por sus hijos directos (conservar el texto)
        pos = list(padre).index(elemento)
        for i, hijo in enumerate(list(elemento)):
            elemento.remove(hijo)
            padre.insert(pos + i, hijo)
        padre.remove(elemento)


def limpiar_docx(ruta_entrada: Path, ruta_salida: Path):
    import zipfile
    import io

    buf_in = ruta_entrada.read_bytes()
    buf_out = io.BytesIO()

    partes_xml = {
        'word/document.xml',
        'word/styles.xml',
    }
    # Añadir cabeceras y pies si existen
    import re
    with zipfile.ZipFile(io.BytesIO(buf_in)) as zin:
        nombres = set(zin.namelist())
        for nombre in nombres:
            if re.match(r'^word/(header|footer)\d*\.xml$', nombre):
                partes_xml.add(nombre)

    with zipfile.ZipFile(io.BytesIO(buf_in), 'r') as zin, \
         zipfile.ZipFile(buf_out, 'w', compression=zipfile.ZIP_DEFLATED) as zout:

        for item in zin.infolist():
            data = zin.read(item.filename)

            if item.filename in partes_xml:
                try:
                    root = etree.fromstring(data)
                    limpiar_elemento(root)
                    data = etree.tostring(root, xml_declaration=True,
                                          encoding='UTF-8', standalone=True)
                except Exception as e:
                    print(f'  [AVISO] No se pudo limpiar {item.filename}: {e}')

            zout.writestr(item, data)

    ruta_salida.write_bytes(buf_out.getvalue())


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Limpia un .docx para usarlo como fragmento de plantilla.')
    parser.add_argument('entrada', help='Fichero .docx de entrada')
    parser.add_argument('-o', '--salida', help='Fichero de salida (por defecto: entrada_limpio.docx)')
    args = parser.parse_args()

    entrada = Path(args.entrada)
    if not entrada.exists():
        print(f'Error: no existe el fichero {entrada}')
        sys.exit(1)

    if args.salida:
        salida = Path(args.salida)
    else:
        salida = entrada.with_name(entrada.stem + '_limpio' + entrada.suffix)

    print(f'Limpiando {entrada} ...')
    limpiar_docx(entrada, salida)
    print(f'Guardado en {salida}')


if __name__ == '__main__':
    main()
