import itertools

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
from app import create_app, db as _db


# Tope de tests que pueden autodesactivarse en una pasada completa (#849).
#
# Un skip no se distingue de un test que pasa cuando solo se mira el resultado
# global: por eso 174 `pytest.skip` repartidos por 52 ficheros podían saltar sin
# que nadie lo supiera. Este tope hace visible la deuda — si sube, la suite
# falla y hay que mirar por qué.
#
# El número SOLO BAJA. Subirlo es aceptar que algo dejó de probarse, y eso se
# decide a propósito, no de pasada. Bajarlo al cerrar cada tanda es lo que
# convierte esto en un trinquete.
#
#   2026-09-05  50  línea base medida antes de tocar nada
#   2026-09-05  19  tras desclavar _login_as de CLG (-21) y revivir test_348 (-10)
#   2026-09-05   4  #428: los tests que buscaban «una tarea sin X» se la fabrican
#   2026-09-05   3  #428: el alta de verificación deja un expediente sin asignar
#   2026-09-06   0  #849.B: la suite corre contra su propia base, sembrada
#
# Cero, y esa es la cifra que hay que defender. Con la base de tests la sembramos
# nosotros: si falta un dato, es un defecto de la semilla y el test tiene que
# decirlo fallando. El único skip legítimo que queda por delante es el de una
# dependencia opcional del entorno (`importorskip`), no el de un dato ausente.
UMBRAL_SKIPS = 0


def pytest_sessionfinish(session, exitstatus):
    """Falla la sesión si los skips superan el tope acordado (#849)."""
    reporter = session.config.pluginmanager.get_plugin('terminalreporter')
    if reporter is None:
        return
    n_skips = len(reporter.stats.get('skipped', []))
    if n_skips <= UMBRAL_SKIPS:
        return
    reporter.write_line('')
    reporter.write_line(
        f'#849 — {n_skips} tests saltados, por encima del tope de {UMBRAL_SKIPS}.',
        red=True, bold=True)
    reporter.write_line(
        '        Un skip por falta de datos es un hueco de cobertura, no un aprobado: '
        'mira el detalle con `pytest -rs`.')
    session.exitstatus = 1


@pytest.fixture(scope='session')
def app():
    """La suite corre contra su propia base de datos (#849).

    `TestingConfig`: base construida desde las migraciones y sembrada por
    `scripts/preparar_bd_test.py`, raíz de ficheros propia, reloj real. Nada de
    esto depende del estado de una máquina concreta, que es lo que este issue
    vino a arreglar.

    Si al arrancar la suite falta la base o le falta la semilla, la salida lo
    dice enseguida —los tests fallan por dato ausente, no se saltan—. Se
    reconstruye con:

        venv/Scripts/python.exe scripts/preparar_bd_test.py --recrear

    `comprobar_aislamiento()` (app/config.py) impide que esto acabe apuntando a
    la base de desarrollo por un despiste en el `.env`.
    """
    return create_app('testing')


@pytest.fixture(scope='function')
def app_ctx(app):
    """Contexto de aplicación con rollback automático al terminar.

    Aísla los tests en un SAVEPOINT: aunque el código de aplicación llame a
    db.session.commit() (p. ej. mutaciones_arbol.crear_fase), join_transaction_mode
    'create_savepoint' reabre el SAVEPOINT tras cada commit/rollback de la sesión,
    de forma que nada sale de la transacción externa.

    OJO: no basta con _db.session.configure(bind=connection, ...) — la Session
    custom de Flask-SQLAlchemy (flask_sqlalchemy.session.Session.get_bind) resuelve
    el bind de CUALQUIER modelo mapeado por su bind_key en _db.engines, ANTES de
    mirar self.bind, así que ignora silenciosamente el bind que le configuremos y
    los commits del código de aplicación llegaban a la BD real de desarrollo (#641).
    Por eso aquí se sustituye _db.session por una scoped_session de SQLAlchemy
    "vainilla" (sin ese override), la única forma de que el bind=connection se respete.
    """
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session_original = _db.session
        _db.session = scoped_session(
            sessionmaker(bind=connection, join_transaction_mode='create_savepoint')
        )
        yield app
        _db.session.remove()
        _db.session = session_original
        transaction.rollback()
        connection.close()


