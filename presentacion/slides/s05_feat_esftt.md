# S05 — Tramitación estructurada

## Metadatos

- **Layout:** Contenido + iframe (mitad izquierda texto, mitad derecha diagrama Miro)
- **Fragments:** Sí — ver detalle de fragments por elemento más abajo
- **Artefacto visual:** Diagrama Miro del árbol ESFTT — vista encuadrada en un ejemplo de solicitud completa

---

## Contenido visible

**Número de sección:** 5

**Título** *(extrabold negro):*
> El expediente y el procedimiento

**Subtítulo** *(bold verde):*
> Cada solicitud en su sitio. Un sitio para múltiples solicitudes.

**Texto introductorio** *(italic gris, visible desde el inicio — no fragment):*
> Un expediente es siempre un proyecto. El proyecto puede evolucionar manteniendo el mismo fin — las distintas solicitudes se tramitan sobre el mismo proyecto y sus modificaciones.
> La estructura refleja el procedimiento legal real: la semántica del procedimiento vive en los tipos, no en los campos.

**Bullets** *(se revelan con clic; los sub-bullets son fragments adicionales dentro del mismo bullet):*

1. Cada expediente tiene una estructura de tramitación en capas: **Expediente → Solicitud → Fase → Trámite → Tarea**. La tarea es la mínima unidad de trabajo.

   - 1.1 *(fragment)* **Expediente** — el contenedor único ligado a un proyecto. Tipos: *Transporte, Distribución, Renovable...*
   - 1.2 *(fragment)* **Solicitud** — el procedimiento que se tramita sobre ese proyecto. Tipos: *Autorización Administrativa Previa (AAP), Autorización Administrativa de Construcción (AAC), Autorización de Explotación (AE)...*
   - 1.3 *(fragment)* **Fase** — contenedor de trámites con resultado propio. Tipos: *Análisis de solicitud, Información pública, Consultas a organismos, Resolución...*
   - 1.4 *(fragment)* **Trámite** — agrupa las tareas de un mismo acto administrativo. Tipos: *Publicación BOE, Publicación BOP, Consulta a organismo X...*
   - 1.5 *(fragment)* **Tarea** — la acción concreta que realiza el tramitador. 7 tipos atómicos: *REDACTAR, FIRMAR, NOTIFICAR, ESPERAR PLAZO...*

2. *(fragment)* El sistema muestra en todo momento en qué punto está cada solicitud y qué acción toca a continuación

3. *(fragment)* Varias fases del mismo expediente pueden avanzar en paralelo sin perder el hilo...

   - 3.1 *(fragment)* ...mientras sean compatibles. *Ejemplo: no podemos iniciar la Información Pública sin la Admisión a Trámite completada.*

4. *(fragment)* Si la situación lo requiere, el tramitador puede salirse del flujo estándar justificadamente...

   - 4.1 *(fragment)* ...de lo que quedará registro en el **cuaderno de bitácora**.
     🎨 *Píldora visual: badge/etiqueta "📓 Cuaderno de bitácora" en verde o gris institucional, aparece inline junto al texto.*

---

## Artefacto visual

🎨 *Iframe Miro: diagrama del árbol ESFTT con un ejemplo de solicitud AAP o AAC completa.*

*El encuadre debe mostrar:*
- *Un nodo raíz "Expediente" con su número AT*
- *Una o dos solicitudes como hijos directos (AAP + AAC si cabe)*
- *Las fases de al menos una solicitud desplegadas (Análisis, Información pública, Consultas, Resolución)*
- *Los trámites de una fase visible*
- *Las tareas de un trámite (REDACTAR, FIRMAR, NOTIFICAR...)*

*Criterio de encuadre: que se vea la jerarquía completa de un camino (raíz → hoja) sin scroll.*
*El presentador puede navegar el Miro en vivo si hay preguntas — el iframe lo permite.*

*URL Miro: pendiente de definir / enlace al tablero ya existente de diagramas ESFTT.*

---

## Notas ponente

Esta es la slide conceptual más importante. El resto de características (documentos, escritos, listado) se apoyan en esta estructura — si se entiende, todo lo demás encaja.

Texto intro: decirlo despacio. "Un expediente es siempre un proyecto" es la clave de la unicidad — si alguien pregunta qué pasa cuando el proyecto cambia, aclarar que puede haber modificaciones de proyecto dentro del mismo expediente, pero el expediente no migra a otro proyecto.

"La semántica del procedimiento vive en los tipos" — no hace falta que la audiencia recuerde la frase. Lo que importa es que entiendan que los nombres que ven en el sistema (AAP, Información Pública, REDACTAR...) son los mismos que usan en papel. No hay que aprender una nomenclatura nueva.

Bullet 1 + sub-bullets 1.1–1.5: señalar el diagrama Miro mientras se van revelando. Cada sub-bullet corresponde a un nivel del árbol visible en el diagrama. No leer la lista entera — presentarla como "de esto ya conocéis la mayoría" y avanzar.

Bullet 2: el cambio práctico más visible frente al Excel. Antes había que reconstruir el estado. Aquí el sistema lo dice.

Bullet 3 + 3.1: útil para expedientes con AAP + AAC simultáneas. La audiencia reconocerá la casuística. El ejemplo de la Información Pública es concreto y cercano.

Bullet 4 + 4.1: no profundizar. Solo dejar claro que el sistema no es una jaula — y que todo queda registrado. La píldora del cuaderno de bitácora es un guiño a que existe ese mecanismo; si alguien pregunta, explicar brevemente.

Transición a S06: "Esta estructura gestiona también los documentos. Os explico cómo."
