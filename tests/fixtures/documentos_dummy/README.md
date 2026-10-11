# Documentos dummy — `tests/fixtures/documentos_dummy/`

Esta carpeta ya **no contiene PDF**. Solo `catalogo_uso.csv` (documentación) y este
README. Los documentos dummy que suben los expedientes-tipo y la semilla de tests se
construyen en el momento; no hay ficheros que versionar ni que mantener al día.

## Qué cambió y por qué (#929)

Hasta #929 había aquí 65 PDF versionados, generados por
`scripts/generar_documentos_dummy.py` (#814). Fallaban de dos maneras:

- **Regenerarlos era ruido y riesgo.** Cada PDF llevaba fecha de creación, fecha de
  modificación y un identificador aleatorio, así que una regeneración cambiaba todos los
  ficheros aunque su contenido no cambiara. Y el modo completo borraba también lo que el
  script no generaba (`doc_proyecto_reformado.pdf`). Por eso nadie regeneraba.
- **El banco se desfasó del catálogo sin que nada lo avisara.** Con 82 tipos de documento
  en el catálogo había 65 PDF: faltaban 18. Solo se notaba cuando un expediente-tipo
  necesitaba uno y abortaba.

Ahora el PDF de un tipo lo construye `pdf_dummy(tipo, variante=None)`, en
`scripts/generar_documentos_dummy.py`, a partir del nombre y el origen del tipo. Cuesta
unos 1,4 ms y es **determinista** (`invariant=1` de reportlab): el mismo tipo da los mismos
bytes, y por tanto el mismo hash, en cada ejecución, de modo que el aviso «este fichero ya
está en el expediente» (ADR-050) se comporta como con ficheros fijos. Cualquier tipo del
catálogo, incluso uno añadido mañana, tiene su documento sin hacer nada.

## Cómo se obtienen

- **Los expedientes-tipo y la semilla** no leen ningún fichero:
  `_comun.subir(...)` sube el documento de un tipo por la ruta real de ingesta y
  `_comun.pdf_de_tipo('MODELO_SOLICITUD')` da los bytes para el alta de expediente. Ver
  `scripts/expedientes_dummy/README.md`.
- **Variantes.** Un tipo puede tener otro contenido para los escenarios que necesitan dos
  documentos distintos del mismo tipo: `variante='reformado'` en `DOC_PROYECTO` (el segundo
  proyecto de un reformado, #903). Pedir una variante que el tipo no tiene lanza
  `ValueError`, no devuelve el documento normal.
- **A mano, en el navegador.** Si una persona necesita un fichero real que subir, se
  vuelcan a disco con `--volcar`.

## `--volcar`

```bash
python scripts/generar_documentos_dummy.py --volcar                  # docs_prueba/documentos_dummy/
python scripts/generar_documentos_dummy.py --volcar /tmp/pdf_dummy   # otra carpeta
python scripts/generar_documentos_dummy.py --volcar salida           # relativa a donde se ejecuta
```

Escribe un PDF por cada tipo de documento del catálogo y por cada variante, como
`<codigo_en_minuscula>.pdf` (`justificante_sede.pdf`, `doc_proyecto_reformado.pdf`…).

- Sin ruta va a `docs_prueba/documentos_dummy/`, que ya está ignorada por git. Con ruta,
  absoluta o relativa al directorio desde el que se ejecuta el comando; se crea si no existe.
- **Siempre sobrescribe y nunca borra nada** de la carpeta: es seguro repetirlo (la salida
  es determinista) y una ruta mal puesta no destruye ficheros ajenos.
- Lee el catálogo de la BD de `DATABASE_URL` (`.env`), como el CSV.

## `catalogo_uso.csv`

Dónde se usa cada tipo de documento: cruza `tramites_tareas_documentos` (el tipo como
ENTRADA o SALIDA de una tarea de un trámite) y `requisitos_documentales` (requisito legal
de aportación). Es documentación, no un fixture: ningún test lo lee. Un tipo sin ningún uso
deja una fila con `fuente_uso` vacío, visible como hueco de catálogo.

```bash
python scripts/generar_documentos_dummy.py      # sin argumentos
```

**Regenerarlo desde el PC.** El orden de clasificación de Postgres en Linux cambia unas 200
líneas respecto al de Windows, y ese ruido no es un cambio del catálogo.

## `.gitattributes`

La regla `*.pdf -text` se mantiene aunque hoy no haya ningún PDF versionado: si alguno
tiene que versionarse en el futuro, no debe pasar por la normalización de fin de línea de
git, que invalidaría su tabla xref.
