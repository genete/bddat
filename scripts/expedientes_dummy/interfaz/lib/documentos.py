"""Los documentos que suben los guiones de interfaz: los PDF dummy de `scripts/generar_documentos_dummy.py`.

Ya no hay carpeta de PDF: `pdf_dummy` los construye en el momento (determinista, ~1,4 ms). Importarlo no tiene
efectos (reportlab se carga dentro de la función) y no toca la base de datos.

Un `tipo` es un `TipoDummy(codigo, nombre, origen)`: el `nombre` es el del tipo en el catálogo, que es el que
ofrecen los desplegables de la aplicación, y el `codigo` da el nombre del fichero (`<codigo>.pdf`).
"""
import uuid

from scripts.generar_documentos_dummy import TipoDummy, nombre_fichero, pdf_dummy

__all__ = ['TipoDummy', 'adjunto', 'fichero']


def fichero(tipo):
    """Nombre con el que el expediente ve el fichero de este tipo."""
    return nombre_fichero(tipo)


def adjunto(tipo, unico=True):
    """El PDF del tipo, listo para `set_input_files` (nombre, tipo MIME y bytes; sin tocar el disco).

    `unico`: añade al final un comentario distinto en cada llamada. `pdf_dummy` es determinista y la aplicación avisa
    «Este fichero ya está en el expediente…» (y pide «Subir igualmente») si el contenido se repite; así cada subida
    es un documento nuevo, con el mismo nombre. Un comentario tras `%%EOF` no altera el PDF."""
    contenido = pdf_dummy(tipo)
    if unico:
        contenido += f'\n% dummy {uuid.uuid4().hex}\n'.encode('ascii')
    return {'name': fichero(tipo), 'mimeType': 'application/pdf', 'buffer': contenido}
