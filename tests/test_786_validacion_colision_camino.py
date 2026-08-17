"""
Tests issue #786 — validación de colisión de camino en catalogo_plazos.

Tras #785 (identificación por camino), un duplicado ciego es dos filas activas
con el mismo `camino` y ninguna con condiciones — una queda siempre inerte, sin
aviso. Si alguna de las filas en colisión tiene condiciones (patrón legítimo
condición + reserva, como CONSULTA_SEPARATA), no se bloquea: se avisa para que
el Supervisor lo revise. Ver `_validar_colision_camino` en
`app/modules/catalogo_plazos/routes.py`.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite) — el fixture autouse de abajo borra al terminar toda fila que no
existiera al empezar (ver tests/smoke/test_smoke_catalogo_plazos.py).
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        previos = {
            fila.id for fila in CatalogoPlazo.query.with_entities(CatalogoPlazo.id).all()
        }
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        # Las condiciones_plazo cuelgan con ON DELETE CASCADE.
        CatalogoPlazo.query.filter(
            CatalogoPlazo.id.notin_(previos)
        ).delete(synchronize_session=False)
        db.session.commit()


def _datos_maestros(app):
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.efectos_plazo import EfectoPlazo
        from app.models.motor_reglas import CatalogoVariable
        tipo = TipoSolicitud.query.first()
        efecto = EfectoPlazo.query.first()
        variable = CatalogoVariable.query.filter_by(activa=True).first()
        if tipo is None or efecto is None or variable is None:
            pytest.skip('Faltan datos maestros en esta BD')
        return tipo.siglas, efecto.id, variable.id


def _alta_solicitud(client, siglas, efecto_id, norma_origen, orden=999):
    return client.post('/catalogo_plazos/crear', data={
        'tipo_elemento': 'SOLICITUD',
        'camino_solicitud': siglas,
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': norma_origen,
        'orden': str(orden),
    }, follow_redirects=False)


def test_crear_bloquea_duplicado_ciego_mismo_camino(usuario_supervisor, app):
    siglas, efecto_id, _var_id = _datos_maestros(app)

    r1 = _alta_solicitud(usuario_supervisor, siglas, efecto_id, 'Base colision (#786)')
    assert r1.status_code == 302

    r2 = _alta_solicitud(usuario_supervisor, siglas, efecto_id, 'Duplicado ciego (#786)')
    assert r2.status_code == 200, 'Debe re-renderizar el formulario con el error, no redirigir'
    assert 'indistinguibles' in r2.get_data(as_text=True)

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        assert CatalogoPlazo.query.filter_by(norma_origen='Duplicado ciego (#786)').first() is None


def test_crear_no_bloquea_camino_distinto(usuario_supervisor, app):
    """Control: dos altas SOLICITUD con camino distinto no colisionan."""
    with app.app_context():
        from app.models.tipos_solicitudes import TipoSolicitud
        from app.models.efectos_plazo import EfectoPlazo
        tipos = TipoSolicitud.query.limit(2).all()
        efecto = EfectoPlazo.query.first()
        if len(tipos) < 2 or efecto is None:
            pytest.skip('Se necesitan al menos 2 tipos_solicitudes en esta BD')
        siglas_a, siglas_b, efecto_id = tipos[0].siglas, tipos[1].siglas, efecto.id

    r1 = _alta_solicitud(usuario_supervisor, siglas_a, efecto_id, 'Camino A (#786)')
    r2 = _alta_solicitud(usuario_supervisor, siglas_b, efecto_id, 'Camino B (#786)')
    assert r1.status_code == 302
    assert r2.status_code == 302


def test_editar_bloquea_duplicado_ciego_con_otra_fila(usuario_supervisor, app):
    siglas, efecto_id, _var_id = _datos_maestros(app)

    r1 = _alta_solicitud(usuario_supervisor, siglas, efecto_id, 'Fila existente (#786)')
    assert r1.status_code == 302

    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.tipos_fases import TipoFase
        tipo_fase = TipoFase.query.first()
        if tipo_fase is None:
            pytest.skip('Faltan tipos_fases en esta BD')
        # Fila propia en otro camino (nivel FASE), a editar para que colisione.
        item = CatalogoPlazo(
            tipo_elemento='FASE',
            camino=f'ANY/ANY/{tipo_fase.codigo}',
            campo_fecha={'fk': 'documento_resultado_id'},
            plazo_valor=1,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto_id,
            norma_origen='Fila a editar (#786)',
            orden=999,
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    r2 = usuario_supervisor.post(f'/catalogo_plazos/{item_id}/editar', data={
        'tipo_elemento': 'SOLICITUD',
        'camino_solicitud': siglas,   # mismo camino que la fila existente sin condiciones
        'plazo_valor': '3',
        'plazo_unidad': 'MESES',
        'efecto_vencimiento_id': str(efecto_id),
        'norma_origen': 'Editada a duplicado (#786)',
    }, follow_redirects=False)
    assert r2.status_code == 302  # ruta de flash+redirect, no XHR

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        sin_cambios = CatalogoPlazo.query.get(item_id)
        assert sin_cambios.tipo_elemento == 'FASE', 'No debe haberse aplicado el cambio bloqueado'


def test_editar_permite_colision_con_condiciones_y_avisa(usuario_supervisor, app):
    siglas, efecto_id, var_id = _datos_maestros(app)

    r1 = _alta_solicitud(usuario_supervisor, siglas, efecto_id, 'Fila con hueco (#786)')
    assert r1.status_code == 302

    with app.app_context():
        from app import db
        from app.models.catalogo_plazos import CatalogoPlazo
        from app.models.tipos_fases import TipoFase
        tipo_fase = TipoFase.query.first()
        if tipo_fase is None:
            pytest.skip('Faltan tipos_fases en esta BD')
        item = CatalogoPlazo(
            tipo_elemento='FASE',
            camino=f'ANY/ANY/{tipo_fase.codigo}',
            campo_fecha={'fk': 'documento_resultado_id'},
            plazo_valor=1,
            plazo_unidad='MESES',
            efecto_vencimiento_id=efecto_id,
            norma_origen='Fila a condicionar (#786)',
            orden=999,
        )
        db.session.add(item)
        db.session.commit()
        item_id = item.id

    r2 = usuario_supervisor.post(
        f'/catalogo_plazos/{item_id}/editar',
        data={
            'tipo_elemento': 'SOLICITUD',
            'camino_solicitud': siglas,  # mismo camino que la fila sin condiciones (#786 fila 1)
            'plazo_valor': '3',
            'plazo_unidad': 'MESES',
            'efecto_vencimiento_id': str(efecto_id),
            'cond_variable_id': str(var_id),
            'cond_operador': 'NOT_NULL',
            'cond_orden': '1',
        },
        headers={'X-Requested-With': 'XMLHttpRequest'},
        follow_redirects=False,
    )
    assert r2.status_code == 200
    payload = r2.get_json()
    assert payload['ok'] is True
    assert payload['warnings'], 'Debe avisar de la colisión, no bloquear'

    with app.app_context():
        from app.models.catalogo_plazos import CatalogoPlazo
        editado = CatalogoPlazo.query.get(item_id)
        assert editado.tipo_elemento == 'SOLICITUD'
        assert len(editado.condiciones) == 1
