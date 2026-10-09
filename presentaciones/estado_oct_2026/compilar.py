"""Compila las fichas de fichas/ de esta zona en un solo HTML: index.html.

Reutiliza el compilador de ../fundamentos/compilar.py (mismo reproductor, mismo
puente de teclado y clic). Aquí solo cambian la carpeta, el título y el orden:
las fichas se toman por orden alfabético de nombre (ficha_01_..., ficha_02_...),
así que añadir una ficha no obliga a editar ninguna lista.

GitHub Pages no compila nada: sirve index.html tal cual. Por eso el index.html
generado se versiona; si se cambia una ficha, hay que volver a ejecutar esto.

Uso:  D:/BDDAT/venv/Scripts/python.exe presentaciones/estado_oct_2026/compilar.py
Solo usa la biblioteca estándar.
"""
import importlib.util
from pathlib import Path

CARPETA = Path(__file__).resolve().parent

# Se carga el compilador de fundamentos sin ejecutarlo (su main() cuelga de __main__)
_spec = importlib.util.spec_from_file_location(
    'compilar_fundamentos', CARPETA.parent / 'fundamentos' / 'compilar.py')
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

base.FICHAS = CARPETA / 'fichas'
base.SALIDA = CARPETA / 'index.html'
base.ORDEN = sorted(p.name for p in base.FICHAS.glob('ficha_*.html'))
base.PAGINA = base.PAGINA.replace(
    '<title>Fundamentos tecnológicos</title>',
    '<title>Estado BDDAT octubre 2026</title>')

if __name__ == '__main__':
    # A veces el visor de la aplicación tiene index.html abierto justo al escribir y el
    # sistema devuelve «Invalid argument»: se reintenta un par de veces antes de fallar.
    import time
    for intento in range(3):
        try:
            base.main()
            break
        except OSError:
            if intento == 2:
                raise
            time.sleep(0.5)
