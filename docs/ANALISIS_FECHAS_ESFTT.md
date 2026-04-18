# Análisis de fechas ESFTT — fuente para `metadatos_fechas`

> **Fecha:** 2026-04-18
> **Estado:** En construcción — sesión de análisis tipo a tipo.
> **Destino:** seed y referencia de la tabla `metadatos_fechas` (diseño en `DISEÑO_FECHAS_PLAZOS.md §3.1`).
>
> **Columnas:**
> - **es_administrativa** — tiene valor legal para cómputo de plazos (art. 21 LPACAP y norma sectorial)
> - **DESINICIAR/DESFINALIZAR** — si puede borrarse el valor una vez puesto
> - **Coherencia** — validaciones de rango/contexto que el sistema debería aplicar
> - **Estado modelo** — situación actual en el modelo Python y la BD
> - **Estado UI** — situación actual en el interfaz
> - **Decisiones/pendientes** — lo que queda por resolver o implementar

---

## SOLICITUD

### `fecha_solicitud`

| Atributo | Valor | Notas |
|---|---|---|
| **es_administrativa** | Sí — todos los tipos | Fecha de entrada en Registro (art. 16 LPACAP). Inicio del cómputo del plazo de resolución (art. 21). |
| **DESINICIAR (→ NULL)** | No permitido | Borrarla equivale a borrar la solicitud. No tiene semántica de DESINICIAR. |
| **Coherencia** | ⬜ No comprobada | No se valida que sea ≤ hoy, ni coherencia con fechas de hijos. |
| **Estado modelo** | ✅ Correcto | `NOT NULL`, tipo `Date`. |
| **Estado UI — creación** | ✅ Correcto | El wizard no permite crear solicitud sin esta fecha. |
| **Estado UI — edición** | ⚠️ Parcial | Se puede editar (cambiar por otra fecha). Error al intentar poner NULL: se captura pero con mensaje no humano. No se valida coherencia de la nueva fecha. |
| **Decisiones/pendientes** | Mejorar mensaje de error al intentar NULL. Añadir validación de coherencia (¿fecha ≤ hoy? ¿fecha ≥ fecha_inicio de hijos?). |

#### Clasificación por tipo

| Tipos | `es_administrativa` | Decisión |
|---|---|---|
| AAP, AAC, DUP, AAE_PROVISIONAL, AAE_DEFINITIVA, AAT, RAIPEE_PREVIA, RAIPEE_DEFINITIVA, RADNE, CIERRE, DESISTIMIENTO, RENUNCIA, AMPLIACION_PLAZO, RECURSO, AAP_AAC | **Sí** | A instancia de parte, con entrada en Registro. Sin duda. |
| CORRECCION_ERRORES | **Sí** | Puede ser de oficio (art. 109 LPACAP) o a instancia. **Decisión de simplificación:** siempre administrativa. El tramitador introduce la fecha del documento de registro o la fecha de hoy si es de oficio. |
| INTERESADO | **Sí** | A instancia de parte tiene entrada en Registro. Cuando la Administración emplaza de oficio (art. 8 LPACAP) se introduce la fecha del oficio. **Decisión de simplificación:** siempre administrativa, igual que el resto. El cierre de la solicitud se gestiona mediante un nuevo tipo de **fase finalizadora** (`RECONOCIMIENTO_INTERESADO`) que porta el resultado y el documento (oficio de reconocimiento o resolución denegatoria). No se añade ningún campo nuevo a Solicitud. La regla del motor para FINALIZAR esta solicitud sería: `EXISTS fase RECONOCIMIENTO_INTERESADO con fecha_fin IS NOT NULL`. |
| OTRO | **Sí** | Mismo criterio de simplificación. La fase finalizadora es de tipo genérico; el tramitador elige el documento de cierre libremente. |

---

### `fecha_fin`

| Atributo | Valor | Notas |
|---|---|---|
| **es_administrativa** | — | **Pendiente de respuesta.** ¿Es la fecha de firma de la resolución o de notificación al interesado? |
| **DESFINALIZAR (→ NULL)** | — | Pendiente — depende de si es administrativa. |
| **Coherencia** | — | Pendiente. |
| **Estado modelo** | — | Pendiente de revisar. |
| **Estado UI** | — | Pendiente de revisar. |
| **Decisiones/pendientes** | Confirmar semántica: ¿firma o notificación? Si notificación → `es_administrativa = true` y el sistema puede computar correctamente el plazo art. 21. Si firma → estudiar si se necesita campo `fecha_notificacion` separado o se asume simplificación consciente. |

---

## FASE

> Pendiente — sesión siguiente.

---

## TRÁMITE

> Pendiente — sesión siguiente.

---

## TAREA

> Pendiente — sesión siguiente.
