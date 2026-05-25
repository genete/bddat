# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> La hoja de ruta es la propuesta de orden para las próximas sesiones — el detalle y
> el porqué de cada decisión está en `docs/historial/REVISION_VALIDEZ_ISSUES_MAYO_2026.md`.

---

**Último cerrado:** #1 (PR #481) — tabla `bitacora`, modelo `Bitacora`, servicio `registrar()`; migración `001_bitacora`; 5 tests.

**Actuales:** —

**Próximo:** **#324** — mecanismo de escape del motor (backend puro): `puede_escapar` en `EvaluacionResult`, parámetro `bypass+justificacion` en endpoints, registro en `bitacora`; sin frontend; diseño completado en sesión 2026-05-25 (ver cuerpo en GitHub).

**Plan de trabajo CONSULTAS (sesión 2026-05-24):** análisis completo de #247 en `docs/historial/ANALISIS_CONSULTAS_ORGANISMOS_2026-05-24.md`. Orden acordado:
1. ~~**#454** — auditoría 345 vs 370: verificar duplicados en `tramites_tareas` antes de tocar cualquier trámite CONSULTA_*.~~ ✓
2. ~~**#247** — núcleo: API CRUD `organismos_expediente` + #458 + #459 en un único PR (decisión sesión 2026-05-24: #458 y #459 absorbidos, no PRs propios).~~ ✓
3. ~~**#461** — endpoint `GET /api/entidades/consultables`: desbloquea la UI #396.~~ ✓
4. ~~**#456** — `tramites_organismos` + ADR-011.~~ ✓
5. ~~**#457** — CB traslados (titular y organismo) tras #456.~~ ✓ ~~**#460** (variables motor CONSULTAS, tras #458)~~ ✓ ~~**#462** (acción en bloque «Enviar consultas»)~~ ✓ Resto: #463 (seed plazos CONSULTAS); #464 (seed demo organismos, M4). Independiente: #455 (variables motor ANALISIS_SOLICITUD, tras #442).

---

## Hoja de ruta — orden propuesto para próximas sesiones

