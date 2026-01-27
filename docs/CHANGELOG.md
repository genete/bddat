# CHANGELOG - BDDAT

**Repositorio:** https://github.com/genete/bddat  
**Historial completo:** [Ver Pull Requests cerrados](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed)  
**Última actualización:** 27 de enero de 2026

---

## Estrategia de Documentación de Cambios

Este archivo mantiene un **resumen de los últimos 5 PRs mergeados** para consulta rápida. Para detalles completos (commits, archivos modificados, diffs), consultar directamente el Pull Request correspondiente en GitHub.

**Fuente de verdad:** Los Pull Requests cerrados en GitHub contienen toda la información histórica del proyecto.

**Actualización del changelog:** Se realiza **en la misma rama de desarrollo** (feature/bugfix/etc.) antes de crear el PR, no en rama separada. Esto reduce overhead de ramas/PRs/acciones.

---

## Últimos Cambios

### 2026-01-27 - [PR #TBD: Mejorar Diseño de Mensajes Informativos](https://github.com/genete/bddat/pull/TBD)

**Objetivo:** Mejorar el diseño visual y comportamiento de los mensajes informativos (toasts) implementando los cambios solicitados en el issue #3.

**Cambios principales:**
- ✅ **Ancho 90%**: Los toasts ocupan el 90% del ancho visible con márgenes del 5% a cada lado
- ✅ **Borde uniforme**: Cambio de borde izquierdo de 4px a borde completo de 1px del color oscuro de cada tipo
- ✅ **Botón cerrar coloreado**: La "X" de cerrar ahora tiene el mismo color que el texto/borde de cada tipo (verde, rojo, amarillo, azul)
- ✅ **Transparencia inicial**: Los mensajes aparecen con opacity 0.9
- ✅ **Efecto hover**: Al pasar el ratón, el mensaje se oscurece (opacity 1), la sombra se intensifica y se eleva ligeramente
- ✅ **Tiempo ampliado**: El tiempo de auto-cierre aumenta de 5 a 8 segundos
- ✅ **Animaciones fade**: Transiciones suaves de 300ms al aparecer y desaparecer con desplazamiento vertical

**Issues resueltos:** #3  
**Archivos:** app/static/css/custom.css, app/templates/base.html

---

### 2026-01-25 - Unificar Actualización de Changelog en Rama de Feature

**Objetivo:** Simplificar workflow eliminando ramas y PRs separados para actualizar el changelog.

**Cambios principales:**
- ✅ **Workflow simplificado**: Changelog se actualiza en la misma rama de desarrollo
- ✅ **Menos overhead**: Elimina rama/PR/acciones separadas solo para changelog
- ✅ **REGLAS_DESARROLLO.md actualizado**: Documenta nueva secuencia de trabajo
- ✅ **ACCESO_RAPIDO_PROYECTO.md actualizado**: Añade regla en sección de workflow
- ✅ **Aplicación inmediata**: Este mismo PR aplica la nueva regla

**Workflow anterior:**
1. Rama feature → commits → PR → merge
2. Rama docs/changelog → commit changelog → PR → merge

**Workflow nuevo:**
1. Rama feature → commits + commit changelog → PR → merge

**Archivos:** docs/fuentesIA/REGLAS_DESARROLLO.md, docs/fuentesIA/ACCESO_RAPIDO_PROYECTO.md, docs/CHANGELOG.md

---

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

**Nota:** Este changelog se mantiene con los últimos 5 PRs. Entradas más antiguas se pueden consultar en el [historial de Pull Requests](https://github.com/genete/bddat/pulls?q=is%3Apr+is%3Aclosed+sort%3Aupdated-desc) de GitHub.