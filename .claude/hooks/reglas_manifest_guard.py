"""
Guard del manifest de React — hook PreToolUse sobre Bash, al hacer `git commit`.

Motivo: `app/static/js/react/manifest.json` es lo único compilado que se versiona y
hace de marca de versión: `scripts/nube/arrancar_app.sh` recompila si algún fichero
que nombra no existe en el contenedor. Si un commit cambia `react-src/` sin llevar el
manifest recompilado, la nube sirve bundles viejos sin avisar. Pasó con #1047: ocho
commits cambiaron la isla del árbol y ninguno actualizó el manifest.

Qué exige: si el commit prepara ficheros que alteran el bundle (`react-src/src/`,
`vite.config.js`, `package.json`, `package-lock.json`), el manifest va en el mismo
commit. Si de verdad no cambia (p. ej. solo comentarios, que el minificado descarta),
el mensaje lo dice:

    Manifest sin cambios: <por qué>               (mín. 20 caracteres)

Lo contrario (manifest sin `react-src/`) no se bloquea: puede ser la corrección de un
desfase. Se avisa al modelo como contexto, nada más.

No pide nada al cerrar un merge o un cherry-pick: los cambios son de otros commits.

Qué diff mira: lo preparado (`--cached`); con `-a`, también lo modificado sin
preparar; con `--amend`, contra el padre de HEAD.

Límite conocido: comprueba que el manifest viaje en el commit, no que esté
recompilado de verdad (eso exigiría compilar dentro del hook). Tampoco ve commits
lanzados desde la tool PowerShell ni hechos a mano fuera de Claude Code.

Contrato del hook (stdin/stdout JSON):
  entrada: {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}
  salida:  nada (silencio = permitido)
           o {"hookSpecificOutput": {"permissionDecision": "deny", ...}}
           o {"hookSpecificOutput": {"additionalContext": "..."}}   (aviso, permite)
Cualquier fallo interno permite: un guard no debe bloquear por un error propio.

Fuente de verdad de la norma: docs/guias/GUIA_REACT_ISLAS.md §«El manifest.json
versionado». Este fichero es derivado.
"""
import json
import os
import re
import sys

# El parseo de `git commit` (comando, opciones, merge) es el mismo que el de
# reglas_asserts_guard.py: se reutiliza en vez de duplicarlo.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reglas_asserts_guard import _commits, _en_merge, _git, _opciones_commit, _ruta_local  # noqa: E402

MANIFEST = 'app/static/js/react/manifest.json'
# Ficheros que alteran el bundle; `react-src/index.html` solo sirve a `npm run dev`.
ALTERA_BUNDLE = re.compile(
    r'\Areact-src/(?:src/.+|vite\.config\.js|package\.json|package-lock\.json)\Z')
MARCA_SIN_CAMBIOS = re.compile(r'^[ \t]*Manifest sin cambios:[ \t]*(.*)$', re.IGNORECASE | re.MULTILINE)
MIN_CARACTERES = 20

REGLA = (
    'El manifest.json de React hace de marca de versión para la nube: sin él recompilado '
    'en el mismo commit, la nube sirve bundles viejos sin avisar. Haz «Build React» y '
    'añade app/static/js/react/manifest.json al commit. Si el cambio no altera el bundle '
    f'(p. ej. solo comentarios), añade al mensaje «Manifest sin cambios: <por qué>» (mín. '
    f'{MIN_CARACTERES} caracteres). Norma: docs/guias/GUIA_REACT_ISLAS.md §«El manifest.json '
    'versionado». (Lo exige .claude/hooks/reglas_manifest_guard.py, no el usuario.)'
)

AVISO = (
    'Este commit lleva app/static/js/react/manifest.json sin ningún fichero de react-src/. '
    'Es legítimo solo si corrige un desfase del repo (build limpio que deja el manifest '
    'distinto); si no, no debería ir.'
)


def _ficheros(repo: str, todo: bool, amend: bool):
    base = 'HEAD~1' if amend else 'HEAD'
    if _git(repo, 'rev-parse', '-q', '--verify', base) is None:
        return None
    args = ['diff', '--name-only', '--no-ext-diff', '--diff-filter=ACDMR']
    if not todo:
        args.append('--cached')
    salida = _git(repo, *args, base)
    return None if salida is None else [f for f in salida.split('\n') if f]


def _resultado(payload: dict):
    """(denegación, aviso); ambos None si se permite en silencio."""
    if payload.get('tool_name') != 'Bash':
        return None, None
    comando = (payload.get('tool_input') or {}).get('command') or ''
    if 'commit' not in comando or 'git' not in comando:
        return None, None
    cwd = _ruta_local(payload.get('cwd') or os.getcwd())

    aviso = None
    for repo, args in _commits(comando, cwd):
        mensaje, todo, amend = _opciones_commit(args, repo)
        if _en_merge(repo):
            continue
        ficheros = _ficheros(repo, todo, amend)
        if not ficheros:
            continue
        toca_react = any(ALTERA_BUNDLE.match(f) for f in ficheros)
        lleva_manifest = MANIFEST in ficheros
        if toca_react and not lleva_manifest:
            if mensaje is None:
                # Mensaje por editor: no se puede saber si trae la marca; se deniega igual.
                return REGLA, None
            if not any(len(' '.join(m.group(1).split())) >= MIN_CARACTERES
                       for m in MARCA_SIN_CAMBIOS.finditer(mensaje)):
                return REGLA, None
        elif lleva_manifest and not toca_react:
            aviso = AVISO
    return None, aviso


def main():
    try:
        # Se lee en bytes: ver el comentario equivalente en reglas_asserts_guard.py.
        payload = json.loads(sys.stdin.buffer.read().decode('utf-8', errors='replace'))
    except Exception:
        return 0  # entrada ilegible: no bloquear nunca por un fallo del guard

    try:
        razon, aviso = _resultado(payload)
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
    elif aviso:
        json.dump({
            'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'additionalContext': aviso,
            }
        }, sys.stdout)
    return 0


if __name__ == '__main__':
    sys.exit(main())
