"""Smoke test — listado de usuarios (/usuarios/) migrado al patrón inspector (#544)."""


def test_usuarios_listado_render(usuario_supervisor):
    r = usuario_supervisor.get('/usuarios/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_usuarios_listado_es_v2(usuario_supervisor):
    """El listado ya no trae filas de BD en Jinja: usa la tabla v2 + la API."""
    r = usuario_supervisor.get('/usuarios/')
    assert r.status_code == 200
    assert b'usuarios-table' in r.data        # tabla del patrón unificado
    assert b'/api/usuarios' in r.data         # datos cargados por ScrollInfinito
