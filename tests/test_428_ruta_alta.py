"""Tests #428 — la ruta del formulario de alta de expediente.

Los del servicio están en `test_428_alta_expediente.py`; aquí se prueba lo que
solo existe en la ruta: el parseo del multipart, la validación que acumula errores
y el repintado sin `redirect` —el defecto del wizard que este issue retiró—.

**Por qué estos no usan `app_ctx`.** El cliente HTTP abre su propio contexto de
aplicación por petición, con su propia sesión, así que no ve el SAVEPOINT y sus
commits llegan a la base de verdad (#836). El único test que llega a crear algo
limpia lo que creó; los demás terminan en rechazo y no persisten nada.

`fs_tmp` sí funciona con el cliente, porque redirige `app.config` sobre la misma
instancia de aplicación que atiende la petición: los ficheros del alta van al
directorio temporal y no al servidor de ficheros de desarrollo.
"""
import io

import pytest

RUTA = '/expedientes/nuevo/'
CONTENIDO = b'%PDF-1.4 escrito de solicitud de prueba de ruta'


def _catalogo(app):
    """Lo que el formulario necesita para un alta válida, por clave natural."""
    with app.app_context():
        from app.models.entidad import Entidad
        from app.models.municipios import Municipio
        from app.models.tipos_expedientes import TipoExpediente
        from app.models.tipos_solicitudes import TipoSolicitud

        tipo_exp = TipoExpediente.query.order_by(TipoExpediente.id).first()
        assert tipo_exp is not None, 'la semilla debe traer algún TipoExpediente'

        tipo_sol = TipoSolicitud.query.filter_by(siglas='AAP').first()
        assert tipo_sol is not None, "la semilla debe traer el TipoSolicitud 'AAP'"

        municipio = Municipio.query.order_by(Municipio.id).first()
        assert municipio is not None, 'la semilla debe traer municipios'

        titular = (Entidad.query
                   .filter_by(activo=True, rol_titular=True)
                   .order_by(Entidad.id).first())
        assert titular is not None, 'la semilla debe traer alguna entidad titular'

        return {
            'tipo_expediente_id': tipo_exp.id,
            'tipo_solicitud_id': tipo_sol.id,
            'municipio_id': municipio.id,
            'entidad_id': titular.id,
        }


def _hoy(app):
    """La fecha de trabajo del sistema — nunca `date.today()` (#824, reloj de #820)."""
    with app.app_context():
        from app.services.reloj_simulado import hoy
        return hoy()


def _formulario(app, cat, *, con_fichero=True, **cambios):
    """Cuerpo multipart de un alta válida, con lo que se quiera romper encima."""
    hoy = _hoy(app)
    datos = {
        'tipo_expediente_id': str(cat['tipo_expediente_id']),
        'responsable_id': '',
        'titulo': 'Proyecto de prueba de ruta #428',
        'descripcion': 'Alta enviada por la suite para probar la ruta.',
        'finalidad': 'Distribución de energía eléctrica',
        'emplazamiento': 'T.M. de prueba',
        'fecha': hoy.isoformat(),
        'ia_id': '',
        'municipios_ids[]': str(cat['municipio_id']),
        'entidad_id': str(cat['entidad_id']),
        'solicitante_id': str(cat['entidad_id']),
        'tipo_solicitud_id': str(cat['tipo_solicitud_id']),
        'observaciones': '[TEST #428 ruta]',
        'fecha_registro': hoy.isoformat(),
    }
    if con_fichero:
        datos['documento_solicitud'] = (io.BytesIO(CONTENIDO), 'solicitud_ruta.pdf')
    datos.update(cambios)
    return datos


