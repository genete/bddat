"""Smoke test — bandeja de mensajes internos (/mensajes_internos/, #28, ADR-040).

Cubre el listado (acceso universal, 4 roles) y, sobre todo, lo que ADR-040 §7
pone en juego: el filtrado por remitente se aplica en el ENDPOINT según
permiso, así que quien no gestiona no puede ver ni tocar peticiones ajenas
aunque fuerce la URL.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as) — las filas creadas se marcan con
'#28 smoke' dentro del payload y se borran en el fixture autouse.
"""
import pytest

from app import db
from app.models.mensajes_internos import MensajeInterno
from app.models.usuarios import Usuario

MARCA = '#28 smoke'


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        MensajeInterno.query.filter(
            db.cast(MensajeInterno.datos, db.Text).like(f'%{MARCA}%')
        ).delete(synchronize_session=False)
        db.session.commit()


def _usuario(app, siglas='CLG'):
    u = Usuario.query.filter_by(siglas=siglas).first()
    if u is None:
        pytest.skip(f'Usuario {siglas} no disponible en esta BD')
    return u


def _crear_mensaje(app, *, propio=True, hecho=False):
    """Crea una petición de prueba y devuelve su id.

    propio=False la firma OTRO usuario, para probar el filtrado por remitente.
    """
    from datetime import datetime, timezone

    with app.app_context():
        clg = _usuario(app)
        if propio:
            remitente = clg
        else:
            remitente = Usuario.query.filter(Usuario.id != clg.id).first()
            if remitente is None:
                pytest.skip('No hay un segundo usuario en la BD de desarrollo')

        m = MensajeInterno(
            remitente_usuario_id=remitente.id,
            tipo='CAMBIO_ROL',
            datos={'rol_solicitado': 'SUPERVISOR', 'justificacion': f'Prueba {MARCA}'},
        )
        if hecho:
            m.hecho = True
            m.resultado = 'ATENDIDA'
            m.hecho_at = datetime.now(timezone.utc)
            m.hecho_por_id = clg.id
        db.session.add(m)
        db.session.commit()
        return m.id


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/mensajes_internos/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    assert usuario_admin.get('/mensajes_internos/', follow_redirects=True).status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    assert usuario_tramitador.get('/mensajes_internos/', follow_redirects=True).status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    assert usuario_administrativo.get('/mensajes_internos/', follow_redirects=True).status_code == 200


# ---------------------------------------------------------------------------
# Filtrado por remitente — en el endpoint, no en el front (ADR-040 §7)
# ---------------------------------------------------------------------------

def test_api_tramitador_solo_ve_las_suyas(usuario_tramitador, app):
    ajeno_id = _crear_mensaje(app, propio=False)
    propio_id = _crear_mensaje(app, propio=True)

    r = usuario_tramitador.get('/api/mensajes-internos?limit=100')
    assert r.status_code == 200
    ids = [m['id'] for m in r.get_json()['data']]
    assert propio_id in ids
    assert ajeno_id not in ids
    assert all(m['es_propio'] for m in r.get_json()['data'])


def test_api_supervisor_ve_las_ajenas(usuario_supervisor, app):
    ajeno_id = _crear_mensaje(app, propio=False)
    r = usuario_supervisor.get('/api/mensajes-internos?limit=100')
    assert r.status_code == 200
    assert ajeno_id in [m['id'] for m in r.get_json()['data']]


def test_fragmento_ajeno_da_403_sin_permiso(usuario_tramitador, app):
    ajeno_id = _crear_mensaje(app, propio=False)
    r = usuario_tramitador.get(f'/mensajes_internos/{ajeno_id}/fragmento')
    assert r.status_code == 403


def test_fragmento_propio_ok_sin_permiso_de_gestion(usuario_tramitador, app):
    propio_id = _crear_mensaje(app, propio=True)
    r = usuario_tramitador.get(f'/mensajes_internos/{propio_id}/fragmento')
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Resolver — solo gestionar_mensajes_internos
# ---------------------------------------------------------------------------

