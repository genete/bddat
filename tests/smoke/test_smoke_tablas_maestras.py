"""Smoke test — catálogos estructurales ESFTT (/tablas_maestras/, #171).

Cubre listado (acceso universal, 4 roles), alta y edición (restringidas a
SUPERVISOR/ADMIN), inmutabilidad del campo identificador tras el alta, y el
catálogo cerrado de Tarea (sin alta, para nadie).

Corre contra la BD real de desarrollo — las filas de prueba se marcan con el
prefijo 'SMOKE171_' en el campo identificador y se borran en el fixture
autouse de abajo.
"""
import pytest

_PREFIJO = 'SMOKE171_'


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.tipos_expedientes import TipoExpediente
        from app.models.tipos_fases import TipoFase
        from app.models.tipos_solicitudes import TipoSolicitud
        TipoExpediente.query.filter(TipoExpediente.tipo.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        TipoFase.query.filter(TipoFase.codigo.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        TipoSolicitud.query.filter(TipoSolicitud.siglas.like(f'{_PREFIJO}%')).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/tablas_maestras/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Alta — solo SUPERVISOR/ADMIN, campo identificador se fija y no se toca más
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear_expediente(usuario_supervisor, app):
    r = usuario_supervisor.post('/tablas_maestras/expediente/crear', data={
        'tipo': f'{_PREFIJO}Autoconsumo',
        'descripcion': 'Tipo de prueba (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_expedientes import TipoExpediente
        creado = TipoExpediente.query.filter_by(tipo=f'{_PREFIJO}Autoconsumo').first()
        assert creado is not None
        assert creado.descripcion == 'Tipo de prueba (#171 smoke)'


def test_tramitador_no_puede_crear(usuario_tramitador):
    r = usuario_tramitador.post('/tablas_maestras/expediente/crear', data={
        'tipo': f'{_PREFIJO}NoAutorizado',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


def test_tarea_no_permite_alta_ni_para_supervisor(usuario_supervisor):
    """Catálogo cerrado (#171): estado_dominio.py asume exactamente 4 códigos."""
    r = usuario_supervisor.post('/tablas_maestras/tarea/crear', data={
        'codigo': f'{_PREFIJO}NUEVA',
    }, follow_redirects=False)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Edición — campo identificador inmutable aunque llegue en el POST
# ---------------------------------------------------------------------------

def _crear_fase_para_editar(app):
    from app import db
    from app.models.tipos_fases import TipoFase
    with app.app_context():
        fase = TipoFase(codigo=f'{_PREFIJO}FASE', nombre='Fase de prueba (#171 smoke)')
        db.session.add(fase)
        db.session.commit()
        return fase.id


def test_supervisor_puede_editar_nombre(usuario_supervisor, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_supervisor.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'nombre': 'Fase renombrada (#171 smoke)',
        'abrev': 'FR',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_fases import TipoFase
        editada = TipoFase.query.get(fase_id)
        assert editada.nombre == 'Fase renombrada (#171 smoke)'
        assert editada.abrev == 'FR'


def test_codigo_no_cambia_aunque_llegue_en_el_post(usuario_supervisor, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_supervisor.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'codigo': f'{_PREFIJO}INTENTO_CAMBIO',
        'nombre': 'Fase de prueba (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.tipos_fases import TipoFase
        editada = TipoFase.query.get(fase_id)
        assert editada.codigo == f'{_PREFIJO}FASE'


def test_tramitador_no_puede_editar(usuario_tramitador, app):
    fase_id = _crear_fase_para_editar(app)
    r = usuario_tramitador.post(f'/tablas_maestras/fase/{fase_id}/editar', data={
        'nombre': 'Intento no autorizado (#171 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
