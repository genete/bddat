# Análisis de fechas ESFTT — conclusión arquitectónica

> **Fecha inicio:** 2026-04-18 | **Fecha cierre:** 2026-04-19
> **Estado:** CERRADO — conclusión arquitectónica alcanzada.
> **Contexto:** sesión de análisis que comenzó tipo a tipo (fases) y llegó a una conclusión general sobre el modelo de fechas en todos los niveles ESFTT.

---

## CONCLUSIÓN ARQUITECTÓNICA

### Ningún elemento ESFTT almacena fechas

Esta conclusión aplica a los cinco niveles: **Expediente, Solicitud, Fase, Trámite y Tarea**.

**Fechas no administrativas** (`fecha_inicio`, `fecha_fin` de fases, trámites, tareas):
Son marcas temporales de acciones del usuario en el sistema ("cuándo hice clic"). No tienen cliente real: no computan plazos legales, no tienen valor jurídico, no aportan nada que no esté ya en el cuaderno de bitácora. La mera existencia del registro con su `id` prueba que el usuario interactuó.

**Fechas administrativas** (`fecha_solicitud`, fechas de notificación, firma, publicación…):
Su único hogar válido es `Documento.fecha_administrativa` del documento que las porta. Leer una fecha administrativa es leer del Documento (fuente de verdad). Almacenar un duplicado en el modelo ESFTT crea un dato que puede divergir del documento real con consecuencias legales, y cuya consistencia no puede garantizarse.

**El estado tampoco se almacena.** Es deducible en tiempo de consulta a partir de las reglas del motor (tablas de reglas) y de los documentos existentes. No es un campo.

### Trazabilidad por FK, no por duplicación

Los documentos son agnósticos: no saben quién los usa. La trazabilidad (quién los produce, a qué elemento pertenecen) vive en FKs en las tablas relacionadas. El FK no almacena el dato — señala dónde está la fuente de verdad.

