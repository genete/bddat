# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. La sección de estado lleva una entrada por línea.
> El detalle y el porqué de cada decisión está en `docs/historial/REVISION_VALIDEZ_ISSUES_MAYO_2026.md`.
> Los issues cerrados están en `git log` — no se duplican aquí.

---

**Último cerrado:** #475 (PR #485) — variable motor `traslado_organismo_titular_vencido` + campo `traslado_titular_vencido` en serialización de organismos; `variables={}` para evitar recursión; 10 tests sin BD real.

**Actuales:** —

**Próximo:** **#471** — vincular trámites `CONSULTA_TRASLADO_*` a `OrganismoExpediente` en `tramites_organismos`; corrige `organismo_supera_iteraciones` que devuelve False para TRASLADOs hasta que esto esté implementado.


## Hoja de ruta — orden propuesto para próximas sesiones

> Una sesión limpia por ítem. Las dependencias se indican con «(tras #X)».

### Pre-frontend — Requisitos estructurales

Estos cuatro issues deben cerrarse antes de arrancar la UI porque condicionan
el diseño del frontend o tienen código activo con huecos conocidos.

1. **#471** — vincular trámites `CONSULTA_TRASLADO_*` a `tramites_organismos`: corrige hueco activo en `organismo_supera_iteraciones` y en `_traslado_titular_vencido` (#475)
2. **#470** — certificado de cierre de fase CONSULTAS (`CERT_FIN_IP_CONSULTAS`) y reglas del motor: cierra el bloque CONSULTAS de extremo a extremo
3. **#466** — `direccion_notificacion_id` en `organismos_expediente`: cambio de schema antes de que la UI (#396) construya sobre el modelo actual
4. **#174** — permisos granulares con traza en bitácora (rediseño: permiso blando + bitácora): afecta todos los endpoints que el frontend va a consumir

### Bloque 5 — Análisis heurístico de PDF

5. **#304** — script de detección del tipo de solicitud
6. **#305** — script de detección del tipo de expediente
7. **#306** — helper de cálculo de tasa y extracción de presupuesto (tras #304)

### Bloque 6 — Issues con rediseño previo necesario

8. **#410** — compatibilidad de tipos de solicitud como reglas del motor
9. **#192** — requisitos documentales por procedimiento (rediseñar: anclar a CREAR fase siguiente, sin tabla `procedimientos`)

### Backlog M3 sin posición en la ruta

Troceo de #248 fuera del recorrido priorizado: **#407** (campo `siglas_escritos`),
**#408** (checklist documental — posible post-producción), **#409** (regla de tasas;
tras #408).

### Backlog M4 — Pre-producción

- **#464** — ampliar `seed_demo` con registros reales en `organismos_expediente` (tras #247).
