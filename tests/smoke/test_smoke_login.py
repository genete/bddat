"""Smoke test — vista de login (/auth/login).

Pública, no requiere autenticación.
"""


def test_login_render(client):
    r = client.get('/auth/login')
    assert r.status_code == 200
    assert b'login' in r.data.lower()
