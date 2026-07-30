# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #714 (sesión 2026-07-30, reversión del diagnóstico). PR #721. El detalle está en el issue y en el PR; aquí queda lo que gobierna lo que venga. Dos reglas de método: (1) **la puerta cerrada es la excepción** — se reserva a cuando el acto ya salió fuera y no se puede deshacer (notificado, LPACAP); en lo demás basta con obligar a pararse y justificar, que ya frena al técnico y deja rastro en bitácora; (2) cuando dos reglas dependen del mismo criterio —aquí la vigencia de un diagnóstico, que leen el cierre de fase (#711) y la reversión (#714)— deben leerlo del **mismo helper**, no reimplementarlo cada una. Queda un supuesto explícito: «posterior» se mide por `Tarea.id` porque las tareas se crean siguiendo `tramites_tareas.orden`, cosa que hoy nada garantiza (#719 es la salida). Revisar la coherencia del conjunto destapó cinco issues: #720, #722, #723, #724 y #725. En firme: el peldaño 3 de ADR-033 §5 sigue cerrado para el `CONSUMIDO` real, porque ahí hay una acción concreta a mano y el antiborrado obliga igualmente a pasar por ella.

**Próximo:** Cabeza de cola (2026-07-30): **#182** — códigos de clasificación embebidos en PDFs internos firmados. Se promueve por su prerequisito **R10**, que es una incógnita externa y no de código: ¿sobreviven las custom properties al pipeline `.docx` → portafirmas → PDF? Si los tokens **no** sobreviven, #182 se cae y hay que **redefinir** los issues que cuelgan de él, empezando por #717 (consumo real del diagnóstico) — de ahí que despejarlo pronto evite planificar sobre una base que puede no existir. #717 sigue esperando a #182 y debe implementarse como **dato, no como regla**, o mata la regla de #711. Después, los issues salidos del análisis de #714, en este orden: **#722** (el borrado del árbol no tiene guardia viva: sin reglas `BORRAR`, `_check_borrar` huérfano en `api_bc` y cascade que se lleva el vínculo del diagnóstico y la fila de `Notificacion` — es la vía alternativa que deja sin efecto lo cerrado en #714), **#720** (una fase cerrada no está sellada; por la vía de «reabrir fase como acto propio» absorbe #716), **#715** (los tests de `invariantes_esftt` mockean `db`: el SQL nunca se ejecuta, y los tres anteriores tocan ese módulo), **#723** (revisión de invariantes: sin vía de escape, fuera del modo global y con motivos que no dicen la verdad) y **#725** (reparto de creación y orden de ESFTT entre dato y motor: la tabla define el universo y su orden, el motor recorta por circunstancias legales; condiciona #719 y elimina `TRAMITES_CADENA_SUBSANACION`). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco: #724 (fricción simétrica: desdecirse de lo ya exigido al titular debe justificarse), #719 (orden canónico de tareas — esperar a #725 si se quiere hacer de una vez), #712 (mejora de `NotificarEditor`: vínculo del justificante en dos actos + cotejo de canal), #444/#555, #630. #698 (nombre "ANY") aplazado: es poblado puro de catálogo (`tipos_tramites.nombre_en_plantilla` vacío en 31/31, `tipos_solicitudes` de AT-2004 con valor incorrecto), sin código de por medio. #572 (ADR-027) sigue ortogonal, diferido por Carlos. Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase es unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
