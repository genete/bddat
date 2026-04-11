# Guía: Diagramas de flujo ESFTT

**Fecha:** 22/03/2026
**Estado:** Decisiones consolidadas — guía operativa activa

---

## Índice

1. [Contexto y motivación](#1-contexto-y-motivación)
2. [Herramienta: Mermaid](#2-herramienta-mermaid)
3. [Estructura en capas](#3-estructura-en-capas)
4. [Principio de contenido mínimo](#4-principio-de-contenido-mínimo)
5. [Flujo de trabajo](#5-flujo-de-trabajo)
6. [Organización en git](#6-organización-en-git)
7. [Relación con el JSON](#7-relación-con-el-json)
8. [Lecciones aprendidas — prueba #249](#8-lecciones-aprendidas--prueba-249)
9. [Procedimientos operativos](#9-procedimientos-operativos)

---

## 1. Contexto y motivación

El sistema ESFTT tiene una complejidad que no es navegable solo con el JSON ni con los documentos de diseño en texto. Un técnico o desarrollador que necesite entender el flujo completo de un expediente no tiene una referencia visual de referencia.

**Necesidades identificadas:**
- El desarrollador necesita ver los flujos para detectar inconsistencias en el motor de reglas y pre-condiciones entre fases.
- El usuario final necesita una referencia visual para entender el procedimiento administrativo.
- La documentación técnica (manual) necesita diagramas navegables entre capas.

**Fuente de verdad para los diagramas:** el JSON de estructura de fases/trámites/tareas es el esqueleto, pero no es suficiente. Los documentos de diseño MD contienen la semántica, las condiciones del motor y las decisiones arquitectónicas. Ambas fuentes deben estar sincronizadas antes de crear cualquier diagrama (ver `REGLAS_ARQUITECTURA.md`).

---

## 2. Herramienta: Mermaid

**Decisión: Mermaid** como formato fuente de los diagramas.

**Motivación:**
- Licencia MIT — sin lock-in. El `.mmd` es texto plano legible incluso sin Mermaid.
- GitHub renderiza Mermaid nativamente en ficheros `.md` — sin artefactos separados para visualización online.
- Sintaxis legible y mantenible directamente en un editor de texto.
- SVG como artefacto renderizado para manual imprimible o importación a Miro/Figma.
- Amplio soporte en el ecosistema (GitLab, Notion, Obsidian, VS Code…).

**Riesgo valorado como bajo:** el respaldo de GitHub hace improbable la discontinuación. En el peor caso, los `.mmd` siguen siendo texto legible y los SVGs comprometidos en git siguen siendo válidos. No hay dependencia funcional en la aplicación BDDAT — los diagramas son documentación, no código.

**Render:** `mmdc -i fichero.mmd -o svg/fichero.svg` (CLI de Node, instalación única).

---

## 3. Estructura en capas

Los diagramas se organizan por capas de abstracción, no por tipo de expediente. Organizar por tipo genera duplicación masiva (el 80% de las fases son comunes) y un coste de mantenimiento inasumible.

### Capa 0 — Conceptual (1 diagrama, estático)
El modelo mental del sistema: qué es una FASE, un TRÁMITE, una TAREA, un PATRÓN y cómo se relacionan entre sí. Sin fases concretas — solo conceptos y relaciones. Va al inicio del manual. Se toca raramente.

### Capa 1 — Patrones de flujo (1 diagrama con fichas pequeñas)
Los patrones A, B, C, C+, D, E, F visualizados como bloques reutilizables. Son los átomos del sistema. Cuando en un diagrama superior aparece "patrón C+", el usuario sabe donde mirar. Casi una transcripción directa del JSON — la más estable de todas las capas.

### Capa 2 — Mapa de fases (1 diagrama maestro)
El flujo entre fases con las condiciones estructurales del motor de reglas: qué habilita cada fase, qué la bloquea. Las variaciones por tipo de expediente se anotan como ramificaciones o notas en este mismo diagrama, no como diagramas separados. Es la capa que más evolucionará durante el desarrollo activo.

### Capa 3 — Fichas de fase (1 diagrama por fase)
Cada fase con sus trámites, sus tareas y las condiciones de cierre del motor. Fichas pequeñas e independientes: una ficha se actualiza sin tocar las demás. Se crean progresivamente según se implementa cada fase. Aquí aparece la capa del motor de reglas integrada con el flujo.

**Orden de creación recomendado:** Capa 1 (estable, útil ya para el desarrollador) → Capa 0 (conceptual, estático) → Capa 2 (requiere sincronización documental completa) → Capa 3 fase a fase según implementación.

---

## 4. Principio de contenido mínimo

Los diagramas solo reflejan la **estructura** del sistema: qué fases existen, qué trámites, qué patrones, qué condiciones del motor son **estructurales**.

**Nunca incluir:**
- Plazos en días (cambian por resolución administrativa)
- Referencias a artículos concretos de normativa (cambian con reformas)
- Datos operacionales de expedientes concretos
- Cualquier dato que pueda cambiar sin cambio conceptual del sistema

**Sí incluir:**
- La existencia de una condición del motor (p.ej. "requiere tasas validadas") sin el detalle legal
- La existencia de una pre-condición entre fases sin el plazo concreto
- La estructura de trámites aunque cambien sus nombres menores

Este principio es la garantía de mínimo mantenimiento: el diagrama solo cambia cuando cambia la arquitectura, no cuando cambia un parámetro operacional.

---

## 5. Flujo de trabajo

1. **Sincronización previa:** verificar que el JSON y los MDs de diseño están alineados para la capa a diagramar (obligatorio antes de Capa 2 y 3).
2. **Creación del `.mmd`:** Claude Code sintetiza las fuentes relevantes y genera el fichero Mermaid.
3. **Revisión:** el usuario revisa el `.mmd` (legible en texto plano) y corrige si es necesario.
4. **Render:** `mmdc -i fichero.mmd -o svg/fichero.svg`
5. **Commit:** ambos ficheros (`.mmd` fuente + `.svg` artefacto).
6. **Para Miro:** importación manual del SVG cuando se quiera el canvas interactivo con navegación entre capas.

---

## 6. Organización en git

```
docs/diagramas_esftt/
  capa0_conceptual.mmd
  capa1_patrones.mmd
  capa2_mapa_fases.mmd
  capa3_analisis_solicitud.mmd
  capa3_consultas.mmd
  capa3_informacion_publica.mmd
  ...
  svg/
    capa0_conceptual.svg
    capa1_patrones.svg
    capa2_mapa_fases.svg
    capa3_analisis_solicitud.svg
    ...
```

---

## 7. Relación con el JSON

El JSON (`ESTRUCTURA_FTT.json`) es el esqueleto estructural pero no es la fuente completa para los diagramas:

- **Lo que el JSON aporta:** qué fases, trámites y patrones existen; la secuencia de tareas dentro de cada trámite.
- **Lo que los MDs de diseño aportan:** condiciones del motor, decisiones arquitectónicas, semántica de cada fase, casos especiales.
- **Lo que no debe estar en el JSON:** notas de diseño extensas, motivaciones, historial de razonamiento. Eso pertenece a los MDs de diseño. El JSON debe ser lean: solo estructura.

La limpieza del JSON (mover notas de prosa a MDs) ya está realizada. El JSON actual es lean: solo estructura operativa.

---

## 8. Lecciones aprendidas — prueba #249

Sesión de prueba realizada el 22/03/2026 antes de consolidar la decisión de Mermaid.
Se generó la Capa 0 (conceptual) y se intentó reproducir el diagrama de flujo AAP_PROPIO de Miro.

### Veredicto: Mermaid es válido

- Maneja sin errores diagramas con ciclos, múltiples terminales y convergencias de ramas.
- La Capa 0 (conceptual) quedó correcta desde la primera generación.
- El SVG renderizado es importable a Miro/Figma y visualizable en GitHub.

### Limitación conocida: layout automático (Dagre)

El motor de layout de Mermaid (Dagre) coloca los nodos según el grafo dirigido. Esto tiene consecuencias en diagramas con ramas paralelas que convergen:
- Ramas que en un diagrama manual son paralelas (lado a lado) quedan apiladas verticalmente.
- Las flechas de retorno (ciclos) se renderizan como arcos largos en el margen, no como flechas compactas.
- No es configurable: Mermaid no permite posicionamiento manual de nodos.

Esto no invalida Mermaid para documentación técnica, pero el resultado visual es menos legible que un diagrama manual de Miro para flujos con muchas convergencias.

### Limitación conocida: generación asistida por IA no es 100% fiable

La IA genera el `.mmd` sintetizando fuentes textuales (JSON, MDs de diseño). Cuando la fuente es una **captura de pantalla de un diagrama compacto con cruces de líneas**, la lectura es ambigua y el `.mmd` generado puede contener errores estructurales (nodos mal conectados, terminales con flechas de salida erróneas, nodos fantasma).

**Regla de trabajo:** la IA genera los diagramas a partir de los MDs de diseño y el JSON — no a partir de capturas o SVGs de Miro. Si se parte de un diagrama Miro existente, debe expandirse sin cruces de líneas antes de pasárselo a la IA.

### Convención de color (extraída del análisis)

Los diagramas de flujo ESFTT usan color para indicar quién tiene la pelota en cada momento:
- **Amarillo** — Administración: nodos de decisión o terminales. No tienen flechas de salida al flujo (son resoluciones administrativas).
- **Verde** — Titular: traslados y acciones que corresponden al titular del expediente.
- **Morado** — Organismo: traslados y acciones que corresponden al organismo consultado.

Esta convención debe respetarse en todos los diagramas de Capa 2 y Capa 3.

---

## 9. Procedimientos operativos

Esta guía define las decisiones de diseño. Los procedimientos paso a paso están en ficheros separados:

- **[PROCEDIMIENTO_MMD_DESDE_DOCUMENTACION.md](PROCEDIMIENTO_MMD_DESDE_DOCUMENTACION.md)** — generación de Capa 3 a partir de MDs de diseño y JSON. Incluye fuentes a consultar, decisiones de diseño tomadas y gaps detectados.
- **[PROCEDIMIENTO_MMD_DESDE_IMAGEN.md](PROCEDIMIENTO_MMD_DESDE_IMAGEN.md)** — generación de diagrama Mermaid a partir de una captura de pantalla de un diagrama existente. Útil cuando se parte de diagramas de Miro o similares.
