# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #711 (sesión 2026-07-29, invariante de cierre de fase). PR #718. La vigencia de un diagnóstico pasa a ser propiedad de la **cadena de subsanación**, no de la fase: dentro de `ANALISIS_DOCUMENTAL` + `REQUERIMIENTO_SUBSANACION` los diagnósticos son iterativos y solo cuenta el último; fuera de ella la regla de #419 queda intacta, porque los de una fase `CONSULTAS` son paralelos (uno por organismo) y ninguno supera a otro. Sin ese matiz el arreglo habría introducido un bug peor. Causa de fondo: el vínculo `CONSUMIDO` sobre un diagnóstico no lo crea ningún camino automático, así que el criterio de #419 nunca se cumplía y una fase con un desfavorable quedaba condenada a cerrarse DESFAVORABLE. El análisis destapó cuatro issues (#714, #715, #716, #717) y un hueco de diseño. Se retiran los tests de #419: mockeaban `db` y pasaban con el check roto.

**Próximo:** Cabeza de cola (2026-07-29): #714 — `revertir_diagnostico` no bloquea nunca: el peldaño 3 de ADR-033 §5 se apoya en el vínculo `CONSUMIDO` que nada crea, así que hoy se puede revertir un diagnóstico ya volcado en un requerimiento notificado y destruir la evidencia de lo comunicado al titular. Se tapa sin esperar a #182, con el criterio simétrico al de #711 (un diagnóstico superado por una vuelta posterior no es reversible). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco y salidos del análisis de #711: #715 (los tests de `invariantes_esftt` mockean `db`; el SQL nunca se ejecuta), #716 (el invariante de cierre se esquiva fuera de la primera asignación de documento). #717 (consumo real del diagnóstico) queda a la espera de #182 — y debe implementarse como **dato, no como regla**, o mata la regla de #711. #712 (mejora de `NotificarEditor`: vínculo del justificante en dos actos + cotejo de canal) sigue en cola, mismo foco. #698 (nombre "ANY") aplazado: es poblado puro de catálogo (`tipos_tramites.nombre_en_plantilla` vacío en 31/31, `tipos_solicitudes` de AT-2004 con valor incorrecto), sin código de por medio. #572 (ADR-027) sigue ortogonal, diferido por Carlos. En cola, mismo foco: #444/#555, #630. Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase es unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
