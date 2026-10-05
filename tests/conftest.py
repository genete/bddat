import contextlib
import itertools

import pytest
from flask import has_app_context
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


@contextlib.contextmanager
def _contexto_de_app(app):
    """El contexto de la app, sin empujar otro si ya hay uno.

    Un `with app.app_context()` anidado, al salir, dispara el teardown de
    Flask-SQLAlchemy (`session.remove()`): cerraría la sesión de `app_ctx` y se llevaría
    por delante lo que el test tenga en su SAVEPOINT (los objetos quedan desligados).
    """
    if has_app_context():
        yield
    else:
        with app.app_context():
            yield


@pytest.fixture(autouse=True)
def _limpieza_ficheros():
    """Borra al terminar el test las filas de `ficheros` que haya creado (ADR-050, #1007).

    Es de uso automático solo por el ORDEN, no para hacer algo en todos los tests: un
    fixture de uso automático se prepara antes que los demás, así que se deshace DESPUÉS
    que ellos, y en particular después del rollback de `app_ctx`. Ese orden importa: el
    módulo de contenido escribe `ficheros` en una conexión propia, que escapa al
    SAVEPOINT; mientras la transacción de `app_ctx` tenga un `documentos` que apunte a
    una fila, el DELETE se queda esperando su bloqueo (la FK) y el test se cuelga. Por
    eso `almacen_tmp` no puede hacerlo ella misma.

    No hace nada, ni toca la BD, si el test no usó `almacen_tmp`.
    """
    registro = {}
    yield registro
    app = registro.get('app')
    if app is None:
        return
    from sqlalchemy import text
    with app.app_context():
        with _db.engine.begin() as conexion:
            conexion.execute(
                text('DELETE FROM public.ficheros WHERE NOT (ref = ANY(CAST(:previas AS text[])))'),
                {'previas': sorted(registro['previas'])},
            )


@pytest.fixture
def almacen_tmp(app, tmp_path_factory, _limpieza_ficheros):
    """Almacén y manifiestos en un temporal, inicializados (ADR-050, #1007).

    Redirige `ALMACEN_BASE` y `MANIFIESTOS_BASE`, y devuelve un objeto con sus rutas
    (`.almacen`, `.manifiestos`). Úsalo en cuanto el código suba un documento o escriba
    un manifiesto: el disco no es transaccional y el contenido quedaría puesto aunque
    la transacción se deshaga. En el corte (PR 4 de #1007) será la base de
    `documento_con_contenido_de_prueba` (#1014).

    Lo que no revierte el SAVEPOINT de `app_ctx` es la fila de `ficheros`, que el módulo
    de contenido escribe en su propia transacción: la borra `_limpieza_ficheros` al
    terminar. Se borran las que no estaban al empezar el test (la semilla puede traer
    alguna), así que un test que cree filas y no pase por aquí las deja puestas.
    """
    from pathlib import Path
    from types import SimpleNamespace

    import almacen
    from sqlalchemy import text

    from app.services.almacenamiento.manifiestos import inicializar as inicializar_manifiestos

    raiz = Path(tmp_path_factory.mktemp('almacen_tmp'))
    rutas = SimpleNamespace(almacen=raiz / 'almacen', manifiestos=raiz / 'manifiestos')
    almacen.inicializar(str(rutas.almacen))
    inicializar_manifiestos(str(rutas.manifiestos))

    originales = (app.config.get('ALMACEN_BASE'), app.config.get('MANIFIESTOS_BASE'))
    app.config['ALMACEN_BASE'] = str(rutas.almacen)
    app.config['MANIFIESTOS_BASE'] = str(rutas.manifiestos)

    with _contexto_de_app(app):
        with _db.engine.connect() as conexion:
            previas = {fila[0] for fila in conexion.execute(text('SELECT ref FROM public.ficheros'))}
    _limpieza_ficheros['app'] = app
    _limpieza_ficheros['previas'] = previas

    yield rutas

    app.config['ALMACEN_BASE'], app.config['MANIFIESTOS_BASE'] = originales


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
        # Rango B9xxxxxxx: el B0000000x es de scripts/semilla_test.py, y chocaba
        # en cuanto el primer alta del proceso era la 1 o la 2 (un fichero suelto).
        nif=f'B9{n:07d}',
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


