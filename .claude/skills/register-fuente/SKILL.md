---
name: register-fuente
description: Registra nuevos documentos derivados en la tabla §2.1 de REGLAS_ARQUITECTURA.md. Lee la cabecera del MD para detectar su fuente de verdad y añade la fila si falta.
argument-hint: "[ruta/al/fichero.md]"
allowed-tools: Read, Edit, Write, Bash(git *)
---

Registra documentos derivados nuevos en la tabla de dependencias documentales del proyecto BDDAT.

## Contexto actual

- Ficheros nuevos (untracked o staged): !`git -C /d/BDDAT status --short`
- Tabla de derivados actual: !`grep -A 50 "Derivados conocidos" /d/BDDAT/docs/REGLAS_ARQUITECTURA.md`

## Pasos a seguir

### 1. Determinar qué ficheros procesar

Si se pasaron argumentos (`$ARGUMENTS`), procesa solo esos ficheros.

Si no hay argumentos: de la lista de ficheros nuevos (status --short), filtra los `.md` que estén dentro de `docs/`. Ignora ficheros en `docs_prueba/` o en cualquier ruta temporal.

Si no hay ficheros `.md` nuevos en `docs/`, informa al usuario y detente: "No hay documentos nuevos en docs/ para registrar."

### 2. Leer la cabecera de cada fichero

Para cada fichero `.md` a procesar, léelo con la tool `Read` y busca la línea:

```
> Fuente de verdad: `<fichero>`
```

### 3a. Si tiene cabecera declarada

Extrae la fuente de verdad de la línea encontrada. Comprueba si ya existe una fila en la tabla §2.1 de `REGLAS_ARQUITECTURA.md` con ese derivado. Si ya existe, informa al usuario y omite ese fichero.

Si no existe, añade la fila a la tabla usando la tool `Edit`. La fila sigue el formato:

```
| `<ruta-relativa-del-derivado>` | `<fuente-de-verdad>` |
```

Añade también la línea `> Última sincronización: <fecha-de-hoy-ISO>` justo debajo de la línea `> Fuente de verdad:` en el fichero derivado, si no existe ya.

### 3b. Si NO tiene cabecera

Pregunta al usuario: "¿Es `<nombre-fichero>` un derivado de otra fuente de verdad? Si es así, ¿de cuál?" (usa la tool `AskUserQuestion`).

- Si responde que sí: añade las líneas de cabecera al fichero (con `Edit`) y después registra la fila en §2.1.
- Si responde que no: informa que el fichero no requiere registro y omítelo.

### 4. Commit si hubo cambios en REGLAS_ARQUITECTURA.md

Si se modificó `REGLAS_ARQUITECTURA.md`, crea un commit con:

- Escribe el mensaje en `D:\BDDAT\docs_prueba\temp\commit_register.txt` con la tool `Write`
- Ejecuta: `git -C /d/BDDAT add docs/REGLAS_ARQUITECTURA.md`
- Ejecuta: `git -C /d/BDDAT commit -F docs_prueba/temp/commit_register.txt`

Formato del mensaje:
```
[DOCS] Registrar derivado <nombre-fichero>
```

Si se registraron varios ficheros en la misma ejecución, agrupa todos en un único commit.

### 5. Mostrar resumen

Muestra al usuario qué ficheros se registraron, cuáles ya existían y cuáles se omitieron.
