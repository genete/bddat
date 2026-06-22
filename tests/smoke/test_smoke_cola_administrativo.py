"""Smoke de la cola de "Mi trabajo" del administrativo (#501, ADR-017 §2).

Verifica el contrato del endpoint contra la BD de desarrollo: forma de la respuesta
y de las filas. No asume que haya tareas pendientes (la cola puede salir vacía).
"""

_CLAVES_RESPUESTA = {'data', 'next_cursor', 'has_more'}
_CLAVES_FILA = {
    'tarea_id', 'expediente_id', 'num_at', 'titular', 'solicitud',
    'fase', 'tramite', 'tarea', 'pendiente', 'pendiente_codigo', 'plazo', 'tocado_por',
}
_TIPOS_TAREA_VALIDOS = {'NOTIFICAR', 'ELABORAR', 'ESPERAR_PLAZO'}


def test_cola_responde_contrato(usuario_administrativo):
    r = usuario_administrativo.get('/api/administrativo/cola?limit=20')
    assert r.status_code == 200
    payload = r.get_json()
    assert _CLAVES_RESPUESTA.issubset(payload.keys())
    assert isinstance(payload['data'], list)


def test_cola_filas_bien_formadas(usuario_administrativo):
    r = usuario_administrativo.get('/api/administrativo/cola?limit=20')
    payload = r.get_json()
    for fila in payload['data']:
        assert _CLAVES_FILA.issubset(fila.keys())
        # Solo tipos administrativos; nunca FIN; nunca ANALIZAR
        assert fila['tarea'] in _TIPOS_TAREA_VALIDOS
        assert fila['pendiente_codigo'] != 'FIN'
        assert fila['pendiente']  # texto no vacío


def test_cola_visible_para_tramitador(usuario_tramitador):
    """ADR-013: la cola es visible para todos los roles, no solo el administrativo."""
    r = usuario_tramitador.get('/api/administrativo/cola?limit=5')
    assert r.status_code == 200
