# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> La hoja de ruta es la propuesta de orden para las próximas sesiones — el detalle y
> el porqué de cada decisión está en `docs/historial/REVISION_VALIDEZ_ISSUES_MAYO_2026.md`.

---

**Último cerrado:** #420 — modelo N:M documento↔tarea: tabla multiusos `documentos_tarea` con campo `rol`, eliminación de las FK `documento_usado_id`/`documento_producido_id` de `tareas` (ADR-010).

**Actuales:** —

**Próximo:** #418.

---

## Hoja de ruta — orden propuesto para próximas sesiones

> Una sesión limpia por ítem. Las dependencias se indican con «(tras #X)».

### Bloque 1 — Correcciones M2 inmediatas

1. ~~**#300** — dirección de notificación del titular en escritos~~ ✓
2. ~~**#366** — renombrar AUDIENCIA → COMUNICACION_AUDIENCIA (corrección de diseño #346)~~ ✓

### Bloque 2 — Catálogo y documentos internos (fundacional)

4. ~~**#377** — seed de tipos_documentos del catálogo ESFTT~~ ✓
5. ~~**#420** — modelo N:M documento↔tarea: tabla multiusos con rol (ADR-010; sustituye a #380 y #376)~~ ✓
6. **#418** — tabla `notificaciones`: documento vitaminado para NOTIFICAR (tras #420; sustituye a #378; ver ADR-008)
7. **#419** — invariante ANALIZAR: bloquear cierre si diagnóstico desfavorable no consumido (tras #418)
8. **#365** — implementar URI `bddat://` y helper `resolver_url()` (ADR-006)
9. **#362** — certificado de plazo cumplido (tras #365; absorbe la limpieza de #357)

### Bloque 3 — Modelo de interesados y Context Builders de escritos

9. **#374** — tabla de interesados del expediente y trámite REGISTRO_INTERESADOS
10. **#402** — CB `ContextoNotificacionOrganismo` (notificación a organismo consultado)
11. **#403** — CB `ContextoResolucion` (escrito de resolución)
12. **#404** — CB `ContextoInformacionPublica` (anuncio de información pública)
13. **#405** — tablas `catalogo_requerimientos` y `requerimientos_tarea`
14. **#406** — CB `ContextoSubsanacion` (requerimiento de subsanación; tras #405)

### Bloque 4 — Motor de reglas

15. **#323** — modo global del motor + tabla configuracion_sistema
16. **#324** — mecanismo de escape con bitácora (tras #323)

### Bloque 5 — Análisis heurístico de PDF

17. **#304** — script de detección del tipo de solicitud
18. **#305** — script de detección del tipo de expediente
19. **#306** — helper de cálculo de tasa y extracción de presupuesto (tras #304)

### Bloque 6 — Issues con rediseño previo necesario

20. **#410** — compatibilidad de tipos de solicitud como reglas del motor
21. **#192** — requisitos documentales por procedimiento
22. **#174** — permisos blandos con traza en bitácora

### Backlog M3 sin posición en la ruta

Troceo de #248 fuera del recorrido priorizado: **#407** (campo `siglas_escritos`),
**#408** (checklist documental — posible post-producción), **#409** (regla de tasas;
tras #408).
