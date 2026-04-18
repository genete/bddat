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

## Principio transversal — Coherencia de fechas

**Las validaciones de coherencia de fechas son invariantes estructurales del sistema, no reglas del motor.**
Se implementan en `invariantes_esftt.py` y se aplican uniformemente a todos los elementos SFTT,
independientemente del tipo. No son imposiciones legales — son la integridad mínima del modelo.

| Invariante | Aplica a |
|---|---|
| `fecha_fin ≥ fecha_inicio` (o `fecha_solicitud`) | Todos los elementos SFTT |
| `fecha_inicio` del hijo ≥ `fecha_inicio` del padre | Fase/Trámite/Tarea respecto a su contenedor |
| `fecha_fin` del hijo ≤ `fecha_fin` del padre | Solo cuando el padre esté cerrado |

La columna **Coherencia** de las tablas siguientes recoge solo las particularidades por tipo,
asumiendo que los invariantes anteriores se comprueban siempre.

---

## Principio transversal — Interior de solo lectura y DESFINALIZAR

**Un contenedor cerrado (`fecha_fin IS NOT NULL`) convierte su interior en solo lectura.**
DESFINALIZAR (borrar `fecha_fin`) es el mecanismo de corrección — sin él el sistema
crea callejones sin salida ante errores en el interior.

| Contenedor cerrado | Interior bloqueado (solo lectura) |
|---|---|
| Solicitud (`fecha_fin IS NOT NULL`) | Fases, Trámites, Tareas |
| Fase (`fecha_fin IS NOT NULL`) | Trámites, Tareas |
| Trámite (`fecha_fin IS NOT NULL`) | Tareas |

### Reglas de implementación

1. **DESFINALIZAR — regla confirmada solo para Solicitud** (`fecha_fin` no administrativa):
   siempre permitido, no pasa por el motor. Sí pasa por `invariantes_esftt.py` para
   verificar coherencia con el exterior (no se puede DESFINALIZAR si el contenedor
   externo está cerrado — primero hay que reabrir el nivel superior).
   **Para Fase, Trámite y Tarea: pendiente de confirmar por tipo.** Si `fecha_fin`
   resulta administrativa en algún tipo, DESFINALIZAR puede requerir condiciones
   adicionales o estar bloqueado. Se resolverá en el análisis tipo a tipo de cada nivel.

2. **DESFINALIZAR Solicitud** resetea también `estado` a `EN_TRAMITE`. Son dos campos que
   se escriben en la misma operación atómica.

3. **Invariante en `invariantes_esftt.py`**: antes de cualquier operación sobre un hijo
   (CREAR, INICIAR, FINALIZAR, BORRAR, editar), comprobar que el contenedor está abierto.
   Si está cerrado → bloquear con mensaje que identifica el contenedor a reabrir.

4. **UX — oferta de reapertura**: la vista puede ofrecer el atajo "¿Reabrir [contenedor]
   primero?" cuando el invariante bloquea. El motor solo bloquea; la vista decide si ofrece
   el atajo. No es responsabilidad del motor ni de `invariantes_esftt.py`.

5. **DESFINALIZAR en cascada**: si el elemento a reabrir está dentro de un contenedor
   cerrado, se bloquea hasta que el usuario reabra primero el contenedor externo.
   El sistema no reabre en cascada automáticamente — el usuario confirma cada nivel.
   La oferta de reapertura puede mostrar la cadena completa para orientar al usuario.

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
| **es_administrativa** | **No** | Marcador operacional — "cierre voluntario de la tramitación por el usuario". Sin valor jurídico propio. La fecha administrativa real vive en el Documento de la fase finalizadora (RESOLUCION, RECONOCIMIENTO_INTERESADO…). Fuente: `DISEÑO_FECHAS_PLAZOS.md §3.0`. |
| **DESFINALIZAR (→ NULL)** | **Permitido** | Mecanismo de corrección necesario. También resetea `estado` → `EN_TRAMITE` en la misma operación atómica. Ver principio transversal de solo lectura. |
| **Coherencia** | Invariante estructural | `fecha_fin ≥ fecha_solicitud`. Comprobado en `invariantes_esftt.py`. |
| **Estado modelo** | ✅ Correcto | `Date nullable`. Regla en docstring: "debería tener fecha_fin si estado ≠ EN_TRAMITE" (débil — correcta). |
| **Estado UI** | ⬜ Pendiente de revisar | Verificar: ¿se puede poner fecha_fin sin que exista fase finalizadora cerrada? ¿Se bloquea la edición del interior cuando fecha_fin IS NOT NULL? |
| **Decisiones/pendientes** | Ver issue #302 (fase finalizadora). Implementar bloqueo de interior cuando solicitud cerrada. Implementar oferta de reapertura en UI. |

---

## FASE

> Pendiente — sesión siguiente.

---

## TRÁMITE

> Pendiente — sesión siguiente.

---

## TAREA

> Pendiente — sesión siguiente.