def test_tramitador_no_puede_resolver(usuario_tramitador, app):
    propio_id = _crear_mensaje(app, propio=True)
    r = usuario_tramitador.post(f'/mensajes_internos/{propio_id}/resolver',
                                data={'resultado': 'ATENDIDA', 'notas': 'x'},
                                follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')

    with app.app_context():
        assert MensajeInterno.query.get(propio_id).hecho is False


def test_administrativo_no_puede_resolver(usuario_administrativo, app):
    propio_id = _crear_mensaje(app, propio=True)
    r = usuario_administrativo.post(f'/mensajes_internos/{propio_id}/resolver',
                                    data={'resultado': 'ATENDIDA'},
                                    follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_supervisor_resuelve_la_misma_fila(usuario_supervisor, app):
    mensaje_id = _crear_mensaje(app, propio=False)
    r = usuario_supervisor.post(f'/mensajes_internos/{mensaje_id}/resolver',
                                data={'resultado': 'DENEGADA', 'notas': f'No procede ({MARCA})'},
                                follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        m = MensajeInterno.query.get(mensaje_id)
        assert m.hecho is True
        assert m.resultado == 'DENEGADA'
        assert m.hecho_at is not None
        assert m.estado == 'resuelto'
        # No se ha creado una fila-respuesta aparte (ADR-040 §3)
        assert MensajeInterno.query.filter(
            db.cast(MensajeInterno.datos, db.Text).like(f'%{MARCA}%')
        ).count() == 1


def test_resultado_invalido_rechazado(usuario_supervisor, app):
    mensaje_id = _crear_mensaje(app, propio=False)
    usuario_supervisor.post(f'/mensajes_internos/{mensaje_id}/resolver',
                            data={'resultado': 'QUIZAS'}, follow_redirects=False)
    with app.app_context():
        assert MensajeInterno.query.get(mensaje_id).hecho is False


# ---------------------------------------------------------------------------
# Acuse — solo el remitente, y solo tras la resolución
# ---------------------------------------------------------------------------

def test_remitente_acusa(usuario_tramitador, app):
    mensaje_id = _crear_mensaje(app, propio=True, hecho=True)
    r = usuario_tramitador.post(f'/mensajes_internos/{mensaje_id}/acusar',
                                follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        assert MensajeInterno.query.get(mensaje_id).acusado_at is not None


def test_supervisor_no_acusa_por_otro(usuario_supervisor, app):
    """Ver una petición ajena sí; acusarla por su remitente, no."""
    mensaje_id = _crear_mensaje(app, propio=False, hecho=True)
    r = usuario_supervisor.post(f'/mensajes_internos/{mensaje_id}/acusar',
                                follow_redirects=False)
    assert r.status_code == 403

    with app.app_context():
        assert MensajeInterno.query.get(mensaje_id).acusado_at is None


def test_acuse_prematuro_no_marca_nada(usuario_tramitador, app):
    mensaje_id = _crear_mensaje(app, propio=True, hecho=False)
    usuario_tramitador.post(f'/mensajes_internos/{mensaje_id}/acusar', follow_redirects=False)
    with app.app_context():
        assert MensajeInterno.query.get(mensaje_id).acusado_at is None


# ---------------------------------------------------------------------------
# Badge — bimodal según permiso del rol activo
# ---------------------------------------------------------------------------

def test_badge_cuenta_pendientes_solo_para_quien_gestiona(usuario_supervisor, app):
    _crear_mensaje(app, propio=False)
    r = usuario_supervisor.get('/api/mensajes-internos/badge')
    assert r.status_code == 200
    assert r.get_json()['total'] >= 1


def test_badge_ignora_ajenas_sin_permiso(usuario_tramitador, app):
    """Una pendiente ajena no suma en el badge de quien no gestiona."""
    r_antes = usuario_tramitador.get('/api/mensajes-internos/badge').get_json()['total']
    _crear_mensaje(app, propio=False)
    r_despues = usuario_tramitador.get('/api/mensajes-internos/badge').get_json()['total']
    assert r_despues == r_antes


# ---------------------------------------------------------------------------
# Sobre del topbar — ADR-014 §5 enmendada, ADR-020 intacta
# ---------------------------------------------------------------------------

def test_topbar_lleva_el_sobre(usuario_tramitador):
    r = usuario_tramitador.get('/perfil/', follow_redirects=True)
    assert r.status_code == 200
    assert b'js-mensajes-topbar-badge' in r.data
    assert b'/mensajes_internos/' in r.data


def test_topbar_conserva_la_campana(usuario_tramitador):
    """El sobre se añade JUNTO a la campana, no en su lugar (ADR-020 no cambia)."""
    r = usuario_tramitador.get('/perfil/', follow_redirects=True)
    assert b'js-dock-topbar-badge' in r.data
    assert b'data-app-shell-toggle="dock"' in r.data


# ---------------------------------------------------------------------------
# Productor N054 — solicitud de cambio de rol desde Mi Perfil
# ---------------------------------------------------------------------------

def test_solicitud_de_rol_persiste(usuario_tramitador, app):
    """Antes de #28 este POST solo hacía flash y no guardaba nada."""
    r = usuario_tramitador.post('/perfil/solicitar-cambio-rol', data={
        'rol_solicitado': 'SUPERVISOR',
        'justificacion': f'Sustitución de agosto ({MARCA})',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        clg = _usuario(app)
        m = MensajeInterno.query.filter(
            MensajeInterno.remitente_usuario_id == clg.id,
            MensajeInterno.tipo == 'CAMBIO_ROL',
            db.cast(MensajeInterno.datos, db.Text).like(f'%{MARCA}%'),
        ).first()
        assert m is not None
        assert m.datos['rol_solicitado'] == 'SUPERVISOR'
        assert MARCA in m.datos['justificacion']
        assert m.estado == 'pendiente'


def test_solicitud_de_rol_sin_justificacion_no_persiste(usuario_tramitador, app):
    usuario_tramitador.post('/perfil/solicitar-cambio-rol', data={
        'rol_solicitado': 'SUPERVISOR',
        'justificacion': '   ',
    }, follow_redirects=False)

    with app.app_context():
        clg = _usuario(app)
        assert MensajeInterno.query.filter(
            MensajeInterno.remitente_usuario_id == clg.id,
            MensajeInterno.tipo == 'CAMBIO_ROL',
            MensajeInterno.hecho.is_(False),
            MensajeInterno.datos['justificacion'].astext == '',
        ).count() == 0


def test_perfil_ofrece_el_modal_con_selector_de_rol(usuario_tramitador):
    r = usuario_tramitador.get('/perfil/', follow_redirects=True)
    assert r.status_code == 200
    assert b'solicitarRolModal' in r.data
    assert b'name="rol_solicitado"' in r.data
    assert b'name="justificacion"' in r.data
