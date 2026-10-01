"""Smoke test — vista del certificado de cierre de la solicitud (#996).

Fragmento para el modal grande (ADR-023 §6), como los de la fase: no lleva
`app-main`, así que se comprueba el botón de cierre del modal. La solicitud se
fabrica en el propio test (`arbol_aislado`): recién dada de alta, sin fases, el
borrador dice que el cierre todavía no puede certificarse.
"""


def test_vista_cert_cierre_solicitud_render(app_ctx, arbol_aislado, usuario_supervisor):
    solicitud = arbol_aislado.solicitud_propia()

    r = usuario_supervisor.get(
        f'/expedientes/{solicitud.expediente_id}/solicitudes/{solicitud.id}'
        f'/certificado-cierre')

    assert r.status_code == 200
    assert b'data-modal-large-close' in r.data
    assert 'El cierre todavía no puede certificarse'.encode() in r.data
