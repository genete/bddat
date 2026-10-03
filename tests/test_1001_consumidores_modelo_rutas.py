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
  (`config['FILESYSTEM_BASE']`)—. Los comentarios y los docstrings no cuentan.
- **Plantillas HTML**, por texto, quitando los comentarios `{# #}` y `<!-- -->`.

`resolver_url()` no está en la lista: sobrevive y pasa a leer del almacén (§M).
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
SIMBOLOS = {
    'ruta_absoluta', 'FILESYSTEM_BASE', 'PLANTILLAS_BASE', 'hash_md5',
    'ruta_plantilla', 'ruta_pdf', 'mover_a_esftt', 'mover_a_pool',
    'nombre_pool_unico', 'ruta_pool_documento', 'ruta_destino_esftt_fichero',
}
# Como variable local, `ruta_absoluta` es un nombre genérico y no el método de
# `Documento`: en `admin_plantillas/routes.py` y `alta_expediente.py` lo es.
SOLO_COMO_METODO = {'ruta_absoluta'}

# Apariciones por fichero el 2026-10-02 (develop en c7d4a49). Solo bajan.
# NO subir un número ni añadir un fichero para hacer pasar el test: el arreglo
# es pedir el contenido por el documento.
PERMITIDOS = {
    'app/config.py': 6,
    'app/models/certificados_fase.py': 1,
    'app/models/documentos.py': 5,
    'app/models/plantillas.py': 1,
    'app/modules/admin_plantillas/routes.py': 10,
    'app/modules/admin_plantillas/templates/admin_plantillas/_detalle_fragmento.html': 1,
    'app/modules/admin_plantillas/templates/admin_plantillas/_editar_fragmento.html': 2,
    'app/modules/admin_plantillas/templates/admin_plantillas/_panel_tokens.html': 1,
    'app/modules/admin_plantillas/templates/admin_plantillas/form.html': 5,
    'app/modules/expedientes/routes.py': 6,
    'app/routes/api_escritos.py': 7,
    'app/services/alta_expediente.py': 3,
    'app/services/cert_fin_instruccion.py': 3,
    'app/services/extraccion_texto_documento.py': 1,
    'app/services/generador_cert.py': 7,
    'app/services/generador_escritos.py': 7,
    'app/services/generador_escritos_docx.py': 2,
    'app/services/generador_escritos_odt.py': 1,
    'app/services/ingesta_pool.py': 9,
    'app/services/mutaciones_arbol.py': 9,
    'app/services/regeneracion_escritos.py': 7,
    'app/services/rutas_esftt.py': 22,
}

_AYUDA = (
    "Lo que necesite un fichero lo pide por el documento: "
    "`documento.resolver_url()`, que sobrevive a ADR-050 y pasará a leer del "
    "almacén. No subas el número ni añadas el fichero a PERMITIDOS: cada "
    "consumidor nuevo es deuda que la fase 1 tendría que deshacer. Ver "
    "REGLAS_DESARROLLO.md, «Documentos: el contenido es del almacén»."
)

_RE_HTML = re.compile(
    r'(?<!\w)_?(' + '|'.join(sorted(SIMBOLOS - SOLO_COMO_METODO))
    + '|' + '|'.join(rf'{s}(?=\s*\()' for s in sorted(SOLO_COMO_METODO))
    + r')(?!\w)'
)
_RE_COMENTARIO_HTML = re.compile(r'\{#.*?#\}|<!--.*?-->', re.S)


def _nombres_python(fuente):
    """(nombre, es_nombre_suelto) de lo que usa el código, sin comentarios ni docstrings."""
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Attribute):
            yield nodo.attr, False
        elif isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield nodo.name, False
        elif isinstance(nodo, ast.Name):
            yield nodo.id, True
        elif isinstance(nodo, ast.alias):
            yield nodo.name, True
        elif isinstance(nodo, ast.keyword) and nodo.arg:
            yield nodo.arg, True
        elif isinstance(nodo, ast.Constant) and nodo.value in SIMBOLOS:
            # Solo la cadena exacta: la clave de configuración, no un texto que la cite.
            yield nodo.value, False


def _apariciones(fichero):
    """Counter {símbolo: veces} de un fichero .py o .html."""
    texto = fichero.read_text(encoding='utf-8')
    if fichero.suffix == '.html':
        texto = _RE_COMENTARIO_HTML.sub('', texto)
        return Counter(m.group(1) for m in _RE_HTML.finditer(texto))
    cuenta = Counter()
    for nombre, suelto in _nombres_python(texto):
        simbolo = nombre.lstrip('_')
        if simbolo in SIMBOLOS and not (suelto and simbolo in SOLO_COMO_METODO):
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
