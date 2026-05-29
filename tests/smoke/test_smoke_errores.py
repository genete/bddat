"""Smoke test — páginas de error (404).

El 500 no se prueba directamente: forzarlo requiere romper la app intencionalmente,
lo que contamina el estado de la sesión de test. El handler se cubre implícitamente
por cualquier test que falle con una excepción no capturada.
"""


def test_404_render(client):
    r = client.get('/ruta/que/no/existe/en/ninguna/parte')
    assert r.status_code == 404
    assert b'404' in r.data