def _borrar_expediente(app, numero_at):
    """Deshace un alta creada por el cliente HTTP, que no revierte sola.

    Mismo orden que `limpiar_reciclables.py`, y por la misma razón: el escrito de
    solicitud lo referencian dos tablas —la solicitud que ancla y el interesado
    TITULAR al que acredita— y solo la segunda se puede neutralizar con un UPDATE.
    """
    with app.app_context():
        from app import db
        from app.models.expedientes import Expediente

        exp = Expediente.query.filter_by(numero_at=numero_at).first()
        if exp is None:
            return
        eid, proyecto_id = exp.id, exp.proyecto_id
        p = {'eid': eid}

        db.session.execute(db.text(
            'UPDATE public.interesados_expediente SET documento_acreditativo_id = NULL '
            'WHERE expediente_id = :eid'), p)
        for sql in (
            'DELETE FROM public.historico_titulares_expediente WHERE expediente_id = :eid',
            'DELETE FROM public.interesados_expediente WHERE expediente_id = :eid',
            'DELETE FROM public.solicitudes WHERE expediente_id = :eid',
            'DELETE FROM public.documentos WHERE expediente_id = :eid',
            'DELETE FROM public.expedientes WHERE id = :eid',
        ):
            db.session.execute(db.text(sql), p)
        if proyecto_id:
            db.session.execute(db.text(
                'DELETE FROM public.municipios_proyecto WHERE proyecto_id = :pid'),
                {'pid': proyecto_id})
            db.session.execute(db.text(
                'DELETE FROM public.proyectos WHERE id = :pid'), {'pid': proyecto_id})

        # Devolver el número al contador. Sin esto cada pasada de la suite se come
        # un AT, y la base de desarrollo no queda como estaba (#849, criterio 5).
        # Condicionado a que siga siendo el último: si alguien pidió otro después,
        # bajarlo repetiría un número, que es justo lo que el contador evita.
        db.session.execute(db.text(
            'UPDATE public.contador_numero_at SET valor = valor - 1 WHERE valor = :n'),
            {'n': numero_at})
        db.session.commit()


# ---------------------------------------------------------------------------
# El formulario se pinta
# ---------------------------------------------------------------------------

def test_get_devuelve_el_formulario(usuario_supervisor):
    r = usuario_supervisor.get(RUTA)
    assert r.status_code == 200
    assert b'class="app-main"' in r.data
    # Las tres tarjetas del formulario único
    assert 'Proyecto técnico'.encode() in r.data
    assert 'Escrito de solicitud'.encode() in r.data


# ---------------------------------------------------------------------------
# Rechazos — ninguno persiste nada
# ---------------------------------------------------------------------------

class TestRechazos:

    def test_sin_fichero_no_crea_el_expediente(self, usuario_supervisor, app, fs_tmp):
        cat = _catalogo(app)
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, con_fichero=False),
            content_type='multipart/form-data')

        assert r.status_code == 422
        assert 'adjuntar el escrito de solicitud'.encode() in r.data

    def test_sin_fecha_de_registro_tampoco(self, usuario_supervisor, app, fs_tmp):
        cat = _catalogo(app)
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, fecha_registro=''),
            content_type='multipart/form-data')

        assert r.status_code == 422
        assert 'fecha de registro de entrada'.encode() in r.data

    def test_fecha_de_registro_futura_rechazada(self, usuario_supervisor, app, fs_tmp):
        """La valida el modelo (#824) y la ruta la repinta en vez de reventar."""
        from datetime import timedelta

        cat = _catalogo(app)
        futura = (_hoy(app) + timedelta(days=1)).isoformat()
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, fecha_registro=futura),
            content_type='multipart/form-data')

        assert r.status_code == 422
        assert 'no puede ser futura'.encode() in r.data

    def test_sin_municipios_no_crea_el_expediente(self, usuario_supervisor, app, fs_tmp):
        cat = _catalogo(app)
        datos = _formulario(app, cat)
        del datos['municipios_ids[]']
        r = usuario_supervisor.post(RUTA, data=datos, content_type='multipart/form-data')

        assert r.status_code == 422
        assert 'al menos un municipio'.encode() in r.data

    def test_el_rechazo_no_consume_numero_de_expediente(self, usuario_supervisor, app, fs_tmp):
        from app import db

        cat = _catalogo(app)
        with app.app_context():
            antes = db.session.execute(
                db.text('SELECT valor FROM public.contador_numero_at')).scalar()

        usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, con_fichero=False),
            content_type='multipart/form-data')

        with app.app_context():
            despues = db.session.execute(
                db.text('SELECT valor FROM public.contador_numero_at')).scalar()
        assert despues == antes


# ---------------------------------------------------------------------------
# Repintado — lo que el wizard hacía mal
# ---------------------------------------------------------------------------