def documento_con_contenido_de_prueba(nombre, contenido, **datos_documento):
    """Documento con contenido propio, como el que deja una subida (#1014).

    El único sitio de la suite que monta un documento con fichero: los tests lo piden
    aquí en vez de escribir el fichero a mano, y así el corte de ADR-050 (PR 4 de #1007)
    cambia este helper por dentro y no los tests que lo usan.

    Recibe lo mismo que `contenido.subir` (`EntradaSubida`): el nombre que traería el
    navegador, los bytes y los datos del documento (`expediente_id`, `tipo_doc_id`,
    `fecha_administrativa`, `asunto`…). Devuelve el `Documento` ya añadido a la sesión.

    Hasta el corte escribe el fichero en FILESYSTEM_BASE y pone `url` con su nombre, como
    hacían los helpers que sustituye; en el corte pasará por `subir`, sobre `almacen_tmp`.
    No comprueba el formato por su cuenta: desde el corte lo hace `subir`, la misma puerta
    que usa la aplicación (ADR-050 §E). Un test que quiera probar un fichero engañoso llama
    a esa puerta, no a este helper.

    Requiere `app_ctx` y `fs_tmp`.
    """
    from pathlib import Path

    from flask import current_app

    from app import db as _db_app
    from app.models.documentos import Documento

    (Path(current_app.config['FILESYSTEM_BASE']) / nombre).write_bytes(contenido)
    doc = Documento(url=nombre, **datos_documento)
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
        from app.models.expedientes import Expediente
        from app.models.entidad import Entidad
        from app.models.tipos_solicitudes import TipoSolicitud
        exp = Expediente.query.first()
        ent = Entidad.query.first()
        tipo = TipoSolicitud.query.first()
        if exp is None or ent is None or tipo is None:
            pytest.skip('Faltan expediente/entidad/tipo_solicitud base en la BD de desarrollo')
        return self.solicitud(exp, tipo, ent)

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

    def solicitud(self, expediente, tipo_solicitud, entidad):
        """Solicitud de `tipo_solicitud` en un expediente que ya existe, con su
        escrito de ancla (`documento_ancla_de_prueba`) y sin hijos.

        Para el test que necesita un tipo concreto o una solicitud más en el mismo
        expediente; la de `solicitud_propia()` nace por el alta real. Es el único
        sitio de la suite que monta una `Solicitud` a mano (#1014), salvo el test
        que la monta mal a propósito (`test_428`).

        El expediente va por la relación, como la solicitud en `fase()`: si el test
        ya leyó `expediente.solicitudes`, la lista incluye la nueva. El tipo y la
        entidad van por el id: un test que los cambie después por el id
        (`test_887` cambia el tipo) no se queda con el anterior en memoria."""
        from app.models.solicitudes import Solicitud
        s = Solicitud(expediente=expediente, tipo_solicitud_id=tipo_solicitud.id,
                      entidad_id=entidad.id,
                      documento_solicitud_id=documento_ancla_de_prueba(expediente.id).id)
        self.db.session.add(s)
        self.db.session.flush()
        return s

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
        # Por la relación, no por el FK a pelo (ADR-044 R5, mismo criterio que
        # crear_fase): si el test ya accedió a `solicitud.fases` antes de este
        # punto, el FK a pelo dejaría esa colección cacheada sin la fase nueva.
        f = Fase(solicitud=solicitud, tipo_fase=self._tipo(TipoFase, codigo_fase))
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
        if codigo_tarea == 'NOTIFICAR':
            # Invariante de #967 (ADR-051 §B): toda NOTIFICAR nace con su fila y
            # su fuente. El builder le pone ya destinatario —el solicitante—
            # porque los tests que lo usan prueban otra cosa; los que prueban el
            # bloqueo sin destinatario crean la tarea por `crear_tarea`.
            from app.models.notificaciones import Notificacion
            solicitante_id = tramite.fase.solicitud.entidad_id
            self.db.session.add(Notificacion(
                tarea_id=ta.id, fuente='SOLICITANTE',
                entidad_id=solicitante_id, dest_nombre='Destinatario de prueba'))
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

    def anclar_proyecto(self, expediente_id, *, sufijo='ancla'):
        """Deja el expediente con su proyecto identificado (#887, ADR-044 §D).

        Desde #887 hay una regla de motor que bloquea seguir la solicitud mientras
        `proyectos.documento_principal_id` esté vacío, así que todo test que pase del
        análisis necesita esto — igual que ya necesita cubrir la tasa (#582). El alta
        real no lo trae: en ese momento el único documento que entra es el escrito de
        solicitud, y el proyecto se ancla cuando llega al pool.
        """
        from app.models.expedientes import Expediente
        from app.services.reloj_simulado import hoy
        expediente = Expediente.query.get(expediente_id)
        doc = self.documento(expediente_id, 'DOC_PROYECTO', f'{sufijo}-{expediente_id}',
                             fecha=hoy())
        expediente.proyecto.documento_principal = doc
        self.db.session.flush()
        return doc

    def reformado(self, expediente_id, *, origen='VOLUNTARIO', sufijo='reformado'):
        """Declara un reformado de proyecto en el expediente (R3, ADR-044 §F, #895).

        Atajo de fábrica como `anclar_proyecto()` de #887: construye la fila
        directamente, sin pasar por `declarar_reformado()` (que exige
        `usuario_id` para la bitácora) — el corte en sí no es lo que estos
        tests necesitan probar, solo que el expediente tenga una versión más
        a la que enganchar la siguiente fase.
        """
        from app.models.reformados_proyecto import ReformadoProyecto
        from app.services.reloj_simulado import hoy
        doc = self.documento(expediente_id, 'DOC_PROYECTO', f'{sufijo}-{expediente_id}', fecha=hoy())
        reformado = ReformadoProyecto(documento_id=doc.id, origen=origen)
        self.db.session.add(reformado)
        self.db.session.flush()
        return reformado

    def vincular(self, tarea, documento, rol):
        from app.models.documentos_tarea import DocumentoTarea
        v = DocumentoTarea(tarea_id=tarea.id, documento_id=documento.id, rol=rol)
        self.db.session.add(v)
        self.db.session.flush()
        return v

    def notificacion(self, tarea, resultado=None, canal='NOTIFICA',
                     sede_justificacion=None, *, documento=None, identificador_envio=None):
        """Rellena la fila de `notificaciones` de la tarea directamente, sin
        pasar por el hook de `editar_tarea`. La fila ya existe desde que nace
        la tarea (#967); si no, se crea con fuente SOLICITANTE. Sin fechas
        (#928): las da la `fecha_administrativa` de los justificantes que
        vincule el test; tampoco número de intento (#568): lo dan los
        `JUSTIFICANTE_POSTAL_1ER`/`_2DO` vinculados.

        Con `tarea()`, lo único de la suite que monta una `Notificacion`
        (#1014): su forma ha cambiado varias veces y así se arregla en un
        sitio. `documento` e `identificador_envio` solo se escriben si se
        pasan, para no pisar lo que haya puesto el hook."""
        from app.models.notificaciones import Notificacion
        n = Notificacion.query.filter_by(tarea_id=tarea.id).first()
        if n is None:
            n = Notificacion(tarea_id=tarea.id, fuente='SOLICITANTE')
            self.db.session.add(n)
        n.resultado = resultado
        n.canal = canal
        n.sede_justificacion = sede_justificacion
        if documento is not None:
            n.documento_id = documento.id
        if identificador_envio is not None:
            n.identificador_envio = identificador_envio
        self.db.session.flush()
        return n

    def tramite_sin_destinatario(self, solicitud=None):
        """Trámite cuya NOTIFICAR no puede saber sola a quién va: el anuncio en
        BOJA, cuyo boletín elige el usuario y nadie ha elegido (#968, ADR-051
        §L). Para probar lo que pasa sin destinatario por el camino real
        (`crear_tarea`), que desde #968 rellena el destinatario si lo sabe."""
        fase = self.fase('INFORMACION_PUBLICA', solicitud=solicitud or self.solicitud_propia())
        return self.tramite(fase, 'ANUNCIO_BOJA')

    def tramite_sin_fuentes(self, solicitud=None):
        """Trámite sin fuentes en `notificacion_fuentes` (el anuncio en el BOE no
        lleva NOTIFICAR desde #964): una NOTIFICAR forzada en él admite
        cualquier entidad indicada, la vía de #967."""
        fase = self.fase('INFORMACION_PUBLICA', solicitud=solicitud or self.solicitud_propia())
        return self.tramite(fase, 'ANUNCIO_BOE')

    def notificar_sin_destinatario(self, tramite, fuente):
        """NOTIFICAR del builder con `fuente` y sin destinatario: la ficha como
        queda cuando nadie ha elegido a quién notificar."""
        tarea = self.tarea(tramite, 'NOTIFICAR')
        notif = tarea.notificacion
        notif.fuente, notif.entidad_id, notif.dest_nombre = fuente, None, None
        self.db.session.flush()
        return tarea

    def notificar_hecha(self, tramite, *, sufijo='notificada'):
        """NOTIFICAR del trámite efectuada: justificante final como producido y
        resultado CORRECTA. Con destinatario (el del builder, el solicitante).

        Desde #968 un trámite que notifica según `notificacion_fuentes` no está
        terminado sin su NOTIFICAR; los tests que necesitan un trámite completo
        para probar otra cosa la añaden con esto."""
        from app.services.reloj_simulado import hoy
        tarea = self.tarea(tramite, 'NOTIFICAR')
        justificante = self.documento(tramite.fase.solicitud.expediente_id,
                                      'JUSTIFICANTE_NOTIFICA', f'{sufijo}-{tarea.id}', fecha=hoy())
        self.vincular(tarea, justificante, 'PRODUCIDO')
        self.notificacion(tarea, resultado='CORRECTA')
        return tarea

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


# ---------------------------------------------------------------------------
# Conteo de consultas SQL (#907, #928, #930)
# ---------------------------------------------------------------------------

def contar_consultas(funcion) -> int:
    """Sentencias SQL que emite `funcion()`, contadas en el motor.

    Para tests de N+1: se compara el conteo de dos variantes (con una y con
    cuatro NOTIFICAR; con y sin el plazo del acto), no un número absoluto, que
    cambiaría con cualquier eager-load ajeno a lo que se prueba.
    """
    from sqlalchemy import event

    contador = {'n': 0}

    def _uno(*_args, **_kwargs):
        contador['n'] += 1

    motor = _db.engine
    event.listen(motor, 'before_cursor_execute', _uno)
    try:
        funcion()
    finally:
        event.remove(motor, 'before_cursor_execute', _uno)
    return contador['n']
