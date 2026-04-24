# Proceso: generación de mmd desde documentación (Capa 3)

Caso concreto: `capa3_informacion_publica.mmd`

---

## Fuentes consultadas y orden

### 1. `GUIA_DIAGRAMAS_ESFTT.md`
Primera lectura obligatoria. Aporta:
- Estructura en capas (Capa 0-3) y qué debe contener cada una.
  Capa 3 = ficha de fase: trámites, tareas, condiciones del motor.
- Convención de color:
  - Amarillo → Administración (terminales, decisiones)
  - Verde → Titular (traslados y esperas del titular)
  - Morado → Organismo/externo (traslados y esperas del organismo)
- Principio de contenido mínimo: no incluir plazos en días ni referencias
  a artículos concretos. Solo estructura.
- Herramienta: Mermaid con `mmdc` para render a SVG.

### 2. `GUIA_GENERAL.md`
Aporta el modelo mental de la tramitación:
- EXPEDIENTE → SOLICITUD → FASE → TRAMITE → TAREA
- Concepto de fase: contenedor de trámites para obtener un requisito.
- Cierre de fase: manual por el usuario (resultado del catálogo).
- La fase solo puede cerrarse cuando todos sus trámites están cerrados.

### 3. `DISEÑO_MOTOR_REGLAS.md`
Aporta las condiciones del motor para INFORMACION_PUBLICA:
- INICIAR: `EXISTS DR_NO_DUP AND ia NOT IN {AAU, AAUS}` → BLOQUEAR
- FINALIZAR (universal): EXISTS trámite sin finalizar (`not tramite.finalizado`: tareas con tipo documental sin `documento_producido_id`) → BLOQUEAR
- Vocabulario de eventos: CREAR, INICIAR, FINALIZAR, BORRAR.
- Principio rector: todo permitido excepto lo prohibido. El motor no
  conduce el flujo — responde a preguntas del usuario.

### 4. `ESTRUCTURA_FTT.json` (sección PATRONES_FLUJO)
Aporta los patrones base: A, B, C, D, E, F con sus secuencias de tareas.
Detectado: los patrones compuestos (C+, EC, AB, C+E+F) no están
formalizados como entradas propias — se describen solo en prosa
en los trámites que los usan.

### 5. `ESTRUCTURA_FTT.json` (sección FASES > INFORMACION_PUBLICA)
Aporta los 7 trámites de la fase con:
- Código y nombre de cada trámite
- `tareas_indicativas`: secuencia de tareas del trámite
- `patron`: referencia al patrón base o combinación
- `nota`: aclaraciones sobre el flujo real (especialmente el doble
  ESPERAR_PLAZO de BOE/BOP/PRENSA, v5.2)

---

## Decisiones de diseño tomadas

### Estructura del diagrama
- Nodo de entrada (INICIO FASE) → motor INICIAR → fork a trámites
- Trámites agrupados en dos subgrafos: PUBLICACIONES y GESTIÓN ALEGACIONES
- Todos los trámites convergen en motor FINALIZAR → nodo de salida

### Colores aplicados
- Amarillo: INI, BLQ, PEND, FIN (terminales administrativos)
- Morado: NOTIFICAR y ESPERAR para BOE/BOP/Prensa/Ayuntamientos
  (la pelota está en el organismo/boletín externo)
- Verde: NOTIFICAR Titular y ESPERAR respuesta Titular en RECEPCION_ALEGACION
- Naranja claro (esp): ESPERAR plazo de alegaciones (plazo público)
- Sin color (defecto): tareas de Administración (REDACTAR, FIRMAR, ANALIZAR,
  PUBLICAR, INCORPORAR)

### Tramites paralelos
Mermaid no soporta gateways paralelos BPMN. Se representan como
ramas independientes que parten del mismo nodo motor INICIAR y
convergen en el motor FINALIZAR. El hecho de que sean paralelos
queda implícito en la agrupación y en los títulos de subgrafo.

### RECEPCION_ALEGACION (repetible)
Se representa como un único subgrafo con un back-edge
`ESPERAR resp. Titular →|nueva alegacion| INCORPORAR aleg.`
La nota "repetible por alegación" en el título indica que en la
práctica se crea un trámite por alegación.

### Imprecisión conocida del diagrama
Los nodos TRAMITE PENDIENTE y FASE CERRADA del motor FINALIZAR
se representan como terminales, pero en la realidad:
- TRAMITE PENDIENTE es un estado temporal resoluble (el usuario
  cierra el trámite y reintenta)
- FASE CERRADA no es automática: el motor da paso libre y el usuario
  registra el resultado manualmente
Mermaid no permite modelar este matiz sin complejidad excesiva.

---

## Gaps detectados que no se pueden resolver solo con las fuentes

1. **DR_NO_DUP**: código referenciado en el motor pero no definido
   en ningún MD ni en el JSON. Semántica desconocida.
2. **Patrones C+, EC, AB, C+E+F**: usados pero no formalizados
   en PATRONES_FLUJO del JSON.
3. **Paralelismo real entre trámites**: el JSON no especifica
   explícitamente cuáles son paralelos y cuáles secuenciales
   dentro de la fase. Se asume paralelismo total por el principio
   "todo permitido excepto lo prohibido".
