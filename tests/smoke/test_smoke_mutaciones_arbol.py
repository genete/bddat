"""Smoke tests — endpoints mutaciones árbol POST/PATCH/DELETE + GET editable (#500, S3b-0)."""
import pytest


def test_editable_expediente_campos_vacios(usuario_supervisor, expediente_seed):
    """GET /nodo/expediente/<id>/editable → 200, campos==[] (expediente no editable en v1)."""
    r = usuario_supervisor.get(
        f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/editable')
    assert r.status_code == 200
    data = r.get_json()
    assert data['nodo'] == {'tipo': 'expediente', 'id': expediente_seed}
    assert data['campos'] == []


def test_crear_hijo_tipo_inexistente_404(usuario_supervisor, expediente_seed):
    """POST /nodo/expediente/<id>/hijos con tipo_id inexistente → 404."""
    r = usuario_supervisor.post(
        f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}/hijos',
        json={'tipo_id': 99999999})
    assert r.status_code == 404


def test_editar_solicitud_idempotente_200(usuario_supervisor, app):
    """PATCH /nodo/solicitud/<id> reenviando su valor actual → 200, ok==True.

    Idempotente de verdad: el test corre contra la BD de desarrollo y la solicitud
    sale de `Solicitud.query.first()` (sin ORDER BY, cuál toca es indeterminado),
    así que nunca debe cambiar su estado. Enviar `observaciones: None` sí la vacía
    —es la forma de decir "vaciar"— y así vació las de tres solicitudes reales (#832).
    """
    with app.app_context():
        from app.models.solicitudes import Solicitud
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        exp_id, sol_id, observaciones = sol.expediente_id, sol.id, sol.observaciones

    r = usuario_supervisor.patch(
        f'/api/expedientes/{exp_id}/nodo/solicitud/{sol_id}',
        json={'observaciones': observaciones})
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('ok') is True


def test_editar_solicitud_sin_la_clave_no_vacia_observaciones(usuario_supervisor, app):
    """PATCH sin la clave `observaciones` conserva su valor (#832).

    Clave ausente ≠ clave con null: antes ambas llegaban al servicio como None y
    lo que el cliente no nombraba desaparecía.
    """
    from app import db
    from app.models.solicitudes import Solicitud

    with app.app_context():
        sol = Solicitud.query.first()
        if sol is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        exp_id, sol_id, previo = sol.expediente_id, sol.id, sol.observaciones
        sol.observaciones = 'Marcador de #832 — no debe desaparecer'
        db.session.commit()

    try:
        r = usuario_supervisor.patch(
            f'/api/expedientes/{exp_id}/nodo/solicitud/{sol_id}', json={})
        assert r.status_code == 200
        with app.app_context():
            assert Solicitud.query.get(sol_id).observaciones == \
                'Marcador de #832 — no debe desaparecer'
    finally:
        with app.app_context():
            Solicitud.query.get(sol_id).observaciones = previo
            db.session.commit()


def test_editar_tarea_sin_la_clave_conserva_los_consumidos(usuario_supervisor, app, monkeypatch):
    """PATCH sin `documentos_consumidos_ids` conserva los vínculos CONSUMIDO (#832).

    El más grave de la familia: `editar_tarea` diffea contra la lista recibida y
    libera a pool/ lo que sobre (ADR-032 §3), así que un cuerpo parcial no borraba
    un texto — desvinculaba documentos y con ellos el disparo del plazo. Es lo que
    obligó al script de #814 a releer y reponer los consumidos previos (#825).

    No escribe en BD: intercepta la llamada al servicio para inspeccionar con qué
    argumentos la habría hecho la ruta.
    """
    from app.models.tareas import Tarea
    from app.models.tramites import Tramite
    from app.models.fases import Fase
    from app.models.documentos_tarea import DocumentoTarea
    from app.services import mutaciones_arbol
    from app.services.mutaciones_arbol import ResultadoMutacion

    with app.app_context():
        # La tarea tiene que colgar de fase ABIERTA: bajo fase sellada el PATCH
        # muere en 422 dentro de `_resolver_nodo` y no llega a la ruta que se
        # está probando (#720, ADR-036 §6 — mismo criterio que #842).
        vinculo = (DocumentoTarea.query
                   .join(Tarea, DocumentoTarea.tarea_id == Tarea.id)
                   .join(Tramite, Tarea.tramite_id == Tramite.id)
                   .join(Fase, Tramite.fase_id == Fase.id)
                   .filter(DocumentoTarea.rol == 'CONSUMIDO',
                           Fase.documento_resultado_id.is_(None))
                   .first())
        if vinculo is None:
            pytest.skip('No hay ninguna tarea con documentos CONSUMIDO bajo fase abierta')
        tarea = Tarea.query.get(vinculo.tarea_id)
        exp_id = tarea.tramite.fase.solicitud.expediente_id
        tarea_id = tarea.id
        esperados = [d.id for d in tarea.documentos_consumidos]

    recibido = {}

    def _falso_editar_tarea(ta, **kwargs):
        recibido.update(kwargs)
        return ResultadoMutacion(ok=True)

    monkeypatch.setattr(mutaciones_arbol, 'editar_tarea', _falso_editar_tarea)

    r = usuario_supervisor.patch(
        f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_id}', json={})
    assert r.status_code == 200
    assert recibido['documentos_consumidos_ids'] == esperados


def test_borrar_solicitud_inexistente_404(usuario_supervisor, expediente_seed):
    """DELETE /nodo/solicitud/99999999 → 404 (solicitud no pertenece al expediente)."""
    r = usuario_supervisor.delete(
        f'/api/expedientes/{expediente_seed}/nodo/solicitud/99999999')
    assert r.status_code == 404


def test_bloqueo_422_surfacea_mensaje_invariante_y_motor(app):
    """El 422 de bloqueo debe surfacear el mensaje legible venga de donde venga (#500).

    La mensajería de bloqueos tiene DOS fuentes (ver EvaluacionResult):
      · motor de reglas   → `motivo`
      · invariantes ESFTT → `norma_compilada` (motivo queda '')
    `_bloqueo_422` surfacea `motivo or norma_compilada`. Sin el fallback, los
    bloqueos de invariante llegaban con motivo='' (regresión histórica).
    """
    from app.routes.api_expedientes import _bloqueo_422
    from app.services.motor_reglas import EvaluacionResult
    from app.services.mutaciones_arbol import ResultadoMutacion

    invariante = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='Mensaje del invariante', url_norma='')          # motivo='' por defecto
    motor = EvaluacionResult(
        permitido=False, nivel='BLOQUEAR', variables_trigger={},
        norma_compilada='norma compilada X', url_norma='', motivo='Motivo del motor')

    with app.app_context():
        resp_inv, status_inv = _bloqueo_422(ResultadoMutacion(ok=False, bloqueo=invariante))
        resp_mot, status_mot = _bloqueo_422(ResultadoMutacion(ok=False, bloqueo=motor))
        body_inv = resp_inv.get_json()
        body_mot = resp_mot.get_json()

    assert status_inv == 422 and status_mot == 422
    # invariante: el mensaje (en norma_compilada) NO debe perderse
    assert body_inv['motivo'] == 'Mensaje del invariante'
    # motor: el `motivo` editorial tiene prioridad sobre norma_compilada
    assert body_mot['motivo'] == 'Motivo del motor'
