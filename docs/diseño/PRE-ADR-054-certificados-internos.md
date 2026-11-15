# PRE-ADR-054 — Certificados internos: qué documentan, cuáles son expediente y dónde vive la motivación

**Estado:** Borrador vivo. Revisión de #1057 en curso: 2 de 6 certificados cerrados.
**Fecha:** 2026-11-15
**Issue:** #1057
**Número:** reservado. Pasará a ADR-054 conservándolo, cuando estén revisados los seis certificados.
**Relacionados:** ADR-027 (pertenencia al expediente) · ADR-043 (fin de instrucción) · ADR-049 (certificados de cierre) · #572 · #614 · #435 · #403

> Solo recoge decisiones de Carlos. Lo que es interpretación va marcado como tal.

---

## Por qué existe

#1057 documentó que BDDAT emite seis certificados internos con seis patrones distintos: dos tablas, tres formas de guardar el contenido, cinco anclas y tres formas de deshacerlos. Unificarlos sin más habría consolidado certificados que quizá no hacen falta. Antes de homogeneizar se revisa **si cada uno debe existir** y para qué, desde el punto de vista legal.

Cada certificado, del más antiguo al más moderno, pasa por estas preguntas. No hace falta responderlas todas: su fin es eliminar alguno.

1. ¿Es documento del expediente, en el sentido del art. 70 LPACAP?
2. ¿Todo lo que dice se deduce de lo que ya existe en BDDAT?
3. ¿Es legalmente necesario?
4. ¿O es solo una forma de resumir lo ocurrido?

`CERT_PLAZO_TABLON` es externo (lo emite el ayuntamiento) y queda fuera.

## Criterios asentados

- **Pertenencia al expediente.** Un certificado interno sin firma ni CSV, generado por BDDAT con información que ya consta, es información auxiliar (art. 70.4 LPACAP): no forma parte del expediente (`integra_expediente = false`, propiedad del tipo, ADR-027 §3). Lo sería si estuviera firmado y con CSV.
- **Motivación.** Solo cabe en la resolución (arts. 35 y 88.3 LPACAP). El certificado es apoyo del técnico para decidir qué relato usa. El sistema avisa de lo que debería incluirse y no bloquea: no puede saber si lo que se salió de la regla es una desviación jurídica o una limitación del sistema.
- **Fuente del relato.** La bitácora y el árbol, no el certificado. El context builder de la resolución debe leer de ellos y ofrecer el relato sin imponerlo en la plantilla.

## Decisiones por certificado

### 1. `CERT_FIN_INSTRUCCION` (#373) — cerrado

- No es expediente: su relato es un resumen, la auditoría del motor es información de la aplicación y los actos salvados son juicio del tramitador.
- No es legalmente necesario: el art. 82 LPACAP regula la audiencia y no exige certificado ni diligencia. Que «instruidos los procedimientos» sea un hecho declarado es una construcción de BDDAT (ADR-043 §A).
- Lo único no derivable de otras fuentes es la declaración «la instrucción ha concluido» y la foto de la auditoría del motor. El relato se deriva del árbol; los actos salvados y sus justificaciones, de la bitácora.
- Los escapes de la fase finalizadora los relatan los certificados de cierre, no este.
- Qué se hace con el certificado (mantener, simplificar, retirar) se decide en conjunto al cerrar la revisión. La guarda del art. 82.1 sobre la fase finalizadora no se toca aquí.

### 2. `CERT_PLAZO_CUMPLIDO` (#425) — cerrado

- Auxiliar y no expediente. Es deducible (copia lo que ya calcula `plazos`) y no es legalmente necesario: ni el RD 1955/2000 (arts. 127.2, 127.4, 131.1 y 131.4) ni la LPACAP (arts. 68, 73 y 80) exigen un documento. El efecto lo produce el transcurso del plazo o, cuando el afectado es el titular, una resolución (arts. 68.1 y 73.3). Su relato es antecedente de hecho de la resolución.
- Para BDDAT, la espera necesita un documento producido para que avance la tramitación, y el certificado cubre ese hueco. Se distinguen tres casos por el **efecto del vencimiento** que ya lleva el catálogo (`efectos_plazo`):

| Caso | Efecto en el catálogo | Qué hace el certificado |
|---|---|---|
| A. No se espera documento | `SIN_EFECTO_AUTOMATICO` | Cubre un hueco estructural de BDDAT |
| B. Se espera, pero se puede proseguir sin él | `CONFORMIDAD_PRESUNTA` | Cierra el trámite y permite continuar |
| C. Se espera y su ausencia tiene efecto desfavorable | `TENER_POR_DESISTIDO` (titular); `DISCONFORMIDAD_PRESUNTA` (organismo, nuevo) | Cubre el hueco; el context builder avisa al técnico |

