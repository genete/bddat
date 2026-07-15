"""Smoke test — CRUD de Norma y CatalogoVariable (/normas_variables/, #637, N083).

Cubre:
  - Listado (acceso universal, 4 roles)
  - Norma: alta/edición restringidas a SUPERVISOR/ADMIN, código inmutable, sin baja
  - CatalogoVariable: solo edición (sin ruta de alta — 404 garantizado), `nombre`
    inmutable, `activa=True` rechazado si el nombre no tiene función en el
    Variable Registry (`app/services/variables/`)

Corre contra la BD real de desarrollo (mismo patrón que el resto de la suite,
ver conftest._login_as). Las filas de prueba se marcan con código/nombre
'ZZ_SMOKE_637'/'zz_smoke_637*' y se borran en el fixture autouse de abajo.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.motor_reglas import CatalogoVariable, Norma
        Norma.query.filter(
            Norma.codigo.like('ZZ_SMOKE_637%')
        ).delete(synchronize_session=False)
        CatalogoVariable.query.filter(
            CatalogoVariable.nombre.like('zz_smoke_637%')
        ).delete(synchronize_session=False)
        db.session.commit()


# ---------------------------------------------------------------------------
# Listado — acceso universal (4 roles)
# ---------------------------------------------------------------------------

def test_listado_render_supervisor(usuario_supervisor):
    r = usuario_supervisor.get('/normas_variables/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_listado_accesible_admin(usuario_admin):
    r = usuario_admin.get('/normas_variables/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_tramitador(usuario_tramitador):
    r = usuario_tramitador.get('/normas_variables/', follow_redirects=True)
    assert r.status_code == 200


def test_listado_accesible_administrativo(usuario_administrativo):
    r = usuario_administrativo.get('/normas_variables/', follow_redirects=True)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Norma — alta, solo SUPERVISOR/ADMIN
# ---------------------------------------------------------------------------

def test_supervisor_puede_crear_norma(usuario_supervisor, app):
    r = usuario_supervisor.post('/normas_variables/normas/crear', data={
        'codigo': 'ZZ_SMOKE_637',
        'titulo': 'Norma de prueba (#637 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/normas_variables/' in r.headers.get('Location', '')

    with app.app_context():
        from app.models.motor_reglas import Norma
        creada = Norma.query.filter_by(codigo='ZZ_SMOKE_637').first()
        assert creada is not None
        assert creada.titulo == 'Norma de prueba (#637 smoke)'


def test_tramitador_no_puede_crear_norma(usuario_tramitador):
    r = usuario_tramitador.post('/normas_variables/normas/crear', data={
        'codigo': 'ZZ_SMOKE_637_NO',
        'titulo': 'Intento no autorizado (#637 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# Norma — edición, código inmutable
# ---------------------------------------------------------------------------

def _crear_norma_para_editar(app):
    from app import db
    from app.models.motor_reglas import Norma
    with app.app_context():
        norma = Norma(codigo='ZZ_SMOKE_637_EDIT', titulo='Norma base para edición (#637 smoke)')
        db.session.add(norma)
        db.session.commit()
        return norma.id


def test_supervisor_puede_editar_norma(usuario_supervisor, app):
    norma_id = _crear_norma_para_editar(app)
    r = usuario_supervisor.post(f'/normas_variables/normas/{norma_id}/editar', data={
        'titulo': 'Norma editada (#637 smoke)',
        'url_eli': 'https://boe.es/ejemplo',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import Norma
        editada = Norma.query.get(norma_id)
        assert editada.codigo == 'ZZ_SMOKE_637_EDIT'  # inmutable
        assert editada.titulo == 'Norma editada (#637 smoke)'
        assert editada.url_eli == 'https://boe.es/ejemplo'


def test_editar_norma_ignora_codigo_enviado(usuario_supervisor, app):
    norma_id = _crear_norma_para_editar(app)
    usuario_supervisor.post(f'/normas_variables/normas/{norma_id}/editar', data={
        'codigo': 'INTENTO_CAMBIO_CODIGO',
        'titulo': 'Norma editada 2 (#637 smoke)',
    }, follow_redirects=False)

    with app.app_context():
        from app.models.motor_reglas import Norma
        editada = Norma.query.get(norma_id)
        assert editada.codigo == 'ZZ_SMOKE_637_EDIT'


def test_tramitador_no_puede_editar_norma(usuario_tramitador, app):
    norma_id = _crear_norma_para_editar(app)
    r = usuario_tramitador.post(f'/normas_variables/normas/{norma_id}/editar', data={
        'titulo': 'Intento no autorizado (#637 smoke)',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')


# ---------------------------------------------------------------------------
# CatalogoVariable — sin ruta de alta
# ---------------------------------------------------------------------------

def test_no_existe_ruta_de_alta_de_variable(usuario_supervisor):
    """No hay POST /normas_variables/variables/crear — 404 garantizado, no solo "sin botón"."""
    r = usuario_supervisor.post('/normas_variables/variables/crear', data={})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# CatalogoVariable — edición, `nombre` inmutable, `activa` gated por el registry
# ---------------------------------------------------------------------------

def _crear_variable_sin_registry(app):
    from app import db
    from app.models.motor_reglas import CatalogoVariable
    with app.app_context():
        variable = CatalogoVariable(
            nombre='zz_smoke_637_sin_funcion',
            etiqueta='Variable de prueba sin función (#637 smoke)',
            tipo_dato='boolean',
            activa=False,
        )
        db.session.add(variable)
        db.session.commit()
        return variable.id


def test_supervisor_puede_editar_variable(usuario_supervisor, app):
    variable_id = _crear_variable_sin_registry(app)
    r = usuario_supervisor.post(f'/normas_variables/variables/{variable_id}/editar', data={
        'etiqueta': 'Variable editada (#637 smoke)',
        'tipo_dato': 'texto',
        'norma_id': '',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        editada = CatalogoVariable.query.get(variable_id)
        assert editada.nombre == 'zz_smoke_637_sin_funcion'  # inmutable
        assert editada.etiqueta == 'Variable editada (#637 smoke)'
        assert editada.tipo_dato == 'texto'


def test_editar_variable_ignora_nombre_enviado(usuario_supervisor, app):
    variable_id = _crear_variable_sin_registry(app)
    usuario_supervisor.post(f'/normas_variables/variables/{variable_id}/editar', data={
        'nombre': 'intento_cambio_nombre',
        'etiqueta': 'Variable editada 2 (#637 smoke)',
        'tipo_dato': 'boolean',
    }, follow_redirects=False)

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        editada = CatalogoVariable.query.get(variable_id)
        assert editada.nombre == 'zz_smoke_637_sin_funcion'


def test_no_se_puede_activar_variable_sin_funcion_en_registry(usuario_supervisor, app):
    """activa=True debe rechazarse si `nombre` no existe en el Variable Registry (#637)."""
    variable_id = _crear_variable_sin_registry(app)
    r = usuario_supervisor.post(f'/normas_variables/variables/{variable_id}/editar', data={
        'etiqueta': 'Variable editada (#637 smoke)',
        'tipo_dato': 'boolean',
        'activa': 'on',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        editada = CatalogoVariable.query.get(variable_id)
        assert editada.activa is False  # rechazado, sigue inactiva


def test_se_puede_activar_variable_con_funcion_en_registry(usuario_supervisor, app):
    """activa=True se acepta cuando `nombre` sí tiene función registrada — usa una
    variable real ya sembrada por #638 (sin_linea_aerea), la deja como estaba."""
    with app.app_context():
        from app.models.motor_reglas import CatalogoVariable
        variable = CatalogoVariable.query.filter_by(nombre='sin_linea_aerea').first()
        assert variable is not None, 'Requiere #638 aplicado (seed de sin_linea_aerea)'
        variable_id = variable.id
        etiqueta_original = variable.etiqueta
        activa_original = variable.activa

    r = usuario_supervisor.post(f'/normas_variables/variables/{variable_id}/editar', data={
        'etiqueta': etiqueta_original,
        'tipo_dato': 'boolean',
        'activa': 'on',
    }, follow_redirects=False)
    assert r.status_code == 302

    with app.app_context():
        from app import db
        from app.models.motor_reglas import CatalogoVariable
        editada = CatalogoVariable.query.get(variable_id)
        assert editada.activa is True
        if editada.activa != activa_original:
            editada.activa = activa_original
            db.session.commit()


def test_tramitador_no_puede_editar_variable(usuario_tramitador, app):
    variable_id = _crear_variable_sin_registry(app)
    r = usuario_tramitador.post(f'/normas_variables/variables/{variable_id}/editar', data={
        'etiqueta': 'Intento no autorizado (#637 smoke)',
        'tipo_dato': 'boolean',
    }, follow_redirects=False)
    assert r.status_code == 302
    assert '/perfil' in r.headers.get('Location', '')
