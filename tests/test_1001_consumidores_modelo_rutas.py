"""ADR-050, fase 0: congelar los consumidores del modelo de rutas (#1001).

Mientras llega el almacén de ADR-050, nada nuevo lee ni escribe ficheros por su
ruta en disco: lo que necesite un fichero lo pide por el documento. El desarrollo
sigue en paralelo, y cada consumidor nuevo del modelo de rutas es deuda que la
fase 1 tendría que deshacer (ADR-050 §I). La regla está en `REGLAS_DESARROLLO.md`
(«Documentos: el contenido es del almacén»); esto es lo que impide olvidarla.

Fallo silencioso que evita: que un consumidor nuevo del disco entre durante el
desarrollo en paralelo sin pasar por §M, y la fase 1 lo deje roto o apuntando a
rutas que ya no existen.

Cómo cuenta
-----------
Busca en `app/` los símbolos de `SIMBOLOS` y compara, fichero a fichero, el número
de apariciones con `PERMITIDOS`. El número es exacto en los dos sentidos: si sube,
ha entrado un consumidor; si baja, una fase de ADR-050 ha retirado alguno y hay
que bajarlo aquí, como el manifiesto de `test_832`. Un fichero permitido no es
carta blanca: los grandes (`expedientes/routes.py`, `mutaciones_arbol.py`,
`api_escritos.py`) siguen recibiendo código nuevo.

- **Python**, por AST: solo el código —atributos, nombres, imports, argumentos con
  nombre, definiciones y cadenas que son exactamente el símbolo
  (`config['PLANTILLAS_BASE']`)—. Los comentarios y los docstrings no cuentan.
- **Plantillas HTML**, por texto, quitando los comentarios `{# #}` y `<!-- -->`.

Desde el PR 5 de #1007 solo quedan los símbolos de las plantillas (`PLANTILLAS_BASE`,
`ruta_plantilla`), que pasan al almacén en la fase 4 (#1009). Los demás —`ruta_absoluta`,
`FILESYSTEM_BASE`, `hash_md5`, `ruta_pdf` y los `mover_*` de `rutas_esftt.py`— ya no
existen: quien los usara fallaría a la vista. `resolver_url()` lee del almacén.
La otra mitad de la regla de ADR-050 §B —solo el subsistema de almacenamiento ve
`ficheros` y la `ref`— es permanente y vive en
`test_1007_subsistema_almacenamiento.py` (llegó con la fase 1). Cuando `PERMITIDOS`
quede vacío, este test ya no puede fallar: se borra.

PUNTO CIEGO CONOCIDO
--------------------
Cuenta apariciones, no consumidores: un commit que retire una y añada otra en el
mismo fichero deja el número igual. Y no ve un acceso al disco que no use ninguno
de estos símbolos; ahí vale la revisión.
"""
import ast
import re
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# ADR-050 §I. Un `_` delante cuenta como el mismo símbolo (`_ruta_plantilla`).
SIMBOLOS = {'PLANTILLAS_BASE', 'ruta_plantilla'}

# Apariciones por fichero el 2026-10-02 (develop en c7d4a49), bajadas en el PR 5 de
# #1007. Solo bajan. NO subir un número ni añadir un fichero para hacer pasar el
# test: el arreglo es pedir el contenido por el documento.
PERMITIDOS = {
    'app/config.py': 3,
    'app/models/plantillas.py': 1,
    'app/modules/admin_plantillas/routes.py': 10,
    'app/modules/admin_plantillas/templates/admin_plantillas/_detalle_fragmento.html': 1,
    'app/modules/admin_plantillas/templates/admin_plantillas/_editar_fragmento.html': 2,
    'app/modules/admin_plantillas/templates/admin_plantillas/_panel_tokens.html': 1,
    'app/modules/admin_plantillas/templates/admin_plantillas/form.html': 5,
    'app/services/generador_escritos.py': 7,
    'app/services/generador_escritos_docx.py': 2,
    'app/services/generador_escritos_odt.py': 1,
}

