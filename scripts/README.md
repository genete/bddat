# scripts/

Scripts de uso interno del proyecto BDDAT.

---

## sedeboja_buscar.py — Descubrir el ID técnico de una norma

Busca una norma por nombre en el portal sedeboja y devuelve su ID técnico
(`recursoLegalAbstractoId`), necesario para `sedeboja_extract.py`.

### Uso

```bash
python scripts/sedeboja_buscar.py "Decreto 550/2022"
python scripts/sedeboja_buscar.py "Ley 7/2021"
python scripts/sedeboja_buscar.py "356/2010"
```

Salida:

```
Buscando: Decreto 550/2022

ID: 34371  (25/10/2022)
    DECRETO 550/2022, de 25 de octubre, por el que se aprueba el Reglamento ...
```

El ID obtenido se pasa directamente a `sedeboja_extract.py`.

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

### Flujo completo (buscar + extraer)

```bash
# 1. Descubrir el ID si no se conoce
python scripts/sedeboja_buscar.py "Decreto 550/2022"
# → ID: 34371

# 2. Descargar y guardar con el ID obtenido
python scripts/sedeboja_extract.py 34371 --guardar
```

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

---

## legalize_xref.py — Búsqueda de referencias cruzadas en legalize-es

Busca una cadena de texto en todos los ficheros MD de legalize-es
(solo `es/` y `es-an/`, ignorando otras comunidades) y compara los
resultados con `normas_catalog.csv`.

Muestra qué normas mencionan la cadena, separando las que ya están en
el catálogo de las que son nuevas. Con `--add` escribe las nuevas como
`IDENTIFICADA`.

### Uso

```bash
python scripts/legalize_xref.py "1955/2000"
python scripts/legalize_xref.py "RD 223/2008"
python scripts/legalize_xref.py "1955/2000" --add
```

### Variable de entorno

`LEGALIZE_DIR` permite sobreescribir la ruta por defecto `D:\legalize-es`.

---

## legalize_compile.py — Compilación de normas para NotebookLM

Lee `normas_catalog.csv`, localiza cada norma en su fuente local
(legalize-es para BOE, `docs/normas/` para sedeboja) y genera ficheros
con cabecera YAML normalizada para subir a Google Drive/NotebookLM.

Las normas sin fichero local se listan como omitidas. Para añadirlas
ejecutar `sedeboja_extract.py {ID} --guardar` primero.

### Uso

```bash
# Un fichero compilado con todas las normas
python scripts/legalize_compile.py

# Solo normas confirmadas (con ámbito asignado, sin OBSOLETA)
python scripts/legalize_compile.py --solo-confirmadas

# Un fichero .txt por norma en la carpeta de Google Drive
python scripts/legalize_compile.py --solo-confirmadas --individual --out "H:/Mi unidad/bddat-notebooklm/"

# Filtrar por ámbito o estado
python scripts/legalize_compile.py --area 6.1 --estado MAPEO_CONTEXTO
```

La salida por defecto es `docs_prueba/temp/normas_compiladas.md`.
En modo `--individual` la salida debe ser una carpeta (genera `{id_tecnico}.txt` por norma).

### Variable de entorno

`LEGALIZE_DIR` permite sobreescribir la ruta por defecto `D:\legalize-es`.

---

## preparar_contexto.py — Volcado de contexto del proyecto

Genera un fichero de texto con el código fuente completo del proyecto
para usarlo como fuente de conocimiento en herramientas IA (Gemini, NotebookLM).

Excluye: `venv/`, `node_modules/`, `docs/normas/`, `docs_prueba/`, `.git/`, `package-lock.json`.
Incluye: `.py`, `.html`, `.md`, `.css`, `.js`, `.json`, `.sql`, `.yaml` y similares.

### Uso

```bash
# Solo en el repositorio local
python scripts/preparar_contexto.py

# Con copia adicional en Google Drive (sincroniza automáticamente)
python scripts/preparar_contexto.py --out "H:/Mi unidad/bddat-notebooklm/contexto_bddat.txt"
```

Salida principal: `contexto_completo_gemini.txt` en la raíz del proyecto.

---

## flask_console.py — GUI de control del servidor Flask

Interfaz gráfica (tkinter) para arrancar, detener y monitorizar el servidor
Flask de desarrollo sin usar la terminal. Muestra logs en tiempo real.

### Uso

```bash
python scripts/flask_console.py
```

---

## reset_maestros_ftt.py — Sincronización de maestros FTT

Lee `docs/ESTRUCTURA_FTT.json` y reconstruye desde cero las tablas maestras:
`tipos_fases`, `tipos_tramites`, `fases_tramites`. Los IDs son deterministas
(orden de aparición en el JSON). Re-ejecutable sin efectos secundarios.

### Uso

```bash
python scripts/reset_maestros_ftt.py           # solo maestros FTT
python scripts/reset_maestros_ftt.py --full    # + datos operativos (dev completo)
```

---

## seed_listado.py — Escenarios de prueba para el listado inteligente

Crea los 11 escenarios de `ANALISIS_LISTADO_INTELIGENTE.md §6`.
Re-ejecutable: borra datos operativos previos antes de insertar.
Requiere haber ejecutado `reset_maestros_ftt.py` al menos una vez.

### Uso

```bash
python scripts/seed_listado.py
```

---

## verificar_seed.py — Verificación de escenarios del listado

Comprueba que `seed_listado.py` ha creado correctamente los 11 escenarios
T01-T11. Sirve como test de regresión.

### Uso

```bash
python scripts/verificar_seed.py
```
