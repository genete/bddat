"""
Operadores de comparación reutilizables para evaluadores de condiciones.

Usados por motor_reglas._evaluar_condiciones y (sesión 4) por plazos._seleccionar_catalogo.

Aquí vive también `camino_casa`, el matcher posicional de caminos calificados
ESFTT: lo comparten el sujeto del motor (`reglas_motor.sujeto`, 2-4 segmentos) y
el camino del catálogo de plazos (`catalogo_plazos.camino`, 2-5 segmentos, #785).
Mismo criterio de extracción que _OPERADORES (IMPLEMENTACION_341.md decisión C):
cuando motor_reglas y plazos necesitan el mismo mecanismo, vive en este módulo.
"""

_OPERADORES = {
    'EQ':          lambda v, ref: v == ref,
    'NEQ':         lambda v, ref: v != ref,
    'IN':          lambda v, ref: v in (ref if isinstance(ref, list) else [ref]),
    'NOT_IN':      lambda v, ref: v not in (ref if isinstance(ref, list) else [ref]),
    'IS_NULL':     lambda v, _: v is None,
    'NOT_NULL':    lambda v, _: v is not None,
    'GT':          lambda v, ref: v is not None and v > ref,
    'GTE':         lambda v, ref: v is not None and v >= ref,
    'LT':          lambda v, ref: v is not None and v < ref,
    'LTE':         lambda v, ref: v is not None and v <= ref,
    'BETWEEN':     lambda v, ref: v is not None and ref[0] <= v <= ref[1],
    'NOT_BETWEEN': lambda v, ref: v is not None and not (ref[0] <= v <= ref[1]),
}


def camino_casa(patron: str, real: str) -> bool:
    """
    Compara segmento a segmento separando por '/'.
    'ANY' en el patrón casa con cualquier valor real en esa posición.
    Distinto número de segmentos → no casa (la longitud codifica el nivel ESFTT).
    """
    partes_patron = patron.split('/')
    partes_real   = real.split('/')
    if len(partes_patron) != len(partes_real):
        return False
    return all(
        p == 'ANY' or p == r
        for p, r in zip(partes_patron, partes_real)
    )