> Una sesión limpia por ítem. Las dependencias se indican con «(tras #X)».

### Bloque 1 — Correcciones M2 inmediatas

1. ~~**#300** — dirección de notificación del titular en escritos~~ ✓
2. ~~**#366** — renombrar AUDIENCIA → COMUNICACION_AUDIENCIA (corrección de diseño #346)~~ ✓

### Bloque 2 — Catálogo y documentos internos (fundacional)

4. ~~**#377** — seed de tipos_documentos del catálogo ESFTT~~ ✓
5. ~~**#420** — modelo N:M documento↔tarea: tabla multiusos con rol (ADR-010; sustituye a #380 y #376)~~ ✓
6. ~~**#418** — tabla `notificaciones`: documento vitaminado para NOTIFICAR (tras #420; sustituye a #378; ver ADR-008)~~ ✓
7. ~~**#419** — invariante ANALIZAR: bloquear cierre si diagnóstico desfavorable no consumido (tras #418)~~ ✓
8. ~~**#365** — implementar URI `bddat://` y helper `resolver_url()` (ADR-006)~~ ✓
9. ~~**#362** — certificado de plazo cumplido (tras #365; absorbe la limpieza de #357)~~ ✓

### Bloque 3 — Modelo de interesados y Context Builders de escritos

9. ~~**#374** — tabla de interesados del expediente y trámite REGISTRO_INTERESADOS~~ ✓
10. ~~**#402** — CB `ContextoNotificacionOrganismo` (notificación a organismo consultado)~~ ✓
11. ~~**#403** — CB `ContextoResolucion` (escrito de resolución)~~ ✓
12. ~~**#404** — CB `ContextoInformacionPublica` (anuncio de información pública)~~ ✓
13. ~~**#405** — tablas `catalogo_requerimientos` y `requerimientos_tarea`~~ ✓
14. ~~**#406** — CB `ContextoSubsanacion` (requerimiento de subsanación; tras #405)~~ ✓

### Bloque 4 — Motor de reglas y plazos

15. ~~**#417** — limpiar referencias a tareas obsoletas v6.0 en `seed_demo.py` y `GUIA_GENERAL.md` (deuda técnica pequeña; independiente)~~ ✓
16. ~~**#283** — capa ES de ESFTT: `ESTRUCTURA_ESF` (.md v2.2 + .json) + arts. 137-138 RD 88/2026~~ ✓
17. ~~**#449** — fix `GRANT SELECT` olvidado en `organismos_expediente` (deuda menor M2, ~5 min, totalmente independiente) — *de la auditoría 22/05*~~ ✓
18. ~~**#448** — HOTFIX seed `catalogo_plazos` RESOLUCION (crítico, bloqueante para motor de plazos): rediseño con `condiciones_plazo` por `tipo_solicitud` + nueva migración + sincronizar `DISEÑO_FECHAS_PLAZOS.md §5.2` — *de la auditoría 22/05*~~ ✓
19. ~~**#454** — auditoría migraciones 345 vs 370 en `tramites_tareas` (prerequisito crítico de #247)~~ ✓
20. ~~**#247** — API CRUD `organismos_expediente` + automatismos #458 + #459 (un único PR; cierra los tres)~~ ✓
21. ~~**#461** — endpoint `GET /api/entidades/consultables` (desbloquea #396)~~ ✓
22. ~~**#456** — `tramites_organismos` + `condicionados_doc_id` + `CONDICIONADO_OFICIO` + criterios completitud CONSULTAS (ADR-011)~~ ✓ → ~~**#457** CB traslados (tras #456)~~ ✓
23. ~~**#460** — variables motor cierre CONSULTAS: `organismos_todos_terminados`, `organismo_supera_iteraciones` (tras #458)~~ ✓
24. ~~**#462** — acción en bloque «Enviar consultas» (tras #247)~~ ✓
25. ~~**#463** — seed `catalogo_plazos` para CONSULTAS (independiente, M3)~~ ✓
26. **#475** — señalización de `CONSULTA_TRASLADO_TITULAR` vencido en organismo (M3; requiere UI #396).
27. ~~**#455** — variables motor cierre `ANALISIS_SOLICITUD` (independiente de CONSULTAS; tras #442).~~ ✓
27. ~~**#451** — ampliar catálogo `normas` (LSE, LPACAP, DL 2/2018, DL 26/2021, RD 1183/2020, RD 244/2019, RD 88/2026) — prerrequisito de #323 — *de la auditoría 22/05*~~ ✓
28. ~~**#323** — modo global del motor + tabla `configuracion_sistema`~~ ✓
28b. ~~**#1** — cuaderno de bitácora agnóstico: tabla `bitacora`, modelo, servicio `registrar()` (prerequisito de #324, #174, #435, #436; movido de M5 a M3 en sesión 2026-05-25)~~ ✓
29. **#324** — mecanismo de escape del motor (backend puro): `puede_escapar` en `EvaluacionResult`, parámetro `bypass+justificacion` en endpoints, registro en `bitacora`; sin frontend (coordinado aparte); tras #1
30. **#450** — seed procedimiento CIERRE: fase `CONSULTA_OPERADOR_SISTEMA` + trámites `SOLICITUD_INFORME_OPERADOR` / `RECEPCION_INFORME_OPERADOR` + plazo (art. 137 RD 1955/2000 mod. RD 88/2026) — *de la auditoría 22/05*
31. **#416** — motor de plazos para TABLON_AYUNTAMIENTOS: fecha administrativa y cierre retroactivo de ESPERAR_PLAZO (edge case del servicio de plazos)

### Bloque 5 — Análisis heurístico de PDF

32. **#304** — script de detección del tipo de solicitud
33. **#305** — script de detección del tipo de expediente
34. **#306** — helper de cálculo de tasa y extracción de presupuesto (tras #304)

### Bloque 6 — Issues con rediseño previo necesario

35. **#410** — compatibilidad de tipos de solicitud como reglas del motor
36. **#192** — requisitos documentales por procedimiento (rediseñar: anclar a CREAR fase siguiente, sin tabla `procedimientos`)
37. **#174** — permisos blandos con traza en bitácora (rediseñar: permiso blando + bitácora, no permiso duro por expediente)

### Backlog M3 sin posición en la ruta

Troceo de #248 fuera del recorrido priorizado: **#407** (campo `siglas_escritos`),
**#408** (checklist documental — posible post-producción), **#409** (regla de tasas;
tras #408).

### Backlog M4 — Pre-producción

- **#464** — ampliar `seed_demo` con registros reales en `organismos_expediente` (tras #247).
