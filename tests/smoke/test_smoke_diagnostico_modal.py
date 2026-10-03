"""Smoke test — fragmento modal de solo lectura del DIAGNOSTICO (#629)."""


def test_diagnostico_modal_render(usuario_supervisor, diagnostico_seed):
    """GET /expedientes/<id>/documentos/<doc_id>/diagnostico-modal → 200 con
    badge de resultado y botón de cierre del modal grande (ADR-023 §6)."""
    expediente_id, doc_id = diagnostico_seed
    r = usuario_supervisor.get(f'/expedientes/{expediente_id}/documentos/{doc_id}/diagnostico-modal')
    assert r.status_code == 200
    assert b'data-modal-large-close' in r.data


def test_diagnostico_modal_doc_no_es_diagnostico_404(usuario_supervisor, expediente_seed, app):
    """GET .../diagnostico-modal sobre un Documento sin Diagnostico asociado → 404."""
    with app.app_context():
        from app.models.documentos import Documento
        # Criterio explícito y ORDER BY (#836): con un first() a secas, el
        # documento elegido dependía del orden físico de las filas.
        doc = (Documento.query
               .filter(Documento.expediente_id == expediente_seed,
                       ~Documento.diagnostico.has())
               .order_by(Documento.id)
               .first())
        assert doc is not None, 'la semilla debe traer un documento sin diagnóstico'
        doc_id = doc.id
    r = usuario_supervisor.get(f'/expedientes/{expediente_seed}/documentos/{doc_id}/diagnostico-modal')
    assert r.status_code == 404
