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

| Orden | Issue | Qué es | Capa | Estado (24/09/2026, tras #932) |
|---|---|---|---|---|
| 1 | **#926** | Bug: dos `Documento` con el mismo fichero rompen `mover_a_esftt` — prerrequisito de N1 | Backend | Cerrado (PR #933) |
| 2 | **#928 (N1)** | Las fechas de notificación solo salen de documentos | Backend | Cerrado (PR #934) |
| — | **#927** | Entradas múltiples en `tramites_tareas_documentos` — desbloqueado por N1; hace falta antes de N5, en paralelo a la cadena principal | Backend | Cerrado (PR #937) |
| 3 | **#930 (N2)** | El plazo es del acto; cumplimiento calculado | Backend | Cerrado (PR #939) |
| 4 | **#931 (N2b)** | Retira filas y funciones antiguas del catálogo; renombra `SOLICITUD` → `ACTO` | Backend | Cerrado (PR #941) |
| 5 | **#796** | Suspensión del art. 22, ahora por acto | Backend | Cerrado (PR #942) |
| 6 | **#922** | Barras de plazo en el árbol/inspector (a reescribir por acto) | Frontend | Abierto, preexistente |
| 7 | **#932 (N3)** | Amplía `certificados` (columnas `tipo`, `fase_id`) — infraestructura para N4 | Backend | Cerrado (PR #944) |
| 8 | **#947 (N4)** | `CERT_CUMPLIMIENTO_FASE`: congela el cálculo del cumplimiento y protege el documento citado | Backend + inspector | Abierto |
| 8b | **N4b** | `CERT_CIERRE_FASE`: el cierre de la fase finalizadora (ocupa `documento_resultado_id`; `reabrir_fase` lo deshace) — partido de N4; va antes de N6 | Backend + inspector | Sin crear, sin número |
| 9 | **N5** | Notificación multi-destinatario (`Tarea.notificacion` → lista) | Backend | Sin crear, sin número |
| 10 | **#568** | Edicto tras notificación infructuosa (art. 44) | Backend | Abierto, preexistente |
| 11 | **N6** | `CERT_CIERRE_SOLICITUD` enumera por acto; cierra #921 y #801 | Backend | Sin crear, sin número |
| — | **#929** | `NotificarEditor` y demás — acumula lo que N2, N5 y #568 le aportan; se ejecuta una sola vez | Frontend | Abierto, acumulando |
| — | **#921** | Cierre propio por fase — superado, lo sustituye N6 | — | Abierto, se cierra al final |
| — | **#801** | Certificado de cierre de solicitud — superado, lo sustituye N6 | — | Abierto, se cierra al final |

## Huecos por definir

**N4b, N5 y N6 no tienen todavía número ni borrador** — solo el nombre que les da el pre-ADR §7.3 (congelado, orientativo; allí N4b iba dentro de N4). Ninguno se ha estudiado en un hilo de trabajo.

- ~~N3 y N4 dependen de cómo quede #796~~ — resuelto: #796 fija que solo la causa a) (22.1.a, `REQUERIMIENTO_SUBSANACION`) suspende, automática e inferida como hoy; la causa d) (informes/consultas a organismos) deja de inferirse porque en la práctica no se acuerda ni se comunica. N4 ya no tiene incertidumbre de diseño pendiente de #796; solo necesita que exista el plazo por acto (existe desde N2). #932 (N3) resultó no depender de #796 en absoluto — es infraestructura de esquema pura.
- ~~#932 (N3) bloquea a N4~~ — cerrado: N4 tiene ya `tipo`, `fase_id` y el índice `(fase_id, tipo)`. ~~Queda para N4 decidir si el PDF se guarda al emitir o se genera al vuelo~~ — decidido en #947: ninguna de las dos, vista HTML única y paso a PDF posterior.
- N5 dependía de #927, ya cerrado.
- N4b depende de #947 (N4): el cierre exige el certificado de cumplimiento.
- N6 depende de N3 (#932), N4 (#947), N4b y N5. Ya no depende de que #796 modele un acuerdo de suspensión: con solo causa a) activa, el certificado no tiene que declarar suspensiones de informes que nunca llegan a existir jurídicamente.

## Historial de esta tabla

- **22/09/2026** — Creada tras cerrar el hilo de N2/N2b. Refleja el estado justo después de crear #930 y #931.
- **22/09/2026** — #796: criterio de suspensión fijado (solo causa a) suspende; causa d) no se implementa, queda como mejora de procedimiento futura sin issue de motor). Sin cambios de código: escrito en el propio issue. Desbloquea el diseño de N3/N4/N6.
- **22/09/2026** — #932 (N3) diseñado y creado: `tipo`/`fase_id` en `certificados`, alternativa mínima frente a endurecer índices existentes (descartado, prematuro) o unificar con `certificados_fase` (descartado, issue aparte del ADR). Bloquea a N4.
- **23/09/2026** — #926 y #928 (N1) cerrados. Orden acordado: #927 y luego #930 (N2).
- **24/09/2026** — #927 cerrado (PR #937): 8 filas `ENTRADA` en `DATOS_CATASTRALES` (las 4 del issue + 4 que exigía `ESTRUCTURA_FTT.json`). N5 queda desbloqueado por este lado. Derivados fuera de la cadena, abiertos: #935 (`sugerencia_subida` mezcla `ENTRADA` y `SALIDA`), #936 (la tabla no distingue por fase) y #938 (repaso general de la tabla contra `ESTRUCTURA_FTT`). Siguiente de la cadena principal: #930 (N2).
- **24/09/2026** — #930 (N2) cerrado (PR #939): el acto como unidad del plazo (`services/actos_solicitud.py`), cumplimiento `calculado` por la notificación al titular, `plazos_de_la_solicitud` para #922 y las 7 filas atómicas migradas (`930_plazo_acto_calculado`). Aditivo: las 4 combinaciones, las 3 filas de fase y las dos funciones antiguas siguen ahí para #931 (N2b). De paso, `NORMATIVA_PLAZOS.md` corregido (art. 40 y AAP+AAC por acto). Derivado fuera de la cadena, abierto: #940 (`afectado_por_reformado` de la tasa marcado solo a mano en desarrollo). Siguiente de la cadena principal: #931 (N2b).
- **24/09/2026** — #931 (N2b) cerrado (PR #941): migración `931_nivel_acto` (fuera las 4 combinaciones y las 3 filas de `FASE`; las 7 atómicas pasan a nivel `ACTO`), retirada del plazo de la solicitud y del de la fase, `EstadoPlazoActo` como única clase y la comunicación de inicio con un plazo por acto. Al verificar el issue contra el código salieron D7–D13; la más seria, D7: el nivel de la fila no es el del nodo del árbol, y renombrar los mapas del nodo habría roto en silencio 3 filas TAREA. `_causas_suspension` se conserva sin llamador para #796 (D8). Siguiente de la cadena principal: #796.
- **24/09/2026** — #796 cerrado (PR #942): migración `796_suspension_solo_causa_a` (marca apagada en las filas de causa d), por camino) y `_plazos_de_actos` conecta las causas, calculadas una vez por solicitud y aplicadas a todos sus actos: el requerimiento cuelga de `ANALISIS_SOLICITUD`, fase de la solicitud entera. La marca sigue siendo dato editable en la administración del catálogo (decisión de Carlos: no se bloquea). La jurisprudencia del issue queda sin verificar y marcada como tal; solo hará falta leerla en CENDOJ si algún día se implementa la causa d). #925 (suspensión a nivel de fase) cerrado como superado por ADR-049 §E. El test de rendimiento de `plazos_de_la_solicitud` pasa de 2 a 3 sentencias por el catálogo de tareas. Siguiente de la cadena principal: #932 (N3).
- **24/09/2026** — #932 (N3) cerrado (PR #944): migración `932_certificados_tipo_fase` (`tipo` con backfill, `fase_id` RESTRICT, índice único parcial `(fase_id, tipo)`), backref `Fase.certificados_cumplimiento` y los dos servicios de certificados pasando `tipo`. Al verificar salió que la ruta `/cert/<id>/pdf` estaba rota desde #425 (`Documento.tipo_documento` no existe); arreglada leyendo `cert.tipo`. Derivado fuera de la cadena: `limpiar_reciclables.py` abortaba por 7 FKs de #887/ADR-044 sin tratar (sesión aparte). Siguiente de la cadena principal: N4, con la decisión PDF guardado / al vuelo pendiente.
- **24/09/2026** — N4 diseñado y creado como **#947**. Cuatro decisiones: (D1) N4 se parte — solo `CERT_CUMPLIMIENTO_FASE`; `CERT_CIERRE_FASE` pasa a un **N4b** propio, antes de N6, que hasta ahora no figuraba en la cadena aunque N6 lo necesita; (D2) sin PDF: una vista HTML única para el borrador calculado y el certificado emitido, con huella, y paso a PDF posterior; ser certificado se lee de la fila de `certificados`, nunca de la url; (D3) el botón de la fase y la vista van en #947; (D4) se protegen el documento citado y su vínculo, no la tarea `NOTIFICAR` entera (POSTAL y NOTIFICA reciben documentos después de emitir). Hallazgo: el pool daba por borrable el documento de un certificado sin tarea (moriría en `IntegrityError`).
