# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 24 de enero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

---

## Últimos Cambios

### 2026-01-24 - [PR #20: Agregar 11 Tablas Faltantes](https://github.com/genete/bddat/pull/20)

**Objetivo:** Completar la base de datos con las 11 tablas faltantes según diseño v3.0.

**Cambios principales:**
- ✅ 4 tablas maestras nuevas en schema `estructura`: municipios, tipos_resultados_fases, tipos_tareas, tipos_tramites
- ✅ 7 tablas operacionales nuevas en schema `public`: documentos, solicitudes, fases, tramites, tareas, documentos_proyecto, municipios_proyecto
- ✅ Correcciones en modelos: fases.py, tramites.py, tareas.py
- ✅ Actualizado schema.sql con 16 tablas totales

**Estado final:** 16 tablas (9 en estructura + 14 en public)

---

### 2026-01-22 - [PR #19: Arquitectura v3.0 Tipos Individuales](https://github.com/genete/bddat/pull/19)

**Objetivo:** Documentar arquitectura v3.0 con tipos de solicitudes individuales y tabla puente N:M.

**Cambios principales:**
- ✅ Documentación tabla puente `solicitudes_tipos` (N:M)
- ✅ Catálogo 17 tipos individuales de solicitudes vs 20+ tipos combinados anteriores
- ✅ Datos maestros iniciales en SQL
- ✅ Incorporación normativa: RDL 7/2025 (AAE provisional/definitiva), RADNE Andalucía, RAIPEE renovables

**Tipo:** Solo documentación (sin cambios en código)

---

### 2026-01-22 - [PR #18: Fix Email Duplicado en Usuarios](https://github.com/genete/bddat/pull/18)

**Objetivo:** Resolver error UNIQUE constraint cuando múltiples usuarios tienen email vacío.

**Cambios principales:**
- ✅ Modelo usuarios.py: Email convertido a property con setter que transforma '' → NULL
- ✅ Rutas: Captura específica de IntegrityError con feedback visual
- ✅ Templates: Validación Bootstrap con mensaje inline
- ✅ Preservación de datos en formulario cuando hay error

**Issues resueltos:** #12, #13

---

### 2026-01-21 - Mejoras UX en Módulo Expedientes

**Cambios principales:**
- ✅ Nomenclatura consistente: "Instrumento Ambiental" en lugar de "Tipo de Instalación"
- ✅ Campo Instrumento Ambiental normalizado en vista detalle (sin alert destacado)
- ✅ Flujo navegación: botón Cancelar redirige a listado en lugar de detalle
- ✅ Visualización heredado: solo muestra check verde cuando aplica

**Archivos:** nuevo.html, editar.html, detalle.html

---

### 2026-01-21 - Feature: Unificación Listado Expedientes

**Objetivo:** Vista unificada de expedientes con filtrado opcional por responsable.

**Cambios principales:**
- ✅ Ruta index() unificada con parámetro `?mis_expedientes=1`
- ✅ Estadísticas en parte superior (sin scroll)
- ✅ Cabeceras multilinea, elipsis en textos largos
- ✅ Columna Heredado simplificada (solo check verde cuando aplica)
- ✅ Redirección desde `/mis_expedientes` a `/expedientes/?mis_expedientes=1`

**Template eliminado:** dashboard/mis_expedientes.html (ya no necesario)

---

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.
