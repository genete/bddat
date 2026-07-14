# ADR-027 — Pertenencia documental al EXPEDIENTE

**Estado:** Adoptada
**Fecha:** 2026-06-22
**Issue:** #572
**Relacionado con:** ADR-004 (recepción externa = producido de ESPERAR_PLAZO) · ADR-005 (DIAGNOSTICO sin efecto jurídico) · ADR-006 (URIs `bddat://`) · ADR-010 (N:M documento-tarea) · ADR-017 §5 (radar de huérfanos / "Mi trabajo"). Desbloquea el generador del expediente de remisión (#573). Fuentes afectadas: `app/models/tipos_documentos.py`, `app/models/documentos.py`, `docs/referencia/TIPOS_DOCUMENTOS_CATALOGO.md`.

---

## Contexto

¿Qué documentos forman el **EXPEDIENTE** (con mayúsculas) — el conjunto que se remite al juzgado o por ENI cuando lo piden? Es la pregunta que define el subsistema documental, y hasta ahora la pertenencia era implícita.

Surgió al diseñar dos piezas que la necesitan:

1. El **radar de documentos huérfanos** (el administrativo sube documentos al pool; el técnico los encaja) — sin una regla de pertenencia, "huérfano" no significa nada.
2. El **generador del expediente de remisión** (#573) — sin saber qué entra, no se puede montar el foliado + índice.

La norma da el criterio. **Art. 70 LPACAP (Ley 39/2015):**

- **70.1** — el expediente es "el conjunto ordenado de documentos y actuaciones que sirven de **antecedente y fundamento** a la resolución, así como las **diligencias** encaminadas a ejecutarla".
- **70.2** — se forma por agregación ordenada de "documentos, pruebas, dictámenes, informes, acuerdos, notificaciones y demás diligencias", con **índice numerado** y **copia certificada de la resolución**.
- **70.4** — **no** forma parte la información de **carácter auxiliar o de apoyo** (notas, borradores, comunicaciones e informes internos) ni los **juicios de valor** de la Administración, **salvo** informes preceptivos y facultativos solicitados.

Se evaluó usar `fecha_administrativa` como discriminador y **se descartó** (ver Alternativa A): el campo está sobrecargado y excluiría documentos que sí son expediente.

---

## Decisión

### 1. Dos requisitos: vínculo a tarea **y** tipo que integra expediente

Un documento forma parte del EXPEDIENTE **si y solo si**:

1. **Está vinculado a una tarea** — rol `CONSUMIDO` o `PRODUCIDO`, vía `DocumentoTarea` (ADR-010). Requisito **general y necesario**: un documento solo es "antecedente y fundamento" (70.1) si alguna tarea lo usa o lo genera. **Sin vínculo no hay pertenencia.**
2. **Su `TipoDocumento` integra expediente** — afina **entre los vinculados**: retira lo que el 70.4 excluye (juicios de valor / auxiliar interno).

El vínculo es necesario pero **no suficiente**: hay un caso vinculado que no es expediente (el DIAGNOSTICO, §3). La relación es asimétrica — fallar el requisito 1 basta para quedar fuera; el requisito 2 solo descuenta entre los que ya pasaron el 1.

### 2. Huérfano = documento del pool sin vínculo a tarea

- Un **fichero** en el pool sin vínculo a ninguna tarea **no es expediente**. Es un **huérfano**: queda pendiente de la decisión del técnico — **enlazarlo** (entra) o **borrarlo** (no era expediente).
- El borrado es **decisión del técnico, nunca automático**; la bitácora lo registra. El radar que se lo presenta es trabajo aparte (ADR-017 §5, "Mi trabajo" del técnico) — candidato concreto al disparador del hub propio del TRAMITADOR que ADR-017 "Deuda conocida" (caso 3) deja condicionado. Ver **#630** (anotado 2026-07-14).
- Los registros internos `bddat://` (diagnósticos, certificados) **nacen vinculados por construcción** (producidos por una tarea) → **nunca son huérfanos**. El huérfano es siempre un fichero.

### 3. `integra_expediente` es propiedad del TIPO, no del documento ni de la fecha

- Flag nuevo: `integra_expediente BOOLEAN NOT NULL DEFAULT true` en `tipos_documentos`.
- **Único `false` hoy: `DIAGNOSTICO`** — juicio de valor del instructor (favorable/condicionado/desfavorable, ADR-005), excluido por el 70.4. Está **vinculado** (producido de ANALIZAR) y permanece en el pool porque ELABORAR lo consume, pero **no viaja** al expediente de remisión.
- La **excepción del 70.4** (informes preceptivos y facultativos solicitados) **entra**: `INFORME_114_RD1955`, `INFORME_COMPATIBILIDAD_AMBIENTAL`, `DOC_DICTAMEN_AMBIENTAL`, `DOC_INFORME_VINCULANTE`, etc., son `integra_expediente = true`. La ley misma separa el juicio de valor interno (fuera) del informe solicitado a otro órgano (dentro).

### 4. `fecha_administrativa` no decide pertenencia

Queda para lo suyo: **plazos y efectos**. No sirve como criterio de pertenencia porque está **sobrecargada** con tres NULL legítimos (documento.py): pendiente de triaje, sin efecto jurídico propio, y registro interno `bddat://` (forzado a NULL por el validador). Solo el segundo equivale a "no es expediente". La corrección de esa sobrecarga en los certificados se trata en su propio issue (ver Consecuencias).

### 5. El expediente de remisión es una consulta

De 1–4 se deduce una operación: `documentos_del_expediente(expediente_id)` = documentos con **vínculo a tarea** y **`tipo.integra_expediente`**. Sobre ella se construye el foliado + índice numerado + copia certificada de la resolución (70.2/70.3) — issue #573.

---

## Por qué

- **Fiel al art. 70**: la pertenencia se decide por la **naturaleza** del documento (antecedente/fundamento vs auxiliar/juicio de valor), que es propiedad del **tipo** — no por la fecha ni por el mecanismo de almacenamiento.
- **Da sentido operativo al radar de huérfanos**: cada huérfano es una decisión binaria "entra/sale", no un montón de pendientes.
- **Desbloquea la generación automática** del expediente de remisión como consulta.
- **Desacopla** la pertenencia tanto de `fecha_administrativa` como del esquema `bddat://`: el huérfano con fecha NULL entra en cuanto se enlaza; el DIAGNOSTICO no entra aunque esté enlazado.

---

## Cómo implementar

Resumen; detalle y checklist en **#572**.

1. **Migración**: `integra_expediente BOOLEAN NOT NULL DEFAULT true` en `tipos_documentos`.
2. **Seed**: `DIAGNOSTICO = false`; resto `true`.
3. **Consulta** `documentos_del_expediente(expediente_id)`: join `DocumentoTarea` (existencia de vínculo) + `TipoDocumento.integra_expediente`.
4. **Tests**: incluye/excluye DIAGNOSTICO; huérfano = sin vínculo; certificado interno = dentro.

---

## Consecuencias

- **Corrección de certificados (issue aparte):** al dejar de usar `fecha_administrativa` como señal de pertenencia se hace visible una inconsistencia previa — el validador fuerza `fecha_administrativa = NULL` para todo `bddat://`, y `crear_cert` guarda la fecha relevante (vencimiento/generación) en `Certificado.datos`/`generado_en` en vez de en la columna, mientras el catálogo afirma que la llevan. Hay que corregir la implementación (quitar el acoplamiento del validador; que `crear_cert` asigne `fecha_administrativa`).
- **`TIPOS_DOCUMENTOS_CATALOGO.md`** gana una columna conceptual: `integra_expediente` por tipo (DIAGNOSTICO el único `false`).
- **Sin impacto retroactivo**: la pertenencia se computa por consulta; no reescribe documentos existentes.

---

## Alternativas descartadas

### A. `fecha_administrativa NOT NULL` como criterio de pertenencia

Descartada. El campo está sobrecargado con tres semánticas (pendiente de triaje, sin efecto jurídico, registro `bddat://` forzado a NULL) y solo una equivale a "no es expediente". Usarlo **excluiría los certificados internos** (`CERT_FIN_INSTRUCCION`, `CERT_PLAZO_CUMPLIDO`, `CERT_FIN_IP_CONSULTAS`), que **son** expediente (diligencias de los arts. 82 y 22 LPACAP). El criterio confundiría el **mecanismo de almacenamiento** con la **naturaleza jurídica**.

### B. `origen` (INTERNO/EXTERNO) como criterio

Descartada. Ambos orígenes pueden ser expediente: `RESOLUCION` es interno y entra; `DIAGNOSTICO` es interno y no. El origen no discrimina pertenencia.

### C. Flag de triaje explícito para definir "huérfano"

Descartada por innecesaria. Huérfano = simplemente **sin vínculo a tarea** (estado derivado, no almacenado). No hace falta un campo: se deduce de la ausencia de `DocumentoTarea`.
