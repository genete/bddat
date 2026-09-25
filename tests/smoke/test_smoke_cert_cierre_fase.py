"""Smoke test — vista del certificado de cierre de la fase finalizadora (#956).

Fragmento para el modal grande (ADR-023 §6), como el de cumplimiento (#947): no
lleva `app-main`, así que se comprueba el botón de cierre del modal. La fase se
fabrica en el propio test (`arbol_aislado`): la semilla no trae finalizadoras.
"""


def test_vista_cert_cierre_fase_render(app_ctx, arbol_aislado, usuario_supervisor):
    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('RESOLUCION', solicitud=solicitud)

    r = usuario_supervisor.get(
        f'/expedientes/{solicitud.expediente_id}/fases/{fase.id}/certificado-cierre')

    assert r.status_code == 200
    assert b'data-modal-large-close' in r.data
    assert 'La fase todavía no puede cerrarse'.encode() in r.data


def test_vista_cert_cierre_fase_no_finalizadora_404(app_ctx, arbol_aislado, usuario_supervisor):
    solicitud = arbol_aislado.solicitud_propia()
    fase = arbol_aislado.fase('ANALISIS_SOLICITUD', solicitud=solicitud)

    r = usuario_supervisor.get(
        f'/expedientes/{solicitud.expediente_id}/fases/{fase.id}/certificado-cierre')

    assert r.status_code == 404
