# PRE-ADR — Workbench, inspector universal y listados list-detail

> **Estado:** Cerrado — convertido en **ADR-022** (#533) y **ADR-023** (#534) el 2026-06-07. Se conserva como memoria del razonamiento, la validación numérica y los cálculos de espacio.
> **Fecha:** 2026-06-07.
> **Deriva en:** dos ADRs previstos — **ADR-022** (sistema visual base) y **ADR-023** (patrón list-detail + inspector universal). Y sus issues.
> **Origen:** revisión de altura de la vista workbench (sesión 2026-06-07). Confirma/matiza afirmaciones del usuario contra código, ADRs e issues.
> **Convención:** `[VERIFICADO]` = comprobado en código/ADR/issue. `[PROPUESTO]` = decisión a confirmar. `[ABIERTO]` = pendiente de cierre en esta sesión.

---

## 1. Problema

La app tiene **dos paradigmas de interacción conviviendo**:

- **Árbol del expediente** (ADR-016): list-detail moderno. Seleccionas un nodo en `main` → el `inspector` muestra su detalle sin cerrar el árbol. Ya construido.
- **Listados v2**: navegación web clásica. Botón "Ver" por fila → carga página de detalle → botón "volver". Legado.

La coexistencia genera la "maraña de accesos cruzados" (necesidad de botones de retorno en cada vista de detalle). Además, la base visual no está unificada.

### Hallazgos verificados

| # | Hallazgo | Evidencia |
|---|---|---|
| H1 | **Tres escalas tipográficas** conviven sin unificar | `body` 16px (`v2-theme.css:92`), tablas 0.875rem/14px (`v2-components.css:120,137`), shell+inspector 13px hardcodeado (`app-shell.css:18,451`) |
| H2 | El "bajar el rem" es **principio, no decisión cerrada** | `ANALISIS_CRITICO §4.1` ("densidad 13-14px"). No hay ADR ni implementación global; el `body` sigue a 16px |
| H3 | **Botón "Ver" por fila** navega a página completa | `v2-scroll-infinito.js:208-216` (`window.location.href = detailUrl(id)`) |
| H4 | **Dos sistemas de tabla** distintos | `data-table` (DIV+grid, `v2-data-table.css`) y `expedientes-table` (HTML, `v2-components.css:99`). La base real usa el segundo |
| H5 | **Truncados/recortes ad-hoc** por implementación | `nth-child` por tabla, `plantillas-table td:nth-child(2) max-width:180px`, media queries que ocultan columnas a mano |
| H6 | **No todos los listados** usan scroll infinito | Plantillas y Usuarios pendientes → **#281 (OPEN)** |
| H7 | Recorte lateral **~95%** (no 90%) por homogeneidad con bloques | `--content-padding: max(1rem, 2.5vw)` (`v2-theme.css:14`); motivo #202 (`v2-components.css:39`). #94 nació "100% ancho" |
| H8 | **Inspector resizable** atado a la isla del árbol, no al shell | `ADR-016 §14` (`react-resizable-panels`). No hay issue ni mecanismo de shell |

---

## 2. Decisión propuesta — dos bloques

### D1 — Sistema visual base `[PROPUESTO]` → ADR-022

Prerrequisito de D2. No es cosmética: sin escala densa y tabla única, el list-detail asfixia el `main`.

1. **Escala tipográfica única y densa.** Un solo conjunto de tamaños (13-14px base) que mata las tres escalas de H1. `[ABIERTO]` cómo: ver §5.
2. **Tokens de color sin fugas.** Consolidar los hardcodeos del shell (`#ebebeb`, `#888`…) sobre las variables de `v2-theme.css`.
3. **Componente de tabla único** con overrides heredables. Un mecanismo general de columnas + truncado (mín/máx, elipsis, prioridad de ocultación responsive declarativa) y particularizaciones que **heredan** el general en vez de reescribirlo. Mata H4 y H5.
4. **Retirar el recorte ~95% (H7)** del listado cuando va en `main`: el recorte tenía sentido para bloques redondeados aislados, no para un maestro que ya está acotado por sidebar + inspector.

### D2 — List-detail con inspector universal `[PROPUESTO]` → ADR-023

1. **Selección, no navegación.** Click en fila → fila seleccionada + `inspector` muestra el detalle en "modo reacción". El listado **no se cierra**. Desaparecen la columna "Acciones/Ver" (H3) y los botones de retorno. Generaliza a los listados lo que ADR-016 §3/§5 ya hace en el árbol.
2. **Las vistas de detalle actuales se reaprovechan**, adaptadas al layout del inspector. No se tiran.
3. **Todo el detalle vive en el inspector** `[PROPUESTO, confirmado por el usuario]`. Se descarta el split-en-main (genera scrolls verticales antipáticos). El inspector se **adapta** a lo que cada detalle necesita.
4. **Inspector redimensionable y negociable a nivel de SHELL** (no de isla React). Sube de ADR-016 §14 a mecanismo del shell. Ver §3 y §4.
5. **Acciones del elemento** (las que hoy se replican por fila) viven en el detalle del inspector.

---

## 3. Modelo de negociación de espacio `[PROPUESTO]`

Modelo del usuario: *cada vista define un "mínimo aceptable"; el inspector intenta su tamaño preferido o cede si el `main` exige su propio mínimo.* Es el modelo de los IDEs (VS Code: paneles con `min-width` + colapso por prioridad). Es correcto y estandarizable.

### Sobre Bootstrap (criterio técnico pedido)

**Bootstrap no gobierna el layout del shell.** El shell es **CSS Grid propio** (`app-shell.css`, `grid-template-areas`); Bootstrap solo aporta componentes (botones, cards, dropdowns, toasts) y su grid `.row/.col` **no se usa** aquí. Por tanto no hay que "sobreseer" a Bootstrap en el layout: ya mandamos nosotros. La negociación se implementa con `minmax()` nativo de Grid:

```
grid-template-columns:
   [sidebar]   auto                              /* 208 / 56 / 0 */
   [main]      minmax(var(--main-min), 1fr)      /* mínimo lo declara la vista */
   [inspector] minmax(0, var(--inspector-width)) /* preferido del usuario, persistido */
```

- `--main-min`: lo declara la **vista de listado** (su versión maestra-reducida).
- `--inspector-width`: gobernado por **drag del splitter + `localStorage`**, acotado por el `--inspector-min` que declara la **vista de detalle** montada (su "mínimo aceptable").
- Si los mínimos no caben todos, el min duro de `main` gana y el inspector cede.

### Regla de prioridad propuesta `[recomendada, pend. OK]`

1. El `main_min` **siempre** se respeta. Se calcula sobre el **maestro reducido** (sin las columnas que migran al detalle) — Q2.
2. El **sidebar colapsa** automáticamente (208→56→0) **antes** de que el inspector ceda.
3. El inspector toma el resto, acotado: nunca por debajo de su `inspector_min` (ruptura) **ni por encima de su `inspector_objetivo`** (ancho donde el detalle se ve completo y cómodo). Por encima del objetivo no crece: no devora espacio que el detalle no aprovecha — Q4.
4. Si ni así cabe (pantalla muy pequeña), el inspector se cierra por toggle y el detalle queda accesible bajo demanda (en móvil ya se oculta, `app-shell.css:742`).

> **Contrato por vista:** cada listado declara `--main-min` (su maestro reducido) y cada tipo de detalle declara `[inspector_min, inspector_objetivo]`. La negociación es aritmética sobre esos cuatro números + el ancho del sidebar.

---

## 4. Validación numérica — Expedientes `[VERIFICADO sobre medidas reales]`

Pedida por el usuario: validar el patrón con el listado **más rico** (seguimiento, 5 pistas) a nivel de cálculos, no de implementación.

**Medidas base:** sidebar 208/56px (`app-shell.css:23-26`); seguimiento = **53rem** de columnas fijas (`custom.css:311`), desglose `AT 5.5 + SOL 9 + FECHA 5.25 + 5×pista(5.75)=28.75 + ACC 4.5`. En list-detail la columna **ACC desaparece** → seguimiento = **48.5rem**.

Conversión de 48.5rem (seguimiento sin columna acciones) según rem base:

| rem base | Seguimiento maestro completo |
|---|---|
| 16px (actual) | 776px |
| 14px | 679px |
| 13px | 631px |

Maestro **reducido** (AT+SOL+FECHA+semáforo agregado ≈ 23.75rem): 380px @16, 333px @14.

### Reparto en 1920×1080 (pantalla de referencia del usuario)

Sidebar colapsado (56). Disponible main+inspector = 1864px.

| Inspector | Main resultante | ¿Cabe seguimiento completo @16 (776)? |
|---|---|---|
| 380 (actual) | 1484 | Sí, sobran 708 |
| 600 (máx ADR-016) | 1264 | Sí, sobran 488 |
| **900 (deseo del usuario)** | **964** | **Sí, sobran 188** |
| 1100 | 764 | No (falta 12) → negociación |

**Resultado:** en 1080p, el inspector puede tomar **900px** y el listado de seguimiento **completo** sigue cabiendo con ~188px de holgura, **incluso sin bajar el rem**. Bajar el rem da margen extra (~100px) y permite inspectores aún mayores. El deseo del usuario es viable con holgura.

### Caso peor — portátil 1366×768

| Configuración | Main | Veredicto |
|---|---|---|
| Inspector 400 (mín ficha) + sidebar 56 | 910 | Seguimiento completo cabe |
| Inspector 900 + maestro **reducido** (333) | 977 disp. → inspector OK | El usuario tiene su inspector grande |
| Inspector 900 + maestro **completo** exigido | 410 < 776 | Inspector **cede** a ~534px (negociación) |

**Conclusión global:** el patrón es holgado en 1080p. El conflicto solo aparece en ≤1366 al combinar inspector muy grande + maestro completo, y se resuelve con (a) modo maestro reducido al abrir el inspector —técnica Gmail/Outlook— y/o (b) la regla de prioridad de mínimos. El "mínimo aceptable por vista" es exactamente el parámetro que gobierna esa negociación: el modelo del usuario es correcto.

---

## 5. Cuestiones

### Cerradas (sesión 2026-06-07)

| ID | Cuestión | Decisión |
|---|---|---|
| Q2 | **Maestro reducido al abrir inspector** | **Sí, reducir columnas.** Las columnas esenciales se definen **por tipo de listado** (no hay regla genérica "las N primeras"): Expedientes/seguimiento tiene su esencial, Entidades el suyo, etc. |
| Q4 | **Rango del inspector** | Acotado por vista: **`inspector_min`** (ruptura) ≤ ancho ≤ **`inspector_objetivo`** (donde el detalle se ve completo y cómodo). No crece más allá del objetivo (no devorador). El `main_min` se mide sobre el maestro reducido (Q2) |

### Recomendadas, pendientes de tu OK

| ID | Cuestión | Recomendación |
|---|---|---|
| Q1 | **Cómo bajar el rem (D1)** | **(c) híbrido con rem global de base:** fijar `html` a 14-15px (mando maestro que unifica Bootstrap + CDN Junta + todo lo que va en rem), **pasar el shell de px a rem** para que obedezca al mando, y reservar tokens solo para excepciones tipográficas deliberadas. Descartada (b) pura: persigue cada componente y arriesga perpetuar la dualidad de escalas |
| Q3 | **Regla de prioridad** (§3) | `main_min` (sobre maestro reducido) se respeta siempre → sidebar colapsa → inspector cede hasta su `inspector_min` → como último recurso el inspector se cierra |
| Q5 | **Reconciliación ADR-016 §14** | **ADR-023 absorbe** el inspector resizable como mecanismo de shell (CSS Grid + JS ligero + `localStorage`); se deja **nota de enmienda en ADR-016 §14** apuntando a ADR-023. `react-resizable-panels` queda solo para splitters *internos* de una isla (p. ej. el split despensa del árbol), no para el inspector del shell |

---

## 6. Alternativas descartadas

- **Split horizontal en `main`** (maestro arriba / detalle abajo, Patrón A de DECISIONES_UI): descartado por el usuario — los scrolls verticales apilados son antipáticos. Todo el detalle va al inspector.
- **Mantener botón "Ver" + navegación**: es el origen de la maraña de retornos (H3).
- **Solo estética (rem + colores) sin tocar comportamiento**: insuficiente — no cura la maraña de navegación, que es estructural. La estética es prerrequisito de D2, no su alternativa.
- **react-resizable-panels para el inspector del shell**: no sirve — vive dentro de islas React; los listados Jinja no lo tienen. El redimensionado debe ser del shell.

---

## 7. Issues previstos (a crear al cierre)

- **ADR-022 / Issue A — Sistema visual base:** escala tipográfica única, tokens sin fugas, componente de tabla unificado con overrides, retirada del recorte ~95%. Absorbe/cierra parte de #281.
- **ADR-023 / Issue B — List-detail + inspector universal:** selección→inspector en listados, retirada de botones "Ver", inspector redimensionable y negociable a nivel de shell, contrato `--main-min` / `--inspector-min` por vista. Reconcilia ADR-016 §14.

> Pendiente de confirmar numeración de ADR (siguientes libres tras ADR-021) y milestone de los issues.
