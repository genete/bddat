"""
Tests #684 — el alta en `catalogo_requerimientos` desde el shuttle de ANALIZAR
exige el mismo permiso que el CRUD de #593.

El bug: `POST .../nodo/tarea/<id>/requerimientos/catalogo` (#440) solo pedía
`gestionar_tarea` (= `gestionar_tareas`, que incluye TRAMITADOR y
ADMINISTRATIVO), así que el checkbox "Guardar en catálogo" del shuttle era una
puerta trasera al catálogo maestro que #593 había restringido a
SUPERVISOR+ADMIN.

Estos tests corren contra la BD real de desarrollo (mismo patrón que el resto
de la suite, ver conftest._login_as); las filas que llegue a crear el caso
permitido se marcan con '#684 test' y las borra el fixture autouse.
"""
import pytest


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        from app import db
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        CatalogoRequerimiento.query.filter(
            CatalogoRequerimiento.texto.like('%#684 test%')
        ).delete(synchronize_session=False)
        db.session.commit()


@pytest.fixture
def tarea_analizar_seed(app):
    """(expediente_id, tarea_id) de una tarea ANALIZAR real de la BD de desarrollo.

    El endpoint resuelve la tarea DESPUÉS del gate de permiso, así que para el
    403 valdría cualquier id; hace falta una de verdad para que el caso
    permitido llegue a crear la fila.
    """
    with app.app_context():
        from app.models import Tarea, TipoTarea, Tramite, Fase, Solicitud
        fila = (
            Tarea.query
            .join(TipoTarea, TipoTarea.id == Tarea.tipo_tarea_id)
            .join(Tramite, Tramite.id == Tarea.tramite_id)
            .join(Fase, Fase.id == Tramite.fase_id)
            .join(Solicitud, Solicitud.id == Fase.solicitud_id)
            .filter(TipoTarea.codigo == 'ANALIZAR')
            .with_entities(Solicitud.expediente_id, Tarea.id)
            .first()
        )
        if fila is None:
            pytest.skip('No hay tareas ANALIZAR en la BD de desarrollo')
        return fila[0], fila[1]


def _payload(marca):
    return {'texto': f'Requerimiento inventado al vuelo ({marca} #684 test)',
            'categoria': 'administrativa'}


def _url(expediente_id, tarea_id):
    return f'/api/expedientes/{expediente_id}/nodo/tarea/{tarea_id}/requerimientos/catalogo'


def _existe(app, marca):
    with app.app_context():
        from app.models.catalogo_requerimientos import CatalogoRequerimiento
        return CatalogoRequerimiento.query.filter(
            CatalogoRequerimiento.texto.like(f'%{marca} #684 test%')
        ).first()


# ---------------------------------------------------------------------------
# Denegado — TRAMITADOR / ADMINISTRATIVO (tienen gestionar_tareas, no el catálogo)
# ---------------------------------------------------------------------------

def test_tramitador_no_puede_crear_en_catalogo(usuario_tramitador, tarea_analizar_seed, app):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_tramitador.post(_url(expediente_id, tarea_id), json=_payload('tramitador'))

    assert r.status_code == 403
    assert _existe(app, 'tramitador') is None


def test_administrativo_no_puede_crear_en_catalogo(usuario_administrativo, tarea_analizar_seed, app):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_administrativo.post(_url(expediente_id, tarea_id), json=_payload('administrativo'))

    assert r.status_code == 403
    assert _existe(app, 'administrativo') is None


# ---------------------------------------------------------------------------
# Permitido — quien puede curar el catálogo (mismo permiso que el CRUD de #593)
# ---------------------------------------------------------------------------

def test_supervisor_si_puede_crear_en_catalogo(usuario_supervisor, tarea_analizar_seed, app):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_supervisor.post(_url(expediente_id, tarea_id), json=_payload('supervisor'))

    assert r.status_code == 200
    assert r.get_json()['ok'] is True

    creado = _existe(app, 'supervisor')
    assert creado is not None
    assert creado.categoria == 'administrativa'
    assert creado.activo is True
