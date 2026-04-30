---
name: pr
description: Crea un Pull Request de la rama actual a develop siguiendo las convenciones de BDDAT, hace merge y borra la rama remota.
argument-hint: "[#issue] [descripción opcional]"
allowed-tools: Bash(git *), Bash(gh *), Write, Read
---

Ejecuta el workflow completo de Pull Request para el proyecto BDDAT.

## Contexto actual

- Rama actual: !`git -C /d/BDDAT branch --show-current`
- Commits respecto a develop: !`git -C /d/BDDAT log origin/develop..HEAD --oneline`
- Ficheros cambiados: !`git -C /d/BDDAT diff origin/develop..HEAD --name-only`

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

Escribe el cuerpo con la tool `Write` en `D:\BDDAT\docs_prueba\temp\pr_body_XX.md` donde `XX` es el número de issue detectado (o el número de PR si no hay issue). Nunca uses heredoc ni redirección bash. Nunca reutilices un fichero existente — el nombre con el número garantiza unicidad.

### 4. Crear el PR

```
gh pr create --base develop --title "..." --body-file /d/BDDAT/docs_prueba/temp/pr_body_XX.md
```

Muestra la URL del PR al usuario.

### 5. Hacer merge

```
gh pr merge --merge --delete-branch
```

(El flag `--delete-branch` borra la rama remota automáticamente.)

### 6. Limpieza

No borres el fichero temporal — el usuario gestiona `docs_prueba/temp/` manualmente.

Informa al usuario de que debe ejecutar localmente:
```
git checkout develop
git pull origin develop
git branch -D <nombre-rama>
```

**No ejecutar `gh issue close`** — si el cuerpo del PR incluía `Closes #XX`, GitHub ya cerró el issue al mergear.
