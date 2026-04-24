# Documentación BDDAT

Sistema de tramitación administrativa de expedientes de autorización de instalaciones de alta tensión en Andalucía.

**Para saber qué está vivo ahora mismo:** [CONTEXTO_ACTUAL.md](CONTEXTO_ACTUAL.md)

---

## guias/
Documentos operativos estables. Leer cuando se trabaja en ese área.

- [REGLAS_BASH.md](guias/REGLAS_BASH.md) — patrones prohibidos en Bash y workarounds
- [REGLAS_DESARROLLO.md](guias/REGLAS_DESARROLLO.md) — Git, commits, ramas, migraciones
- [GUIA_VISTAS_BOOTSTRAP.md](guias/GUIA_VISTAS_BOOTSTRAP.md) — UI, layouts, Bootstrap
- [GUIA_COMPONENTES_INTERACTIVOS.md](guias/GUIA_COMPONENTES_INTERACTIVOS.md) — JS, SelectorBusqueda, ScrollInfinito
- [GUIA_GENERAL.md](guias/GUIA_GENERAL.md) — arquitectura general y lógica de negocio
- [GUIA_ROLES.md](guias/GUIA_ROLES.md) — roles y permisos

## referencia/
Consultar cuando se trabaja ese subsistema. No cargar por defecto.

### Motor de reglas y plazos
- [DISEÑO_CONTEXT_ASSEMBLER.md](referencia/DISEÑO_CONTEXT_ASSEMBLER.md)
- [DISEÑO_FECHAS_PLAZOS.md](referencia/DISEÑO_FECHAS_PLAZOS.md)

### Subsistema documental y escritos
- [DISEÑO_SUBSISTEMA_DOCUMENTAL.md](referencia/DISEÑO_SUBSISTEMA_DOCUMENTAL.md)
- [DISEÑO_GENERACION_ESCRITOS.md](referencia/DISEÑO_GENERACION_ESCRITOS.md)
- [GUIA_CONTEXT_BUILDERS.md](referencia/GUIA_CONTEXT_BUILDERS.md)

### Procedimiento AT — fases pendientes
- [DISEÑO_ANALISIS_SOLICITUD.md](referencia/DISEÑO_ANALISIS_SOLICITUD.md)
- [DISEÑO_CONSULTAS_ORGANISMOS.md](referencia/DISEÑO_CONSULTAS_ORGANISMOS.md)

### Normativa
- [NORMATIVA_PLAZOS.md](referencia/NORMATIVA_PLAZOS.md)
- [NORMATIVA_EXCEPCIONES_AT.md](referencia/NORMATIVA_EXCEPCIONES_AT.md)
- [NORMATIVA_MAPA_PROCEDIMENTAL.md](referencia/NORMATIVA_MAPA_PROCEDIMENTAL.md)
- [NORMATIVA_LEGISLACION_AT.md](referencia/NORMATIVA_LEGISLACION_AT.md)
- [NORMATIVA_SOLICITUDES.md](referencia/NORMATIVA_SOLICITUDES.md)
- [normas/](referencia/normas/) — textos consolidados extraídos (BOE/BOJA)

### Estructura ESFTT
- [ESTRUCTURA_FTT.md](referencia/ESTRUCTURA_FTT.md) — catálogo legible
- [ESTRUCTURA_FTT.json](referencia/ESTRUCTURA_FTT.json) — fuente de verdad para código

### Visión
- [PLAN_ESTRATEGIA.md](referencia/PLAN_ESTRATEGIA.md) — 14 bloques funcionales

## decisiones/
ADRs — registro append-only de decisiones arquitectónicas no obvias desde el código.

- [ADR-001](decisiones/ADR-001-motor-agnostico.md) — Motor agnóstico de dominio
- [ADR-002](decisiones/ADR-002-esftt-sin-fechas.md) — Ningún elemento ESFTT almacena fechas

## historial/
Documentos congelados. Contexto histórico, no referencia activa.

- ANALISIS_*, DISEÑO_MOTOR_*, DISEÑO_NUMERACION_AT, PROCEDIMIENTO_*, REGLAS_ARQUITECTURA
