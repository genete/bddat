# Estado de la cadena de issues — ADR-049

> Registro vivo. `ADR-049` es la fuente de verdad de las decisiones de diseño y vive en
> `docs/decisiones/`; el `PRE-ADR` queda congelado y desfasado a propósito (ver ADR-049,
> cabecera). Aquí solo se lleva la cuenta de en qué issue está cada pieza y en qué orden,
> para no perder el hilo entre sesiones. Se actualiza a mano, sin issue ni rama propios
> (documento de diseño vivo), cada vez que se crea o cierra un issue de la cadena.

---

## Origen

`ADR-049` — [`docs/decisiones/ADR-049-fechas-notificacion-cumplimiento-certificados-cierre.md`](../decisiones/ADR-049-fechas-notificacion-cumplimiento-certificados-cierre.md) — sustituye a #921 y #801, que se cerrarán al final de la cadena con el mismo comentario. El cambio de paradigma del 21/09/2026 (el plazo de resolver es del **acto**, no de la solicitud ni de la fase) partió lo que iba a ser un único N2 en dos: **N2** (aditivo) y **N2b** (destructivo).

## Cadena, en orden

| Orden | Issue | Qué es | Capa | Estado (22/09/2026) |
|---|---|---|---|---|
| 1 | **#926** | Bug: dos `Documento` con el mismo fichero rompen `mover_a_esftt` — prerrequisito de N1 | Backend | Abierto |
| 2 | **#928 (N1)** | Las fechas de notificación solo salen de documentos | Backend | Abierto, no mergeado |
| — | **#927** | Entradas múltiples en `tramites_tareas_documentos` — bloqueado por N1; hace falta antes de N5, en paralelo a la cadena principal | Backend | Abierto |
| 3 | **#930 (N2)** | El plazo es del acto; cumplimiento calculado | Backend | Creado |
| 4 | **#931 (N2b)** | Retira filas y funciones antiguas del catálogo; renombra `SOLICITUD` → `ACTO` | Backend | Creado |
| 5 | **#796** | Suspensión del art. 22, ahora por acto | Backend | Diseño fijado (22/09/2026); pendiente de implementar en M3 |
| 6 | **#922** | Barras de plazo en el árbol/inspector (a reescribir por acto) | Frontend | Abierto, preexistente |
| 7 | **N3** | Amplía `certificados` (columnas `tipo`, `fase_id`) — infraestructura para N4 | Backend | Sin crear, sin número |
| 8 | **N4** | `CERT_CUMPLIMIENTO_FASE`: congela el cálculo del cumplimiento | Backend | Sin crear, sin número |
| 9 | **N5** | Notificación multi-destinatario (`Tarea.notificacion` → lista) | Backend | Sin crear, sin número |
| 10 | **#568** | Edicto tras notificación infructuosa (art. 44) | Backend | Abierto, preexistente |
| 11 | **N6** | `CERT_CIERRE_SOLICITUD` enumera por acto; cierra #921 y #801 | Backend | Sin crear, sin número |
| — | **#929** | `NotificarEditor` y demás — acumula lo que N2, N5 y #568 le aportan; se ejecuta una sola vez | Frontend | Abierto, acumulando |
| — | **#921** | Cierre propio por fase — superado, lo sustituye N6 | — | Abierto, se cierra al final |
| — | **#801** | Certificado de cierre de solicitud — superado, lo sustituye N6 | — | Abierto, se cierra al final |

## Huecos por definir

**N3, N4, N5 y N6 no tienen todavía número ni borrador** — solo el nombre que les da el pre-ADR §7.3 (congelado, orientativo). Ninguno se ha estudiado en un hilo de trabajo.

- ~~N3 y N4 dependen de cómo quede #796~~ — resuelto: #796 fija que solo la causa a) (22.1.a, `REQUERIMIENTO_SUBSANACION`) suspende, automática e inferida como hoy; la causa d) (informes/consultas a organismos) deja de inferirse porque en la práctica no se acuerda ni se comunica. N3 y N4 ya no tienen incertidumbre de diseño pendiente de #796; solo necesitan que exista el plazo por acto (existe desde N2).
- N5 depende de #927.
- N6 depende de N3, N4 y N5. Ya no depende de que #796 modele un acuerdo de suspensión: con solo causa a) activa, el certificado no tiene que declarar suspensiones de informes que nunca llegan a existir jurídicamente.

## Historial de esta tabla

- **22/09/2026** — Creada tras cerrar el hilo de N2/N2b. Refleja el estado justo después de crear #930 y #931.
- **22/09/2026** — #796: criterio de suspensión fijado (solo causa a) suspende; causa d) no se implementa, queda como mejora de procedimiento futura sin issue de motor). Sin cambios de código: escrito en el propio issue. Desbloquea el diseño de N3/N4/N6.
