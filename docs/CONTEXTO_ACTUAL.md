# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** **#814 — Banco de documentos dummy y expediente-tipo reproducible.** [PR #828](https://github.com/genete/bddat/pull/828). Lo que no está en el issue ni en los ADRs: el método demostró rendir más de lo previsto. Recorrer un expediente completo **por el circuito real** —no simulado— destapó cinco huecos que ninguna pieza aislada revela, porque todos están en la costura entre piezas que funcionan bien por separado; dos de ellos ni siquiera aparecieron con el expediente realista, sino al sustituir las llamadas directas al servicio por los endpoints reales de ANALIZAR. Contrapartida asumida: cada hueco que se cierra invalida el expediente que lo destapó, y hay que regenerarlo. En BD de desarrollo quedan **AT-19** (vigente) y **AT-15**, conservado con su marca `[RECICLAR]` como caso real contra el que contrastar #823.

**Próximo: cerrar los cinco huecos antes de ampliar el catálogo** — volverían a aparecer en cualquier otro tipo de expediente, así que se pagan una vez. Orden propuesto:

1. **#826 + #825** (hermanos, juntos). Son los únicos que ya corrompen datos: los consumidos se acumulan en cada ANALIZAR y el plazo de admisión del art. 21.4 arranca con el documento equivocado (11 días de desfase, reproducido en AT-19). Todo expediente que se cree hoy nace con ellos.
2. **#823 — invariantes de precedencia al crear nodos.** Diseño ya decidido (los tres checks como invariante); solo falta confirmar si son puerta cerrada. Es lo que impide seguir construyendo expedientes en mal orden, así que va antes de fabricar más.
3. **#827 — conectar el generador de certificados de fase al cierre.** Lo que falta para *terminar* bien una fase, no solo para construirla. Lleva más decisiones abiertas (mapa fase → tipo de certificado), y es el ancla del guardián de reapertura que #823 deja fuera de alcance.
4. **#824 — fecha administrativa a futuro.** Borrador, sin alcance decidido. Afecta a producción pero no bloquea la construcción de expedientes; entra cuando se acote.

Después, **ampliar el catálogo de expedientes-tipo** (issue por abrir: falta decidir qué expediente y qué situación). La confianza que da un expediente-tipo alcanza solo a lo que ejercita — hoy, AAP+AAC exento sin IP ni consultas con dos vueltas dentro de plazo—, así que esa elección decide qué zona se ilumina después.

**Fuera del foco:** #607 aplazado · #572 va con el compilador de expediente para recurso/contencioso · #568 diferido (sin casos en años) · #306/#428/#304 son helpers · #743, #570 (emparejable con #755) en la cola general · #773 espera la ampliación de `Usuario` · ADR-021 y #644-648 aparcados.

**Nota de foco de fase — arrastrar a cada repaso (2026-08-07, #764):** todo `ESPERAR_PLAZO` que pueda recibir documentación de terceros exige un `ANALIZAR` posterior —propio, del trámite receptor hermano, o añadido tras él si es el último trámite de la fase—. Esta exigencia se comprueba durante el desarrollo mediante repaso de fase a fase, sin crear issues a futuro, sino sobre la marcha. Detectados y **sin issue a propósito**, por la fase en que se corrigen: en `AAU_AAUS_INTEGRADA`, `DISCREPANCIA_INF_VINC` (sin trámite receptor definido en catálogo) más `RECEPCION_DICTAMEN`, `RECEPCION_PROPUESTA_INF_VINC` y `REMISION_RESULTADO_IP_CONSULTAS`; en `FIGURA_AMBIENTAL_EXTERNA`, `SOLICITUD_FIGURA`. Estos cuatro últimos tienen receptor plausible pero no formalizado en el catálogo ESFTT. **Ojo al leer notas anteriores a #778:** hablaban de formalizarlo en `_TRAMITES_CIERRE` de `plazos.py`, lista que ya no existe — el plazo lo cierra el documento producido de su propia espera (`campo_fecha_cumplimiento`), no un trámite hermano. La exigencia del `ANALIZAR` posterior sigue en pie por lo que es: quien recibe documentación de terceros tiene que estudiarla. `SOLICITUD_INFORME_OPERADOR` está en el JSON pero sin poblar en BD (#450): al poblarlo, darle receptor con `ANALIZAR`.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
