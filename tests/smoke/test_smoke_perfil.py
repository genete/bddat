"""Smoke test — perfil del usuario (/perfil/)."""


def test_perfil_render(usuario_supervisor):
    r = usuario_supervisor.get('/perfil/', follow_redirects=True)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data


def test_perfil_editar_parcial_no_borra_el_email(usuario_supervisor, app):
    """POST /perfil/editar sin la clave `email` conserva el email (#832).

    `usuarios.email` es nullable: antes, un cuerpo al que le faltara el campo
    dejaba al usuario sin email sin que nada avisara (nombre y apellido1, NOT NULL,
    al menos reventaban). El `finally` restaura por si el fix estuviera roto.
    """
    from app import db
    from app.models.usuarios import Usuario

    with app.app_context():
        u = Usuario.query.filter_by(siglas='CLG').first()
        uid, email_previo, apellido2_previo = u.id, u.email, u.apellido2
        nombre_actual = u.nombre

    try:
        # Cuerpo parcial: solo el nombre, con su valor actual. El resto calla.
        r = usuario_supervisor.post('/perfil/editar', data={'nombre': nombre_actual},
                                    follow_redirects=False)
        assert r.status_code == 302
        with app.app_context():
            u = Usuario.query.get(uid)
            assert u.email == email_previo
            assert u.apellido2 == apellido2_previo
    finally:
        with app.app_context():
            u = Usuario.query.get(uid)
            u.email, u.apellido2 = email_previo, apellido2_previo
            db.session.commit()
