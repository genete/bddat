---
name: legalize
description: Busca una norma en el repositorio local legalize-es y devuelve su contenido consolidado en Markdown. Primera parada antes de usar red.
argument-hint: "[BOE:|BOJA:] <referencia>  — ej: 'BOJA: DL 2/2018' | 'BOE: Ley 24/2013' | 'Real Decreto 1955/2000'"
allowed-tools: Grep, Glob, Read
---

Eres un buscador especializado en legislación consolidada local.
Tu argumento es: `$ARGUMENTS`

Devuelve el contenido completo del fichero si lo encuentras, o `NOT_FOUND` con motivo si no.

---

## PASO 0 — docs/normas/ (primera parada, normas propias de BDDAT)

Antes de buscar en legalize-es, busca en `docs/normas/` dentro del repo BDDAT:

```
Grep pattern="<término>" path=docs/normas -i output_mode=files_with_matches
```

Los ficheros tienen frontmatter con `referencia:` y `sedeboja_id:`. Si hay match, leer el fichero y devolver su contenido. Si no hay ficheros o no hay match, continuar con el paso siguiente.

---

## ESTRUCTURA DEL REPOSITORIO (legalize-es)

```
/d/legalize-es/
  es/          ← BOE estatal (8 646 normas, BOE-A-*.md)
  es-an/       ← Andalucía: BOE-A-*.md (históricas) + BOJA-b-*.md (desde 2012)
  es-ct/       ← Cataluña
  es-ar/       ← Aragón
  ... (17 CCAA)
```

Cada fichero tiene frontmatter YAML:
```yaml
---
title: "Decreto-ley 2/2018, de 26 de junio, de simplificación..."
identifier: "BOJA-b-2018-90370"
status: "in_force" | "repealed"
jurisdiction: "es-an" | "es" | ...
---
```

---

## ALGORITMO DE BÚSQUEDA

### Paso 1 — Identificar tipo de fuente

| Señal en el argumento | Dónde buscar |
|---|---|
| Prefijo `BOJA:` o "Decreto-ley X/YYYY" sin prefijo BOE | `/d/legalize-es/es-an/` |
| Prefijo `BOE:` o norma estatal clara (RD, Ley, RDL con nº único) | `/d/legalize-es/es/` |
| Sin prefijo, ambiguo | Buscar primero en `es-an/`, luego en `es/` |

### Paso 2 — Grep por título

Usa `Grep` con el número y año de la norma en el `title` del frontmatter:

```
Grep pattern="decreto-ley 2/2018" path=/d/legalize-es/es-an -i output_mode=files_with_matches
```

Variantes útiles:
- `decreto.ley` cubre "decreto-ley" y "decreto ley"
- Usa `-i` siempre (case insensitive)
- Si no hay match, prueba solo con número/año: `pattern="2/2018"` acotado al tipo

### Paso 3 — Si hay candidatos

Lee con `Read` el fichero que coincida. Comprueba `title` del frontmatter para confirmar identidad exacta.

### Paso 4 — Respuesta

- **Si encontrado:** devuelve el contenido completo del fichero (frontmatter + texto).
- **Si no encontrado:** responde exactamente `NOT_FOUND: <motivo>` donde motivo es:
  - `sin cobertura` — la norma no está en el repo (puede ser pre-2012 para BOJA o simplemente no indexada)
  - `derogada` — `status: repealed` en el frontmatter
  - Cualquier otra causa relevante

---

## NORMAS CLAVES DEL PROYECTO BDDAT — BOJA

| Referencia | Fichero esperado |
|---|---|
| Decreto-ley 2/2018 | `es-an/BOJA-b-2018-90370.md` |
| Decreto-ley 26/2021 | `es-an/BOJA-b-2021-90434.md` |
| Decreto-ley 3/2024 | `es-an/BOJA-b-2024-*.md` (verificar con Grep) |
| Decreto 356/2010 (AAU) | puede estar en `es-an/BOE-A-*.md` (publicado en BOE) |

---

## NOTAS

- El repo se actualiza diariamente — si una norma reciente no está, puede no haberse indexado aún.
- Los ficheros contienen el texto consolidado vigente (no el original publicado).
- Para normas BOJA anteriores a 2012, responde `NOT_FOUND: sin cobertura (pre-2012)`.
