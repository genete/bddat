# Prompts NotebookLM — Extracción normativa BDDAT

## Workflow previo al prompt

Antes de analizar una norma nueva, regenerar el consolidado:

```bash
python scripts/compile_hallazgos.py --out "H:/Mi unidad/bddat-notebooklm/hallazgos_consolidados.txt"
```

El cuaderno de NotebookLM debe tener como fuentes:
- `hallazgos_consolidados.txt` — todas las normas ya analizadas (este fichero)
- `contexto_normativo_nblm.txt` — contexto del proyecto BDDAT
- El `.txt` de la norma a analizar (generado con `legalize_compile.py` o copiado de `legalize-es/`)

---

## Prompt estándar (primera norma analizada, sin hallazgos previos)

```
Analiza el documento {ID} ({nombre completo}) desde la perspectiva de un sistema de
tramitación de expedientes de autorización de instalaciones de alta tensión en Andalucía.

Extrae lo relevante para los procedimientos: AAP, AAC, AE, Transmisión y Cierre.

Para cada regla, documenta en formato tabla:
**{ID}-NN**; Descripción; Tipo_solicitud; Fase_afectada; Condición_activación; Excepción_de; Fuente_legal; Notas

Además, en secciones separadas:
1. Plazos — días, silencio administrativo, quién resuelve
2. Variables — parámetros que condicionan el procedimiento, en formato tabla:
   Variable; Tipo; Naturaleza (dato/calculado/derivado_doc); Estado; Norma de origen
3. Excepciones y regímenes simplificados
4. Contradicciones o complementos respecto a normas ya analizadas (si las hay en fuentes)

No incluyas párrafo introductorio. Empieza directamente con la sección de reglas.
```

---

## Prompt intermedio (segunda norma en adelante)

```
Analiza el documento {ID} ({nombre completo}) desde la perspectiva de un sistema de
tramitación de expedientes de autorización de instalaciones de alta tensión en Andalucía.

Extrae lo relevante para los procedimientos: AAP, AAC, AE, Transmisión y Cierre.

Para cada regla, documenta en formato tabla:
**{ID}-NN**; Descripción; Tipo_solicitud; Fase_afectada; Condición_activación; Excepción_de; Fuente_legal; Notas

En las fuentes tienes hallazgos_consolidados.txt con todas las normas ya analizadas.
Para cada sección, aplica las siguientes instrucciones:

**Sección Reglas del Motor:**
- Si una regla de esta norma cubre el mismo supuesto que una ya documentada, indica en Notas:
  "Complementa/Supera a [NORMA-NN]".
- Si una regla nueva deroga o restringe una anterior, indica: "Prevalece sobre [NORMA-NN]
  por [rango jerárquico / fecha]" o al revés.
- Solo omite una regla si cubre exactamente el mismo supuesto. Si añade condiciones, plazos
  o matices procedimentales propios, inclúyela aunque referencie la norma anterior.
  Usa "Cubierta por [NORMA-NN]" solo si es idéntica; si amplía, usa "Complementa a".

**Sección Variables:**
- Para cada variable, documenta en formato tabla:
  Variable; Tipo; Naturaleza (dato/calculado/derivado_doc); Estado; Norma de origen
- En Estado indica: "Ya existe (ver [NORMA-NN])" si ya estaba documentada, "Nueva" si es
  realmente nueva, o "Renombrar: coincide con [nombre_existente]" si hay solapamiento
  semántico con nombre distinto.

**Sección Excepciones:**
- Si la excepción ya fue documentada en otra norma, indica de qué regla proviene y si esta
  norma la amplía, restringe o confirma.

**Sección 4 — Contradicciones o complementos (OBLIGATORIA):**
- Lista explícita de cada punto de contacto con normas ya analizadas en hallazgos_consolidados.txt.
- Cita siempre la regla concreta (p.ej. LSE-07, RD1955-04, LPACAP-08) y el artículo exacto
  de esta norma.
- Para cada punto indica: Contradicción / Complemento / Prevalencia y quién gana y por qué.

Además, en secciones separadas:
1. Plazos — días, silencio administrativo, quién resuelve
2. Variables (con cruce según lo indicado)
3. Excepciones y regímenes simplificados (con cruce según lo indicado)
4. Contradicciones o complementos (ver instrucciones arriba)

No incluyas párrafo introductorio. Empieza directamente con la sección de reglas.
```

---

## Convenciones de nomenclatura

| Norma | Prefijo ID | Fichero hallazgos |
|---|---|---|
| LPACAP — Ley 39/2015 | `LPACAP` | `BOE-A-2015-10565_reglas.md` |
| LSE — Ley 24/2013 | `LSE` | `BOE-A-2013-13645_reglas.md` |
| RD 1955/2000 | `RD1955` | `BOE-A-2000-24019_reglas.md` |
| Ley 21/2013 EIA | `EIA` | `BOE-A-2013-12913_reglas.md` |

Al añadir una norma nueva, añadir su fila aquí y en `ORDEN_JERARQUICO` de `compile_hallazgos.py`.
