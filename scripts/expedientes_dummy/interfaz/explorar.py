"""Mira una ruta como un usuario: login, ir, captura y árbol de accesibilidad a fichero. No modifica nada.

Sirve para escribir guiones nuevos: el árbol de accesibilidad es lo que ve un lector de pantalla y, por tanto, con
lo que se puede localizar un elemento sin `data-testid` (roles, nombres, etiquetas).

    venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.explorar --usuario <SIGLAS> --password <CLAVE> --ruta expedientes/ --nombre listado
    venv/Scripts/python.exe -m scripts.expedientes_dummy.interfaz.explorar ... --ruta "expedientes/{id}/arbol" --nombre arbol

La ruta va SIN barra inicial: Git Bash (Windows) convierte un argumento que empieza por `/` en una ruta de disco
(`C:/Users/…/Git/expedientes/`). `{id}` se sustituye por el expediente del último guion que se ejecutó (`--tipo`, por
defecto analisis_doc_dos_vueltas). Las salidas (`<nombre>.png` en capturas/ y `aria-<nombre>.yml`) van a
`docs_prueba/ui_dummy/explorar/`.
"""
import argparse
import sys

from .lib.contexto import cargar_estado
from .lib.sesion import SALIDAS, Sesion, anadir_opciones_comunes, exigir_credenciales

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
anadir_opciones_comunes(p)
p.add_argument('--ruta', default='expedientes/', help='ruta de la aplicación, sin barra inicial; admite {id}')
p.add_argument('--nombre', default='exploracion')
p.add_argument('--esperar', type=int, default=1500, help='ms de espera tras cargar')
p.add_argument('--tipo', default='analisis_doc_dos_vueltas', help='de qué expediente-tipo es el {id} de la ruta')
opts = p.parse_args()
exigir_credenciales(opts)

ruta = '/' + opts.ruta.lstrip('/')
if '{id}' in ruta:
    estado = cargar_estado(SALIDAS / opts.tipo)
    if not estado or not estado.get('id'):
        sys.exit(f'No hay expediente en docs_prueba/ui_dummy/{opts.tipo}/estado.json: ejecuta antes el guion.')
    ruta = ruta.replace('{id}', str(estado['id']))

carpeta = SALIDAS / 'explorar'
s = Sesion(opts, carpeta)
codigo = 0
try:
    with s.paso('login', 'name + rol'):
        s.login()
    with s.paso(f'ir a {ruta}', 'URL'):
        s.page.goto(f'{opts.url}{ruta}', wait_until='networkidle')
        s.page.wait_for_timeout(opts.esperar)
    print(f'  url: {s.page.url}  «{s.page.title()}»')
    s.captura(opts.nombre)
    s.aria(opts.nombre)
    print(f'  captura y aria-{opts.nombre}.yml en {carpeta}')
except Exception:  # noqa: BLE001
    codigo = 1
s.cerrar(f'diario-{opts.nombre}')
sys.exit(codigo)
