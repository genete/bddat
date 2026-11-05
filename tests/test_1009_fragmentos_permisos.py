"""
#1009 (ADR-050 §J) — un tramitador no puede crear, editar, guardar ni activar fragmentos.

Fallo silencioso que evita: una ruta de fragmentos sin `require_permiso('gestionar_plantillas')`
no se nota desde el supervisor, que es quien las usa: un tramitador que conociera la URL
sustituiría o desactivaría un fragmento que citan todas las plantillas (el pie de recurso, los
fundamentos) y los escritos saldrían con otro texto, o dejarían de generarse, sin que nada lo
avisara. No hay una auditoría genérica de rutas (`test_497` solo cubre las de plantillas), así que
cada ruta nueva depende de que alguien se acuerde del decorador.
"""
import pytest

from app import db

# (método, ruta). `{id}` se rellena con el fragmento de la fixture.
RUTAS = [
    ('get', '/plantillas/fragmentos/{id}/editar-fragmento'),
    ('post', '/plantillas/fragmentos/{id}/guardar'),
    ('post', '/plantillas/fragmentos/{id}/activar'),
    ('post', '/plantillas/fragmentos/crear'),
]


@pytest.mark.parametrize('metodo,ruta', RUTAS, ids=[r.rsplit('/', 1)[-1] for _, r in RUTAS])
def test_un_tramitador_no_puede_tocar_un_fragmento(usuario_tramitador, app, fragmento_commiteado,
                                                   metodo, ruta):
    from app.models.fragmentos import Fragmento

    # `crear` usa el nombre del fragmento que ya existe: si la ruta dejara pasar al tramitador,
    # el alta se rechazaría por duplicada y no dejaría un fragmento de prueba suelto en la BD.
    datos = {'nombre': 'Test_1009_Fragmento', 'descripcion': 'cambiada', '_form_completo': '1'}
    url = ruta.format(id=fragmento_commiteado)

    if metodo == 'get':
        r = usuario_tramitador.get(url, follow_redirects=False)
    else:
        r = usuario_tramitador.post(url, data=datos, follow_redirects=False)

    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
    with app.app_context():
        fragmento = db.session.get(Fragmento, fragmento_commiteado)
        assert fragmento.activo is True
        assert fragmento.descripcion == 'original'
