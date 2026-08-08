"""
Helpers de respuesta JSON compartidos por las APIs que consultan al motor.

Rescatados de `app/routes/api_bc.py` (#577) al retirar aquel blueprint: eran
helpers privados de un módulo de rutas, pero `api_expedientes.py` ya importaba
`_leer_bypass` desde allí (#616) y el servicio de consultas también los necesita.
Aquí dejan de ser privados y dejan de colgar de un fichero de rutas.

Devuelven tuplas `(respuesta, status)` listas para `return` desde un endpoint.
"""
from flask import jsonify


def bloqueo(res_eval):
    """Respuesta de error cuando el motor bloquea la acción."""
    return jsonify({
        'ok': False,
        'motivo': res_eval.motivo,
        'error': res_eval.norma_compilada or 'Acción no permitida',
        'url_norma': res_eval.url_norma,
        'puede_escapar': res_eval.puede_escapar,
    }), 422


def leer_bypass(form):
    """
    Lee bypass + justificacion de la petición (form-urlencoded o dict JSON — #616:
    api_expedientes.py reutiliza esta función con el body JSON, donde bypass llega
    como bool nativo en vez de string).

    Devuelve (justificacion, None) si bypass=true con texto válido,
    (None, None) si bypass está ausente o es false,
    (None, respuesta_400) si bypass=true pero justificacion está vacía.
    """
    if form.get('bypass') not in ('true', '1', 'True', True):
        return None, None
    justificacion = (form.get('justificacion') or '').strip()
    if not justificacion:
        return None, (jsonify({'ok': False, 'error': 'justificacion es obligatoria para el bypass'}), 400)
    return justificacion, None


def advertencia(res_eval):
    """Dict de advertencia para incluir en la respuesta ok (o None si no hay)."""
    if res_eval and res_eval.nivel == 'ADVERTIR':
        return {'motivo': res_eval.motivo, 'norma_compilada': res_eval.norma_compilada, 'url_norma': res_eval.url_norma}
    return None