@pytest.fixture(scope='function')
def client(app):
    """Flask test client — sin contexto de BD gestionado."""
    with app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Fixtures de autenticación por rol (#503 — smoke tests ADR-019)
# ---------------------------------------------------------------------------

def _login_as(client, app, rol_nombre):
    """
    Autentica el cliente de test usando session_transaction: fija _user_id
    y rol_activo_nombre directamente en la sesión sin simular el formulario.
    Devuelve True si algún usuario de la BD tiene ese rol, False si no.

    Busca el primer usuario ACTIVO con el rol pedido, en vez de exigir unas
    siglas concretas (#849). Clavarlo a 'CLG' hacía que TODO test con
    `usuario_admin` se autodesactivara en silencio —CLG tiene SUPERVISOR,
    TRAMITADOR y ADMINISTRATIVO, pero no ADMIN—, dejando sin cobertura efectiva
    las pantallas de administración. El orden por id es lo que mantiene a CLG
    como usuario de los otros tres roles: es quien los tiene con id más bajo.
    """
    with app.app_context():
        from app.models.usuarios import Rol, Usuario
        u = (Usuario.query
             .join(Usuario.roles)
             .filter(Rol.nombre == rol_nombre, Usuario.activo.is_(True))
             .order_by(Usuario.id)
             .first())
        if u is None:
            return False
        rol = next(r for r in u.roles if r.nombre == rol_nombre)
        uid, rol_id, rol_nombre_db = str(u.id), rol.id, rol.nombre

    with client.session_transaction() as sess:
        sess['_user_id'] = uid
        sess['_fresh'] = True
        sess['rol_activo_id'] = rol_id
        sess['rol_activo_nombre'] = rol_nombre_db
    return True


def id_usuario_autenticado(client):
    """El usuario que autenticó una fixture `usuario_*`, leído de su sesión.

    La alternativa a `Usuario.query.filter_by(siglas='CLG')` en un test que solo
    necesita saber quién es el usuario del cliente (#849): las siglas dependen
    de la base —desarrollo tiene CLG, la de tests tiene los siete de
    `scripts/semilla_test.py`— y clavarlas convierte el test en un skip.
    """
    with client.session_transaction() as sess:
        uid = sess.get('_user_id')
    assert uid is not None, 'el cliente no está autenticado: usa una fixture usuario_*'
    return int(uid)


@pytest.fixture
def usuario_admin(client, app):
    """Cliente autenticado con rol ADMIN."""
    if not _login_as(client, app, 'ADMIN'):
        pytest.skip('Ningún usuario activo con rol ADMIN en esta BD')
    return client


@pytest.fixture
def usuario_supervisor(client, app):
    """Cliente autenticado con rol SUPERVISOR."""
    if not _login_as(client, app, 'SUPERVISOR'):
        pytest.skip('Ningún usuario activo con rol SUPERVISOR en esta BD')
    return client


@pytest.fixture
def usuario_tramitador(client, app):
    """Cliente autenticado con rol TRAMITADOR."""
    if not _login_as(client, app, 'TRAMITADOR'):
        pytest.skip('Ningún usuario activo con rol TRAMITADOR en esta BD')
    return client


@pytest.fixture
def usuario_administrativo(client, app):
    """Cliente autenticado con rol ADMINISTRATIVO."""
    if not _login_as(client, app, 'ADMINISTRATIVO'):
        pytest.skip('Ningún usuario activo con rol ADMINISTRATIVO en esta BD')
    return client


# Las fixtures `*_seed` van todas con ORDER BY explícito, por lo mismo que
# `primer_usuario_id` (#849, #836): un `first()` a secas devuelve la primera tupla
# FÍSICA, y esa se mueve con cada UPDATE de la tabla. Basta con que un test asigne
# un responsable y lo revierta para que la pasada siguiente vea otro expediente —
# la intermitencia que hizo indiagnosticable #832. Detectado de nuevo en #428, al
# aparecer un expediente sin responsable que sí encuentra el test de asignación
# masiva: dos pasadas seguidas daban 7 y 3 skips.


@pytest.fixture
def expediente_seed(app):
    """ID del primer expediente en la BD de desarrollo. Skip si no existe ninguno."""
    with app.app_context():
        from app.models.expedientes import Expediente
        exp = Expediente.query.order_by(Expediente.id).first()
        if exp is None:
            pytest.skip('No hay expedientes en la BD de desarrollo')
        return exp.id


@pytest.fixture
def entidad_seed(app):
    """ID de la primera entidad en la BD de desarrollo. Skip si no existe ninguna."""
    with app.app_context():
        from app.models.entidad import Entidad
        e = Entidad.query.order_by(Entidad.id).first()
        if e is None:
            pytest.skip('No hay entidades en la BD de desarrollo')
        return e.id


@pytest.fixture
def plantilla_seed(app):
    """ID de la primera plantilla en la BD de desarrollo. Skip si no existe ninguna."""
    with app.app_context():
        from app.models.plantillas import Plantilla
        p = Plantilla.query.order_by(Plantilla.id).first()
        if p is None:
            pytest.skip('No hay plantillas en la BD de desarrollo')
        return p.id


@pytest.fixture
def primer_usuario_id(app):
    """ID del primer usuario en la BD de desarrollo. Skip si no existe ninguno.

    Con ORDER BY explícito (#849): un `first()` a secas devuelve la primera
    tupla FÍSICA, que se mueve con cada UPDATE de la tabla —el mecanismo que
    hizo indiagnosticable #832 y que #836 documenta—. Sin orden, esta fixture
    apunta a un usuario distinto según la pasada.
    """
    with app.app_context():
        from app.models.usuarios import Usuario
        u = Usuario.query.order_by(Usuario.id).first()
        if u is None:
            pytest.skip('No hay usuarios en la BD de desarrollo')
        return u.id


@pytest.fixture
def diagnostico_seed(app):
    """(expediente_id, documento_id) del primer Diagnostico en la BD de desarrollo.

    Skip si no existe ninguno (#629 — fragmento modal de diagnóstico).
    """
    with app.app_context():
        from app.models.diagnosticos import Diagnostico
        diag = Diagnostico.query.order_by(Diagnostico.id).first()
        if diag is None:
            pytest.skip('No hay diagnósticos en la BD de desarrollo')
        return diag.documento.expediente_id, diag.documento_id


@pytest.fixture
def fs_tmp(app, tmp_path):
    """Redirige FILESYSTEM_BASE a un directorio temporal (#674).

    app_ctx revierte la BD por SAVEPOINT, pero el filesystem no es
    transaccional — cualquier test que genere un documento/certificado real
    dentro de una transacción que luego revierte deja el fichero físico
    huérfano en el servidor de ficheros de desarrollo real
    (FILESYSTEM_BASE=D:/BDDAT/docs_prueba en .env). Usar en cualquier test
    que cree un Expediente/Documento con esquema local y pueda disparar
    escritura a disco (certificados, escritos, pool).
    """
    base_original = app.config.get('FILESYSTEM_BASE')
    app.config['FILESYSTEM_BASE'] = str(tmp_path)
    yield tmp_path
    app.config['FILESYSTEM_BASE'] = base_original


# ---------------------------------------------------------------------------
# Fábrica de expedientes propios (#428) — la alternativa a buscar en la base
# ---------------------------------------------------------------------------

_SECUENCIA_PRUEBA = itertools.count(1)

CONTENIDO_SOLICITUD_PRUEBA = b'%PDF-1.4 escrito de solicitud fabricado por la suite'


def _catalogo_para_alta():
    """Las filas de catálogo que necesita un alta, por clave natural.

    Con `assert` y no con `pytest.skip`: el catálogo lo siembran las migraciones,
    en desarrollo y en la base de tests por igual, así que su ausencia es un
    defecto de la semilla y el test debe decirlo fallando (#849, criterio 6).
    """
    from app.models.municipios import Municipio
    from app.models.tipos_expedientes import TipoExpediente
    from app.models.tipos_solicitudes import TipoSolicitud

    tipo_exp = TipoExpediente.query.order_by(TipoExpediente.id).first()
    assert tipo_exp is not None, 'la semilla debe traer algún TipoExpediente'

    tipo_sol = TipoSolicitud.query.filter_by(siglas='AAP').first()
    assert tipo_sol is not None, "la semilla debe traer el TipoSolicitud 'AAP'"

    municipio = Municipio.query.order_by(Municipio.id).first()
    assert municipio is not None, 'la semilla debe traer municipios'

    return tipo_exp, tipo_sol, municipio


def crear_expediente_de_prueba(*, documento='normal', fecha_registro=None):
    """Expediente completo fabricado por el test, por la vía real (#428).

    Pasa por `alta_expediente()` y no por INSERT sueltos, que es lo que garantiza
    que lo fabricado se parezca a lo que produce la aplicación: solicitud anclada a
    su documento, fila TITULAR con acreditativo y plazo que arranca. Un test que
    monte el árbol a mano se queda probando contra un estado que el sistema ya no
    sabe producir.

    Requiere `app_ctx` (la transacción que lo revierte) y `fs_tmp` (el alta escribe
    un fichero real; el disco no revierte solo).

    `documento=None` o un `DocumentoSolicitud` propio permiten ejercitar el rechazo
    y los casos de fecha. Las fechas salen de `reloj_simulado.hoy()` y nunca de
    `date.today()`: bajo `app_ctx` el validador de #824 compara contra el reloj de
    desarrollo, y una fecha de hoy real le resulta futura si el reloj quedó
    atrasado.
    """
    from datetime import timedelta

    from app import db as _db_app
    from app.models.entidad import Entidad
    from app.services.alta_expediente import (
        DatosAlta, DocumentoSolicitud, alta_expediente,
    )
    from app.services.reloj_simulado import hoy

    n = next(_SECUENCIA_PRUEBA)
    tipo_exp, tipo_sol, municipio = _catalogo_para_alta()

    entidad = Entidad(
        nombre_completo=f'Titular de prueba {n}, S.L.',
        nif=f'B{n:08d}',
        rol_titular=True,
        rol_consultado=False,
        rol_publicador=False,
        activo=True,
    )
    _db_app.session.add(entidad)
    _db_app.session.flush()

    if documento == 'normal':
        documento = DocumentoSolicitud(
            contenido=CONTENIDO_SOLICITUD_PRUEBA,
            nombre_original=f'solicitud_prueba_{n}.pdf',
            fecha_registro=fecha_registro or hoy(),
        )

    return alta_expediente(DatosAlta(
        tipo_expediente_id=tipo_exp.id,
        responsable_id=None,
        heredado=False,
        titulo=f'Proyecto de prueba {n}',
        descripcion='Expediente fabricado por la suite.',
        finalidad='Distribución de energía eléctrica',
        emplazamiento='T.M. de prueba',
        fecha_proyecto=hoy() - timedelta(days=30),
        ia_id=None,
        municipios_ids=[municipio.id],
        titular_id=entidad.id,
        tipo_solicitud_id=tipo_sol.id,
        solicitante_id=entidad.id,
        observaciones=f'[TEST] expediente de prueba {n}',
        documento=documento,
    ))


def documento_ancla_de_prueba(expediente_id, *, fecha=None):
    """Documento mínimo que sirve de ancla a una `Solicitud` de test (#428).

    Desde que `solicitudes.documento_solicitud_id` es NOT NULL, ningún test puede
    construir una `Solicitud` a mano sin darle su escrito. Este es el atajo para
    los que solo necesitan que la fila exista y les da igual el documento —los que
    prueban el alta de verdad usan `crear_expediente_de_prueba()`—.

    Con esquema `bddat://` a propósito: no toca el disco, así que quien lo use no
    necesita `fs_tmp`. La fecha sale del reloj del sistema porque el modelo rechaza
    las futuras (#824), y sin fecha el ancla no serviría para computar plazos.
    """
    from app import db as _db_app
    from app.models.documentos import Documento
    from app.models.tipos_documentos import TipoDocumento
    from app.services.reloj_simulado import hoy

    tipo = TipoDocumento.query.filter_by(codigo='MODELO_SOLICITUD').first()
    assert tipo is not None, "la semilla debe traer el TipoDocumento 'MODELO_SOLICITUD'"

    doc = Documento(
        expediente_id=expediente_id,
        url=f'bddat://test-ancla/{next(_SECUENCIA_PRUEBA)}',
        tipo_doc_id=tipo.id,
        fecha_administrativa=fecha or hoy(),
        asunto='Escrito de solicitud (test)',
    )
    _db_app.session.add(doc)
    _db_app.session.flush()
    return doc


@pytest.fixture
def alta_propia(app_ctx, fs_tmp):
    """Un expediente recién fabricado, con su solicitud anclada. Se revierte al salir."""
    return crear_expediente_de_prueba()


@pytest.fixture
def tramitador_usuario_id(app):
    """ID del primer usuario activo con rol TRAMITADOR. Skip si no existe ninguno."""
    with app.app_context():
        from app.models.usuarios import Usuario, Rol
        u = Usuario.query.filter_by(activo=True).join(Usuario.roles).filter(
            Rol.nombre == 'TRAMITADOR'
        ).order_by(Usuario.id).first()
        if u is None:
            pytest.skip('No hay usuarios con rol TRAMITADOR en la BD de desarrollo')
        return u.id


# ---------------------------------------------------------------------------
# Árbol ESFTT mínimo reutilizable (#715)
# ---------------------------------------------------------------------------

class ArbolESFTT:
    """Builder de árbol ESFTT mínimo para tests de invariantes contra SQL real.

    Monta solo los niveles que cada test necesita (fase/trámite/tarea/
    documento/vínculo/notificación), siempre bajo `app_ctx`: la sesión con
    SAVEPOINT revierte todo al terminar el test, igual que ya hacía
    `_montar_fase` en test_711_cierre_fase_cadena.py (de donde se extrae este
    builder para no duplicarlo en cada fichero de test — #715 checklist punto 1).

    Sin mocks: cada método hace un INSERT real y `flush()` para que las
    consultas de los checks (`app/services/invariantes_esftt.py`) vean las
    filas dentro de la misma transacción.
    """

    def __init__(self, db):
        self.db = db

    def _tipo(self, modelo, codigo):
        fila = modelo.query.filter_by(codigo=codigo).first()
        if fila is None:
            pytest.skip(f'{modelo.__name__} {codigo!r} no está en el catálogo de esta BD')
        return fila

    def solicitud_existente(self):
        """Primera solicitud de la BD de desarrollo. Puede tener hijos previos —
        usar `solicitud_nueva()` cuando el test necesite un árbol garantizado vacío."""
        from app.models.solicitudes import Solicitud
        s = Solicitud.query.first()
        if s is None:
            pytest.skip('No hay solicitudes en la BD de desarrollo')
        return s

    def solicitud_nueva(self):
        """Solicitud aislada, sin fases: para el caso 'sin hijos' de _check_borrar,
        donde reutilizar `solicitud_existente()` arriesga hijos previos ajenos al test."""
        from app.models.solicitudes import Solicitud
        from app.models.expedientes import Expediente
        from app.models.entidad import Entidad
        from app.models.tipos_solicitudes import TipoSolicitud
        exp = Expediente.query.first()
        ent = Entidad.query.first()
        tipo = TipoSolicitud.query.first()
        if exp is None or ent is None or tipo is None:
            pytest.skip('Faltan expediente/entidad/tipo_solicitud base en la BD de desarrollo')
        s = Solicitud(expediente_id=exp.id, entidad_id=ent.id, tipo_solicitud_id=tipo.id,
                      documento_solicitud_id=documento_ancla_de_prueba(exp.id).id)
        self.db.session.add(s)
        self.db.session.flush()
        return s

    def solicitud_propia(self):
        """Solicitud de un expediente que fabrica este mismo builder (#428).

        La alternativa sin skips a `solicitud_existente()`: en vez de pescar la
        primera solicitud de la base —que puede venir con fases, trámites y
        documentos de cualquier otro sitio— crea un expediente entero por la vía
        real y devuelve la suya, garantizada sin hijos.

        Necesita `fs_tmp` en el test, porque el alta escribe el documento de
        solicitud a disco. Usar la fixture `arbol_aislado`, que ya lo trae.
        """
        return crear_expediente_de_prueba().solicitud

    def tarea_propia(self, codigo_tarea, *, codigo_fase='ANALISIS_SOLICITUD',
                     codigo_tramite='ANALISIS_DOCUMENTAL'):
        """Tarea del tipo pedido, recién nacida y sin nada colgando.

        Atajo para el patrón que más `pytest.skip` provocaba en la suite: buscar
        «una tarea NOTIFICAR sin vínculos» o «una ANALIZAR sin documento
        producido». Fabricada no hay que buscarla, y además está garantizada
        limpia — la encontrada solo lo estaba mientras nadie tramitara ese
        expediente.
        """
        solicitud = self.solicitud_propia()
        fase = self.fase(codigo_fase, solicitud=solicitud)
        tramite = self.tramite(fase, codigo_tramite)
        return self.tarea(tramite, codigo_tarea)

    def fase(self, codigo_fase, solicitud=None):
        from app.models.fases import Fase
        from app.models.tipos_fases import TipoFase
        solicitud = solicitud or self.solicitud_existente()
        f = Fase(solicitud_id=solicitud.id, tipo_fase_id=self._tipo(TipoFase, codigo_fase).id)
        self.db.session.add(f)
        self.db.session.flush()
        return f

    def tramite(self, fase, codigo_tramite):
        from app.models.tramites import Tramite
        from app.models.tipos_tramites import TipoTramite
        t = Tramite(fase_id=fase.id, tipo_tramite_id=self._tipo(TipoTramite, codigo_tramite).id)
        self.db.session.add(t)
        self.db.session.flush()
        return t

    def tarea(self, tramite, codigo_tarea):
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea
        ta = Tarea(tramite_id=tramite.id, tipo_tarea_id=self._tipo(TipoTarea, codigo_tarea).id)
        self.db.session.add(ta)
        self.db.session.flush()
        return ta

    def documento(self, expediente_id, codigo_tipo_doc, sufijo, *, fecha=None):
        """Documento del pool. `fecha` es la administrativa: opcional para casi
        todos los tipos, obligatoria para DOC_PROYECTO desde #885 —es la que
        ordena las versiones del proyecto, y el modelo la exige al escribir."""
        from app.models.documentos import Documento
        from app.models.tipos_documentos import TipoDocumento
        doc = Documento(
            expediente_id=expediente_id,
            tipo_doc_id=self._tipo(TipoDocumento, codigo_tipo_doc).id,
            url=f'bddat://test-715/{sufijo}',
            fecha_administrativa=fecha,
        )
        self.db.session.add(doc)
        self.db.session.flush()
        return doc

    def vincular(self, tarea, documento, rol):
        from app.models.documentos_tarea import DocumentoTarea
        v = DocumentoTarea(tarea_id=tarea.id, documento_id=documento.id, rol=rol)
        self.db.session.add(v)
        self.db.session.flush()
        return v

    def notificacion(self, tarea, resultado=None, canal='NOTIFICA', fecha=None, numero_intento=None):
        from app.models.notificaciones import Notificacion
        import datetime
        kwargs = dict(
            tarea_id=tarea.id,
            resultado=resultado,
            canal=canal,
            fecha_puesta_disposicion=fecha or datetime.date.today(),
        )
        if numero_intento is not None:
            kwargs['numero_intento'] = numero_intento
        n = Notificacion(**kwargs)
        self.db.session.add(n)
        self.db.session.flush()
        return n

    def diagnostico(self, tarea, resultado, defectos=None):
        """Diagnóstico PRODUCIDO por `tarea` (ANALIZAR): Documento + Diagnostico + vínculo.

        Formaliza el patrón que test_714/test_717/test_724 duplicaban cada uno a mano
        con su propio `_montar_fase`/`_montar_cadena` (#752).
        """
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.diagnosticos import Diagnostico
        from app.models.tipos_documentos import TipoDocumento
        expediente_id = tarea.tramite.fase.solicitud.expediente_id
        doc = Documento(
            expediente_id=expediente_id,
            tipo_doc_id=self._tipo(TipoDocumento, 'DIAGNOSTICO').id,
            url=f'bddat://diagnosticos/test/{tarea.id}',
        )
        self.db.session.add(doc)
        self.db.session.flush()
        diag = Diagnostico(documento_id=doc.id, resultado=resultado, defectos=defectos or [])
        self.db.session.add(diag)
        self.db.session.add(DocumentoTarea(tarea_id=tarea.id, documento_id=doc.id, rol='PRODUCIDO'))
        self.db.session.flush()
        return diag

    def elaborar_producido(self, tramite):
        """Tarea ELABORAR de `tramite` con su Documento PRODUCIDO genérico, sin
        diagnóstico: el escrito redactado/firmado de una vuelta de subsanación (#724)."""
        from app.models.tareas import Tarea
        from app.models.tipos_tareas import TipoTarea
        from app.models.documentos import Documento
        from app.models.documentos_tarea import DocumentoTarea
        from app.models.tipos_documentos import TipoDocumento
        elaborar = Tarea(tramite_id=tramite.id, tipo_tarea_id=self._tipo(TipoTarea, 'ELABORAR').id)
        self.db.session.add(elaborar)
        self.db.session.flush()
        tipo_doc = TipoDocumento.query.first()
        if tipo_doc is None:
            pytest.skip('No hay tipos de documento en el catálogo de esta BD')
        doc = Documento(
            expediente_id=tramite.fase.solicitud.expediente_id,
            tipo_doc_id=tipo_doc.id,
            url=f'bddat://escritos/test/{elaborar.id}.odt',
        )
        self.db.session.add(doc)
        self.db.session.flush()
        self.db.session.add(DocumentoTarea(tarea_id=elaborar.id, documento_id=doc.id, rol='PRODUCIDO'))
        self.db.session.flush()
        return elaborar


@pytest.fixture
def arbol_esftt(app_ctx):
    """Builder `ArbolESFTT` listo para usar, sobre la transacción de `app_ctx`."""
    from app import db
    return ArbolESFTT(db)


@pytest.fixture
def arbol_aislado(app_ctx, fs_tmp):
    """`ArbolESFTT` con raíz de ficheros propia, para `solicitud_propia`/`tarea_propia`.

    Mismo builder que `arbol_esftt`; lo que añade es `fs_tmp`, que hace falta en
    cuanto el árbol nace de un alta real — el documento de solicitud se escribe a
    disco y el SAVEPOINT no lo revierte.
    """
    from app import db
    return ArbolESFTT(db)
