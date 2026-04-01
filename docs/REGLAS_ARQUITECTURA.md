# Reglas de arquitectura y documentación de decisiones — BDDAT

**Fecha:** 25/03/2026
**Estado:** Cerrado — issue #250

---

## Índice

1. [Contexto y problema](#1-contexto-y-problema)
2. [Tipos de documento y su rol](#2-tipos-de-documento-y-su-rol)
   - [2.1 Documentos derivados](#21-documentos-derivados)
3. [Flujo de una decisión arquitectónica](#3-flujo-de-una-decisión-arquitectónica)
4. [Reglas del JSON de estructura](#4-reglas-del-json-de-estructura)
5. [Cuándo una decisión está cerrada](#5-cuándo-una-decisión-está-cerrada)
6. [Sincronización documental](#6-sincronización-documental)
7. [Skills de mantenimiento](#7-skills-de-mantenimiento)
8. [Árbol de decisión](#8-árbol-de-decisión----qué-hago-con-esta-idea-o-necesidad)
9. [Ciclo de vida de un documento](#9-ciclo-de-vida-de-un-documento)
10. [Historial del documento](#10-historial-del-documento)

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
| `ANALISIS_*.md` | Documento de trabajo durante la fase de análisis/planificación de un issue complejo. Recoge el diagnóstico, las decisiones en curso y los pendientes. Evoluciona durante el estudio; queda congelado al arrancar la implementación. **No es la referencia post-implementación** — eso es el `DISEÑO_*.md` asociado. | Mientras dure el análisis; congelado al implementar |
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
| `ESTRUCTURA_FTT.md` | `ESTRUCTURA_FTT.json` |
| `ANALISIS_TAREAS_INVERSO.md` | `ESTRUCTURA_FTT.json` |
| `ANALISIS_LISTADO_INTELIGENTE.md` | `ESTRUCTURA_FTT.json` |
| `ANALISIS_GENERACION_DIAGRAMA_EXPEDIENTE.md` | `ESTRUCTURA_FTT.json` |
| `DISEÑO_FECHAS_PLAZOS.md` | `NORMATIVA_PLAZOS.md` |

---

## 3. Flujo de una decisión arquitectónica

```
IDEA / NECESIDAD
      │
      ├─ Simple (1-2 archivos, sin análisis previo)
      │       └─ Ver §8 (árbol de decisión)
      │
      └─ Compleja (requiere análisis, múltiples decisiones, issue)
              │
              ▼
        ANÁLISIS_*.md  ← documento de trabajo durante el estudio
          - Diagnóstico, preguntas abiertas, alternativas
          - Evoluciona con cada sesión de análisis
          - Se congela al arrancar la implementación
              │
              ▼
        Issue de implementación en GitHub
          - Checklist de tareas concretas
          - Referencia al ANÁLISIS_*.md
              │
              ▼
        Implementación (rama feature → PR → develop)
          - Modelo, migración, servicio, vista
              │
              ▼
        DISEÑO_*.md  ← síntesis post-implementación  ◄─── NUEVO PASO OBLIGATORIO
          - Qué se hizo y por qué se hizo así
          - Alternativas descartadas y motivo
          - Cómo está implementado (claves de diseño, no manual de código)
          - Qué NO hace y por qué
          - El ANÁLISIS_*.md queda como contexto histórico; este doc es la referencia futura
              │
              ▼
        Actualización del JSON (si afecta a fases/trámites/tareas)
          - Solo estructura, sin notas de diseño
          - Bump de versión en metadata
              │
              ▼
        Actualización de diagramas afectados (Capa 2 o 3)
          - Solo cuando el MD y el JSON estén alineados
```

Ningún paso puede saltarse. Si una decisión solo existe en la conversación sin MD, se considera **no documentada** y por tanto inestable — puede perderse o reinterpretarse incorrectamente en una sesión futura.

> **Regla ANÁLISIS → DISEÑO:** todo `ANÁLISIS_*.md` que desemboque en implementación debe tener su `DISEÑO_*.md` correspondiente antes de cerrar el issue. El análisis explica el camino; el diseño explica la llegada.

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

Antes de crear diagramas de Capa 2 o Capa 3, y antes de iniciar la implementación de cualquier fase nueva, debe realizarse una verificación de coherencia.

**Cuándo se convoca una sesión de sincronización:**
- Se modificó `ESTRUCTURA_FTT.json` (cualquier cambio de estructura)
- Un diagrama tiene fecha de sincronización anterior a la del JSON
- Dos MDs de diseño parecen contradecirse

**Checklist de sincronización:**
- [ ] Todas las decisiones de sesiones recientes tienen MD de diseño
- [ ] El JSON refleja el estado actual de los MDs de diseño
- [ ] Los items "A ESTUDIAR" pendientes tienen issue asignado
- [ ] Las notas extensas del JSON se han movido a MDs de diseño
- [ ] Los derivados conocidos (tabla §2.1) tienen su `> Última sincronización:` al día

**Cómo ejecutar cada verificación:**

1. **Decisiones sin MD** — revisar el log de commits recientes y comparar con la lista de `DISEÑO_*.md` en `docs/`:
   - `git -C /d/BDDAT log --oneline -20` para ver sesiones recientes
   - `ls docs/DISEÑO_*.md` para ver los MDs existentes

2. **JSON vs MDs** — comparar la versión del JSON (`metadata.version`) con la fecha de los MDs de diseño relacionados. Si algún MD es posterior al JSON, el JSON está desactualizado.

3. **Items "A ESTUDIAR" sin issue** — buscar en todos los MDs:
   - `grep -rn "A ESTUDIAR" docs/` para listar los abiertos
   - Cada resultado debe tener un issue de GitHub asignado

4. **Notas extensas en el JSON** — revisar campos `nota` del JSON. Si alguno supera 3 líneas, mover el contenido a un `DISEÑO_*.md` y dejar solo `"ver DISEÑO_X.md §Y"`.

5. **Derivados desactualizados** — usar el skill `/sync-derivados` para detectar qué fuentes cambiaron y qué derivados están desfasados.

**Qué produce una sesión de sincronización:**

Un commit con prefijo `[SYNC]` que lista explícitamente qué se ha sincronizado:

```
[SYNC] #250 Actualizar derivados tras cambios en ESTRUCTURA_FTT.json

- ANALISIS_TAREAS_INVERSO.md: Última sincronización actualizada
- capa0_conceptual.mmd: Última sincronización actualizada
```

---

## 7. Skills de mantenimiento

Dos skills automatizan las tareas más repetitivas de sincronización y registro:

| Skill | Invocación | Función |
|---|---|---|
| `sync-derivados` | `/sync-derivados` | Detecta fuentes modificadas y actualiza `> Última sincronización:` en sus derivados |
| `register-fuente` | `/register-fuente` | Registra un MD nuevo en la tabla §2.1, detectando su fuente desde la cabecera |

Ambos skills leen el contexto git en tiempo real y operan sin argumentos en el caso habitual.

---

## 8. Árbol de decisión — ¿qué hago con esta idea o necesidad?

```
IDEA O NECESIDAD
      │
      ├─ ¿Es una corrección puntual o aclaración de algo ya decidido?
      │       └─ Sí → Edita directamente el doc afectado + commit [DOCS]
      │
      ├─ ¿Implica análisis profundo antes de decidir? (múltiples opciones, impacto amplio)
      │       └─ Sí → ANÁLISIS_*.md (doc de trabajo) → decisiones → issue → implementación
      │               → Al terminar: DISEÑO_*.md (síntesis) — ver §3
      │               → ANÁLISIS_*.md queda congelado como contexto histórico
      │
      ├─ ¿Implica una decisión de diseño simple? (arquitectura puntual, sin análisis largo)
      │       └─ Sí → Sesión de diseño → DISEÑO_*.md directamente
      │               → Si afecta JSON: actualizar ESTRUCTURA_FTT.json + bump versión
      │               → Si implica código: abrir issue con checklist + referencia al MD
      │
      ├─ ¿Es una tarea de implementación ya decidida?
      │       └─ Sí → Abrir issue → rama feature → código → PR a develop
      │
      ├─ ¿Afecta a la estructura global? (JSON + diagramas + varios MDs)
      │       └─ Sí → Sesión de sincronización → /sync-derivados → commit [SYNC]
      │
      └─ ¿Es conocimiento normativo externo? (legislación, instrucciones Consejería)
              └─ Sí → NORMATIVA_*.md con cabecera:
                       > Fuente: <referencia legal>
                       > Aplica a: <subsistema o fase>
```

**Regla de oro:** si la idea solo existe en la conversación, no está documentada. Una conversación no es un doc de diseño.

---

## 9. Ciclo de vida de un documento

### Nacimiento

| Tipo | Quién lo crea | Estructura mínima obligatoria |
|---|---|---|
| `DISEÑO_*.md` | Claude o el usuario, en sesión de diseño | Título, fecha, decisión tomada, alternativas descartadas |
| `NORMATIVA_*.md` | El usuario, con asistencia de Claude | Cabecera `> Fuente:` y `> Aplica a:`, texto de la norma |
| `GUIA_*.md` | Claude, cuando hay suficiente implementación que documentar | Contexto, pasos, ejemplos |
| `REGLAS_*.md` | Claude o el usuario, cuando se establece una norma de trabajo | Norma, motivación, ejemplos |
| `ANALISIS_*.md` | Claude, como diagnóstico puntual | Fecha, alcance, hallazgos |
| `ESTRUCTURA_*.md` | Claude, derivado del JSON | Cabecera `> Fuente de verdad:` + `> Última sincronización:` |

### Actualización vs. archivo

Un documento se **actualiza** cuando la decisión, norma o guía que describe cambia.

Un documento se **archiva** (`docs/archivo/`) cuando:
- La decisión fue revertida o sustituida por otra
- El subsistema fue eliminado o renombrado completamente
- Existe un `DISEÑO_*.md` más reciente que lo supera

Un `DISEÑO_*.md` queda **congelado** cuando la implementación lo supera: se anota `> Estado: implementado` en la cabecera y no se vuelve a modificar. Sirve como registro histórico de por qué se tomó la decisión, no como referencia activa.

### Derivados: cuándo se desactualizan

Un derivado queda desactualizado cuando su fuente de verdad cambia. La señal visible es que la fecha en `> Última sincronización:` es anterior a la fecha del último commit que tocó la fuente. El skill `/sync-derivados` detecta esta situación automáticamente.

---

## 10. Historial del documento

- **2026-03-22:** Primera versión — §1 a §5, checklist §6 básico
- **2026-03-25:** Cierre borrador — §6 con procedimiento ejecutable, §7 skills, §8 árbol de decisión, §9 ciclo de vida (issue #250)
- **2026-03-26:** Añadir patrón ANÁLISIS_*.md → DISEÑO_*.md — §2, §3 y §8 actualizados
