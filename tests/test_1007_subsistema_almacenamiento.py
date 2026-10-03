"""#1007 (ADR-050 §B) — quién puede ver `ficheros`, `fichero_ref` y la librería del almacén.

Permanente: no se borra con `test_1001` cuando se retire el modelo de rutas. Es la otra
mitad de la regla de §B: solo el subsistema de almacenamiento (`app/services/almacenamiento/`)
lee o escribe `ficheros`, `documentos.fichero_ref` o una `ref`, y dentro de `app/` solo el
adaptador importa la librería `almacen`.

Fallo silencioso que evita: un servicio que escriba `fichero_ref` por su cuenta se salta
las comprobaciones que dan coherencia al contenido (sellado, bitácora, comprobación al
vincular) y un documento sellado cambia de contenido sin que nada lo detecte; o un
servicio habla con la librería sin pasar por el adaptador y se salta el tiempo límite y
el semáforo, de modo que un almacén colgado le agota los workers.

Cómo cuenta
-----------
Por AST, solo el código (atributos, nombres, imports, argumentos con nombre y cadenas que
son exactamente el símbolo, o SQL que nombra la tabla): los comentarios y los docstrings
no cuentan. Las plantillas, por texto sin comentarios. Lo permitido son ficheros enteros
(el modelo define la columna y la tabla; el subsistema las usa).

PUNTO CIEGO CONOCIDO: no ve un acceso a `ficheros` por una cadena SQL que la construya
por partes, ni lo que haga el JavaScript con una `ref`: ahí vale la revisión, y la API
nunca devuelve una `ref` ni una ruta (§B).
"""
import ast
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / 'app'
SUBSISTEMA = 'app/services/almacenamiento/'

# Nombres que solo puede usar el subsistema (más lo que el modelo necesita para definirlos).
SIMBOLOS = {'fichero_ref', 'plantilla_ref', 'Fichero'}
PERMITIDOS_MODELO = {
    'app/models/__init__.py',      # importa `Fichero`
    'app/models/ficheros.py',      # define la tabla
    'app/models/documentos.py',    # define la columna `fichero_ref`
}
SOLO_ADAPTADOR = 'app/services/almacenamiento/adaptador.py'

_RE_SQL_FICHEROS = re.compile(r'\bpublic\.ficheros\b|\b(?:FROM|JOIN|INTO|UPDATE)\s+ficheros\b', re.I)
_RE_HTML = re.compile(r'\b(?:fichero_ref|plantilla_ref)\b')
_RE_COMENTARIO_HTML = re.compile(r'\{#.*?#\}|<!--.*?-->', re.S)

_AYUDA = (
    'Lo que necesite el contenido de un documento lo pide al módulo de contenido '
    '(`app.services.almacenamiento.contenido`: subir, leer, comprobar_para_vincular, '
    'servir_descarga), que es quien comprueba el sellado y deja la bitácora. No añadas el '
    'fichero a la lista de permitidos. Ver ADR-050 §B.'
)


def _ficheros(sufijos):
    for fichero in sorted(APP.rglob('*')):
        if fichero.suffix in sufijos and fichero.is_file():
            yield fichero, fichero.relative_to(RAIZ).as_posix()


def _usos_de_ficheros(fuente):
    """Lo que de `ficheros` / `fichero_ref` toca este código Python."""
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Attribute) and nodo.attr in SIMBOLOS:
            yield nodo.attr
        elif isinstance(nodo, ast.Name) and nodo.id in SIMBOLOS:
            yield nodo.id
        elif isinstance(nodo, ast.alias) and nodo.name in SIMBOLOS:
            yield nodo.name
        elif isinstance(nodo, ast.keyword) and nodo.arg in SIMBOLOS:
            yield nodo.arg
        elif isinstance(nodo, ast.ImportFrom) and nodo.module == 'app.models.ficheros':
            yield 'app.models.ficheros'
        elif isinstance(nodo, ast.Constant) and isinstance(nodo.value, str):
            if nodo.value in SIMBOLOS or _RE_SQL_FICHEROS.search(nodo.value):
                yield nodo.value


def _importa_almacen(fuente):
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import) and any(a.name.split('.')[0] == 'almacen' for a in nodo.names):
            return True
        if isinstance(nodo, ast.ImportFrom) and nodo.level == 0 and (nodo.module or '').split('.')[0] == 'almacen':
            return True
    return False


def test_solo_el_subsistema_ve_ficheros_y_la_ref():
    intrusos = {}
    for fichero, relativo in _ficheros({'.py'}):
        if relativo.startswith(SUBSISTEMA) or relativo in PERMITIDOS_MODELO:
            continue
        usos = sorted(set(_usos_de_ficheros(fichero.read_text(encoding='utf-8'))))
        if usos:
            intrusos[relativo] = usos
    for fichero, relativo in _ficheros({'.html'}):
        texto = _RE_COMENTARIO_HTML.sub('', fichero.read_text(encoding='utf-8'))
        usos = sorted(set(_RE_HTML.findall(texto)))
        if usos:
            intrusos[relativo] = usos

    assert not intrusos, f'Fuera del subsistema de almacenamiento: {intrusos}. {_AYUDA}'


def test_solo_el_adaptador_importa_la_libreria_del_almacen():
    intrusos = [
        relativo for fichero, relativo in _ficheros({'.py'})
        if relativo != SOLO_ADAPTADOR and _importa_almacen(fichero.read_text(encoding='utf-8'))
    ]

    assert not intrusos, (
        f'Importan la librería `almacen` sin ser el adaptador: {intrusos}. '
        'Lo que necesiten del almacén lo piden al adaptador (o al módulo de contenido). '
        'Ver ADR-050 §B.')
