"""
Guard de tests/README.md §3 — hook PreToolUse sobre Bash, al hacer `git commit`.

Motivo (#1014): cuando un test se pone rojo hay tres lecturas, y solo una
justifica tocar su `assert`:

  1. cambió la decisión que el test fijaba → se actualiza, diciendo cuál;
  2. se rompió por su forma → el arreglo va a un helper de `conftest.py`, sin
     tocar `assert`;
  3. el código se desvía de una decisión estable → se corrige el código, que es
     para lo que existe el test.

En septiembre de 2026, 128 retoques adaptaron el test de un issue al código de
otro sin decir cuál de las tres era: quien disparaba la alarma la apagaba sin
dejar rastro. La regla escrita no bastó. Este hook la exige.

Qué exige: si el commit modifica o borra un `assert` (o un `pytest.raises`, o un
`.assert_*(` de mock) de un `tests/**/test_*.py` que ya existía —smoke incluidos—,
el mensaje lleva una de estas líneas:

    Decisión que cambia: <ADR-NNN §… o #NNN>     (debe citar un ADR o un issue)
    Test retirado: <por qué>                      (mín. 40 caracteres)

No la pide:
  - si el número de issue del fichero (`test_<N>_…`) aparece como `#N` en el
    asunto del commit (la primera línea): es el desarrollo del mismo issue;
  - si la línea quitada reaparece igual, salvo espacios, en cualquier test del
    mismo commit: solo se mueve o se reformatea;
  - en tests nuevos;
  - al cerrar un merge o un cherry-pick: los cambios son de otros commits.

Qué diff mira: lo preparado (`--cached`); con `-a`, también lo modificado sin
preparar; con `--amend`, contra el padre de HEAD.

Límites conocidos: no ve un valor esperado que cambie dentro de un `parametrize`,
ni las líneas de continuación de un `assert` partido en varias; no ve commits
lanzados desde la tool PowerShell ni hechos a mano fuera de Claude Code. El hook
obliga a nombrar la decisión, no puede juzgar si es verdad: eso se ve en el diff.

Contrato del hook (stdin/stdout JSON):
  entrada: {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}
  salida:  nada (silencio = permitido)
           o {"hookSpecificOutput": {"permissionDecision": "deny", ...}}
Cualquier fallo interno permite: un guard no debe bloquear por un error propio.

Fuente de verdad de la norma: tests/README.md §3. Este fichero es derivado.
"""
import collections
import json
import os
import re
import shlex
import subprocess
import sys

# tests/test_*.py en cualquier profundidad, smoke incluidos; fuera fixtures/.
RUTA_TEST = re.compile(r'(?:\A|/)tests/(?!fixtures/)(?:[^/]+/)*test_[^/]+\.py\Z')
ISSUES_FICHERO = re.compile(r'\Atest_((?:\d+_)+)')
LINEA_ASSERT = re.compile(r'^\s*assert\b|\bpytest\.raises\(|\.assert_\w*\(')
REFERENCIA = re.compile(r'#\d+|\bADR-\d+', re.IGNORECASE)
MARCA_DECISION = re.compile(r'^[ \t]*Decisi[oó]n que cambia:[ \t]*(.*)$', re.IGNORECASE | re.MULTILINE)
MARCA_RETIRADO = re.compile(r'^[ \t]*Test retirado:[ \t]*(.*)$', re.IGNORECASE)
MIN_CARACTERES_RETIRADO = 40
OPERADORES = {'&&', '||', ';', '|', '&'}
# Opciones cortas de `git commit` que consumen valor (pegado o en el token siguiente).
CORTAS_CON_VALOR = set('mFCct')
MAX_LINEAS_EN_MENSAJE = 3
TIEMPO_GIT = 5

REGLA = (
    'Un test rojo admite tres lecturas: (1) cambió la decisión que fijaba → añade al '
    'mensaje «Decisión que cambia: ADR-NNN §… o #NNN»; (2) se rompió por su forma (un '
    'constructor, una fixture, una firma) → el arreglo va a un helper de conftest.py y '
    'el assert no se toca; (3) el código se desvía de una decisión estable → corrige el '
    'código, no el test. Si se retira un test que no supera tests/README.md §3: «Test '
    f'retirado: <por qué>» (mín. {MIN_CARACTERES_RETIRADO} caracteres). Si no sabes cuál '
    'de las tres es, no adaptes el test: díselo al usuario. '
    '(Lo exige .claude/hooks/reglas_asserts_guard.py, no el usuario.)'
)


