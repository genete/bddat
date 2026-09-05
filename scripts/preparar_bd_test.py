"""Construye la base de datos de tests desde las migraciones (#849).

Uso:
    venv/Scripts/python.exe scripts/preparar_bd_test.py            # aplica migraciones
    venv/Scripts/python.exe scripts/preparar_bd_test.py --recrear  # borra y reconstruye

Por qué desde las migraciones y no con `db.create_all()`: el autogenerate está
prohibido en este proyecto (bug de `include_schemas`, REGLAS_DESARROLLO.md), así
que las 138 migraciones se escriben a mano y pueden derivar del modelo sin que
nada lo diga. Si la BD de test se creara desde los modelos, la deriva quedaría
tapada justo donde debería saltar. Aquí se aplica `upgrade heads`, que es lo
mismo que correrá una instalación nueva.

Lo que este script NO hace: sembrar datos de negocio (expedientes, solicitudes,
documentos). Esa es la semilla, y va aparte — los expedientes-tipo de
`scripts/expedientes_dummy/` son su sitio natural.
"""
import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # para semilla_test
load_dotenv(os.path.join(RAIZ, '.env'))


def _comprobar_urls():
    """Devuelve la URL de test, tras negarse a tocar la de desarrollo.

    Es la salvaguarda del script: `--recrear` hace DROP DATABASE, así que una
    TEST_DATABASE_URL mal copiada borraría la base de trabajo. Se compara la
    base y el host, no la cadena completa: dos URL con distinta contraseña o
    distinto driver siguen apuntando al mismo sitio.
    """
    url_test_raw = os.environ.get('TEST_DATABASE_URL')
    url_dev_raw = os.environ.get('DATABASE_URL')
    if not url_test_raw:
        sys.exit('TEST_DATABASE_URL no está configurada en .env — ver .env.example')

    url_test = make_url(url_test_raw)
    if url_dev_raw:
        url_dev = make_url(url_dev_raw)
        mismo_sitio = (
            url_test.database == url_dev.database
            and url_test.host == url_dev.host
            and url_test.port == url_dev.port
        )
        if mismo_sitio:
            sys.exit(
                'TEST_DATABASE_URL apunta a la MISMA base que DATABASE_URL '
                f'({url_test.database}). Abortado: este script la reconstruye.'
            )
    return url_test


def _recrear_base(url_test):
    """DROP + CREATE de la base de test, conectando a `postgres`.

    CREATE/DROP DATABASE no pueden ir dentro de una transacción: de ahí el
    AUTOCOMMIT. Y no se puede borrar una base con sesiones abiertas, así que
    primero se intenta echar a quien esté conectado (un pgAdmin abierto, por
    ejemplo). Ese intento es best-effort: `bddat_admin` no es superusuario y
    Postgres no le deja cerrar sesiones de roles que sí lo son. Si queda alguna
    viva, el DROP falla, y entonces se recurre a vaciar el esquema: deja la
    base igual de limpia y no necesita exclusividad. Pasa de verdad —una
    ventana de pgAdmin abierta sobre la base basta, y si su sesión es del
    usuario `postgres` no hay forma de echarla desde aquí.
    """
    nombre = url_test.database
    url_admin = url_test.set(database='postgres')
    eng = create_engine(url_admin, isolation_level='AUTOCOMMIT')
    borrada = False
    with eng.connect() as c:
        try:
            c.execute(text(
                'SELECT pg_terminate_backend(pid) FROM pg_stat_activity '
                'WHERE datname = :n AND pid <> pg_backend_pid()'), {'n': nombre})
        except Exception as exc:
            print(f'[recrear] aviso: no se pudieron cerrar sesiones ajenas '
                  f'({exc.__class__.__name__}); se intenta el DROP igualmente')
        try:
            c.execute(text(f'DROP DATABASE IF EXISTS "{nombre}"'))
            c.execute(text(f'CREATE DATABASE "{nombre}"'))
            borrada = True
        except OperationalError:
            print(f'[recrear] «{nombre}» está en uso por otra sesión '
                  f'(¿pgAdmin abierto?): se vacía su esquema en vez de borrarla')
    eng.dispose()

    if borrada:
        print(f'[recrear] base «{nombre}» borrada y creada de nuevo')
        return

    eng = create_engine(url_test, isolation_level='AUTOCOMMIT')
    with eng.connect() as c:
        c.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
        c.execute(text('CREATE SCHEMA public'))
    eng.dispose()
    print(f'[recrear] esquema public de «{nombre}» vaciado y recreado')


