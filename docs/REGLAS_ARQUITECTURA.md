# Reglas de arquitectura y documentación de decisiones — BDDAT

**Fecha:** 22/03/2026
**Estado:** En progreso — pendiente cerrar según issue #250

---

## Índice

1. [Contexto y problema](#1-contexto-y-problema)
2. [Tipos de documento y su rol](#2-tipos-de-documento-y-su-rol)
   - [2.1 Documentos derivados](#21-documentos-derivados)
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

| Prefijo | Rol | Cambia cuando |
|---|---|---|
| `DISEÑO_*.md` | Decisión arquitectónica propia: qué se decide, por qué, alternativas descartadas. | Cambia la decisión |
| `NORMATIVA_*.md` | Conocimiento externo (legislación, instrucciones Consejería). Incluye `Fuente:` y `Aplica a:` en cabecera. | Cambia la norma |
| `GUIA_*.md` | Instrucciones prácticas de implementación de un subsistema. | Cambia la implementación |
| `REGLAS_*.md` | Normas de trabajo obligatorias (workflow Git, antibloqueos Bash, este doc). | Cambia el criterio |
| `PLAN_*.md` | Planificación y roadmap. Estado de milestones e iniciativas. | Avanza la implementación |
| `ANALISIS_*.md` | Diagnóstico puntual o estudio. Puede ser derivado de otra fuente de verdad. | No debería — es histórico |
| `PROCEDIMIENTO_*.md` | Pasos secuenciales para una operación concreta. | Cambia el proceso |
| `ESTRUCTURA_*.md` | Catálogo estructural del dominio (reemplaza al JSON como lectura humana). | Cambia la estructura ESFTT |
| `ESTRUCTURA_FTT.json` | Fuente de verdad estructural ESFTT para código e IA. Solo estructura, sin prosa. | Cambia la estructura ESFTT |
| Diagramas `.mmd` / `.svg` | Representación visual del sistema. Cara legible del JSON. | Cambia el JSON |

### 2.1 Documentos derivados

Un documento es **derivado** cuando su contenido se genera o extrae de otra fuente de verdad (normalmente el JSON de estructura). Estos documentos deben declarar su dependencia en cabecera para que el §6 de sincronización sea accionable.

**Convención de cabecera para MDs derivados:**

```markdown
> Fuente de verdad: `<fichero>`
> Última sincronización: <fecha ISO 8601>
```

**Convención para diagramas `.mmd`** (no admiten cabecera Markdown):

```
%% Fuente: <fichero> | Sincronizado: <fecha ISO 8601>
```

Esta línea va como primer comentario del archivo, antes de la declaración del diagrama (o después del bloque frontmatter `---` si existe).

**Derivados conocidos actualmente:**

| Documento derivado | Fuente de verdad |
|---|---|
| `ANALISIS_TAREAS_INVERSO.md` | `ESTRUCTURA_FTT.json` |
| `diagramas_esftt/capa0_conceptual.mmd` | `ESTRUCTURA_FTT.json` |
| `diagramas_esftt/capa3_informacion_publica.mmd` | `ESTRUCTURA_FTT.json` |

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

## 7. Pendientes de la sesión dedicada (#250)

Este documento es un borrador. Los puntos pendientes se rastrean en el issue #250. Resumen:

- [x] Disolver `docs/fuentesIA/` — JSON movido a `docs/ESTRUCTURA_FTT.json` (v5.5)
- [x] Limpieza del JSON y conversión a `ESTRUCTURA_FTT.md`
- [ ] Redistribuir contenido de `ANALISIS_167_*` en documentos con prefijo correcto
- [ ] Completar secciones de árbol de decisión, sesión de sincronización y ciclo de vida (ver issue)
- [ ] Revisar si `GUIA_GENERAL.md` sigue siendo válida como referencia general
- [ ] Skills de mantenimiento de dependencias documentales (ver issue #250 §disciplina futura)
