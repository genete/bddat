"""
Guard de tests/README.md §3 — hook PreToolUse sobre las tools Write y Edit.

Motivo: `tests/README.md` §3 y `CLAUDE.md` piden que todo test nuevo nombre el
fallo silencioso que evita, pero eso exige una ACCIÓN de Claude que se olvida
issue tras issue. Este hook no recuerda la regla: la exige. Si lo que se va a
escribir añade tests y no trae la justificación, se deniega con el motivo y
Claude la formula (o le dice al usuario que no sabe nombrarla y no escribe el test).

La justificación es una línea (admite continuación hasta la primera línea en
blanco, o una lista con guiones):

    Fallo silencioso que evita: <qué se rompería sin que nadie lo vea>

Qué se exige, según lo que se escribe en `tests/**/test_*.py`:
  - Write de un fichero NUEVO: la línea, en el docstring del módulo.
  - Write sobre un fichero existente: si tiene más `def test_` que el del disco,
    más justificaciones que el del disco.
  - Edit: si `new_string` tiene más `def test_` que `old_string`, más
    justificaciones que `old_string`. Un Edit que añade varios tests hermanos
    comparte una sola justificación; en el docstring de la función o en un
    comentario justo encima.
Retocar, renombrar o arreglar un test existente no añade `def test_` y no se toca.

Quedan fuera `tests/smoke/` (ADR-019: obligatorio con cada vista, su razón es
fija), `tests/fixtures/` y `conftest.py`.

El hook obliga a formularlo, no puede juzgar si es verdad: eso lo ve quien
revisa el diff. Tampoco ve lo que se escriba desde Bash (`cat >`, `git mv`).

Contrato del hook (stdin/stdout JSON):
  entrada: {"tool_name": "Write"|"Edit", "tool_input": {...}}
  salida:  nada (silencio = permitido)
           o {"hookSpecificOutput": {"permissionDecision": "deny", ...}}

Fuente de verdad de la norma: tests/README.md §3. Este fichero es derivado.
"""
import ast
import json
import os
import re
import sys

# tests/test_*.py en cualquier profundidad, salvo smoke/ y fixtures/.
RUTA_TEST = re.compile(r'(?:\A|/)tests/(?!smoke/|fixtures/)(?:[^/]+/)*test_[^/]+\.py\Z')
DEF_TEST = re.compile(r'^[ \t]*(?:async[ \t]+)?def[ \t]+test_\w*', re.MULTILINE)
# El marcador puede ir en docstring (con o sin las comillas delante) o en comentario.
MARCADOR = re.compile(
    r'^[ \t]*(?:#|"""|\'\'\')?[ \t]*Fallo silencioso que evita:[ \t]*(.*)$',
    re.IGNORECASE,
)
MIN_CARACTERES = 40
VACIAS = re.compile(r'\A(?:todo|tbd|n/?a|ninguno|nada|-|\.\.\.|…|<.*>)\Z', re.IGNORECASE)

REGLA = (
    'Antes de escribirlo: (1) ¿ya hay un fichero que pruebe ese módulo? Amplíalo '
    '(README §5). (2) ¿Vigila algo de la lista «Sí» del §3 (calcula o decide, '
    'escribe, permisos, restricción de BD, regresión de un bug real)? Si es una '
    'vista de solo lectura, un texto o una combinación más, no lleva test más allá '
    'de su smoke. Si merece test, añade una línea «Fallo silencioso que evita: …» '
    f'(mín. {MIN_CARACTERES} caracteres) diciendo qué se rompería sin que nadie lo vea. '
    'Si no sabes nombrarlo, no escribas el test: díselo al usuario. '
    '(Lo exige .claude/hooks/reglas_tests_guard.py, no el usuario.)'
)
MENSAJE_FICHERO_NUEVO = (
    'tests/README.md §3 — fichero de test nuevo sin justificación en el docstring del módulo. '
    + REGLA
)
MENSAJE_TEST_AÑADIDO = (
    'tests/README.md §3 — se añade un test sin justificación. La línea va en el docstring de '
    'la función o en un comentario justo encima; un bloque de tests hermanos comparte una. '
    + REGLA
)


def _normalizar(ruta: str) -> str:
    return ruta.replace('\\', '/')


def _justificaciones(texto: str) -> int:
    """Nº de justificaciones válidas (marcador + texto suficiente) en `texto`."""
    lineas = texto.split('\n')
    validas = 0
    for i, linea in enumerate(lineas):
        m = MARCADOR.match(linea)
        if not m:
            continue
        partes = [m.group(1)]
        for siguiente in lineas[i + 1:]:
            limpia = siguiente.strip()
            if not limpia or limpia.startswith(('"""', "'''")):
                break  # línea en blanco o cierre del docstring
            partes.append(limpia.lstrip('#').strip() if limpia.startswith('#') else limpia)
            if limpia.endswith(('"""', "'''")):
                break
        # Un docstring de una línea cierra en la propia línea del marcador.
        justificacion = re.split(r'"""|\'\'\'', ' '.join(partes))[0]
        justificacion = ' '.join(justificacion.split())
        if len(justificacion) >= MIN_CARACTERES and not VACIAS.match(justificacion):
            validas += 1
    return validas


def _docstring_de_modulo(contenido: str):
    """Docstring del módulo, '' si no hay, None si el fichero no compila.

    Si no compila, pytest lo dirá enseguida: un guard no debe convertir un error de
    sintaxis en un bloqueo con otro motivo.
    """
    try:
        return ast.get_docstring(ast.parse(contenido)) or ''
    except SyntaxError:
        return None


def _leer(ruta: str):
    try:
        with open(ruta, encoding='utf-8', errors='replace') as f:
            return f.read()
    except OSError:
        return None


def _mensaje_denegacion(herramienta: str, entrada: dict):
    """Texto de denegación, o None si se permite."""
    ruta_real = entrada.get('file_path') or ''
    if not RUTA_TEST.search(_normalizar(ruta_real)):
        return None

    if herramienta == 'Write':
        contenido = entrada.get('content') or ''
        if not os.path.exists(ruta_real):
            docstring = _docstring_de_modulo(contenido)
            if docstring is not None and _justificaciones(docstring) == 0:
                return MENSAJE_FICHERO_NUEVO
            return None
        en_disco = _leer(ruta_real)
        if en_disco is None:
            return None
        añadidos = len(DEF_TEST.findall(contenido)) - len(DEF_TEST.findall(en_disco))
        if añadidos > 0 and _justificaciones(contenido) <= _justificaciones(en_disco):
            return MENSAJE_TEST_AÑADIDO
        return None

    if herramienta == 'Edit':
        antes = entrada.get('old_string') or ''
        despues = entrada.get('new_string') or ''
        añadidos = len(DEF_TEST.findall(despues)) - len(DEF_TEST.findall(antes))
        if añadidos > 0 and _justificaciones(despues) <= _justificaciones(antes):
            return MENSAJE_TEST_AÑADIDO
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # entrada ilegible: no bloquear nunca por un fallo del guard

    try:
        razon = _mensaje_denegacion(payload.get('tool_name'), payload.get('tool_input') or {})
    except Exception:
        return 0  # un fallo interno tampoco bloquea

    if razon:
        json.dump({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': razon,
            }
        }, sys.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
