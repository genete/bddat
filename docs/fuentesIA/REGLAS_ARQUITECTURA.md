# Reglas de arquitectura y documentación de decisiones — BDDAT

**Fecha:** 22/03/2026
**Estado:** Borrador inicial — requiere sesión dedicada para cerrar y consolidar

---

## Índice

1. [Contexto y problema](#1-contexto-y-problema)
2. [Tipos de documento y su rol](#2-tipos-de-documento-y-su-rol)
3. [Flujo de una decisión arquitectónica](#3-flujo-de-una-decisión-arquitectónica)
4. [Reglas del JSON de estructura](#4-reglas-del-json-de-estructura)
5. [Cuándo una decisión está cerrada](#5-cuándo-una-decisión-está-cerrada)
6. [Sincronización documental](#6-sincronización-documental)
7. [Pendientes de la sesión dedicada](#7-pendientes-de-la-sesión-dedicada)

---

## 1. Contexto y problema

El sistema BDDAT genera decisiones arquitectónicas con rapidez. Las decisiones fluyen en este orden real:

> conversación → documento de diseño MD → JSON de estructura → diagramas

El problema es que cada eslabón va por detrás del anterior. En un momento dado:
- El JSON refleja decisiones de hace dos o tres sesiones
- Los MDs de diseño reflejan decisiones de la sesión anterior
- Los diagramas no existen aún

Esta brecha se ensancha con cada sesión y genera confianza falsa: el desarrollador o la IA leen el JSON creyendo que está actualizado, y no lo está. El JSON es especialmente peligroso porque tiene apariencia de fuente de verdad formal.

`REGLAS_DESARROLLO.md` cubre el workflow de código (Git, commits, ramas, migraciones). Este documento cubre el workflow de **decisiones estructurales**: cómo nacen, dónde se documentan y cómo se mantienen coherentes entre sí.

---

## 2. Tipos de documento y su rol

| Documento | Rol | Audiencia | Estabilidad |
|---|---|---|---|
| `Estructura_fases_tramites_tareas.json` | Esqueleto estructural del ESFTT. Qué fases, trámites, tareas y patrones existen. Solo estructura, sin prosa. | IA + código | Media — cambia con cada nueva fase o trámite |
| `DISEÑO_*.md` | Decisiones de diseño con motivación y alternativas descartadas. Nivel de detalle suficiente para implementar. | Desarrollador + IA | Alta — solo cambia si la decisión cambia |
| `GUIA_*.md` | Referencia técnica de implementación de un subsistema concreto. | Desarrollador + IA | Alta |
| `GUIA_GENERAL.md` | Arquitectura general y lógica de negocio. Visión de conjunto. | Desarrollador + IA | Muy alta |
| `REGLAS_DESARROLLO.md` | Workflow de código: Git, commits, ramas, migraciones. | Desarrollador + IA | Muy alta |
| `REGLAS_ARQUITECTURA.md` (este doc) | Workflow de decisiones estructurales. | Desarrollador + IA | Muy alta |
| Diagramas `.mmd` / `.svg` | Representación visual del sistema. Cara legible del JSON. | Usuario + Desarrollador | Media — se actualiza cuando cambia el JSON |

---

## 3. Flujo de una decisión arquitectónica

```
IDEA / NECESIDAD
      │
      ▼
Discusión en sesión → conclusiones en memoria de conversación
      │
      ▼
Documento de diseño MD (DISEÑO_*.md)
  - Qué se decide y por qué
  - Alternativas descartadas y motivo
  - Impacto en modelo de datos
  - Impacto en motor de reglas
      │
      ▼
Actualización del JSON (si afecta a fases/trámites/tareas)
  - Solo estructura, sin notas de diseño
  - Bump de versión en metadata
      │
      ▼
Issue de implementación en GitHub
  - Checklist de tareas concretas
  - Referencia al MD de diseño
      │
      ▼
Actualización de diagramas afectados (Capa 2 o 3)
  - Solo cuando el MD y el JSON estén alineados
```

Ningún paso puede saltarse. Si una decisión solo existe en la conversación sin MD, se considera **no documentada** y por tanto inestable — puede perderse o reinterpretarse incorrectamente en una sesión futura.

---

## 4. Reglas del JSON de estructura

El JSON tiende a crecer con notas de prosa que explican motivaciones y razonamientos. Eso corresponde a los MDs de diseño, no al JSON.

**El JSON solo debe contener:**
- Códigos y nombres de fases, trámites y tareas
- Secuencia de tareas por trámite
- Patrón de flujo asignado
- Referencias a documentos de diseño (ruta del MD)
- Versión y fecha de última actualización

**Nunca en el JSON:**
- Notas extensas de motivación o razonamiento
- Historial de cambios con argumentación (eso va en el MD o en git log)
- Decisiones pendientes o "A ESTUDIAR"
- Texto que duplique lo que ya está en un MD de diseño

**Regla de tamaño:** si el campo `nota` de un trámite supera 3 líneas, el contenido pertenece a un MD de diseño. La nota del JSON queda como referencia: `"ver DISEÑO_X.md §Y"`.

---

## 5. Cuándo una decisión está cerrada

Una decisión arquitectónica está **cerrada** cuando:

1. Existe un MD de diseño con la decisión documentada (no solo en memoria de conversación)
2. El JSON está actualizado si la decisión afecta a fases/trámites/tareas
3. Existe un issue de GitHub con el checklist de implementación

Una decisión está **pendiente** si:
- Solo existe en conversación (riesgo alto de pérdida)
- Está en el MD pero no en el JSON (brecha documental)
- Está documentada pero sin issue (no trazable en el backlog)

Los items "A ESTUDIAR" en los MDs de diseño son decisiones **abiertas** — deben tener su propio issue y resolverse antes de implementar el componente que los necesita.

---

## 6. Sincronización documental

Antes de crear diagramas de Capa 2 o Capa 3, y antes de iniciar la implementación de cualquier fase nueva, debe realizarse una verificación de coherencia:

**Checklist de sincronización:**
- [ ] Todas las decisiones de sesiones recientes tienen MD de diseño
- [ ] El JSON refleja el estado actual de los MDs de diseño
- [ ] Los items "A ESTUDIAR" pendientes tienen issue asignado
- [ ] Las notas extensas del JSON se han movido a MDs de diseño
- [ ] Los issues de diseño abiertos (actualmente #247, #248) tienen sus MDs de diseño correctamente referenciados

---

## 7. Pendientes de la sesión dedicada

Este documento es un borrador. Los siguientes puntos requieren sesión dedicada para cerrarse:

- [ ] Reorganización de `docs/fuentesIA/`: los documentos han crecido sin criterio de organización explícito. Definir subcarpetas o convención de nombres.
- [ ] Limpieza del JSON: auditar campo por campo qué notas pasan a MDs y cómo queda el JSON lean.
- [ ] Definir criterio formal de "sesión de sincronización": cuándo se convoca, qué cubre, qué produce.
- [ ] Revisar si `GUIA_GENERAL.md` sigue siendo la referencia correcta o ha quedado desfasada por los MDs de diseño posteriores.
- [ ] Decidir si los `DISEÑO_*.md` necesitan una sección estándar de "impacto en otros documentos" para facilitar la propagación de cambios.