# ── Lectura del comando ─────────────────────────────────────────────────────

def _ruta_local(ruta: str) -> str:
    """`/d/BDDAT` (MSYS) → `D:/BDDAT` cuando el Python que corre el hook es de Windows."""
    if os.name == 'nt':
        m = re.match(r'\A/([a-zA-Z])(/.*)?\Z', ruta)
        if m:
            return f'{m.group(1).upper()}:{m.group(2) or "/"}'
    return ruta


def _resolver(base: str, ruta: str) -> str:
    ruta = _ruta_local(ruta)
    return ruta if os.path.isabs(ruta) else os.path.normpath(os.path.join(base, ruta))


def _segmentos(comando: str):
    lexer = shlex.shlex(comando, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    actual = []
    for token in lexer:
        if token in OPERADORES:
            if actual:
                yield actual
            actual = []
        else:
            actual.append(token)
    if actual:
        yield actual


def _commits(comando: str, cwd: str):
    """Cada `git … commit …` del comando: (directorio del repo, argumentos de commit)."""
    for tokens in _segmentos(comando):
        if tokens[0] == 'cd' and len(tokens) == 2:
            cwd = _resolver(cwd, tokens[1])
            continue
        if os.path.basename(tokens[0]) not in ('git', 'git.exe'):
            continue
        repo = cwd
        i = 1
        while i < len(tokens) and tokens[i].startswith('-'):
            if tokens[i] == '-C' and i + 1 < len(tokens):
                repo = _resolver(repo, tokens[i + 1])
                i += 2
            elif tokens[i] == '-c' and i + 1 < len(tokens):
                i += 2
            else:
                i += 1
        if i < len(tokens) and tokens[i] == 'commit':
            yield repo, tokens[i + 1:]


def _opciones_commit(args, repo: str):
    """(mensaje o None si no se puede saber, todo, amend)."""
    mensajes, fichero, todo, amend = [], None, False, False
    i = 0
    while i < len(args):
        arg = args[i]
        siguiente = args[i + 1] if i + 1 < len(args) else ''
        if arg == '--':
            break
        if arg in ('--all',):
            todo = True
        elif arg == '--amend':
            amend = True
        elif arg.startswith('--message='):
            mensajes.append(arg.split('=', 1)[1])
        elif arg == '--message':
            mensajes.append(siguiente)
            i += 1
        elif arg.startswith('--file='):
            fichero = arg.split('=', 1)[1]
        elif arg == '--file':
            fichero = siguiente
            i += 1
        elif arg.startswith('-') and not arg.startswith('--') and len(arg) > 1:
            for pos, letra in enumerate(arg[1:], start=1):
                if letra == 'a':
                    todo = True
                if letra in CORTAS_CON_VALOR:
                    valor = arg[pos + 1:]
                    if not valor:
                        valor = siguiente
                        i += 1
                    if letra == 'm':
                        mensajes.append(valor)
                    elif letra == 'F':
                        fichero = valor
                    break
        i += 1

    if mensajes:
        return '\n\n'.join(mensajes), todo, amend
    if fichero and fichero != '-':
        try:
            with open(_resolver(repo, fichero), encoding='utf-8', errors='replace') as f:
                return f.read(), todo, amend
        except OSError:
            return None, todo, amend
    if amend:
        return _git(repo, 'log', '-1', '--format=%B'), todo, amend
    return None, todo, amend


# ── Lectura del diff ────────────────────────────────────────────────────────

def _git(repo: str, *args):
    r = subprocess.run(['git', '-C', repo, '-c', 'core.quotepath=false', *args],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=TIEMPO_GIT)
    return r.stdout if r.returncode == 0 else None


def _en_merge(repo: str) -> bool:
    return any(_git(repo, 'rev-parse', '-q', '--verify', ref) is not None
               for ref in ('MERGE_HEAD', 'CHERRY_PICK_HEAD'))


def _diff(repo: str, todo: bool, amend: bool):
    base = 'HEAD~1' if amend else 'HEAD'
    if _git(repo, 'rev-parse', '-q', '--verify', base) is None:
        return None  # sin commit base no hay tests que ya existieran
    args = ['diff', '--no-color', '--no-ext-diff', '-U0', '-M', '--diff-filter=ADMR']
    if not todo:
        args.append('--cached')
    return _git(repo, *args, base, '--', 'tests/')


def _normalizada(linea: str) -> str:
    return ''.join(linea.split())


def _asserts_quitados(diff: str):
    """{fichero preexistente: [líneas de assert quitadas que no reaparecen]}."""
    quitados = collections.defaultdict(list)
    añadidos = collections.Counter()
    fichero, origen, nuevo, cabecera = None, None, False, False
    for linea in diff.split('\n'):
        if linea.startswith('diff --git '):
            fichero, origen, nuevo, cabecera = None, None, False, True
        elif linea.startswith('@@'):
            cabecera = False
        elif cabecera:
            if linea.startswith('new file mode'):
                nuevo = True
            elif linea.startswith('--- '):
                ruta = linea[4:]
                origen = ruta[2:] if ruta.startswith('a/') else None
            elif linea.startswith('+++ '):
                ruta = linea[4:]
                # Un fichero borrado llega como `+++ /dev/null`: cuenta con su ruta de origen.
                fichero = ruta[2:] if ruta.startswith('b/') else origen
        elif fichero and RUTA_TEST.search(fichero):
            if linea.startswith('+') and LINEA_ASSERT.search(linea[1:]):
                añadidos[_normalizada(linea[1:])] += 1
            elif linea.startswith('-') and not nuevo and LINEA_ASSERT.search(linea[1:]):
                quitados[fichero].append(linea[1:].strip())

    resultado = {}
    for fichero, lineas in quitados.items():
        sin_par = []
        for linea in lineas:
            clave = _normalizada(linea)
            if añadidos[clave] > 0:
                añadidos[clave] -= 1  # movida o reformateada
            else:
                sin_par.append(linea)
        if sin_par:
            resultado[fichero] = sin_par
    return resultado


# ── Decisión ────────────────────────────────────────────────────────────────

def _issues_del_fichero(fichero: str) -> set:
    m = ISSUES_FICHERO.match(os.path.basename(fichero))
    return set(m.group(1).strip('_').split('_')) if m else set()


def _justificado(mensaje: str) -> bool:
    for m in MARCA_DECISION.finditer(mensaje):
        if REFERENCIA.search(m.group(1)):
            return True
    lineas = mensaje.split('\n')
    for i, linea in enumerate(lineas):
        m = MARCA_RETIRADO.match(linea)
        if not m:
            continue
        partes = [m.group(1)]
        for siguiente in lineas[i + 1:]:
            if not siguiente.strip():
                break
            partes.append(siguiente.strip())
        if len(' '.join(' '.join(partes).split())) >= MIN_CARACTERES_RETIRADO:
            return True
    return False


def _mensaje_denegacion(payload: dict):
    """Texto de denegación, o None si se permite."""
    if payload.get('tool_name') != 'Bash':
        return None
    comando = (payload.get('tool_input') or {}).get('command') or ''
    if 'commit' not in comando or 'git' not in comando:
        return None
    cwd = _ruta_local(payload.get('cwd') or os.getcwd())

    for repo, args in _commits(comando, cwd):
        mensaje, todo, amend = _opciones_commit(args, repo)
        if mensaje is None or _en_merge(repo):
            continue  # sin mensaje que leer (editor) o cambios ajenos al commit
        diff = _diff(repo, todo, amend)
        if not diff:
            continue
        # Solo el asunto (`[CAT] #N …`) dice de qué issue es el commit; un `#N`
        # citado de pasada en el cuerpo no lo hace suyo (bc301dca cambió el 500
        # de test_885 a 422 citando «#885» en el cuerpo).
        issues_asunto = set(re.findall(r'#(\d+)', mensaje.strip().split('\n', 1)[0]))
        pendientes = {f: lineas for f, lineas in _asserts_quitados(diff).items()
                      if not (_issues_del_fichero(f) & issues_asunto)}
        if pendientes and not _justificado(mensaje):
            detalle = '; '.join(
                f'{f}: ' + ' | '.join(lineas[:MAX_LINEAS_EN_MENSAJE])
                + (' …' if len(lineas) > MAX_LINEAS_EN_MENSAJE else '')
                for f, lineas in sorted(pendientes.items()))
            return ('tests/README.md §3 — el commit modifica o borra asserts de tests de '
                    f'otro issue sin decir por qué. {detalle}. ' + REGLA)
    return None


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # entrada ilegible: no bloquear nunca por un fallo del guard

    try:
        razon = _mensaje_denegacion(payload)
    except Exception:
        return 0  # un fallo interno tampoco bloquea

    if razon:
        json.dump({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'deny',
                'permissionDecisionReason': razon,
            }
        }, sys.stdout, ensure_ascii=False)
    return 0


if __name__ == '__main__':
    sys.exit(main())