class TestRepintado:
    """El paso 2 del wizard rebotaba con `redirect` y perdía los siete campos.

    Ahora se re-renderiza con lo escrito. Lo único que no puede volver es el
    fichero, y la plantilla lo dice en vez de fingir que sigue puesto.
    """

    def test_conserva_los_campos_de_texto(self, usuario_supervisor, app, fs_tmp):
        cat = _catalogo(app)
        r = usuario_supervisor.post(
            RUTA,
            data=_formulario(app, cat, con_fichero=False,
                             titulo='Un título que no se debe perder'),
            content_type='multipart/form-data')

        assert r.status_code == 422
        assert 'Un título que no se debe perder'.encode() in r.data
        assert 'Alta enviada por la suite para probar la ruta.'.encode() in r.data

    def test_conserva_el_municipio_elegido(self, usuario_supervisor, app, fs_tmp):
        """El formulario solo manda el id; la ruta resuelve el nombre para repintarlo."""
        with app.app_context():
            from app.models.municipios import Municipio
            municipio = Municipio.query.order_by(Municipio.id).first()
            assert municipio is not None, 'la semilla debe traer municipios'
            nombre = municipio.nombre

        cat = _catalogo(app)
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, con_fichero=False),
            content_type='multipart/form-data')

        assert r.status_code == 422
        assert nombre.encode() in r.data

    def test_avisa_de_que_hay_que_reseleccionar_el_fichero(self, usuario_supervisor, app, fs_tmp):
        cat = _catalogo(app)
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat, con_fichero=False),
            content_type='multipart/form-data')

        assert 'volver a seleccionar el escrito de solicitud'.encode() in r.data


# ---------------------------------------------------------------------------
# Camino feliz — el único que persiste, y limpia lo suyo
# ---------------------------------------------------------------------------

def test_alta_completa_crea_el_expediente_anclado(usuario_supervisor, app, fs_tmp):
    """Un solo alta para todo lo que hay que comprobar del camino feliz.

    No se parte en varios tests a propósito: el cliente HTTP commitea de verdad, así
    que cada alta consume un número de expediente y hay que devolverlo a mano. Uno
    basta para ver la fila, el ancla, el acreditativo, el plazo y el fichero.
    """
    import os

    from app import db

    cat = _catalogo(app)
    with app.app_context():
        siguiente = db.session.execute(
            db.text('SELECT valor + 1 FROM public.contador_numero_at')).scalar()

    try:
        r = usuario_supervisor.post(
            RUTA, data=_formulario(app, cat), content_type='multipart/form-data')

        assert r.status_code == 302
        assert '/expedientes/' in r.headers['Location']

        # El escrito acaba en AT-N/pool/, y en ningún otro sitio.
        pool = os.path.join(str(fs_tmp), f'AT-{siguiente}', 'pool')
        assert os.path.isdir(pool)
        assert len(os.listdir(pool)) == 1
        assert os.listdir(str(fs_tmp)) == [f'AT-{siguiente}']

        with app.app_context():
            from app.models.expedientes import Expediente
            from app.models.interesados_expediente import InteresadoExpediente
            from app.services.plazos import obtener_estado_plazo_solicitud

            exp = Expediente.query.filter_by(numero_at=siguiente).one()
            solicitud = exp.solicitudes[0]

            # Anclada, con su documento del tipo correcto…
            assert solicitud.documento_solicitud_id is not None
            assert solicitud.documento_solicitud.tipo_doc.codigo == 'MODELO_SOLICITUD'

            # …el titular acreditado por ese mismo documento…
            titular = InteresadoExpediente.query.filter_by(
                expediente_id=exp.id, tipo_origen='TITULAR').one()
            assert titular.documento_acreditativo_id == solicitud.documento_solicitud_id

            # …y el plazo corriendo, que es de lo que iba el issue.
            assert obtener_estado_plazo_solicitud(solicitud).estado != 'SIN_PLAZO'
    finally:
        _borrar_expediente(app, siguiente)


def test_la_suite_devuelve_el_numero_de_expediente_que_gasta(usuario_supervisor, app, fs_tmp):
    """El contador queda como estaba tras un alta completa y su limpieza.

    Es el criterio 5 de #849 —la base de desarrollo no cambia— aplicado al único
    recurso que el resto de tests no puede revertir con un rollback: el contador
    gapless, que el alta mueve con un UPDATE atómico ya confirmado.
    """
    from app import db

    with app.app_context():
        antes = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()

    cat = _catalogo(app)
    try:
        usuario_supervisor.post(
            RUTA, data=_formulario(app, cat), content_type='multipart/form-data')
    finally:
        _borrar_expediente(app, antes + 1)

    with app.app_context():
        despues = db.session.execute(
            db.text('SELECT valor FROM public.contador_numero_at')).scalar()
    assert despues == antes
