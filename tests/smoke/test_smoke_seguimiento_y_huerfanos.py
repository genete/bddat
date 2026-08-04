"""Smoke test — hub "Seguimiento y Huérfanos" del TRAMITADOR (#630, ADR-038).

Extraído de /expedientes/seguimiento/ (#501/#559), que era vista prestada del
dominio de expedientes (ADR-017 "Deuda conocida", caso 3). Ahora hub propio,
mismo patrón que tareas_y_subidas/gestion_y_control.
"""

import pytest


def test_seguimiento_y_huerfanos_render(usuario_supervisor):
    r = usuario_supervisor.get('/seguimiento_y_huerfanos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


# ── Inspector de seguimiento (ADR-023 / #559) ────────────────────────────────

def test_seguimiento_fragmento_render(usuario_supervisor, app):
    """GET /seguimiento_y_huerfanos/seguimiento/<id>/fragmento → 200 con el detalle del agregado."""
    with app.app_context():
        from app.models.solicitudes import Solicitud
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        sol_id = sol.id
    r = usuario_supervisor.get(f'/seguimiento_y_huerfanos/seguimiento/{sol_id}/fragmento')
    assert r.status_code == 200
    # El botón de delegación al árbol está siempre presente en el fragmento.
    assert 'Ir a tramitar'.encode() in r.data


def test_seguimiento_fragmento_inexistente(usuario_supervisor):
    """GET del fragmento de una solicitud inexistente → 404."""
    r = usuario_supervisor.get('/seguimiento_y_huerfanos/seguimiento/99999999/fragmento')
    assert r.status_code == 404
