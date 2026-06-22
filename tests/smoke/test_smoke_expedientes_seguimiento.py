"""Smoke test — seguimiento de expedientes (/expedientes/seguimiento/).

Precursor del área "Mi trabajo" (#501, aún no implementada).
Cuando exista /mi_trabajo/, añadir test_smoke_mi_trabajo.py en ese mismo PR.
"""

import pytest


def test_expedientes_seguimiento_render(usuario_supervisor):
    r = usuario_supervisor.get('/expedientes/seguimiento/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


# ── Inspector de seguimiento (ADR-023 / #559) ────────────────────────────────

def test_seguimiento_fragmento_render(usuario_supervisor, app):
    """GET /expedientes/seguimiento/<id>/fragmento → 200 con el detalle del agregado."""
    with app.app_context():
        from app.models.solicitudes import Solicitud
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        sol_id = sol.id
    r = usuario_supervisor.get(f'/expedientes/seguimiento/{sol_id}/fragmento')
    assert r.status_code == 200
    # El botón de delegación al árbol está siempre presente en el fragmento.
    assert 'Ir a tramitar'.encode() in r.data


def test_seguimiento_fragmento_inexistente(usuario_supervisor):
    """GET del fragmento de una solicitud inexistente → 404."""
    r = usuario_supervisor.get('/expedientes/seguimiento/99999999/fragmento')
    assert r.status_code == 404