- **Un solo certificado, sin tipo nuevo.** El aviso del context builder sale de comprobar a qué fase o trámite pertenece la ausencia de respuesta.
- Si en el caso C el documento llega después, ocupa el hueco que cubría el certificado. El técnico decide en la resolución; BDDAT no automatiza esa decisión. *[Interpretación: el documento puede ocupar el hueco hasta que se notifique la resolución, art. 73.3.]*
- En el caso B, el documento tardío es otra cosa que se tratará más adelante (art. 80.4: «podrá no ser tenido en cuenta»). Sin issue por ahora.
- No hace falta registrar quién emite el certificado: el relato es lo importante y se genera con la información de ese momento.
- *[Interpretación: queda por decidir si el texto del certificado debe distinguir «plazo cumplido» (caso A) de «ausencia de respuesta» (casos B y C).]*

### 3 a 6. Pendientes de revisar

`CERT_FIN_IP_CONSULTAS` (#470) · `CERT_CUMPLIMIENTO_FASE` (#947) · `CERT_CIERRE_FASE` (#956) · `CERT_CIERRE_SOLICITUD` (#996), en ese orden.

## Asuntos nuevos que han salido

1. **Hueco del catálogo: el silencio negativo del organismo consultado** (informe de la Ley de Impulso para la Sostenibilidad del Territorio de Andalucía, LISTA), que equivale a una **disconformidad presunta**. Ningún efecto de `efectos_plazo` lo cubre. Se prevé `DISCONFORMIDAD_PRESUNTA`, pareja de `CONFORMIDAD_PRESUNTA`. Es un dato, no código (la tabla es maestra, no un ENUM): una fila por migración que se añadirá con el trámite LISTA, el cual necesitará además su fila de plazo (las esperas sin plazo, #789, no admiten el certificado). La variable `ausencia_informe_lista_en_plazo` del context builder sale de comprobar que la ausencia de respuesta corresponde a la fase o trámite LISTA. *Pendiente: leer la LISTA y confirmar el silencio negativo con la norma.*
2. **Resolución asistida.** Issue `[DISEÑO]` nuevo, enlazado a #435: el context builder de la resolución lee bitácora y árbol y ofrece relato para antecedentes y fundamentos reglados; avisa, no bloquea. Hoy `ContextoResolucion` (#403) solo lee cuatro textos escritos a mano de `resoluciones`.
3. **Bitácora.** El detalle del escape no guarda `solicitud_id`, así que un escape sobre algo borrado es irrecuperable para el informe. Se arregla dentro de #614 (que no se divide), por trozos y sin esperar al ADR del log, que forma parte de #614. #530 no cubre esto: es la API del dock.
4. **La espera no pinta «tarde».** El tratamiento de la llegada fuera de plazo existe solo en el plazo de resolver del acto. En `ESPERAR_PLAZO` la barra queda verde sin distinguir y el plazo de la tarea no lleva `cumplido_fuera_de_plazo`. Mejora pequeña pendiente.
5. **Vía de retirada del certificado** cuando llega el documento tardío (caso C), cerrada una vez notificada la resolución. Hoy no existe.

## Documentos afectados

| Qué | Acción | Estado |
|---|---|---|
| ADR-027 (Alternativa A y §2) | Corrección fechada | Hecho |
| `plazos.py` (`EstadoPlazo.efecto`) | Docstring: el hueco y el efecto previsto | Hecho |
| `DISEÑO_FECHAS_PLAZOS.md` §2.4 | Nota del hueco | Hecho |
| `informe_instruccion.py` (comentario «#430, ADR-035») | Referencia a este PRE-ADR | Hecho |
| #572 | Tipos que entran con `integra_expediente = false` | Pendiente (GitHub) |
| #1057, #614, #435 | Comentario que enlace aquí | Pendiente (GitHub) |
| Issue `[DISEÑO]` de resolución asistida | Crearlo | Pendiente (GitHub) |
| `INVENTARIO_BACKEND.md` l.283 y ADR-030 §5 («los 9 valores no-nulos») | Al añadir la fila del efecto | Al implementar |
| `TIPOS_DOCUMENTOS_CATALOGO.md` l.64 y l.70, y la descripción sembrada en BD (migración 377) | Incoherencias de #1057: el fin de instrucción no es automático | Al implementar #1057 |
| `app/models/certificados.py` (docstring) | Lista `CERT_FIN_INSTRUCCION` entre los tipos con `datos` | Al implementar #1057 |
