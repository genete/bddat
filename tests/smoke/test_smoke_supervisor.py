"""Smoke de "Mi trabajo del supervisor" (#579, ADR-028 / ADR-019).

Hub de dos bloques (CONTROL · GESTIÓN) + hoja de estadísticas (placeholder),
acceso por `acceder_supervision` y entrada role-adaptive vía `mi_trabajo.index`.
"""


def test_supervisor_hub_renderiza_shell(usuario_supervisor):
    r = usuario_supervisor.get('/supervisor/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'Control' in r.data
    assert 'Gestión'.encode('utf-8') in r.data


def test_supervisor_estadisticas_monta_isla(usuario_supervisor):
    """La hoja de estadísticas monta la isla React (#579, ADR-028 §2)."""
    r = usuario_supervisor.get('/supervisor/estadisticas')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'data-react-island="estadisticas"' in r.data


def test_supervisor_api_estadisticas_json(usuario_supervisor):
    """El endpoint de agregados responde 200 con las tres claves del contrato."""
    r = usuario_supervisor.get('/supervisor/api/estadisticas')
    assert r.status_code == 200
    datos = r.get_json()
    assert set(datos) == {'kpis', 'por_estado', 'por_tecnico'}
    assert set(datos['kpis']) == {'total', 'en_tramite', 'plazos_vencidos', 'finalizados'}


def test_supervisor_api_estadisticas_denegado(usuario_tramitador):
    """Sin `acceder_supervision` el endpoint no sirve agregados."""
    r = usuario_tramitador.get('/supervisor/api/estadisticas', follow_redirects=False)
    assert r.status_code in (302, 403)


def test_mi_trabajo_supervisor_redirige_al_hub(usuario_supervisor):
    """El "Mi trabajo" del supervisor aterriza en su hub, no en el seguimiento."""
    r = usuario_supervisor.get('/mi_trabajo/', follow_redirects=False)
    assert r.status_code == 302
    assert '/supervisor/' in r.headers.get('Location', '')


def test_supervisor_denegado_sin_permiso(usuario_tramitador):
    """Sin `acceder_supervision` (TRAMITADOR) el hub redirige fuera (perfil)."""
    r = usuario_tramitador.get('/supervisor/', follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
