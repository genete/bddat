"""
Código de trazabilidad embebido en escritos generados (#182).

RESPONSABILIDAD:
    Componer el código que se inyecta en el escrito (`generador_escritos_odt`,
    gancho de #726) y extraerlo/verificarlo de vuelta a partir del texto de un
    documento incorporado (uso futuro: #181 preclasificación, #717 vínculo
    CONSUMIDO). Aquí no se toca ODF ni PDF: es lógica pura sobre un id de
    tarea y una cadena de texto.

FORMATO DEL CÓDIGO — 'BDDAT-<tarea_id>-<letra>':
    El id de instancia es tarea_id (#711): con él se deduce entero el
    encuadramiento ESFTT, así que no hace falta repetirlo en el código
    (DISEÑO_GENERACION_ESCRITOS.md §"Trazabilidad"). ASCII sin acentos: R10
    midió que los acentos se trocean al extraer texto de un PDF, los tokens
    ASCII no.

DÍGITO DE CONTROL:
    Letra de LETRAS_CONTROL en la posición tarea_id % 23 — misma mecánica que
    la letra del NIF/DNI. Cubre el escenario real del issue: una alteración
    accidental del código (edición en Writer, corrupción del pipeline, mal
    tecleado al transcribir) dejaría de cuadrar con el id y se detecta. No
    pretende resistir a alguien que, con acceso al código fuente, fabrique a
    propósito el código de una tarea ajena — ese nivel de protección se
    descartó por desproporcionado para el riesgo real.
"""

import re

LETRAS_CONTROL = 'TRWAGMYFPDXBNJZSQVHLCKE'

RE_CODIGO = re.compile(r'BDDAT-(\d+)-([A-Z])')


def componer_codigo(tarea_id: int) -> str:
    """Código de seguimiento a embeber para la tarea dada."""
    letra = LETRAS_CONTROL[tarea_id % len(LETRAS_CONTROL)]
    return f'BDDAT-{tarea_id}-{letra}'


def extraer_tarea_id(texto: str) -> int | None:
    """
    Busca un código de seguimiento en `texto` y devuelve su tarea_id si es
    válido.

    Returns:
        int  — tarea_id, si el código aparece y su letra de control cuadra.
        None — no hay código, o el que hay no supera la verificación (código
               alterado: se trata igual que ausente, nunca como válido).
    """
    m = RE_CODIGO.search(texto or '')
    if not m:
        return None

    tarea_id = int(m.group(1))
    letra = m.group(2)

    if LETRAS_CONTROL[tarea_id % len(LETRAS_CONTROL)] != letra:
        return None

    return tarea_id
