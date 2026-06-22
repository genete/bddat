"""Permisos del ADMINISTRATIVO sobre el árbol del expediente (#501, ADR-017 §6).

Frontera hoja / estructura:
  - gestionar_tareas        → incluye ADMINISTRATIVO (completar tareas previstas).
  - gestionar_estructura_*  → NO incluye ADMINISTRATIVO (crear fases/trámites/solicitudes).
  - subir al pool           → sin limitación de rol (ADR-027).

Control de acceso: verificar_acceso_expediente devuelve redirect (truthy) si falla
el permiso; api_bc lo traduce a 403 JSON. Las rutas del pool devuelven ese redirect
directamente (302). Por eso las aserciones distinguen 302/403 (bloqueo) del resto.
"""
import pytest

from app.utils.permisos import PERMISOS


# ---------------------------------------------------------------------------
# Definición del dict PERMISOS (sin BD)
# ---------------------------------------------------------------------------

def test_gestionar_tareas_incluye_administrativo():
    assert 'ADMINISTRATIVO' in PERMISOS['gestionar_tareas']


def test_gestionar_estructura_excluye_administrativo():
    assert 'ADMINISTRATIVO' not in PERMISOS['gestionar_estructura_expediente']
    # Pero sí el tramitador (que "tramita" por definición).
    assert 'TRAMITADOR' in PERMISOS['gestionar_estructura_expediente']


# ---------------------------------------------------------------------------
# Efecto real en los endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def solicitud_id(app):
    with app.app_context():
        from app.models.solicitudes import Solicitud
        s = Solicitud.query.first()
        if s is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        return s.id


@pytest.fixture
def tramite_id(app):
    with app.app_context():
        from app.models.tramites import Tramite
        t = Tramite.query.first()
        if t is None:
            pytest.skip('No hay trámites en la BD de desarrollo')
        return t.id


def test_administrativo_no_puede_crear_fase(usuario_administrativo, solicitud_id):
    """Estructura: crear fase está vedado al ADMINISTRATIVO → 403."""
    r = usuario_administrativo.post(f'/api/bc/solicitud/{solicitud_id}/fases/nueva',
                                    data={'tipo_fase_id': '1'})
    assert r.status_code == 403, f'ADMINISTRATIVO no debería crear fases (status {r.status_code})'


def test_administrativo_puede_actuar_sobre_tarea(usuario_administrativo, tramite_id):
    """Hoja: el permiso de tarea pasa para ADMINISTRATIVO.

    Sin tipo_tarea_id el endpoint responde 400 (validación), pero NUNCA 403: eso
    confirma que el guard de permiso (gestionar_tareas) dejó pasar al admin.
    """
    r = usuario_administrativo.post(f'/api/bc/tramite/{tramite_id}/tareas/nueva', data={})
    assert r.status_code != 403, 'El permiso gestionar_tareas debería incluir al ADMINISTRATIVO'


def test_administrativo_puede_subir_al_pool(usuario_administrativo, expediente_seed):
    """Pool: registrar una URL externa no edita el expediente → sin bloqueo de rol.

    El permiso 'subir_documento' (acceder_expediente) deja pasar al admin; lo que
    venga después (validación/registro) no es 302/403 de permiso.
    """
    r = usuario_administrativo.post(
        f'/expedientes/{expediente_seed}/documentos/url-externa',
        json={'url': 'https://www.boe.es/test-501', 'tipo_doc_id': 1},
    )
    assert r.status_code not in (302, 403), (
        f'El ADMINISTRATIVO debería poder registrar en el pool (status {r.status_code})'
    )


_NODO_INEXISTENTE = 999999999


def test_admin_puede_editar_tarea_en_arbol(usuario_administrativo, expediente_seed):
    """Endpoint REAL del árbol (api_expedientes): editar una TAREA pasa el permiso.

    Se usa un nodo inexistente para no mutar datos: si el permiso pasa, el endpoint
    llega a resolver el nodo y devuelve 404 (no 403/405). Eso prueba gestionar_tareas.
    """
    r = usuario_administrativo.patch(
        f'/api/expedientes/{expediente_seed}/nodo/tarea/{_NODO_INEXISTENTE}',
        json={'notas': 'x'},
    )
    assert r.status_code not in (403, 405), (
        f'El ADMINISTRATIVO debería poder editar tareas en el árbol (status {r.status_code})'
    )


def test_admin_no_puede_editar_estructura_en_arbol(usuario_administrativo, expediente_seed):
    """Editar una FASE (estructura) está vedado al ADMINISTRATIVO → 403 JSON (no redirect)."""
    r = usuario_administrativo.patch(
        f'/api/expedientes/{expediente_seed}/nodo/fase/{_NODO_INEXISTENTE}',
        json={'observaciones': 'x'},
    )
    assert r.status_code == 403, f'Editar estructura no debería permitirse al admin (status {r.status_code})'
    assert r.is_json, 'La denegación debe ser 403 JSON, no un redirect (evita el 405 al seguirlo)'


def test_admin_no_puede_crear_fase_en_arbol(usuario_administrativo, expediente_seed):
    """Crear hijo bajo una SOLICITUD (=fase, estructura) vedado al admin → 403."""
    r = usuario_administrativo.post(
        f'/api/expedientes/{expediente_seed}/nodo/solicitud/{_NODO_INEXISTENTE}/hijos',
        json={'tipo_id': 1},
    )
    assert r.status_code == 403


def test_tramitador_sigue_pudiendo_crear_fase(usuario_tramitador, solicitud_id):
    """Control de no-regresión: el TRAMITADOR conserva la gestión de estructura.

    Sin tipo_fase_id válido puede dar 400/404/422, pero nunca 403 de permiso.
    """
    r = usuario_tramitador.post(f'/api/bc/solicitud/{solicitud_id}/fases/nueva', data={})
    assert r.status_code != 403, 'El TRAMITADOR debe conservar gestionar_estructura_expediente'
