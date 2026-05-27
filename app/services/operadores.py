"""
Operadores de comparación reutilizables para evaluadores de condiciones.

Usados por motor_reglas._evaluar_condiciones y (sesión 4) por plazos._seleccionar_catalogo.
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
