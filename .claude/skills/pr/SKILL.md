---
name: pr
description: Crea un Pull Request de la rama actual a develop siguiendo las convenciones de BDDAT, hace merge y borra la rama remota.
argument-hint: "[#issue] [descripción opcional]"
allowed-tools: Bash(git *), Bash(gh *), Write, Read
---

Ejecuta el workflow completo de Pull Request para el proyecto BDDAT.

## Contexto actual

- Rama actual: !`git branch --show-current`
- Commits respecto a develop: !`git log origin/develop..HEAD --oneline`
- Ficheros cambiados: !`git diff origin/develop..HEAD --name-only`

Se ejecuta desde la raíz del repo, en el PC y en la nube. Si alguna línea sale vacía o con error (en la nube, `origin/develop` puede no estar traído), ejecuta `git fetch origin develop` y repítela.

## Pasos a seguir

### 1. Verificación previa

Comprueba que la rama actual NO es `develop` ni `main`. Si lo es, detente y avisa al usuario.

### 2. Detectar issue relacionado

Intenta extraer el número de issue de:
1. Los argumentos pasados al skill: `$ARGUMENTS`
2. El nombre de la rama (patrón `issue-XX` o `issue-XX-descripcion`)
3. Los mensajes de commit (busca referencias `#XX`)

### 3. Redactar el PR

Analiza los commits y ficheros cambiados para redactar:

- **Título:** breve (≤70 caracteres), en imperativo, sin prefijo de categoría
- **Cuerpo:** sección "## Cambios" con bullets de los cambios principales. Si se detectó un issue, la **última línea del cuerpo DEBE ser `Closes #XX`** — GitHub cierra el issue automáticamente al mergear, sin necesidad de `gh issue close`.

Escribe el cuerpo con la tool `Write` en un fichero **nuevo y único** dentro de `docs_prueba/temp/` de la raíz del repo (ruta absoluta para `Write`: en el PC, `D:\BDDAT\docs_prueba\temp\`; en la nube, la salida de `git rev-parse --show-toplevel` seguida de `/docs_prueba/temp/`), y **redáctalo desde cero** a partir de los commits/diff actuales — **nunca copies el texto de un PR anterior ni reutilices/sobrescribas** un `pr_body_*.md` existente. El número de issue NO garantiza unicidad (un mismo issue puede tener varios PRs en distintas sesiones), así que añade un sufijo distintivo: p. ej. `pr_body_<issue>_<rama-o-fecha>.md` (ej. `pr_body_500_arbol-edicion.md`); si aun así existe, usa `-v2`, `-v3`… Nunca uses heredoc ni redirección bash.

### 4. Crear el PR

Saca `<owner>/<repo>` de `git remote get-url origin` (las dos últimas partes de la ruta, sin `.git`). Se pasa siempre `--repo`, por si `gh` no reconoce el remoto: en la nube es un proxy local.

Sube la rama (no hace nada si ya está al día; en la nube el push solo vale para la rama de trabajo de la sesión):

```
git push -u origin <rama>
```

```
gh pr create --repo <owner>/<repo> --base develop --head <rama> --title "..." --body-file docs_prueba/temp/pr_body_XX.md
```

Muestra la URL del PR al usuario. Su última parte es el número del PR.

### 5. Hacer merge

```
gh pr merge <nº> --repo <owner>/<repo> --merge --delete-branch
```

(El flag `--delete-branch` borra la rama remota automáticamente.) Si el borrado falla —en la nube el acceso a git está limitado a la rama de trabajo—, no insistas ni busques otra vía: dilo en el resumen.

### 6. Limpieza

No borres el fichero temporal — el usuario gestiona `docs_prueba/temp/` manualmente.

Informa al usuario de que debe ejecutar localmente:
```
git checkout develop
git pull origin develop
git branch -D <nombre-rama>
```

Si no se pudo borrar la rama remota: `git push origin --delete <nombre-rama>`.

**No ejecutar `gh issue close`** — si el cuerpo del PR incluía `Closes #XX`, GitHub ya cerró el issue al mergear.
