"""Checker del registro de usos de un documento frente al modelo (#881).

Mismo patrón que `registro_variables.py` (#587): un desajuste que no da ningún error —aquí, una FK
hacia `documentos.id` sin su uso registrado deja el documento «libre» y se puede borrar, con
`CASCADE` o `SET NULL` perdiendo el dato— se hace visible al arrancar en vez de esperar a que
alguien lo descubra por el dato perdido. Es la guarda dentro del código que `tests/README.md` §3
(tercera pregunta) prefiere a un test.

`validar_usos_documento()` es el único sitio que lo comprueba; la comparación vive en
`app.services.usos_documento.desajustes_del_registro`, junto al registro que valida. Llamar desde
`create_app()` junto a `validar_catalogo()` (#347) y `validar_registro_variables()` (#587). No
necesita la BD: solo mira el modelo.
"""
from __future__ import annotations

import logging
from typing import List

log = logging.getLogger(__name__)


def validar_usos_documento() -> List[str]:
    """Registra como error cada desajuste entre `REFERENCIAS` y las FK hacia `documentos`
    (ver `desajustes_del_registro`) y los devuelve. Lista vacía → todo cuadra. Nunca lanza.
    """
    from app.services.usos_documento import desajustes_del_registro

    avisos = desajustes_del_registro()
    if avisos:
        log.error(
            'usos_documento: el registro de usos no cuadra con las FK hacia documentos:\n%s',
            '\n'.join(f'  - {a}' for a in avisos),
        )
    return avisos
