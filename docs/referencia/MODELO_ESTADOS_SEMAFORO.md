# Modelo de estados-semáforo y decoradores del nodo ESFTT

**Estado:** Vigente
**Fecha:** 2026-05-30 (actualizado 2026-07-23 — nuevo estado `PENDIENTE_RESULTADO_NOTIFICACION`, ADR-034/#657/#658)
**Relacionado:** #500 (vista de árbol), #558 (núcleo unificado), ADR-016, ADR-034,
`app/services/estado_dominio.py` (núcleo), `app/services/seguimiento.py`,
mockup `docs/mockups/Mockup_Nodo_Arbol.html`.
**Supera:** §4.1–§4.4 de `docs/historial/ANALISIS_LISTADO_INTELIGENTE.md` (histórico; allí
`PUBLICAR`, `REDACTAR`/`FIRMAR` como tareas e `INCORPORAR` ya no existen).

> **Fuente de verdad** del color/estado y de los decoradores (documentos, plazo) y de la
> anatomía de cada nodo del árbol del expediente (Expediente · Solicitud · Fase · Trámite ·
> Tarea). Lo consumen: la **vista de árbol** (#500), el **listado inteligente** y
> `services/seguimiento.py`.

---

## 1. Dos planos: estado de dominio vs estado-semáforo

- **Estado de dominio** (properties existentes `Solicitud.estado`, `Fase.estado`,
  `Tramite.estado`, `Tarea.estado`): sale de la **completitud estructural** (¿tengo hijos?;
  en tareas, ¿tengo los documentos?). Es grueso.
- **Estado-semáforo**: el color fino que se muestra. El dominio lo **acota**:

  | Estado de dominio | Semáforo |
  |---|---|
  | planificada (sin hijos / sin doc de entrada) | siempre **TRAMITAR** 🔴 |
  | en curso | uno de los intermedios (ver tablas) |
  | `PDTE_CIERRE` (solo fase) | **ESTUDIAR** 🔴 o **CERRAR** 🟠 |
  | finalizada / ejecutada | **FIN** 🟢 |

  El cómputo se concentra en el "en curso": planificada y finalizada las da el dominio directo.

---

## 2. Semántica de colores

Ordenados por urgencia; la prioridad de §5 es coherente con esta escala (#558).

| Color | Significado |
|---|---|
| 🔴 Rojo | Acción del tramitador (incl. notificación agotada → procede boletín) |
| 🟠 Naranja | Gestión nuestra: cerrar fase / 2.º intento de notificación |
| 🟡 Amarillo | Espera interna que no depende del tramitador (firma); paraliza si falta |
| 🔵 Azul | Espera de un externo ajeno a la administración (destinatario, boletín) |
| ⚪ Gris | Espera pasiva (plazo legal, respuesta de administrado u organismo) |
| 🟢 Verde | Finalizado |

---

## 3. Estado-semáforo por tipo de tarea

Tipos vigentes: **ANALIZAR · ELABORAR · NOTIFICAR · ESPERAR_PLAZO**.
Regla general: **verde = tarea ejecutada**; el **naranja CERRAR no aplica a tareas** (solo a
fase/solicitud, §4).

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

El PDF listo para firma entra como **consumido** (insumo del subpaso de firma); el firmado es
el **único producido**. Requiere el tipo de documento `BORRADOR_FIRMA` (§11). Hoy el envío a
firma lo hace el usuario; se automatizará con scheduler + Playwright (futuro).

### NOTIFICAR  *(absorbe el azul de la antigua PUBLICAR)*
Usa el modelo `Notificacion` (`resultado` CORRECTA|INCORRECTA|NULL, `numero_intento` 1|2 —
LPACAP), anclado a `tarea_id` (ADR-034, #657/#658 — corrige ADR-008): la fila puede existir
sin documento producido (camino A, "Registrar envío") y sin resultado mientras se espera el
justificante definitivo.
| Situación | Estado | Color |
|---|---|---|
| sin documento firmado que notificar | PENDIENTE_TRAMITAR | 🔴 |
| documento presente, sin fila `Notificacion` | PENDIENTE_NOTIFICAR | 🔵 |
| fila `Notificacion` con `resultado IS NULL` (envío registrado, falta el definitivo) | PENDIENTE_RESULTADO_NOTIFICACION | 🔵 |
| `Notificacion` CORRECTA | FIN | 🟢 |
| INCORRECTA, `numero_intento = 1` (queda 2º intento) | NOTIFICACION_FALLIDA | 🟠 |
| INCORRECTA, `numero_intento = 2` (agotada → procede edicto) | NOTIFICACION_AGOTADA | 🔴 |

### ESPERAR_PLAZO  *(estado de plazo vía `services/plazos.obtener_estado_plazo`)*
| Situación | Estado | Color |
|---|---|---|
| plazo no configurado (`SIN_PLAZO`) | PENDIENTE_TRAMITAR | 🔴 |
| plazo activo o indefinido (`EN_PLAZO`) | PENDIENTE_PLAZOS / PENDIENTE_SUBSANAR | ⚪ |
| plazo vencido (`VENCIDO`) | PENDIENTE_ESTUDIO | 🔴 |
| tarea ejecutada | FIN | 🟢 |

El detalle temporal del plazo (incl. "próximo a vencer") **no** va en el círculo: se muestra
con la **barra de progreso** (§9).

---

## 4. Estado-semáforo de los contenedores (no-tarea)

| Nodo | Situación | Estado | Color |
|---|---|---|---|
| Cualquiera | sin hijos (planificado) | PENDIENTE_TRAMITAR | 🔴 |
| Fase finalizadora | `PDTE_CIERRE` sin `resultado_fase` (falta decidir) | PENDIENTE_ESTUDIO | 🔴 |
| Fase finalizadora | `PDTE_CIERRE` con resultado, falta formalizar | PENDIENTE_CERRAR | 🟠 |
| Fase intermedia | `PDTE_CIERRE` (cierra por certificado; `resultado_fase` NULL) | PENDIENTE_CERRAR | 🟠 |
| Solicitud | todas las pistas en FIN pero aún EN_TRAMITE | PENDIENTE_CERRAR | 🟠 |
| Cualquiera | en curso con hijos | **mayor prioridad** del subárbol (§5) |
| Cualquiera | finalizado | FIN | 🟢 |

---

## 5. Agregación de abajo arriba (colapso) y prioridad

El núcleo `estado_dominio` (#558) es la única fuente, compartida por la vista de árbol y
por `seguimiento.py`: se recorre de abajo arriba y prevalece el estado de **mayor
prioridad**; cada proyección acumula su propio contador.

**Prioridad canónica** (1 = más urgente; orden total, coherente con el color):

| # | Estado | Color |
|---|---|---|
| 1 | PENDIENTE_TRAMITAR | 🔴 |
| 2 | PENDIENTE_ESTUDIO | 🔴 |
| 3 | PENDIENTE_REDACTAR | 🔴 |
| 4 | NOTIFICACION_AGOTADA | 🔴 |
| 5 | PENDIENTE_CERRAR | 🟠 |
| 6 | NOTIFICACION_FALLIDA | 🟠 |
| 7 | PENDIENTE_FIRMA | 🟡 |
| 8 | PENDIENTE_NOTIFICAR | 🔵 |
| 9 | PENDIENTE_RESULTADO_NOTIFICACION | 🔵 |
| 10 | PENDIENTE_PLAZOS | ⚪ |
| 11 | FIN | 🟢 |

`PENDIENTE_SUBSANAR` no es del núcleo: es el relabel de `PENDIENTE_PLAZOS` en la pista SOL
del seguimiento (mismo gris).

---

## 6. Anatomía del bloque

Todos los nodos comparten la **misma caja** (rectángulo redondeado): se distinguen por el
**icono de tipo**, no por forma ni por color de borde. Disposición (ver mockup
`docs/mockups/Mockup_Nodo_Arbol.html`):

- **Cabecera** (con raya horizontal inferior): icono de tipo a la **izquierda** (sin
  separador) · **título** centrado en MAYÚSCULAS · **círculo-semáforo** a la derecha.
- **Cuerpo**: zona central libre (badges, fecha, texto) y, a la **derecha sin raya** (solo
  separación), la columna de **documentos** (consumido ▼ arriba, producido ▲ abajo).
- **Footer** (con raya horizontal superior): **barra(s) de progreso** de plazo, solo si aplica.

Únicas líneas del bloque: las **dos horizontales** (bajo cabecera y sobre footer). **Sin rayas
verticales** — máxima limpieza.

**Iconos de tipo** (versión base de `Iconos_ESFTT+TAREAS-ESTADOS.html`; el estado lo da el
semáforo, no el icono):

| Nivel | Icono |
|---|---|
| Expediente | `bi-folder2` |
| Solicitud | `bi-file-earmark` |
| Fase | `bi-diagram-3` |
| Trámite | `bi-clipboard` |
| Tarea ANALIZAR | `bi-person-gear` |
| Tarea ELABORAR | `bi-pen` |
| Tarea NOTIFICAR | `bi-send` |
| Tarea ESPERAR_PLAZO | `bi-hourglass-split` |

---

## 7. Decorador de ESTADO: círculo-semáforo

- **Un único canal cromático**: el **círculo-semáforo** en la cabecera, a la derecha (§6).
- Todos los nodos lo llevan: por defecto **hueco con borde gris**.
- Se **rellena** solo si el nodo "tiene algo que decir": tareas (casi siempre), fases en
  `PDTE_CIERRE`, nodos sin hijos (TRAMITAR 🔴).
- En **colapso**, toma el **color de mayor prioridad** del subárbol (§5); de ahí el placeholder
  universal.
- El **significado** del color aparece en el **hover**.

---

## 8. Decorador de DOCUMENTOS: icono-flecha + contador

Columna a la derecha del cuerpo (sin raya, §6). Por cada rol (consumido / producido):

- **Icono de documento con flecha**: flecha **entrando** ▼ = consumido (arriba); flecha
  **saliendo** ▲ = producido (abajo).
- **Gris atenuado** si no existe; **con color** si existe.
- **Contador** al lado, pequeño y en **negrita**: `(n)` con el número; `(0)` si puede haber y
  no hay; **`(-)`** si el nodo **no produce/consume** documento de ese rol (p. ej. el producido
  de una solicitud).
- Ámbito: **tareas** y **solicitud**. Los nodos sin documentos (expediente, fase, trámite) no
  llevan la columna.

Backend: **sin coste** — el árbol ya manda `doc_consumido`/`doc_producido` con `{presente, count}`.

---

## 9. Decorador de PLAZO: barra de progreso

Una **barra de progreso** que recorre el bloque de lado a lado (con pequeños márgenes
inicio/fin), en el **footer** (raya superior), simple y sin adornos.

- **Track** (fondo de la barra): gris **más claro** que el fondo del bloque.
- **Relleno** según el estado del plazo:
  | Situación | Relleno |
  |---|---|
  | no vencido | gris medio |
  | próximo a vencer | 🟠 naranja |
  | vencido | 🔴 rojo (barra al 100%) |
  | tarea completada | 🟢 verde, **congelada** a la fecha del documento producido |
- **v1 (vigente): relleno SEMÁNTICO** — la longitud refleja el *estado* del plazo (en plazo:
  parcial gris · próximo: naranja · vencido: 100% rojo · ejecutada: verde congelado). Usa solo
  lo que ya computa el backend → **coste ≈ 0**.
- **Diferido: relleno PROPORCIONAL** — longitud = tiempo hábil transcurrido / total. Más fiel,
  pero exige exponer el progreso en **días hábiles** desde `plazos.py`. No entra en v1.

**Dónde aplica:**
- **Tarea ESPERAR_PLAZO**: siempre.
- **Tarea NOTIFICAR**: plazo de **lectura** de la notificación; **dos barras** si hay 2º intento.
- **Solicitud**: si el cálculo de plazos da un plazo administrativo de solicitud.

---

## 10. Implicación de implementación

- **Estado (círculo):** sale del estado-semáforo, que **no** viaja hoy (el árbol manda el
  `estado` de dominio). `services/arbol_expediente.py` deberá computarlo por nodo —mirando
  **tipos** de documento consumidos (ELABORAR → `BORRADOR_FIRMA`) y filas **`Notificacion`**
  (resultado + `numero_intento`)— y propagar la mayor prioridad a los no-hoja, **reutilizando
  `seguimiento.py`** (hecho en #558 vía el núcleo `estado_dominio.py`).
- **Plazo (barra):** la v1 semántica usa el `estado` de plazo ya disponible. La proporcional
  (diferida) exigirá el progreso en días hábiles + plazo de **solicitud** y de **lectura de
  notificación** por intento.
- **Documentos:** sin cambios de backend.

**Deuda resuelta (#558):** unificada en el núcleo `estado_dominio`. `seguimiento.py` y la
vista de árbol son ahora proyecciones sobre la misma fuente; `PENDIENTE_ELABORAR` (🟡 único)
queda desdoblado en `PENDIENTE_REDACTAR` (🔴) + `PENDIENTE_FIRMA` (🟡).

---

## 11. Pendientes / futuro

- Tipo de documento `BORRADOR_FIRMA` en `tipos_documentos` (migración) — para el subestado FIRMA.
- Scheduler + Playwright que envíe a firma las tareas en estado FIRMA.
- Barra de plazo **proporcional** (progreso en días hábiles), plazo de **solicitud** y de
  **lectura de notificación** por intento.
- ~~Refinar la prioridad numérica fina al unificar con `seguimiento.PRIORIDAD`.~~ Hecho en #558 (§5).
