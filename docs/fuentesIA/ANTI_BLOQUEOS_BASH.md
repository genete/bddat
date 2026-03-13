# Anti-bloqueos Bash — Claude Code (BDDAT)

Los checks de seguridad de Claude Code son **hardcoded** y no los desactiva la allowlist
ni el modo "accept edits". Evitarlos cambiando el patrón.

---

## Mensajes de aprobación y su causa

| Mensaje que aparece | Causa | Solución |
|---------------------|-------|----------|
| `output redirection >` | `cmd > fichero` | Usar tool `Write` |
| `command contains newlines that could separate multiple commands` | heredoc en Bash | Escribir con `Write` → pasar como fichero |
| `quoted newline + #-line` | `## Header` dentro de heredoc | Ídem (fichero temporal) |
| `command contains quoted characters in flag names` | comillas dentro de `--body "..."` o interpolación con comillas en nombre de flag | Usar fichero temporal para el valor |
| `backtick or $() substitution` / `command contains $() command substitution` | `` cmd=`...` `` o `$(...)` | Separar en llamadas Bash secuenciales |
| `backslash before shell operator` | `\|`, `\;`, `\&`, `\<`, `\>` en comandos | Eliminar la barra — nunca escapar operadores de shell |
| `sed command contains operations that require explicit approval` | `sed -i` u otras operaciones de escritura con sed | Usar tool `Edit` en su lugar |

---

## Ficheros temporales — ruta obligatoria

En Windows, `/tmp/` no es fiable: la tool `Write` y `bash` (MSYS2) pueden resolver
a rutas distintas. **Usar siempre ruta absoluta dentro del repo:**

```
D:\BDDAT\docs_prueba\temp\   ← ignorado por .gitignore (docs_prueba/)
```

Esta ruta está en la allowlist del proyecto (`always allow access`).
Borrar el fichero tras uso con `rm`.

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
