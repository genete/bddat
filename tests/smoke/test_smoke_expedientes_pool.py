"""Smoke test — pool de documentos del expediente (/expedientes/<id>/documentos)."""


def test_expediente_pool_render(usuario_supervisor, expediente_seed):
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/documentos', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_pool_documento_fragmento_render(usuario_supervisor, expediente_seed, app):
    """GET /expedientes/<id>/documentos/<doc_id>/fragmento → el inspector del documento (#881)."""
    from app.models.documentos import Documento
    with app.app_context():
        doc = Documento.query.filter_by(expediente_id=expediente_seed).order_by(Documento.id).first()
        assert doc is not None, 'la semilla debe traer documentos en el expediente de prueba'
        doc_id = doc.id
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/documentos/{doc_id}/fragmento')
    assert r.status_code == 200
    assert b'data-inspector-frame="ver"' in r.data