def _crear_si_falta(url_test):
    """Crea la base solo si no existe. No toca una base ya poblada."""
    nombre = url_test.database
    eng = create_engine(url_test.set(database='postgres'), isolation_level='AUTOCOMMIT')
    with eng.connect() as c:
        existe = c.execute(
            text('SELECT 1 FROM pg_database WHERE datname = :n'), {'n': nombre}
        ).scalar()
        if not existe:
            c.execute(text(f'CREATE DATABASE "{nombre}"'))
            print(f'[crear] base «{nombre}» creada')
    eng.dispose()


def _preparar_tabla_version(url_test):
    """Crea `alembic_version` con la columna ancha antes de que la cree Alembic.

    Alembic la crea con VARCHAR(32) y no ofrece forma de configurar ese ancho,
    pero este proyecto usa identificadores de revisión descriptivos: por
    ejemplo '488_seed_tramites_tareas_registro_interesados', que son 45
    caracteres. El upgrade moría al registrar esa revisión.

    En la BD de desarrollo no pasa porque la columna es VARCHAR(128) — se
    amplió a mano en algún momento y nunca se formalizó. Aquí se hace lo mismo
    pero por escrito: si la tabla ya existe cuando Alembic arranca, la usa tal
    cual. El ancho es el mismo que el de desarrollo, para que las dos bases
    coincidan.
    """
    eng = create_engine(url_test, isolation_level='AUTOCOMMIT')
    with eng.connect() as c:
        c.execute(text(
            'CREATE TABLE IF NOT EXISTS public.alembic_version ('
            'version_num VARCHAR(128) NOT NULL, '
            'CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))'
        ))
    eng.dispose()


def _aplicar_migraciones():
    """`flask db upgrade heads` sobre la config de testing."""
    from flask_migrate import upgrade

    from app import create_app

    app = create_app('testing')
    with app.app_context():
        upgrade(directory=os.path.join(RAIZ, 'migrations'), revision='heads')
    return app


def _informe(app):
    """Qué ha quedado en la base tras el upgrade.

    Interesa el catálogo estructural: las migraciones `*_seed_*` lo siembran, y
    saber qué llega solo y qué no es lo que decide el tamaño de la semilla.
    """
    from app import db
    from app.checks.catalogo_requerido import REGISTROS_REQUERIDOS, validar_catalogo

    with app.app_context():
        n_tablas = db.session.execute(text(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema NOT IN ('pg_catalog','information_schema')")).scalar()
        revision = db.session.execute(text(
            'SELECT version_num FROM alembic_version')).scalar()
        print(f'\ntablas creadas: {n_tablas}   revisión alembic: {revision}\n')

        modelos = {
            'TipoTramite': ('tipos_tramites', 'codigo'),
            'TipoTarea': ('tipos_tareas', 'codigo'),
            'TipoFase': ('tipos_fases', 'codigo'),
            'TipoSolicitud': ('tipos_solicitudes', 'siglas'),
            'TipoDocumento': ('public.tipos_documentos', 'codigo'),
            'TipoResultadoFase': ('tipos_resultados_fases', 'codigo'),
            'Rol': ('public.roles', 'nombre'),
        }
        print(f'{"tabla":28} {"filas":>7}   códigos requeridos')
        for nombre_modelo, (tabla, _attr) in modelos.items():
            n = db.session.execute(text(f'SELECT count(*) FROM {tabla}')).scalar()
            print(f'{tabla:28} {n:>7}   {len(REGISTROS_REQUERIDOS[nombre_modelo])}')

        for extra in ('public.municipios', 'public.usuarios', 'public.normas',
                      'public.catalogo_plazos', 'public.reglas_motor',
                      'public.efectos_plazo', 'fases_tramites', 'tramites_tareas'):
            n = db.session.execute(text(f'SELECT count(*) FROM {extra}')).scalar()
            print(f'{extra:28} {n:>7}')

        faltantes = validar_catalogo()
        if faltantes:
            print(f'\ncatálogo INCOMPLETO — {len(faltantes)} registros que el código espera:')
            for f in faltantes:
                print(f'  - {f}')
        else:
            print('\ncatálogo completo: validar_catalogo() no echa nada en falta')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recrear', action='store_true',
                        help='borra la base de test y la crea de nuevo antes de migrar')
    args = parser.parse_args()

    url_test = _comprobar_urls()
    print(f'base de test: {url_test.database} en {url_test.host}:{url_test.port}')

    if args.recrear:
        _recrear_base(url_test)
    else:
        _crear_si_falta(url_test)

    _preparar_tabla_version(url_test)
    app = _aplicar_migraciones()

    from semilla_test import sembrar
    sembrar(app)

    _informe(app)


if __name__ == '__main__':
    main()
