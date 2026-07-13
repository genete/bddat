"""Smoke de "Control y Gestión" (#579 ADR-028, universalizado #588 ADR-029).

Hub de dos bloques (CONTROL · GESTIÓN) + hoja de estadísticas (placeholder),
acceso universal por `acceder_gestion_control` (4 roles) y entrada de sidebar
propia además de la role-adaptive `mi_trabajo.index`.
"""


def test_gestion_control_hub_renderiza_shell(usuario_supervisor):
    r = usuario_supervisor.get('/gestion_y_control/')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'Control' in r.data
    assert 'Gestión'.encode('utf-8') in r.data


def test_gestion_control_hub_universal_4_roles(usuario_admin, usuario_supervisor,
                                                usuario_tramitador, usuario_administrativo):
    """ADR-029 §2: acceder_gestion_control ya no se restringe a SUPERVISOR/ADMIN."""
    for cliente in (usuario_admin, usuario_supervisor, usuario_tramitador, usuario_administrativo):
        r = cliente.get('/gestion_y_control/')
        assert r.status_code == 200


def test_gestion_control_estadisticas_monta_isla(usuario_supervisor):
    """La hoja de estadísticas monta la isla React (#579, ADR-028 §2)."""
    r = usuario_supervisor.get('/gestion_y_control/estadisticas')
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    assert b'data-react-island="estadisticas"' in r.data


def test_gestion_control_api_estadisticas_json(usuario_supervisor):
    """El endpoint de agregados responde 200 con las tres claves del contrato."""
    r = usuario_supervisor.get('/gestion_y_control/api/estadisticas')
    assert r.status_code == 200
    datos = r.get_json()
    assert set(datos) == {'kpis', 'por_estado', 'por_tecnico'}
    assert set(datos['kpis']) == {'total', 'en_tramite', 'plazos_vencidos', 'finalizados'}


def test_mi_trabajo_supervisor_redirige_al_hub(usuario_supervisor):
    """El "Mi trabajo" del supervisor aterriza en Control y Gestión."""
    r = usuario_supervisor.get('/mi_trabajo/', follow_redirects=False)
    assert r.status_code == 302
    assert '/gestion_y_control/' in r.headers.get('Location', '')
