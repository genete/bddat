"""Copia en app/static/vendor/ los CSS, JS y tipografías que la app cargaba de los CDN (#984).

Uso:
    python scripts/vendorizar_jda.py

Vuelve a generar TODO app/static/vendor/ desde el CDN de la Junta de Andalucía y desde
npm (jsdelivr). Es la vía para actualizar de versión: cambiar las constantes de abajo,
ejecutar, comparar las capturas y commitear. No se edita a mano nada de esa carpeta.

Qué es copia literal y qué no:
  - Literal: custom-jda-bootstrap.css, all.css, bootstrap.bundle.min.js, y los .woff2.
  - Única modificación (aceptada en #984): en fonts.css y bootstrap-icons.css se dejan solo
    los formatos woff2 en cada `src:`. Los navegadores actuales solo piden ese formato, y
    así no se versionan los .woff/.ttf/.otf de repuesto. Cada fichero modificado lleva
    una línea de comentario que lo dice.
"""
import os
import re
import sys
import urllib.request

# Versiones fijadas: cambiarlas aquí y solo aquí.
JDA_VERSION = '1.2.5'
BOOTSTRAP_ICONS = '1.11.1'
BOOTSTRAP = '5.3.3'          # licencia del núcleo del tema (cabecera de custom-jda-bootstrap.css)
FONT_AWESOME = '6.5.1'       # licencia de all.css (cabecera del propio fichero)

JDA = f'https://cdn.juntadeandalucia.es/components/sass/{JDA_VERSION}/'
NPM = 'https://cdn.jsdelivr.net/npm/'
GH = 'https://cdn.jsdelivr.net/gh/'

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DESTINO = os.path.join(RAIZ, 'app', 'static', 'vendor')

# Textos de licencia que hay que conservar junto a lo redistribuido.
LICENCIAS = {
    'bootstrap-MIT.txt': NPM + f'bootstrap@{BOOTSTRAP}/LICENSE',
    'bootstrap-icons-MIT.txt': NPM + f'bootstrap-icons@{BOOTSTRAP_ICONS}/LICENSE',
    'font-awesome-free.txt': NPM + f'@fortawesome/fontawesome-free@{FONT_AWESOME}/LICENSE.txt',
    'montserrat-OFL-1.1.txt': GH + 'JulietaUla/Montserrat@master/OFL.txt',
    'source-sans-OFL-1.1.txt': GH + 'adobe-fonts/source-sans@release/LICENSE.md',
}

# Modificación de #984: de cada `src:` solo el woff2.
PATRON_SRC = re.compile(r'src:[^;]*;')
PATRON_WOFF2 = re.compile(r'url\([^)]*woff2[^)]*\)\s*format\(["\']woff2["\']\)')


def descargar(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def guardar(ruta_relativa, datos):
    destino = os.path.join(DESTINO, ruta_relativa)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'wb') as f:
        f.write(datos)
    print(f'{len(datos):>9}  {ruta_relativa}')
    return len(datos)


def solo_woff2(texto):
    """Deja en cada `src:` únicamente la fuente woff2. Devuelve (texto, nº de src tocados)."""
    tocados = 0

    def cambiar(m):
        nonlocal tocados
        woff2 = PATRON_WOFF2.search(m.group(0))
        if not woff2:
            return m.group(0)
        tocados += 1
        return f'src: {woff2.group(0)};'

    return PATRON_SRC.sub(cambiar, texto), tocados


def con_nota(texto, origen):
    return (f'/* Copia de {origen} (#984). Modificación: solo formatos woff2 en cada src. '
            f'Ver ../LEEME.md. */\n') + texto


def main():
    total = 0

    # --- Junta de Andalucía: CSS y JS literales ---
    for css in ('all.css', 'custom-jda-bootstrap.css'):
        total += guardar(f'jda/css/{css}', descargar(JDA + f'css/{css}'))
    total += guardar('jda/js/bootstrap.bundle.min.js', descargar(JDA + 'js/bootstrap.bundle.min.js'))

    # --- fonts.css: se modifica y se bajan los .woff2 que referencia ---
    fonts = descargar(JDA + 'css/fonts.css').decode('utf-8')
    urls = sorted(set(re.findall(r'url\(["\']?([^"\')]+\.woff2)["\']?\)', fonts)))
    nuevo, tocados = solo_woff2(fonts)
    total += guardar('jda/css/fonts.css', con_nota(nuevo, JDA + 'css/fonts.css').encode('utf-8'))
    print(f'          fonts.css: {tocados} declaraciones src reducidas a woff2')
    for u in urls:
        ruta = os.path.normpath(os.path.join('jda/css', u)).replace('\\', '/')
        total += guardar(ruta, descargar(JDA + 'css/' + u))

    # --- Bootstrap Icons (jsdelivr/npm) ---
    bi = NPM + f'bootstrap-icons@{BOOTSTRAP_ICONS}/font/'
    css = descargar(bi + 'bootstrap-icons.css').decode('utf-8')
    nuevo, tocados = solo_woff2(css)
    total += guardar('bootstrap-icons/bootstrap-icons.css',
                     con_nota(nuevo, bi + 'bootstrap-icons.css').encode('utf-8'))
    print(f'          bootstrap-icons.css: {tocados} declaraciones src reducidas a woff2')
    total += guardar('bootstrap-icons/fonts/bootstrap-icons.woff2', descargar(bi + 'fonts/bootstrap-icons.woff2'))

    # --- Textos de licencia ---
    for nombre, url in LICENCIAS.items():
        total += guardar(f'licencias/{nombre}', descargar(url))

    print(f'{total:>9}  TOTAL en {os.path.relpath(DESTINO, RAIZ)}')


if __name__ == '__main__':
    sys.exit(main())
