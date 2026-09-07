# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#862 — segundo expediente-tipo: `CONSULTAS_VARIOS_ESTADOS`** ([PR #866](https://github.com/genete/bddat/pull/866)). Línea aérea 66 kV en Jerez de la Frontera (AAP+AAC, exenta, sin IP) con tres organismos consultados y la foto tomada a 40 días hábiles de notificar las separatas: silencio vencido sin analizar, ciclo cerrado con condicionados y traslado al titular todavía corriendo. El escenario se construye **hacia atrás desde hoy** —el ancla es la notificación, no el alta—, que es lo que decide qué plazos han vencido. Con él se van dos cosas: el `catalogo_expedientes.csv` (la base ya sabe qué expedientes-tipo hay, por la marca `[DUMMY:<CODIGO>]` de `Solicitud.observaciones`, y el CSV solo guardaba la última ejecución) y la duplicación entre scripts, ahora en `scripts/expedientes_dummy/_comun.py`. El catálogo de la carpeta vive en su `README.md`, y los dos expedientes-tipo alimentan ya la base de tests ([PR #867](https://github.com/genete/bddat/pull/867)) — no por cobertura, que ningún test los usa todavía, sino para que `preparar_bd_test.py --recrear` falle en el acto el día que un cambio de la aplicación rompa uno de los scripts. · **#863 — la condición de `DR_NO_DUP` estaba invertida** ([PR #865](https://github.com/genete/bddat/pull/865)): se exigía cuando la solicitud incluye DUP, y es al revés — la declaración de *no* necesidad se presenta cuando no se pide. En un expediente sin DUP el requisito no salía en el checklist y el documento se quedaba en el pool sin nada a lo que casarse.

**Próximo:**

1. **El expediente-tipo del modificado de proyecto**, que es el que falta para trabajar la segunda ronda —de consultas y de información pública— y el que obliga a decidir cómo se modela: una sola fase `ANALISIS_SOLICITUD` con varios `ANALISIS_DOCUMENTAL`, o varias fases. Esa decisión es **#819** (asociar consultas e IP al conjunto documental del proyecto y sus modificados) y es **requisito previo**, no una consecuencia: sin ella no se puede escribir el escenario ni la variable que necesita **#864** — la advertencia al abrir una fase con `ANALISIS_SOLICITUD` sin cerrar, diferida por lo mismo (una variable ingenua cogería la fase cerrada del proyecto original y callaría justo en la ronda del modificado).

---

**Poda del 2026-09-07.** Todo lo que este documento arrastraba fuera de **Hecho**
y **Próximo** se trasladó a su sitio o ya estaba en él: guías, ADR-004/021/031/041/043,
`ESTRUCTURA_FTT.md`, `docs/README.md` y `scripts/expedientes_dummy/README.md`. Los motivos
de aplazamiento pasaron a comentario en su propio issue: **#450, #568, #570, #572, #607,
#755, #839** y **#644-#648**. El mapa completo de qué fue a dónde está en el mensaje del
commit de esta poda.
