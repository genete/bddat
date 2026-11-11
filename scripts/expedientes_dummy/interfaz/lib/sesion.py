"""Navegador, página y diario de pasos de los guiones de interfaz.

Instalación (una vez, en el venv del proyecto; `playwright` no está en `requirements.txt` a propósito):

    venv/Scripts/python.exe -m pip install playwright
    venv/Scripts/python.exe -m playwright install chromium

En la nube, con el Chromium del contenedor: variable de entorno `CHROMIUM_PATH=/opt/pw-browsers/chromium`.

Las salidas de cada ejecución (estado, capturas, diario, copias del árbol de accesibilidad) van a
`docs_prueba/ui_dummy/<expediente-tipo>/`, que git ignora.
"""
import argparse
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - depende del entorno
    sys.exit('Falta el paquete `playwright` (herramienta a demanda, no está en requirements.txt):\n'
             '  venv/Scripts/python.exe -m pip install playwright\n'
             '  venv/Scripts/python.exe -m playwright install chromium')

# scripts/expedientes_dummy/interfaz/lib/sesion.py → la raíz del repositorio, no una ruta fija (también corre en Linux).
RAIZ = Path(__file__).resolve().parents[4]
SALIDAS = RAIZ / 'docs_prueba' / 'ui_dummy'

# Windows con la salida redirigida (o sin consola UTF-8): Python usa cp1252 y revienta al imprimir ✔ ✘ → −.
for _flujo in (sys.stdout, sys.stderr):
    if hasattr(_flujo, 'reconfigure'):
        _flujo.reconfigure(encoding='utf-8', errors='replace')


def anadir_opciones_comunes(p):
    """Las opciones que comparten todos los guiones de interfaz. Sin credenciales en el código: por argumento o
    por variable de entorno (`BDDAT_UI_USUARIO`, `BDDAT_UI_PASSWORD`). En la BD de la nube, los usuarios de la
    semilla (`scripts/nube/README.md`)."""
    p.add_argument('--usuario', default=os.environ.get('BDDAT_UI_USUARIO'), help='siglas (o BDDAT_UI_USUARIO)')
    p.add_argument('--password', default=os.environ.get('BDDAT_UI_PASSWORD'), help='contraseña (o BDDAT_UI_PASSWORD)')
    p.add_argument('--rol', default='TRAMITADOR', help='rol, si el usuario tiene varios (login de dos pasos)')
    p.add_argument('--url', default='http://127.0.0.1:5000', help='dirección de la aplicación')
    p.add_argument('--visible', action='store_true', help='abre la ventana del navegador (por defecto, en segundo plano)')
    p.add_argument('--lento', type=int, default=0, help='ms de pausa entre acciones')
    return p


def exigir_credenciales(opts):
    if not opts.usuario or not opts.password:
        sys.exit('Faltan credenciales: --usuario y --password (o BDDAT_UI_USUARIO y BDDAT_UI_PASSWORD).')


class Sesion:
    """Navegador, página y diario de pasos (qué estrategia de localizador funcionó en cada uno).

    `paso()` es el único sitio por el que pasa cada acción con nombre: ahí se cuelga, a futuro, lo que cada paso
    necesite (rótulos y pausas para grabar un tutorial, por ejemplo)."""

    def __init__(self, opts, carpeta):
        self.opts = opts
        self.carpeta = Path(carpeta)
        self.capturas = self.carpeta / 'capturas'
        self.capturas.mkdir(parents=True, exist_ok=True)
        self.diario = []
        self.consola = []
        self.errores_app = []
        self._pw = sync_playwright().start()
        ruta = os.environ.get('CHROMIUM_PATH')
        self.navegador = self._pw.chromium.launch(
            headless=not opts.visible, slow_mo=opts.lento,
            **({'executable_path': ruta} if ruta else {}))
        self.page = self.navegador.new_page(viewport={'width': 1920, 'height': 1080})
        self.page.on('console', lambda m: self.consola.append(m.text) if m.type == 'error' else None)
        self.page.on('pageerror', lambda e: self.consola.append(f'pageerror: {e}'))
        self.page.on('response', lambda r: self.errores_app.append(f'{r.status} {r.url[len(opts.url):]}')
                     if r.status >= 400 and r.url.startswith(opts.url) else None)

    @contextmanager
    def paso(self, nombre, estrategia):
        t0 = time.time()
        try:
            yield
        except Exception as e:  # noqa: BLE001
            msg = ' | '.join(str(e).splitlines()[:3])
            self.diario.append({'paso': nombre, 'ok': False, 'ms': int((time.time() - t0) * 1000),
                                'estrategia': estrategia, 'error': msg})
            print(f'  ✘ {nombre}  [{estrategia}]  {msg}')
            self.captura('FALLO-' + re.sub(r'\W+', '_', nombre))
            raise
        ms = int((time.time() - t0) * 1000)
        self.diario.append({'paso': nombre, 'ok': True, 'ms': ms, 'estrategia': estrategia})
        print(f'  ✔ {nombre}  [{estrategia}]  {ms} ms')

    def captura(self, nombre):
        try:
            self.page.screenshot(path=str(self.capturas / f'{nombre}.png'))
        except Exception:  # noqa: BLE001
            pass

    def aria(self, nombre, locator=None):
        """Vuelca el árbol de accesibilidad (lo que ve un lector de pantalla) a `aria-<nombre>.yml`."""
        snap = (locator or self.page.locator('body')).aria_snapshot()
        (self.carpeta / f'aria-{nombre}.yml').write_text(snap, encoding='utf-8')
        return snap

    def login(self):
        """Login de dos pasos: siglas + contraseña y, si el usuario tiene varios roles, la elección del rol."""
        o, page = self.opts, self.page
        page.goto(f'{o.url}/auth/login')
        page.locator('input[name="siglas"]').fill(o.usuario)
        page.locator('input[name="password"]').fill(o.password)
        with page.expect_response(lambda r: r.request.method == 'POST' and '/auth/login' in r.url):
            page.locator('input[name="password"]').press('Enter')
        page.wait_for_load_state('load')
        rol = page.locator('select[name="rol_id"]')
        if rol.count():
            textos = rol.locator('option').all_text_contents()
            elegida = next((t for t in textos if o.rol.upper() in t.upper()), None)
            if not elegida:
                raise RuntimeError(f'{o.usuario} no tiene el rol {o.rol}: {textos}')
            rol.select_option(label=elegida.strip())
            with page.expect_response(lambda r: r.request.method == 'POST' and '/auth/login' in r.url):
                rol.evaluate('s => s.form.requestSubmit()')
            page.wait_for_load_state('load')
        page.wait_for_url(lambda u: '/auth/login' not in u, timeout=10000)

    def cerrar(self, nombre_diario='diario'):
        """Guarda el diario, cierra el navegador y devuelve (pasos correctos, pasos en total)."""
        (self.carpeta / f'{nombre_diario}.json').write_text(json.dumps(
            {'diario': self.diario, 'consola': self.consola[:20], 'errores_app': self.errores_app},
            ensure_ascii=False, indent=2), encoding='utf-8')
        if self.errores_app:
            print('respuestas de error de la app:', ' · '.join(self.errores_app))
        if self.consola:
            print(f'errores de consola ({len(self.consola)}):', ' | '.join(self.consola[:5]))
        ok = sum(1 for d in self.diario if d['ok'])
        self.navegador.close()
        self._pw.stop()
        return ok, len(self.diario)
