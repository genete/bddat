"""Construye la BD de desarrollo de una sesión en la nube (#949, parte B).

Uso (lo llama scripts/nube/arrancar_app.sh; también se puede lanzar suelto):
    python scripts/nube/preparar_bd_desarrollo.py

Misma receta que la BD de tests (`scripts/preparar_bd_test.py`), sobre
`DATABASE_URL`: crea la base si falta, aplica `upgrade heads` y termina con
`semilla_test.sembrar()`. Idempotente: con la base ya sembrada solo aplica las
migraciones pendientes.

**Solo en la nube.** Se niega a correr sin `CLAUDE_CODE_REMOTE=true`, y no hay
forma de forzarlo: en el PC, `DATABASE_URL` es la BD de desarrollo de verdad,
y la semilla le añadiría 7 usuarios con contraseña `test` y 4 expedientes
ficticios. Esta base no es una copia de la del PC ni debe parecerlo: sin datos
reales ni los ajustes acumulados (REGLAS_DESARROLLO.md §Migraciones).

Dos efectos de la semilla que conviene conocer (vienen de la de tests):
- desactiva las plantillas sembradas por migración, porque apuntan a .docx que
  aquí no están: generar escritos exige registrar antes una plantilla;
- construye los expedientes-tipo sin reloj simulado (`efectos_desarrollo=False`).
"""
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import make_url

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))   # preparar_bd_test, semilla_test
load_dotenv(os.path.join(RAIZ, '.env'))

from preparar_bd_test import _crear_si_falta, _preparar_tabla_version  # noqa: E402


def main():
    if os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        sys.exit('preparar_bd_desarrollo: solo en la nube (CLAUDE_CODE_REMOTE=true). '
                 'En el PC sembraría usuarios de prueba en la BD de desarrollo real.')

    url_raw = os.environ.get('DATABASE_URL')
    if not url_raw:
        sys.exit('DATABASE_URL no está configurada en .env')
    url = make_url(url_raw)
    url_test_raw = os.environ.get('TEST_DATABASE_URL')
    if url_test_raw and make_url(url_test_raw).database == url.database:
        sys.exit(f'DATABASE_URL y TEST_DATABASE_URL apuntan a la misma base ({url.database})')
    print(f'base de desarrollo: {url.database} en {url.host}:{url.port}')

    _crear_si_falta(url)
    _preparar_tabla_version(url)

    from flask_migrate import upgrade

    from app import create_app, db
    app = create_app('development')
    with app.app_context():
        upgrade(directory=os.path.join(RAIZ, 'migrations'), revision='heads')

    from semilla_test import sembrar
    sembrar(app)

    with app.app_context():
        n_exp = db.session.execute(text('SELECT count(*) FROM expedientes')).scalar()
        n_usr = db.session.execute(text('SELECT count(*) FROM public.usuarios')).scalar()
    print(f'\nBD de desarrollo lista: {n_exp} expedientes, {n_usr} usuarios '
          '(siglas TADM, TSUP, TTRA, TADV, TMUL, TTR2, TOFF; contraseña «test»)')


if __name__ == '__main__':
    main()
