"""
Tests #28 — "Solicitar guardado en catálogo" desde el shuttle de ANALIZAR.

Cierra el contrato que dejó #684: aquel issue restringió el alta directa en
`catalogo_requerimientos` a quien puede curarlo y dejó, en la misma posición de
la interfaz, una casilla inerte para el resto. Ahora esa casilla envía una
propuesta al Supervisor.

Lo que estos tests fijan es la frontera entre las dos vías: la propuesta NO
escribe en el catálogo. Si algún día alguien "simplifica" reutilizando el
endpoint de #440 con un flag, esto se pone rojo.

Corren contra la BD real de desarrollo (ver conftest._login_as); las filas
creadas se marcan con '#28 test' y las borra el fixture autouse.
"""
import pytest

from app import db
from app.models.catalogo_requerimientos import CatalogoRequerimiento
from app.models.mensajes_internos import MensajeInterno

MARCA = '#28 test'


@pytest.fixture(autouse=True)
def _limpiar_datos_prueba(app):
    yield
    with app.app_context():
        MensajeInterno.query.filter(
            db.cast(MensajeInterno.datos, db.Text).like(f'%{MARCA}%')
        ).delete(synchronize_session=False)
        CatalogoRequerimiento.query.filter(
            CatalogoRequerimiento.texto.like(f'%{MARCA}%')
        ).delete(synchronize_session=False)
        db.session.commit()


@pytest.fixture
def tarea_analizar_seed(app):
    """(expediente_id, tarea_id) de una tarea ANALIZAR real de la BD de desarrollo,
    bajo fase ABIERTA: si la fase está sellada el POST muere en 422 dentro de
    `_resolver_nodo` sin llegar al endpoint (#720, ADR-036 §6 — misma trampa
    que dejó rojos los tests de #765, ver #842)."""
    with app.app_context():
        from app.models import Tarea, TipoTarea, Tramite, Fase, Solicitud
        fila = (
            Tarea.query
            .join(TipoTarea, TipoTarea.id == Tarea.tipo_tarea_id)
            .join(Tramite, Tramite.id == Tarea.tramite_id)
            .join(Fase, Fase.id == Tramite.fase_id)
            .join(Solicitud, Solicitud.id == Fase.solicitud_id)
            .filter(TipoTarea.codigo == 'ANALIZAR',
                    Fase.documento_resultado_id.is_(None))
            .with_entities(Solicitud.expediente_id, Tarea.id)
            .first()
        )
        if fila is None:
            pytest.skip('No hay tareas ANALIZAR bajo fase abierta en la BD de desarrollo')
        return fila[0], fila[1]


def _url(expediente_id, tarea_id):
    return (f'/api/expedientes/{expediente_id}/nodo/tarea/{tarea_id}'
            f'/requerimientos/catalogo/solicitar')


def _mensajes(app):
    with app.app_context():
        return MensajeInterno.query.filter(
            db.cast(MensajeInterno.datos, db.Text).like(f'%{MARCA}%')
        ).all()


# ---------------------------------------------------------------------------
# La propuesta llega al Supervisor y NO toca el catálogo
# ---------------------------------------------------------------------------

def test_tramitador_puede_proponer(usuario_tramitador, app, tarea_analizar_seed):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_tramitador.post(_url(expediente_id, tarea_id), json={
        'texto': f'Falta el certificado de dirección de obra ({MARCA})',
        'categoria': 'documental',
    })
    assert r.status_code == 200
    assert r.get_json()['ok'] is True

    creados = _mensajes(app)
    assert len(creados) == 1
    assert creados[0].tipo == 'ALTA_CATALOGO_REQUERIMIENTO'
    assert creados[0].datos['categoria'] == 'documental'
    assert creados[0].estado == 'pendiente'


def test_la_propuesta_no_escribe_en_el_catalogo(usuario_tramitador, app, tarea_analizar_seed):
    """El punto de la frontera con #440: es un aviso, no un alta."""
    expediente_id, tarea_id = tarea_analizar_seed
    usuario_tramitador.post(_url(expediente_id, tarea_id), json={
        'texto': f'Requerimiento propuesto ({MARCA})',
        'categoria': 'tecnica',
    })

    with app.app_context():
        assert CatalogoRequerimiento.query.filter(
            CatalogoRequerimiento.texto.like(f'%{MARCA}%')
        ).count() == 0


def test_administrativo_puede_proponer(usuario_administrativo, app, tarea_analizar_seed):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_administrativo.post(_url(expediente_id, tarea_id), json={
        'texto': f'Propuesta del administrativo ({MARCA})',
        'categoria': 'administrativa',
    })
    assert r.status_code == 200
    assert len(_mensajes(app)) == 1


# ---------------------------------------------------------------------------
# Validación del payload — la hace el registro de tipos del servicio
# ---------------------------------------------------------------------------

def test_categoria_invalida_rechazada(usuario_tramitador, app, tarea_analizar_seed):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_tramitador.post(_url(expediente_id, tarea_id), json={
        'texto': f'Texto válido ({MARCA})',
        'categoria': 'inventada',
    })
    assert r.status_code == 422
    assert _mensajes(app) == []


def test_texto_vacio_rechazado(usuario_tramitador, app, tarea_analizar_seed):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_tramitador.post(_url(expediente_id, tarea_id), json={
        'texto': '   ',
        'categoria': 'documental',
    })
    assert r.status_code == 422


def test_tarea_inexistente_da_404(usuario_tramitador, tarea_analizar_seed):
    expediente_id, _ = tarea_analizar_seed
    r = usuario_tramitador.post(_url(expediente_id, 99999999), json={
        'texto': f'Texto ({MARCA})', 'categoria': 'documental',
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Regresión de #684 — la vía directa sigue cerrada
# ---------------------------------------------------------------------------

def test_alta_directa_sigue_prohibida_al_tramitador(usuario_tramitador, tarea_analizar_seed):
    expediente_id, tarea_id = tarea_analizar_seed
    r = usuario_tramitador.post(
        f'/api/expedientes/{expediente_id}/nodo/tarea/{tarea_id}/requerimientos/catalogo',
        json={'texto': f'Alta directa no autorizada ({MARCA})', 'categoria': 'documental'},
    )
    assert r.status_code == 403
