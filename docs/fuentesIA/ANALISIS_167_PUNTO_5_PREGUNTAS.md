> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 5) Preguntas — TODAS RESUELTAS

Preguntas que requerian respuesta del usuario antes de implementar.
Organizadas por fase. **Todas resueltas en sesion 4 (2026-03-15).**

---

### Para Fase 1 (solicitudes + whitelist)

#### P1. Semantica de `EXISTE_TIPO_SOLICITUD` con tipos combinados (R1) — RESUELTA

**Pregunta:** Cuando se escriban reglas en el motor, como se refieren a tipos
de solicitud combinados?

**Resolucion:** Comparacion exacta. La inteligencia esta en la regla, no en el motor.

El motor compara `solicitud.tipo_solicitud.siglas == siglas` (match exacto).
El supervisor, al escribir una regla, lista todos los tipos que la satisfacen.

Ejemplo: *"Para RESOLUCION, el tipo de solicitud debe incluir AAP"*
→ El supervisor escribe una regla con lista: `[AAP, AAP_AAC, AAP_AAC_DUP, AAP_AAC_AAU, AAP_AAC_AAU_DUP]`.
El motor evalua "esta el tipo de esta solicitud en esta lista?".

No se crea criterio `INCLUYE_TIPO_SOLICITUD`. No se descomponen siglas.
El motor ya tiene capacidad de evaluar pertenencia a lista — se usa eso.

> **Comentario del usuario:** "Es el propio supervisor el que crea las reglas
> necesarias para que el match se produzca, no porque el motor de reglas lo
> tenga programado. Todo este cambio de solicitudes individuales con combinacion
> es una decision de base y desgraciadamente la estamos tomando tarde,
> pero bueno, todo no se puede prever."

**Impacto en implementacion:** La reescritura de `_criterio_existe_tipo_solicitud()`
es trivial — una linea de comparacion exacta. El riesgo R1 queda resuelto.

---

#### P2. Completitud de tipos combinados a crear — RESUELTA

**Pregunta:** Falta algun tipo combinado?

**Resolucion:** Los 6 tipos definidos son seed inicial, no lista cerrada.
Un INSERT futuro amplia el catalogo. El sistema no falla si falta un tipo
— simplemente no aparece en selectores hasta que se cree.

No es bloqueante. Se implementa con los 6 tipos y se amplia bajo demanda.

---

### Para Fase 2 (plantillas + tipos_documentos)

#### P3. Clasificacion de tipos de documentos por `origen` — RESUELTA

**Pregunta:** Clasificar cada tipo de documento como INTERNO/EXTERNO/AMBOS.

**Resolucion:** Solo existen OTROS y DR_NO_DUP. Son valores estructurales
que se extenderan. No son criticos ahora.

Clasificacion para la migracion:
- `OTROS` → `AMBOS` (default, cajon de sastre)
- `DR_NO_DUP` → `EXTERNO` (lo presenta el solicitante)
- Nuevos tipos futuros → `AMBOS` por defecto (server_default en la columna)

---

### Para Fase 3 (nomenclatura)

#### P4. Valores de `nombre_en_plantilla` para tipos existentes — RESUELTA

**Resolucion:** Confirmado. Se preparara la lista al escribir la migracion
de Fase 3 y se presentara para revision. No bloqueante para el analisis.

---

### Para Fase 4 (admin plantillas + cascada)

#### P5. Mecanismo del principio de escape en selectores (R5) — RESUELTA

**Pregunta:** Como se presenta la via de escape en la interfaz?

**Resolucion:** Toggle invertido respecto a la propuesta original.

- **Por defecto:** se muestran TODAS las opciones (estado permisivo, sin callejon sin salida)
- **Toggle "Solo aplicables al contexto":** filtra por whitelist ESFTT,
  mostrando solo las combinaciones validas para el nivel superior seleccionado

El estado natural es el permisivo. El filtro es la ayuda, no la restriccion.

> **Comentario del usuario:** "Seria al reves. Toggle 'solo plantillas
> aplicables al contexto'."

**Impacto en implementacion:**
- El endpoint AJAX devuelve siempre TODAS las opciones
- Si el toggle esta activo, el endpoint recibe parametro `?filtrar=1`
  y devuelve solo las de la whitelist
- Sin toggle (o toggle desactivado): todas las opciones visibles,
  sin badge ni advertencia (son opciones validas, no excepciones)
- El registro en bitacora aplica solo si el supervisor elige una combinacion
  fuera de whitelist Y el filtro estaba activo (accion consciente de escape)

---

### Para Fase 5 (motor de generacion)

#### P6. Ubicacion de endpoints de generacion (I1) — RESUELTA

**Pregunta:** Donde viven los endpoints de generacion de escritos?

**Resolucion:** Fichero API dedicado `routes/api_escritos.py` (NUEVO).

Endpoints API pura (JSON in, JSON/file out) desacoplados de cualquier vista.
Los consume la vista BC (o cualquier vista futura) mediante AJAX.

---

#### P8. Checkboxes de generacion: estado por defecto — RESUELTA

**Resolucion:** Confirmado.

- Registrar en pool: **marcado** por defecto
- Asignar como documento producido: **marcado** por defecto
- Abrir carpeta contenedora: **desmarcado** por defecto

---

### Resuelta fuera de fase

#### P7. FK `plantilla_id` en tabla `documentos` (I4) — RESUELTA: NO

**Pregunta:** Anadir FK nullable `plantilla_id` en documentos?

**Resolucion:** No. La trazabilidad plantilla→documento va embebida
en el propio documento, no en la BD:

- **Via metadatos inyectados (#182):** custom properties del .docx incluyen
  el ID de la plantilla (ej: `plantilla_id: 356`). Viaja con el documento.
- **Via texto en pie de pagina:** opcionalmente, texto discreto
  tipo `Template ID: 356`. Sobrevive a impresion y escaneo.
- Ambas vias ya estan previstas en C3 (trazabilidad) — no requieren
  columna adicional en BD ni codigo para rellenarla.

> **Comentario del usuario:** "Esto ya va con el documento y siempre
> es recuperable. Es lo mas sano, creo yo. Esto nos evita mas codigo
> que se ocupe de rellenar eso."

**Impacto:** Fase 6 se simplifica — no hay migracion para plantilla_id.
La inconsistencia I4 del punto 3 queda resuelta.

---

### Resumen

| # | Pregunta | Fase | Estado |
|---|----------|:----:|:------:|
| P1 | Semantica EXISTE_TIPO_SOLICITUD | 1 | **RESUELTA** — comparacion exacta, supervisor lista tipos |
| P2 | Completitud tipos combinados | 1 | **RESUELTA** — 6 iniciales, ampliable con INSERT |
| P3 | Clasificacion tipos_documentos | 2 | **RESUELTA** — OTROS=AMBOS, DR_NO_DUP=EXTERNO |
| P4 | Valores nombre_en_plantilla | 3 | **RESUELTA** — diferida a migracion, se revisara |
| P5 | Mecanismo escape selectores | 4 | **RESUELTA** — toggle "Solo aplicables" (defecto=todas) |
| P6 | Ubicacion endpoints generacion | 5 | **RESUELTA** — `routes/api_escritos.py` nuevo |
| P7 | FK plantilla_id en documentos | — | **RESUELTA: NO** — trazabilidad va en metadatos del .docx |
| P8 | Checkboxes por defecto | 5 | **RESUELTA** — pool+doc marcados, carpeta desmarcado |

> **Todas las preguntas resueltas.** No quedan decisiones pendientes
> para comenzar la implementacion. Siguiente paso: Fase 0 (fix R6 + exports).
