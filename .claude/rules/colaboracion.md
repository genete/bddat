# Colaboración con Carlos

Criterios de trabajo acumulados en sesiones anteriores. Las reglas de proceso (git, migraciones, tests) están en `docs/guias/REGLAS_DESARROLLO.md`; las decisiones de diseño, en `docs/decisiones/`.

## Cómo responder

- **El objetivo, antes que nada**: antes de plantear hallazgos y decisiones, explicar en llano el objetivo del asunto y lo que se pretende (Carlos, 2026-10-05).
- **Resumen primero, en lenguaje llano**: qué he encontrado, qué cambia y qué hay que decidir (como mucho 3-4 preguntas). El detalle va a `docs_prueba/temp/<nombre nuevo>.md`, se enlaza y se ofrece; no se pega en el chat. La tabla de consumidores sigue siendo obligatoria antes de escribir código.
- **No dar la razón sin verificar**: antes de «tienes razón» o «no», leer el código o consultar la BD y traer el dato concreto. Retirar una recomendación propia cuando su argumento cae, sin rodeos.
- **Pensar antes de ejecutar literalmente**: inferir el objetivo real y ofrecer alternativas superiores (p. ej. buscar la API subyacente antes de hacer scraping). No preguntar «¿quieres que haga X?» si X es lo que acaba de pedir.
- **Reflexión conceptual** («¿me equivoco conceptualmente?»): razonar en prosa con las capas ley / modelo / mapeo y el supuesto que provocó el error. Las comprobaciones de código son evidencia de apoyo, no el cuerpo de la respuesta.
- **Varios «[No preference]» seguidos** en decisiones que importan: puede haber un encuadre propio que no encaja en las opciones. Preguntar «¿o el encuadre es otro?» y, si llega, rehacer el análisis diciendo qué propuestas anteriores caen.
- No releer ficheros que ya están en el contexto de la sesión.

## Qué no asumir

- **Conformidad**: sin confirmación explícita no se implementa una propuesta de diseño ni se elimina contenido que ya figuraba en una fuente de verdad (p. ej. `CONTEXTO_ACTUAL.md`). Si una reescritura quita algo, decirlo en la propuesta.
- **Documentos de diseño**: transcribir lo que dijo Carlos, no lo que se infiere. Lo inferido se marca como «interpretación» y se avisa antes del commit. Menos es más.
- **«Crea documento de traspaso y finalizamos»** es orden de parar. El mensaje automático de reanudación tras un límite de uso no lo escribe Carlos y no reactiva trabajo que había cerrado.
- **Urgencia**: BDDAT no está en producción. No tratar un bug como incidente salvo que Carlos lo pida; sí es válido señalar el coste de diferirlo.

## Método de análisis

- Ante «esto no me cuadra»: `git log -p --follow` / `git blame` y datos, no solo releer el código actual.
- **La BD de desarrollo ilustra, no prueba.** Los datos de operación (expedientes, notificaciones, documentos, fechas) no son evidencia ni condicionan migraciones o alcance: se tiran. Los de catálogo sí son fuente de verdad. Tras probar en la interfaz, no revertir datos de operación: decir qué se tocó. Excepción: las filas de prueba en tablas de catálogo se borran (en el PC, `scripts/comparar_catalogo.py` las detecta). Los tests sí limpian lo que escriben.
- **Atribución código → catálogo por grep**: rastrear la clase real detrás de un `.codigo` (puede ser un dataclass sin tabla). Si la conclusión va a una fuente de verdad, ejecutar el chequeo contra datos reales.
- **Cuestiones jurídicas**: leer la norma (`/boe`, `/boja`, `/legalize`) antes de diseñar. El código y los docs de diseño derivan de lecturas anteriores y arrastran premisas falsas. Si Carlos corrige una premisa, revisar si contamina el resto del análisis.
- **Enganchar una automatización** en el punto más temprano en que el dato disparador ya se fija de forma obligatoria, no donde se consume el resultado.
- **Salvaguardas**: antes de implementarlas, decir si son invariante (hardcode), modelo legal (`reglas_motor`) o dato de catálogo (ADR-037, ADR-036, ADR-043). Por defecto, permitir con justificación; el bloqueo duro solo cuando el acto ya salió y no se puede deshacer (p. ej. notificado).

## Prioridades

- Orden: infraestructura → migrar lo existente → vistas nuevas aisladas. Distinguir lo preceptivo de lo meramente importante; adelantar una vista nueva solo por presión de negocio que decide Carlos.
- El desarrollo avanza **fase a fase del procedimiento**. Al proponer el «Próximo» o agrupar issues, preguntar de qué fase es cada uno; lo particular de una fase se ancla a cuando el foco llegue a ella. Si queda un hueco conocido, señalarlo una vez.
- Carlos prefiere los issues que generan código a los de poblado puro de catálogos, salvo que el poblado sea prerrequisito bloqueante.
