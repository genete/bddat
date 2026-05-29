"""Smoke test — seguimiento de expedientes (/expedientes/seguimiento/).

Precursor del área "Mi trabajo" (#501, aún no implementada).
Cuando exista /mi_trabajo/, añadir test_smoke_mi_trabajo.py en ese mismo PR.
"""


def test_expedientes_seguimiento_render(usuario_supervisor):
    r = usuario_supervisor.get('/expedientes/seguimiento/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