**Implicación para `Solicitud`:** debe existir un FK `documento_solicitud_id` que apunta al documento de solicitud en el pool. Este FK permite al motor y al usuario localizar la fuente de verdad de los dos datos capitales de la solicitud:
- **cuándo** → `Documento.fecha_administrativa` del documento referenciado.
- **qué** → tipo deducible por análisis del PDF (ver issue #304).

`documento_solicitud_id` **no existe actualmente en el modelo** — debe añadirse.

### Cuaderno de bitácora

Todo episodio de interacción usuario → sistema se compila en el cuaderno de bitácora: evento del clic, contexto ensamblado, respuesta del motor, resultado. Es el único registro inmutable de "qué pasó y cuándo". Admin y supervisor pueden auditar y rebobinar desde ahí. La regla de escape ante cualquier incidencia (regla del motor incorrecta, validación hardcodeada que falló) siempre está en la bitácora.

El motor **no** se apoya en la bitácora. El motor es agnóstico y consulta exclusivamente las tablas de reglas.

### Cómo se capturan las fechas administrativas

Las fechas administrativas no se introducen manualmente en campos de modelos ESFTT. El flujo:

1. El documento se sube al pool (requisito previo al acto que lo origina).
2. BDDAT analiza el documento: metadata del PDF, firma digital (issues existentes), OCR si hace falta.
3. El sistema **propone** la fecha extraída para validación del usuario — nunca asignación automática sin confirmación.
4. El usuario valida. La fecha queda en `Documento.fecha_administrativa`.
5. Solo en caso extremo el usuario introduce la fecha manualmente en el Documento. La bitácora lo registra.

Este flujo aplica también al **wizard de creación de expediente**: el documento de solicitud debe estar en el pool antes de crear el expediente. La fecha de solicitud se extrae del documento, no de un campo `Solicitud.fecha_solicitud`. El documento de proyecto puede estar ausente (el administrado lo omitió) — eso no bloquea la apertura del expediente sino que genera un trámite de reclamación; el tipo de solicitud se deduce igualmente del documento de solicitud.

---

## MAPA DE FECHAS ADMINISTRATIVAS POR FASE

El análisis tipo a tipo de la sesión reveló qué documento porta la fecha administrativa relevante en cada fase. Este mapa es referencia para el seed de reglas del motor y para la UI (dónde apuntar al usuario para ver la fecha clave de cada fase).

| Fase | Fecha administrativa | Documento que la porta | Tarea productora |
|---|---|---|---|
| ANALISIS_SOLICITUD | — | No aplica (contenedor puro) | — |
| CONSULTA_MINISTERIO | Notificación al Ministerio | Doc. de notificación | NOTIFICAR en `SOLICITUD_INFORME` |
| COMPATIBILIDAD_AMBIENTAL | Notificación a Medio Ambiente | Doc. de notificación | NOTIFICAR en `SOLICITUD_COMPATIBILIDAD` |
| CONSULTAS | Notificación a cada organismo (30/15 días) | Doc. de separata/traslado | NOTIFICAR en `CONSULTA_SEPARATA` y traslados |
| INFORMACION_PUBLICA | Fecha de publicación en cada medio | Doc. publicado/incorporado | PUBLICAR o INCORPORAR por trámite |
| FIGURA_AMBIENTAL_EXTERNA | Notificación al titular | Doc. de notificación al titular | NOTIFICAR en `SOLICITUD_FIGURA` |
| AAU_AAUS_INTEGRADA | Notificación al órgano ambiental | Doc. de notificación | NOTIFICAR en `REMISION_MEDIO_AMBIENTE` |
| RESOLUCION | Firma, notificación y publicación | Doc. de resolución / notif. / publicación | FIRMAR, NOTIFICAR, PUBLICAR (un doc. por trámite) |

**Nota RESOLUCION:** los tres trámites interiores (`ELABORACION`, `NOTIFICACION`, `PUBLICACION`) portan fechas con efectos jurídicos distintos (inicio de plazo de recurso, publicidad registral, etc.). Se analizarán en detalle cuando se aborde el nivel Trámite.

---

## REFACTORIZACIÓN PENDIENTE

### Campos a eliminar de los modelos

| Modelo | Campo | Motivo |
|---|---|---|
| `Solicitud` | `fecha_solicitud` | Vive en `Documento.fecha_administrativa` del doc. de solicitud |
| `Solicitud` | `fecha_fin` | Marcador operacional sin valor; se registra en bitácora |
| `Solicitud` | `estado` | Deducible por motor; no almacenable |
| `Fase` | `fecha_inicio` | Marcador operacional; bitácora |
| `Fase` | `fecha_fin` | Marcador operacional; bitácora |
| `Tramite` | `fecha_inicio` | Ídem |
| `Tramite` | `fecha_fin` | Ídem |
| `Tarea` | `fecha_inicio` | Ídem |
| `Tarea` | `fecha_fin` | Ídem |

### Campos a añadir

| Modelo | Campo | Tipo | Motivo |
|---|---|---|---|
| `Solicitud` | `documento_solicitud_id` | FK → `documentos.id` nullable | Ancla de trazabilidad al documento fundacional |

### Lógica a adaptar

- **Wizard de creación de expediente**: requiere que el documento de solicitud esté en el pool antes de crear el expediente. Integrar helper de extracción de fecha y propuesta de tipo (issues #304, #305).
- **Motor de reglas**: cualquier lectura de `solicitud.fecha_solicitud` pasa a leer `Documento.fecha_administrativa` del documento referenciado por `documento_solicitud_id`.
- **Cómputo de plazos** (art. 21 LPACAP): ídem.
- **UI**: eliminar campos de fecha y estado de las vistas de Solicitud, Fase, Trámite y Tarea. Mostrar únicamente fechas leídas desde los documentos correspondientes.
- **`invariantes_esftt.py`**: las invariantes de coherencia de fechas quedan obsoletas al no existir los campos. Revisar qué lógica permanece válida.

### Issues abiertos en esta sesión

| Issue | Título | Estado |
|---|---|---|
| #303 | Acción RE_INICIAR | **CERRADO** — innecesario al no existir los campos |
| #304 | Script detección tipo de solicitud por PDF | Abierto |
| #305 | Script detección tipo de expediente por proyecto | Abierto |
| #306 | Helper cálculo de tasa + extracción presupuesto | Abierto |

---

## HISTÓRICO DE ANÁLISIS

> El análisis detallado tipo a tipo que sigue fue el camino que llevó a la conclusión arquitectónica anterior. Se mantiene como contexto histórico de la sesión. Las tablas de atributos por campo (es_administrativa, DESINICIAR, coherencia, estado modelo, estado UI) corresponden a campos que, según la conclusión alcanzada, **no deben existir en el modelo**.

---

### Principio transversal original — Coherencia de fechas

*(Supersedido por la conclusión arquitectónica. Los invariantes de coherencia de fechas quedan sin efecto al eliminarse los campos.)*

### Principio transversal original — Interior de solo lectura y DESFINALIZAR

*(Supersedido. La lógica de "contenedor cerrado bloquea su interior" pasa a ser responsabilidad del motor evaluando el estado deducido, sin leer campos fecha_fin.)*

---

### SOLICITUD — análisis histórico

#### `fecha_solicitud`
Conclusión del análisis: fecha administrativa (art. 16 LPACAP). Inicio del cómputo del plazo de resolución (art. 21). Clasificada como `es_administrativa = Sí` para todos los tipos. **Conclusión arquitectónica posterior:** no debe existir como campo en `Solicitud` — vive en `Documento.fecha_administrativa` del documento de solicitud vinculado por `documento_solicitud_id`.

Clasificación por tipo (referencia para seed de reglas):

| Tipos | Nota |
|---|---|
| AAP, AAC, DUP, AAE_PROVISIONAL, AAE_DEFINITIVA, AAT, RAIPEE_PREVIA, RAIPEE_DEFINITIVA, RADNE, CIERRE, DESISTIMIENTO, RENUNCIA, AMPLIACION_PLAZO, RECURSO, AAP_AAC | A instancia de parte, entrada en Registro. |
| CORRECCION_ERRORES | Puede ser de oficio o a instancia. Decisión de simplificación: siempre administrativa. |
| INTERESADO | Cierre mediante fase finalizadora `RECONOCIMIENTO_INTERESADO`. No requiere campo nuevo en Solicitud. |
| OTRO | Fase finalizadora genérica; el tramitador elige el documento de cierre. |

#### `fecha_fin`
Conclusión del análisis: no administrativa (marcador operacional). La fecha administrativa real vive en el documento de la fase finalizadora. **Conclusión arquitectónica posterior:** no debe existir como campo.

---

### FASE — análisis histórico

*(Todas las fases analizadas. Conclusión uniforme: fecha_inicio y fecha_fin son marcadores operacionales sin valor de dominio. No deben existir como campos. Ver mapa de fechas administrativas por fase en la sección anterior.)*
