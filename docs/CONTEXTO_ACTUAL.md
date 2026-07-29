# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #688 (sesión 2026-07-29, marco de edición del inspector — el par Guardar/Cancelar de los campos directos se unifica en la cabecera fija para todo tipo de nodo, incluida la superficie-de-trabajo; enmienda ADR-023 §5 bis, que fijaba lo contrario). PR #713. Cierra el punto abierto en #657/#658 sobre dónde vive el Guardar del pie de `NotificarEditor`. De paso corrige dos bugs del guardado inline de Notas (#677): no participaba de `hayCambios` —cerrar descartaba en silencio— y el Guardar del pie revertía las notas recién guardadas. `notas` pasa a ser accesible en ELABORAR y NOTIFICAR, donde no se pintaba.

**Próximo:** Cabeza de cola (2026-07-29): #711 — bug preexistente de #419: la invariante de cierre de fase no reconoce un diagnóstico superado por vuelta de subsanación; bloquea el foco fijo (una fase que no se puede cerrar no es "completamente tramitable"). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. #712 (mejora de `NotificarEditor`: vínculo del justificante en dos actos + cotejo de canal) queda en cola, mismo foco. #698 (nombre "ANY") aplazado: es poblado puro de catálogo (`tipos_tramites.nombre_en_plantilla` vacío en 31/31, `tipos_solicitudes` de AT-2004 con valor incorrecto), sin código de por medio. #572 (ADR-027) sigue ortogonal, diferido por Carlos. En cola, mismo foco: #444/#555, #630. Hueco de diseño sin issue: `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5). Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
