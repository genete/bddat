"""Smoke test — vista del certificado de cumplimiento de la fase (#947).

Fragmento para el modal grande (ADR-023 §6), como el del diagnóstico: no lleva
`app-main`, así que se comprueba el botón de cierre del modal.

La BD de tests no trae ninguna fase finalizadora en la semilla: se fabrica una en
el propio test (`arbol_aislado`, sobre el SAVEPOINT de `app_ctx`). La petición del
cliente reutiliza ese contexto de aplicación —Flask no abre otro si ya hay uno de
la misma app— y con él la sesión del test, así que ve la fase sin que salga de la
transacción.
"""


def test_vista_cert_cumplimiento_fase_render(app_ctx, arbol_aislado, usuario_supervisor):
    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)

    r = usuario_supervisor.get(
        f'/expedientes/{solicitud.expediente_id}/fases/{fase.id}/certificado-cumplimiento')

    assert r.status_code == 200
    assert b'data-modal-large-close' in r.data
    assert 'No consta la notificación al titular'.encode() in r.data


def test_vista_cert_cumplimiento_fase_no_finalizadora_404(
        app_ctx, arbol_aislado, usuario_supervisor):
    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)

    r = usuario_supervisor.get(
        f'/expedientes/{solicitud.expediente_id}/fases/{fase.id}/certificado-cumplimiento')

    assert r.status_code == 404
