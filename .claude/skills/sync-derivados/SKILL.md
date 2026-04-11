---
name: sync-derivados
description: Detecta qué fuentes de verdad han cambiado y actualiza la línea "Última sincronización" en sus derivados. Muestra qué secciones requieren revisión manual.
argument-hint: ""
allowed-tools: Read, Edit, Bash(git *)
---

Ejecuta la sincronización de documentos derivados para el proyecto BDDAT.

## Contexto actual

- Ficheros modificados en el último commit: !`git -C /d/BDDAT diff --name-only HEAD~1 HEAD`
- Ficheros modificados sin commitear: !`git -C /d/BDDAT diff --name-only HEAD`
- Tabla de derivados conocidos: !`grep -A 50 "Derivados conocidos" /d/BDDAT/docs/REGLAS_ARQUITECTURA.md`

## Pasos a seguir

### 1. Identificar fuentes modificadas

Combina ambas listas de ficheros modificados (último commit + sin commitear). De esa lista, filtra los que aparecen en la columna "Fuente de verdad" de la tabla §2.1 de `REGLAS_ARQUITECTURA.md`.

Si ninguna fuente ha cambiado, informa al usuario y detente: "No hay fuentes de verdad modificadas. No se requiere sincronización."

### 2. Localizar derivados afectados

Para cada fuente modificada, consulta la tabla §2.1 y obtén todos sus documentos derivados.

### 3. Actualizar la fecha de sincronización

Para cada documento derivado:

- Si es un `.md`: lee el fichero y localiza la línea `> Última sincronización: <fecha>`. Actualízala con la fecha de hoy en formato ISO 8601 (YYYY-MM-DD). Usa la tool `Edit` (nunca `sed`).
- Si es un `.mmd`: localiza la línea `%% Fuente: ... | Sincronizado: <fecha>` y actualiza la fecha. Usa la tool `Edit`.

Si el derivado no tiene la línea de sincronización, añádela justo debajo de la línea `> Fuente de verdad:` (para `.md`) o al inicio del fichero como primer comentario (para `.mmd`).

### 4. Identificar secciones que requieren revisión manual

Según el tipo de cambio en la fuente, indica qué partes del derivado probablemente necesitan revisión humana:

- Si cambió `ESTRUCTURA_FTT.json`: revisar secciones de fases, trámites o tareas en el derivado
- Si cambió un `DISEÑO_*.md`: revisar secciones que describan el subsistema afectado
- En general: cualquier sección que mencione el nombre del fichero fuente

### 5. Mostrar resumen

Muestra al usuario una tabla con:

| Derivado | Fecha actualizada | Requiere revisión manual |
|---|---|---|
| `<fichero>` | Sí (automático) | `<secciones a revisar>` |

Finaliza con: "Sincronización completada. Revisa manualmente las secciones marcadas antes de hacer commit."
