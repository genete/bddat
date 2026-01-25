# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 25 de enero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

---

## Últimos Cambios

### 2026-01-25 - [PR #24: Detección de Proyectos Interprovinciales](https://github.com/genete/bddat/pull/24)

**Objetivo:** Añadir lógica al modelo Proyecto para detectar automáticamente si afecta a más de una provincia.

**Cambios principales:**
- ✅ **Propiedad `es_interprovincial`**: Booleana, detecta proyectos con municipios de 2+ provincias
- ✅ **Propiedad `provincias_afectadas`**: Lista ordenada de nombres de provincias únicas
- ✅ **Lógica**: Usa primeros 2 dígitos del código INE (PPMMM) del municipio
- ✅ **Sin migración**: Propiedades calculadas en runtime con `@property`

**Uso:**
```python
if proyecto.es_interprovincial:
    flash('⚠️ Proyecto interprovincial', 'warning')

provincias = proyecto.provincias_afectadas  # ['Almería', 'Granada']
```

**Archivos:** app/models/proyectos.py

---

### 2026-01-25 - Carga Inicial de Municipios de Andalucía

**Objetivo:** Poblar tabla `estructura.municipios` con catálogo completo de municipios andaluces basado en datos oficiales del INE.

**Cambios principales:**
- ✅ **785 municipios cargados** en `estructura.municipios` (8 provincias andaluzas)
- ✅ **Fuente oficial:** INE - Fichero 25codmun.xlsx a 1 de enero de 2025
- ✅ **COMMENT añadido** a la tabla documentando fuente, fecha y trazabilidad
- ✅ **Secuencia actualizada:** `estructura.municipios_id_seq` → 785
- ✅ **datos_estructurales.sql regenerado** con pg_dump (commit c9de403)

**Distribución por provincia:**
- Almería (04): 103 municipios | Cádiz (11): 45 municipios
- Córdoba (14): 77 municipios | Granada (18): 174 municipios  
- Huelva (21): 80 municipios | Jaén (23): 97 municipios
- Málaga (29): 103 municipios | Sevilla (41): 106 municipios

**Utilidad:**
- Códigos INE de 5 dígitos (CPRO + CMUN) para identificación única
- Detección de proyectos interprovinciales: `LEFT(codigo, 2)` extrae provincia
- Validación de datos de localización en expedientes
- Integración con sistemas externos que usen códigos INE

**Documentación:** [25codmun.xlsx](https://www.ine.es/daco/daco42/codmun/25codmun.xlsx)

---

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

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.