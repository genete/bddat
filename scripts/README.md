# scripts/

Scripts de uso interno del proyecto BDDAT.

---

## sedeboja_extract.py — Extracción de legislación andaluza consolidada

Descarga el texto consolidado de una norma desde el portal sedeboja de la Junta de
Andalucía **sin navegador** (dos peticiones HTTP: portlet → iframe estático).

Los ficheros persistidos en `docs/normas/` son **fuente de verdad generada** —
no se editan a mano. Los cambios entre versiones consolidadas quedan visibles en
`git log docs/normas/`.

### Requisitos

Python 3 estándar (sin dependencias externas). No requiere el entorno virtual.

### Argumentos

```
python scripts/sedeboja_extract.py {ID} [opciones]
```

| Argumento | Descripción |
|---|---|
| `{ID}` | ID técnico numérico de sedeboja (ver tabla más abajo) |
| `--indice` | Lista las secciones disponibles de la norma |
| `"artículo N"` | Extrae una sección concreta (acepta varios separados por espacios) |
| `"disposición adicional única"` | Disposición adicional (única / primera / segunda…) |
| `"disposición transitoria única"` | Disposición transitoria |
| `"disposición derogatoria única"` | Disposición derogatoria |
| `"disposición final primera"` | Disposición final (primera / segunda…) |
| `--todo` | Extrae el texto completo estructurado (stdout) |
| `--guardar` | Igual que `--todo` pero persiste en `docs/normas/sedeboja_{ID}.md` |

### Uso típico

```bash
# 1. Ver qué secciones tiene la norma antes de extraer
python scripts/sedeboja_extract.py 21892 --indice

# 2. Leer artículos concretos (stdout, sin guardar)
python scripts/sedeboja_extract.py 21892 "artículo 5" "artículo 6"

# 3. Leer disposiciones
python scripts/sedeboja_extract.py 26974 "disposición adicional única" "disposición final segunda"

# 4. Descargar y persistir el texto completo
python scripts/sedeboja_extract.py 21892 --guardar

# 5. Ver los cambios respecto a la versión anterior guardada
git diff docs/normas/sedeboja_21892.md
```

Si la norma ya existe en `docs/normas/` y se vuelve a ejecutar `--guardar`,
sobreescribe con la versión consolidada más reciente que devuelva sedeboja.
El frontmatter actualiza `version_consolidada` y `extraido`.

### IDs técnicos — normas del catálogo BDDAT

La lista completa está en `docs/NORMATIVA_LEGISLACION_AT.md §6` (columna "ID técnico").
Normas de uso frecuente:

| Norma | ID |
|---|---|
| Decreto-ley 2/2018 — Simplificación energía | 26974 |
| Decreto-ley 26/2021 — Simplificación administrativa | 33520 |
| Decreto 356/2010 — AAU | 21892 |
| Decreto 9/2011 — Procedimientos industria y energía | 22168 |
| Ley 2/2026 — Gestión Ambiental de Andalucía | 40751 |

### Formato del fichero guardado

```
docs/normas/sedeboja_{ID}.md
```

```markdown
---
referencia: "Nombre completo de la norma"
sedeboja_id: 21892
version_consolidada: 2024-05-25
extraido: 2026-04-06
iframe_url: "https://ws040.juntadeandalucia.es/sedeboja/lconsolidada/..."
---

# Nombre completo de la norma

## Exposición de motivos

...

## Artículo 1

...
```
