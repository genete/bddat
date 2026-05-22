# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> La hoja de ruta es la propuesta de orden para las próximas sesiones — el detalle y
> el porqué de cada decisión está en `docs/historial/REVISION_VALIDEZ_ISSUES_MAYO_2026.md`.

---

**Último cerrado:** #283 — completar la capa ES de ESFTT: `ESTRUCTURA_ESF.md` v2.2 + `ESTRUCTURA_ESF.json` v2.2 (mapeo tipo_solicitud × tipo_expediente → secuencia de fases con leyenda 4 símbolos ✅⚠️🔀🚫, principio S-dominante); CONSULTAS marcado como 🔀 en todos los procedimientos; DESISTIMIENTO/RENUNCIA/INTERESADO incorporan `ANALISIS_SOLICITUD` para activar `CERT_FIN_INSTRUCCION`; renumeración RD 88/2026 (art. 136→137, 137→138) aplicada en FTT.json/md, NORMATIVA_MAPA y DISEÑO_FECHAS_PLAZOS.

**Hallazgo posterior — auditoría exhaustiva de migraciones (22 mayo 2026):** 1 bug crítico (#448, seed plazos RESOLUCION nunca insertó), 1 deuda menor (#449, GRANT olvidado en `organismos_expediente`), 2 seeds pendientes (#450 CIERRE, #451 catálogo normas). Informe en `docs_prueba/temp/AUDITORIA_MIGRACIONES_2026-05-22.md`. **Acción inmediata aplicable antes de cualquier issue:** `flask db upgrade` para llevar la BD local de `403_resolucion` a la HEAD `405_catalogo_requerimientos` (aplica las migraciones de #404 y #405 ya committed).

**Actuales:** —

**Próximo:** a confirmar — propuesta: **#449** (fix GRANT, ~5 min, deuda menor independiente) como warm-up antes de **#448** (HOTFIX crítico, requiere rediseño del seed de plazos).

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
16. ~~**#283** — capa ES de ESFTT: `ESTRUCTURA_ESF` (.md v2.2 + .json) + renumeración RD 88/2026~~ ✓
17. **#449** — fix `GRANT SELECT` olvidado en `organismos_expediente` (deuda menor M2, ~5 min, totalmente independiente) — *de la auditoría 22/05*
18. **#448** — HOTFIX seed `catalogo_plazos` RESOLUCION (crítico, bloqueante para motor de plazos): rediseño con `condiciones_plazo` por `tipo_solicitud` + nueva migración + sincronizar `DISEÑO_FECHAS_PLAZOS.md §5.2` — *de la auditoría 22/05*
19. **#247** — cerrar las fases CONSULTAS y ANALISIS_TECNICO con reglas del motor (lo ya implementado en #391 cubre el modelo; queda la lógica de cierre); reescribir cuerpo antes de planificar
20. **#451** — ampliar catálogo `normas` (LSE, LPACAP, DL 2/2018, DL 26/2021, RD 1183/2020, RD 244/2019, RD 88/2026) — prerrequisito de #323 — *de la auditoría 22/05*
21. **#323** — modo global del motor + tabla `configuracion_sistema`
22. **#324** — mecanismo de escape con bitácora (tras #323; reescribir cuerpo: enum CREAR|BORRAR, no INICIAR|FINALIZAR)
23. **#450** — seed procedimiento CIERRE: fase `CONSULTA_OPERADOR_SISTEMA` + trámites `SOLICITUD_INFORME_OPERADOR` / `RECEPCION_INFORME_OPERADOR` + plazo (art. 137 RD 1955/2000 mod. RD 88/2026) — *de la auditoría 22/05*
24. **#416** — motor de plazos para TABLON_AYUNTAMIENTOS: fecha administrativa y cierre retroactivo de ESPERAR_PLAZO (edge case del servicio de plazos)

### Bloque 5 — Análisis heurístico de PDF

25. **#304** — script de detección del tipo de solicitud
26. **#305** — script de detección del tipo de expediente
27. **#306** — helper de cálculo de tasa y extracción de presupuesto (tras #304)

### Bloque 6 — Issues con rediseño previo necesario

28. **#410** — compatibilidad de tipos de solicitud como reglas del motor
29. **#192** — requisitos documentales por procedimiento (rediseñar: anclar a CREAR fase siguiente, sin tabla `procedimientos`)
30. **#174** — permisos blandos con traza en bitácora (rediseñar: permiso blando + bitácora, no permiso duro por expediente)

### Backlog M3 sin posición en la ruta

Troceo de #248 fuera del recorrido priorizado: **#407** (campo `siglas_escritos`),
**#408** (checklist documental — posible post-producción), **#409** (regla de tasas;
tras #408).
