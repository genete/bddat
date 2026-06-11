"""Smoke test — detalle y fragmento de entidad (ADR-023 / #534)."""


def test_entidad_detalle_redirige_a_index(usuario_supervisor, entidad_seed):
    """GET /entidades/<id> redirige a /entidades/?sel=<id> (ADR-023 §9)."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}')
    assert r.status_code == 302
    assert f'sel={entidad_seed}' in r.location


def test_entidad_detalle_sigue_redireccion(usuario_supervisor, entidad_seed):
    """Seguir la redirección llega al listado (200 con shell)."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_entidad_fragmento_render(usuario_supervisor, entidad_seed):
    """GET /entidades/<id>/fragmento → 200 con contenido del parcial."""
    r = usuario_supervisor.get(f'/entidades/{entidad_seed}/fragmento')
    assert r.status_code == 200
    assert b'Identificaci' in r.data
