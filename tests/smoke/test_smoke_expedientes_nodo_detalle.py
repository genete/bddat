"""Smoke test — detalle lazy de nodo del árbol (/api/expedientes/<id>/nodo/<tipo>/<id>, #500)."""


def test_nodo_detalle_expediente(usuario_supervisor, expediente_seed):
    # La raíz siempre existe: pedir su detalle no depende de que haya solicitudes.
    r = usuario_supervisor.get(
        f'/api/expedientes/{expediente_seed}/nodo/expediente/{expediente_seed}')
    assert r.status_code == 200
    data = r.get_json()
    assert data['nodo'] == {'tipo': 'expediente', 'id': expediente_seed}
    assert isinstance(data['campos'], list)
    assert isinstance(data['documentos'], list)
    assert data['referencia'].startswith('AT-')


def test_nodo_detalle_404_si_no_pertenece(usuario_supervisor, expediente_seed):
    # Un id de solicitud absurdo no pertenece al expediente → 404.
    r = usuario_supervisor.get(
        f'/api/expedientes/{expediente_seed}/nodo/solicitud/99999999')
    assert r.status_code == 404
