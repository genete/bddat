# Modelo de estados-semáforo ESFTT

**Estado:** Vigente
**Fecha:** 2026-05-30
**Relacionado:** #500 (vista de árbol), ADR-016, `app/services/seguimiento.py`
**Supera:** §4.1–§4.4 de `docs/historial/ANALISIS_LISTADO_INTELIGENTE.md` (histórico; allí
`PUBLICAR`, `REDACTAR`/`FIRMAR` como tareas e `INCORPORAR` ya no existen).

> **Fuente de verdad** del color/estado que comunica cada nodo del árbol del expediente
> (Expediente · Solicitud · Fase · Trámite · Tarea) y, en general, del semáforo de
> seguimiento. Lo consumen: la **vista de árbol** (#500), el **listado inteligente** y
> `services/seguimiento.py`.

---

## 1. Dos planos: estado de dominio vs estado-semáforo

- **Estado de dominio** (properties ya existentes: `Solicitud.estado`, `Fase.estado`,
  `Tramite.estado`, `Tarea.estado`): sale de la **completitud estructural** (¿tengo hijos?;
  en tareas, ¿tengo los documentos?). Es grueso.
- **Estado-semáforo**: el color fino que se muestra. El dominio lo **acota**:

  | Estado de dominio | Semáforo |
  |---|---|
  | planificada (sin hijos / sin doc de entrada) | siempre **TRAMITAR** 🔴 |
  | en curso | uno de los intermedios (ver tablas) |
  | `PDTE_CIERRE` (solo fase) | **ESTUDIAR** 🔴 o **CERRAR** 🟠 |
  | finalizada / ejecutada | **FIN** 🟢 |

  El trabajo de cómputo se concentra en el **"en curso"**: planificada y finalizada se
  resuelven con el estado de dominio directo.

---

## 2. Semántica de colores

| Color | Significado |
|---|---|
| 🔴 Rojo | Acción pendiente del tramitador |
| 🟡 Amarillo | En espera de algo interno que no depende del tramitador (firma) |
| 🔵 Azul | En espera de un externo ajeno a la administración (destinatario, boletín) |
| 🟠 Naranja | Listo para cerrar / reintento disponible |
| ⚪ Gris | Espera pasiva (plazo legal, respuesta de administrado u organismo) |
| 🟢 Verde | Finalizado |

---

## 3. Estado-semáforo por tipo de tarea

Tipos de tarea vigentes: **ANALIZAR · ELABORAR · NOTIFICAR · ESPERAR_PLAZO**.
Regla general: **verde = tarea ejecutada**; el **naranja CERRAR no aplica a tareas**
(solo a fase/solicitud, §4).

### ANALIZAR
| Situación (documentos) | Estado | Color |
|---|---|---|
| sin documento consumido | PENDIENTE_TRAMITAR | 🔴 |
| consumido presente, sin producido | PENDIENTE_ESTUDIO | 🔴 |
| producido (informe) y tarea ejecutada | FIN | 🟢 |

### ELABORAR  *(absorbe las antiguas REDACTAR + FIRMAR como subestados)*
| Situación (documentos) | Estado | Color |
|---|---|---|
| sin documento consumido | PENDIENTE_TRAMITAR | 🔴 |
| consumido (p. ej. de ANALIZAR), sin `BORRADOR_FIRMA` | PENDIENTE_REDACTAR | 🔴 |
| consumido + PDF `BORRADOR_FIRMA` (listo para firma) | PENDIENTE_FIRMA | 🟡 |
| producido = PDF firmado (tarea ejecutada) | FIN | 🟢 |

El PDF listo para firma entra como documento **consumido** (insumo del subpaso de firma);
el firmado es el **único producido** (resultado). Requiere un tipo de documento nuevo
`BORRADOR_FIRMA` (ver §6). El envío a firma lo hace hoy el usuario; se automatizará con un
scheduler + Playwright (futuro).

### NOTIFICAR  *(absorbe el azul de la antigua PUBLICAR: notificación a interesado y publicación en boletín)*
Usa el modelo `Notificacion` (`resultado` CORRECTA|INCORRECTA, `numero_intento` 1|2 — regla
LPACAP de dos intentos).
| Situación | Estado | Color |
|---|---|---|
| sin documento firmado que notificar | PENDIENTE_TRAMITAR | 🔴 |
| documento presente, sin notificación registrada | PENDIENTE_NOTIFICAR | 🔵 |
| `Notificacion` CORRECTA | FIN | 🟢 |
| INCORRECTA, `numero_intento = 1` (queda 2º intento) | NOTIFICACION_FALLIDA | 🟠 |
| INCORRECTA, `numero_intento = 2` (agotada → procede edicto) | NOTIFICACION_AGOTADA | 🔴 |

### ESPERAR_PLAZO  *(el estado de plazo lo computa `services/plazos.obtener_estado_plazo`)*
| Situación | Estado | Color |
|---|---|---|
| plazo no configurado (`SIN_PLAZO`) | PENDIENTE_TRAMITAR | 🔴 |
| plazo activo o indefinido (`EN_PLAZO`) | PENDIENTE_PLAZOS / PENDIENTE_SUBSANAR | ⚪ |
| plazo vencido (`VENCIDO`) | PENDIENTE_ESTUDIO | 🔴 |
| tarea ejecutada | FIN | 🟢 |

El **"próximo a vencer"** (`PROXIMO_VENCER`) **no** se refleja en el círculo de estado: va
por el **badge de plazo** del nodo (canal aparte, §5).

---

## 4. Estado-semáforo de los contenedores (no-tarea)

| Nodo | Situación | Estado | Color |
|---|---|---|---|
| Cualquiera | sin hijos (planificado) | PENDIENTE_TRAMITAR | 🔴 |
| Fase | `PDTE_CIERRE` sin `resultado_fase` | PENDIENTE_ESTUDIO | 🔴 |
| Fase | `PDTE_CIERRE` con resultado decidido, falta formalizar | PENDIENTE_CERRAR | 🟠 |
| Solicitud | todas las pistas en FIN pero aún EN_TRAMITE | PENDIENTE_CERRAR | 🟠 |
| Cualquiera | en curso con hijos | **color de mayor prioridad** de su subárbol (§5) |
| Cualquiera | finalizado | FIN | 🟢 |

---

## 5. Agregación de abajo arriba (colapso) y prioridad

Mismo algoritmo que `services/seguimiento.py`: se recorre el árbol de abajo arriba y
**prevalece el estado de mayor prioridad**; el contador acumula a través de niveles.

**Prioridad de urgencia** (1 = más urgente; alineada con `seguimiento.PRIORIDAD`, refinable
al implementar):

| # | Estado | Color |
|---|---|---|
| 1 | PENDIENTE_TRAMITAR | 🔴 |
| 2 | PENDIENTE_ESTUDIO | 🔴 |
| 3 | PENDIENTE_REDACTAR | 🔴 |
| 3 | NOTIFICACION_AGOTADA | 🔴 |
| 4 | PENDIENTE_FIRMA | 🟡 |
| 5 | PENDIENTE_NOTIFICAR | 🔵 |
| 6 | NOTIFICACION_FALLIDA | 🟠 |
| 6 | PENDIENTE_CERRAR | 🟠 |
| 7 | PENDIENTE_SUBSANAR / PENDIENTE_PLAZOS | ⚪ |
| 8 | FIN | 🟢 |

---

## 6. Presentación en la vista de árbol (#500)

- **Un único canal cromático**: un **círculo-semáforo** en una esquina de la caja. El borde
  de la caja **no** lleva color de nivel (el nivel se reconoce por tamaño/posición).
- **Todos los nodos** llevan el círculo: por defecto **hueco con borde gris**.
- Se **rellena** con color solo si el nodo "tiene algo que decir": las **tareas** (casi
  siempre), las **fases** en `PDTE_CIERRE`, y los nodos **sin hijos** (TRAMITAR 🔴).
- **En colapso**, el círculo toma el **color de mayor prioridad** del subárbol (§5). El
  placeholder universal existe justamente para poder pintar ese resumen.
- El **significado** del color aparece en el **hover** (tooltip).

---

## 7. Implicación de implementación

El color sale del **estado-semáforo**, que **no** viaja hoy en el árbol (que manda el
`estado` de dominio). El serializador del árbol (`services/arbol_expediente.py`) deberá
computarlo por nodo —incluyendo mirar los **tipos** de documento consumidos (ELABORAR →
`BORRADOR_FIRMA`) y las filas **`Notificacion`** (resultado + `numero_intento`)— y propagar
el de mayor prioridad a los no-hoja, **reutilizando `services/seguimiento.py`**.

**Deuda a alinear:** `seguimiento.py` implementa hoy una versión previa donde
`PENDIENTE_ELABORAR` es un único estado amarillo; este modelo lo desdobla en
`PENDIENTE_REDACTAR` (🔴) + `PENDIENTE_FIRMA` (🟡). Al implementar el círculo del árbol hay
que unificar ambos consumidores contra este documento.

---

## 8. Pendientes / futuro

- Tipo de documento `BORRADOR_FIRMA` en `tipos_documentos` (migración) — necesario para el
  subestado FIRMA de ELABORAR.
- Scheduler + Playwright que envíe a firma las tareas en estado FIRMA (hoy lo hace el usuario).
- Refinar la prioridad numérica fina al unificar con `seguimiento.PRIORIDAD`.
