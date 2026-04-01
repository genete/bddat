# Anti-bloqueos Bash — Claude Code (BDDAT)

Los checks de seguridad de Claude Code son **hardcoded** y no los desactiva la allowlist
ni el modo "accept edits". Evitarlos cambiando el patrón.

---

## Mensajes de aprobación y su causa

| Mensaje que aparece | Causa | Solución |
|---------------------|-------|----------|
| `output redirection >` | `cmd > fichero` | Usar tool `Write` |
| `command contains newlines that could separate multiple commands` | heredoc en Bash, **`python -c "...multilínea..."`** o bucle `for/do/done` multilínea | Escribir con `Write` → pasar como fichero (`python script.py`; si es bucle, `bash fichero.sh`) |
| `quoted newline + #-line` | Cualquier línea que empiece por `#` tras un salto dentro de cadena entrecomillada: `## Header` en heredoc/`--body`, **comentario `# ...` en `python -c "..."`**, etc. | Usar fichero temporal (`Write` → `-F`/`--body-file` o `python script.py`) |
| `command contains quoted characters in flag names` | comillas dentro de `--body "..."` o flag con valor entrecomillado | Usar fichero temporal para el valor |
| `backtick or $() substitution` / `command contains $() command substitution` | `` cmd=`...` `` o `$(...)` | Separar en llamadas Bash secuenciales |
| `backslash before shell operator` | `\|`, `\;`, `\&`, `\<`, `\>` en comandos — **incluido `grep 'pat1\|pat2'`** | Eliminar barra — usar `grep -E 'pat1|pat2'` o `-e pat1 -e pat2` |
| `sed command contains operations that require explicit approval` | `sed -i` u otras operaciones de escritura con sed | Usar tool `Edit` en su lugar |
| `command contains consecutive quote characters at word start (potential obfuscation)` | `""` o `''` como primer carácter de un argumento, p. ej. `echo ""texto` o `cmd ''arg` | Nunca empezar un argumento con comilla doble vacía; si el valor puede quedar vacío, usar variable o fichero temporal |
| `allow reading from <ruta>\` / `allow access to <ruta>\` | Ruta con **backslash** Windows en comando Bash (p. ej. `app\models\`) | En Bash (MSYS2) las rutas van con `/`. Usar siempre `app/models/`, nunca `app\models\` |

---

## Ficheros temporales — ruta obligatoria

En Windows, `/tmp/` no es fiable: la tool `Write` y `bash` (MSYS2) pueden resolver
a rutas distintas. **Usar siempre ruta absoluta dentro del repo:**

```
D:\BDDAT\docs_prueba\temp\   ← ignorado por .gitignore (docs_prueba/)
```

Esta ruta está en la allowlist del proyecto (`always allow access`).
**No borrar ni mover** tras uso — `rm` y `mv` quedan bloqueados por permisos. Dejar el fichero; el usuario lo borra manualmente cuando quiere. La carpeta está gitignored.

**Ejemplos:**
- `Write` a `D:\BDDAT\docs_prueba\temp\commit_msg.txt` → `git -C /d/BDDAT commit -F docs_prueba/temp/commit_msg.txt`
- `Write` a `D:\BDDAT\docs_prueba\temp\gh_body.md` → `gh pr create --body-file /d/BDDAT/docs_prueba/temp/gh_body.md`

---

## Patrones concretos obligatorios

- **cd + git:** usar SIEMPRE `git -C /ruta` — NUNCA `cd /ruta && git`
- **`$()` y backticks:** NUNCA — separar en llamadas Bash secuenciales o usar fichero temporal
- **cd + redirección / escritura:** separar en dos llamadas Bash distintas
- **`gh issue create` / `gh pr create`:** `Write` body → `--body-file`
- **`git commit` con mensaje largo:** `Write` mensaje → `commit -F fichero`
- **`sed -i`:** usar tool `Edit` siempre
- **`python -c "...multilínea..."`:** `Write` el script a `docs_prueba/temp/` → `python docs_prueba/temp/script.py`
- **`grep 'pat1\|pat2'`:** usar `grep -E 'pat1|pat2'` (ERE sin barra) o `-e pat1 -e pat2`
