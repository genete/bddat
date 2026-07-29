"""
Guard de REGLAS_BASH.md — hook PreToolUse sobre la tool Bash.

Motivo: `CLAUDE.md` ordena leer `docs/guias/REGLAS_BASH.md` antes de cualquier
comando Bash, pero eso exige una ACCIÓN de Claude que se olvida turnos después
(ver recaídas documentadas). Este hook no recuerda la regla: la aplica. Si el
comando trae un anti-patrón conocido, se deniega con el arreglo concreto, y
Claude reescribe sin que el usuario vea una petición de aprobación.

Contrato del hook (stdin/stdout JSON):
  entrada: {"tool_name": "Bash", "tool_input": {"command": "..."}}
  salida:  nada (silencio = permitido)
           o {"hookSpecificOutput": {"permissionDecision": "deny", ...}}

Fuente de verdad de las reglas: docs/guias/REGLAS_BASH.md. Si esa tabla cambia,
actualizar REGLAS aquí — este fichero es derivado, no la fuente.
"""
import json
import re
import sys

# (patrón, etiqueta de la regla, arreglo concreto)
# Solo entran anti-patrones de alta confianza: un falso positivo aquí es una
# interrupción igual de cara que la que intentamos evitar.
REGLAS = [
    (r'\$\(',
     'sustitución $()',
     'Separar en llamadas Bash secuenciales, o Write a docs_prueba/temp/ y pasar el fichero.'),
    (r'`',
     'backticks',
     'Separar en llamadas Bash secuenciales, o Write a docs_prueba/temp/ y pasar el fichero.'),
    (r'\n',
     'saltos de línea en el comando',
     'Write el script completo a docs_prueba/temp/ y ejecutarlo (python fichero.py / bash fichero.sh).'),
    (r'\bsed\b[^;|]*\s-i\b',
     'sed -i (escritura con sed)',
     'Usar la tool Edit.'),
    (r'\bsed\b[^;|]*\*',
     'glob en ruta de sed',
     'Resolver la ruta antes con la tool Glob, o leer rangos con la tool Read (offset/limit).'),
    (r'\\\|',
     r'grep con \| (BRE escapado)',
     "Usar grep -E 'pat1|pat2' o -e pat1 -e pat2."),
    (r"\$'",
     'ansi_c_string ($\'...\')',
     'Reformular sin $\'...\', o procesar con un script Python en docs_prueba/temp/.'),
    (r'source\s+\S*venv/Scripts/activate',
     'source venv/Scripts/activate',
     'Usar directamente venv/Scripts/python.exe (no hace falta activar).'),
    # (cd + git: ver REGLAS_COMPUESTAS — no basta un patrón lineal)
    (r'\b(rm|mv)\b[^;|]*docs_prueba/temp',
     'rm/mv sobre docs_prueba/temp',
     'No hacer nada: los temporales se dejan, Carlos los borra a mano. Si el nombre destino ya existe, crear otro con sufijo distinto.'),
    (r'--body\s+"[^"]*#',
     '--body con # (se lee como línea de comentario)',
     'Write el cuerpo a docs_prueba/temp/ y usar --body-file.'),
    (r'[A-Za-z0-9_]{2,}\\[A-Za-z0-9_]{3,}',
     'ruta con backslash de Windows',
     'En Bash (MSYS2) las rutas van con /: app/models/, nunca app\\models\\.'),
]


def _es_palabra_de_comando(comando: str, palabra: str) -> bool:
    """`palabra` aparece como comando, no como argumento ni dentro de otra palabra."""
    return re.search(r'(?:\A|[;&|]\s*)' + palabra + r'\s', comando) is not None


def _cd_junto_a_git(comando: str) -> bool:
    """`cd` y `git` en el mismo comando, en cualquier orden y con cualquier separador.

    La tabla de REGLAS_BASH.md solo documentaba `cd /ruta && git`, pero el evaluador
    marca la mera convivencia de ambos ("changes directory before running git, which
    can execute untrusted hooks from the target directory") — da igual que el git vaya
    delante y que el separador sea `;`.
    """
    return _es_palabra_de_comando(comando, 'cd') and _es_palabra_de_comando(comando, 'git')


# Reglas que no caben en un patrón lineal: (predicado, etiqueta, arreglo).
REGLAS_COMPUESTAS = [
    (_cd_junto_a_git,
     'cd conviviendo con git en el mismo comando',
     'Usar git -C /ruta y, si hace falta otro comando, emitirlo en una llamada Bash aparte.'),
]


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # entrada ilegible: no bloquear nunca por un fallo del guard

    comando = (payload.get('tool_input') or {}).get('command') or ''
    if not comando:
        return 0

    detectadas = [
        (etiqueta, arreglo)
        for patron, etiqueta, arreglo in REGLAS
        if re.search(patron, comando)
    ] + [
        (etiqueta, arreglo)
        for predicado, etiqueta, arreglo in REGLAS_COMPUESTAS
        if predicado(comando)
    ]

    if not detectadas:
        return 0

    etiqueta, arreglo = detectadas[0]
    razon = (
        f'REGLAS_BASH.md — anti-patrón detectado: {etiqueta}. '
        f'{arreglo} '
        f'(tabla completa en docs/guias/REGLAS_BASH.md; este bloqueo lo emite '
        f'.claude/hooks/reglas_bash_guard.py, no el usuario)'
    )
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
