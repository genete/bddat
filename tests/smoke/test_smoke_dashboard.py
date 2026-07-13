"""Smoke test — dashboard (/) y demo React (/demo/diagrama).

/demo/diagrama no requiere login y sirve como referencia de assert del shell
React (class="app-shell", <div id="app-root"), según nota de implementación #503.
"""
import re


def test_dashboard_render(usuario_supervisor):
    r = usuario_supervisor.get('/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_dashboard_proyeccion_1a1_module_nav(app, usuario_tramitador):
    """El dashboard muestra exactamente las tarjetas de module_nav (#589, ADR-029 §3).

    Ni una más (sin "Mis Expedientes"/"Nuevo Expediente"/"Tareas" retiradas) ni
    una menos — mismas etiquetas que generaría el sidebar para el mismo rol,
    más las dos excepciones hardcodeadas (Inicio, Mi Perfil).
    """
    with app.test_request_context():
        from flask import session
        from app.modules import ModuleRegistry
        # rol_activo_nombre lo fija el login real; aquí basta con TRAMITADOR
        # (mismo rol que el fixture) para reproducir el filtro de la petición.
        etiquetas_esperadas = {
            item['label'] for item in ModuleRegistry.get_navigation(['TRAMITADOR'])
        }

    r = usuario_tramitador.get('/')
    html = r.data.decode('utf-8')
    etiquetas_en_pagina = set(re.findall(r'<h2 class="card-title">([^<]+)</h2>', html))

    assert 'Mis Expedientes' not in etiquetas_en_pagina
    assert 'Nuevo Expediente' not in etiquetas_en_pagina
    assert 'Tareas' not in etiquetas_en_pagina
    assert etiquetas_esperadas <= etiquetas_en_pagina
    assert etiquetas_en_pagina == etiquetas_esperadas | {'Mi Perfil'}


def test_demo_diagrama_render(client):
    """Demo React — pública, sin login. Verifica shell React básico."""
    r = client.get('/demo/diagrama', follow_redirects=True)
    assert r.status_code == 200
    assert b'app-shell' in r.data or b'app-root' in r.data