_AYUDA = (
    "Lo que necesite un fichero lo pide por el documento, al módulo de contenido "
    "(`app.services.almacenamiento.contenido`). No subas el número ni añadas el "
    "fichero a PERMITIDOS: cada consumidor nuevo es deuda que la fase 4 tendría "
    "que deshacer. Ver REGLAS_DESARROLLO.md, «Documentos: el contenido es del almacén»."
)

_RE_HTML = re.compile(r'(?<!\w)_?(' + '|'.join(sorted(SIMBOLOS)) + r')(?!\w)')
_RE_COMENTARIO_HTML = re.compile(r'\{#.*?#\}|<!--.*?-->', re.S)


def _nombres_python(fuente):
    """Los nombres que usa el código, sin comentarios ni docstrings."""
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Attribute):
            yield nodo.attr
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield nodo.name
        elif isinstance(nodo, ast.Name):
            yield nodo.id
        elif isinstance(nodo, ast.alias):
            yield nodo.name
        elif isinstance(nodo, ast.keyword) and nodo.arg:
            yield nodo.arg
        elif isinstance(nodo, ast.Constant) and nodo.value in SIMBOLOS:
            # Solo la cadena exacta: la clave de configuración, no un texto que la cite.
            yield nodo.value


def _apariciones(fichero):
    """Counter {símbolo: veces} de un fichero .py o .html."""
    texto = fichero.read_text(encoding='utf-8')
    if fichero.suffix == '.html':
        texto = _RE_COMENTARIO_HTML.sub('', texto)
        return Counter(m.group(1) for m in _RE_HTML.finditer(texto))
    cuenta = Counter()
    for nombre in _nombres_python(texto):
        simbolo = nombre.lstrip('_')
        if simbolo in SIMBOLOS:
            cuenta[simbolo] += 1
    return cuenta


def _consumidores():
    """{fichero relativo a la raíz: Counter} de los ficheros de app/ que usan el modelo de rutas."""
    resultado = {}
    for fichero in sorted((RAIZ / 'app').rglob('*')):
        if fichero.suffix in ('.py', '.html') and fichero.is_file():
            cuenta = _apariciones(fichero)
            if cuenta:
                resultado[fichero.relative_to(RAIZ).as_posix()] = cuenta
    return resultado


def _detalle(cuenta):
    return ', '.join(f'{s} ×{n}' for s, n in sorted(cuenta.items()))


def test_ningun_consumidor_nuevo_del_modelo_de_rutas():
    """Ningún fichero de app/ usa el modelo de rutas más veces que las permitidas."""
    de_mas = {
        fichero: cuenta for fichero, cuenta in _consumidores().items()
        if sum(cuenta.values()) > PERMITIDOS.get(fichero, 0)
    }
    assert not de_mas, (
        "Consumidores nuevos del modelo de rutas (ADR-050 §I, #1001):\n" +
        '\n'.join(
            f'  - {fichero}: {sum(c.values())}, permitidas '
            f'{PERMITIDOS.get(fichero, 0)} ({_detalle(c)})'
            for fichero, c in sorted(de_mas.items())
        ) +
        f"\n\n{_AYUDA}"
    )


def test_permitidos_baja_con_cada_fase():
    """Lo que retira una fase de ADR-050 sale de PERMITIDOS: el número solo baja."""
    actuales = _consumidores()
    de_menos = {
        fichero: (permitidas, sum(actuales.get(fichero, Counter()).values()))
        for fichero, permitidas in PERMITIDOS.items()
        if sum(actuales.get(fichero, Counter()).values()) < permitidas
    }
    assert not de_menos, (
        "Estos ficheros usan ya menos el modelo de rutas de lo que dice "
        "PERMITIDOS; baja el número, o borra la entrada si ha llegado a 0:\n" +
        '\n'.join(
            f'  - {fichero}: permitidas {permitidas}, hay {hay}'
            for fichero, (permitidas, hay) in sorted(de_menos.items())
        )
    )
