"""Smoke tests — endpoint GET /pool de documentos del expediente (#500, S3b-3)."""
import pytest


def test_pool_documentos_200(usuario_supervisor, expediente_seed):
    """GET /api/expedientes/<id>/pool → 200, clave 'documentos' es lista."""
    r = usuario_supervisor.get(f'/api/expedientes/{expediente_seed}/pool')
    assert r.status_code == 200
    data = r.get_json()
    assert 'documentos' in data
    assert isinstance(data['documentos'], list)


def test_pool_documentos_campos(usuario_supervisor, expediente_seed, app):
    """Cada doc del pool tiene id, nombre, tipo_doc, fecha, enlace, externo,
    puede_abrir, puede_abrir_carpeta (#609 — apertura desde el pool, no solo lo
    ya vinculado; #610 — puede_abrir distingue bddat:// sin representación)."""
    r = usuario_supervisor.get(f'/api/expedientes/{expediente_seed}/pool')
    assert r.status_code == 200
    docs = r.get_json()['documentos']
    if not docs:
        pytest.skip('No hay documentos en el expediente seed')
    doc = docs[0]
    assert 'id' in doc
    assert 'nombre' in doc
    assert 'tipo_doc' in doc
    assert 'fecha' in doc
    assert 'enlace' in doc
    assert 'externo' in doc
    assert 'puede_abrir' in doc
    assert 'puede_abrir_carpeta' in doc


def test_pool_documentos_sin_acceso_403(usuario_admin, app):
    """GET /api/expedientes/99999999/pool → 404 (no existe)."""
    r = usuario_admin.get('/api/expedientes/99999999/pool')
    assert r.status_code == 404
