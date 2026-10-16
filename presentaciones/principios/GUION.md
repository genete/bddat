# Guion — «Cómo funciona BDDAT» (borrador 1, en bruto)

> **Para qué.** Presentación larga para el personal técnico de la ADA, que va a dar
> cobertura a BDDAT. No explica la tecnología (eso es `../fundamentos/`), sino **los
> principios de funcionamiento**: por qué BDDAT está hecho como está.
>
> **Formato previsto.** El de `../fundamentos/`: fichas HTML autónomas de 1280×720,
> compiladas en un `index.html`, una sola línea de avance y pequeñas animaciones por
> pasos (`data-paso`) que construyen cada concepto.
>
> **Cómo leer este guion.** Cada ficha lleva su **idea fuerza**, lo que se cuenta, una
> **animación** propuesta y la **fuente** donde está decidido. Las fichas marcadas
> **[Carlos]** son los puntos que pediste, con tu título; las marcadas **[propuesta]** las
> añado yo para depurar. Material reutilizable: las fichas de
> `../estado_oct_2026/` y las capturas de `traspaso_pc_trabajo/capturas_presentacion_ADA/`.

---

## 0. Portada

BDDAT · Cómo funciona. Principios de funcionamiento del sistema de tramitación de
expedientes de alta tensión.

---

## 1. Tramitación de expedientes de autorización de alta tensión — [Carlos]

**Idea fuerza:** el problema que resuelve BDDAT es un procedimiento largo, con muchos
actores, plazos legales y caminos que se ramifican.

- Un expediente es siempre un **proyecto** de instalación (línea, centro de
  transformación, subestación…) cuyo titular pide uno o varios actos: AAP, AAC, DUP…
- Intervienen el **titular** (a veces representado), los **organismos** consultados,
  ayuntamientos, boletines (BOE, BOP)…
- El procedimiento tiene **fases** (análisis documental, consultas, información
  pública, resolución…), algunas en paralelo, con **iteraciones** (subsanaciones,
  traslados) y **cambios de proyecto** a mitad (reformados).
- Todo con **plazos legales** que corren, se suspenden y vencen con efectos.
- Hoy se lleva con hojas de cálculo y una base Access.

**Animación:** una línea de tiempo del procedimiento que, paso a paso, se ramifica
(fases en paralelo, una subsanación que vuelve atrás, un reformado que la duplica).

**Fuente:** ficha 5 de `estado_oct_2026`; `ficha_bddat_borrador.md` §1; los
expedientes-tipo de `scripts/expedientes_dummy/`.

---

## 2. Flujo de procedimiento rígido vs. total libertad — [Carlos]

**Idea fuerza:** BDDAT no es ni un workflow rígido ni una carpeta libre; está en un
punto intermedio.

- **Flujo rígido** (tipo BPM): el sistema impone el siguiente paso. Lo imprevisto
  (alegación fuera de plazo, cambio de rumbo, un organismo que no contesta) no cabe, y
  el tramitador acaba trabajando fuera del sistema.
- **Libertad total** (carpeta, hoja de cálculo): todo cabe, pero nada se controla ni
  se calcula; el estado depende de que alguien lo apunte.
- **BDDAT:** la estructura legal del procedimiento **guía**, el tramitador tiene la
  **iniciativa**, el sistema **prohíbe** solo lo que no debe pasar y siempre deja una
  **salida justificada**.

**Animación:** un eje con los dos polos; ejemplos que caen en cada extremo; el punto
de BDDAT se coloca en medio y se le añaden sus tres piezas (estructura, prohibiciones,
escape).

**Fuente:** ficha 1 de `estado_oct_2026` (motor configurable con escape, validación
no obstructiva); `docs/historial/DISEÑO_MOTOR_REGLAS.md` (principio de escape).

---

## 3. Todo vale mientras no esté prohibido — [Carlos]

**Idea fuerza:** el sistema no describe los caminos permitidos; describe lo prohibido
en cada momento.

- Principio del motor: **«todo permitido salvo lo expresamente prohibido»** (lista
  negra, no lista blanca).
- El motor no genera el flujo: responde a una sola pregunta, **«¿está esto prohibido
  ahora, en estas circunstancias?»**.
- Consecuencia práctica: no hay que modelar todos los caminos posibles del
  procedimiento (imposible), solo los que la norma veda.
- Por eso se eliminaron las listas blancas de combinaciones de la estructura.

**Animación:** un mapa con muchos caminos abiertos; aparecen unas pocas barreras; el
resto sigue libre.

**Fuente:** `DISEÑO_MOTOR_REGLAS.md` §Principio rector; ADR-007 (eliminar whitelists
ESFT); `INVENTARIO_BACKEND.md` §3.1.

---

## 4. El documento como núcleo del dato. Concepto de expediente — [Carlos]

**Idea fuerza:** el expediente **es** el conjunto de sus documentos; el estado y las
fechas salen de ellos.

- Las fechas son **del documento** (fecha administrativa, la que cuenta legalmente,
  no la del fichero). La estructura no guarda fechas.
- El **estado se deriva**: lo que toca hacer sale de los documentos que hay y de dónde
  están vinculados; nadie lo actualiza a mano.
- Las **tareas consumen y producen documentos** (consumido N, producido 1): se sabe
  qué borrador produjo qué resolución firmada.
- **Expediente = documentos vinculados.** Un documento sin vincular no forma parte del
  expediente (es un «huérfano» del pool).

**Animación:** documentos que llegan sueltos; al vincularse a tareas se encienden las
fechas y cambia el color del estado.

**Fuente:** ADR-002 (ESFTT sin fechas), ADR-010 (documento-tarea N:M), ADR-027
(pertenencia documental); fichas 5 y 7 de `estado_oct_2026`; `ficha_bddat_borrador.md`
§4.

---

## 5. Expediente / Solicitud / Fase / Trámite / Tarea. Semántica en los tipos — [Carlos]

**Idea fuerza:** cinco niveles fijos; lo que distingue un procedimiento de otro está
en los **tipos**, no en añadir campos.

- Estructura **ESFTT**: Expediente → Solicitud → Fase → Trámite → Tarea. *(Tu punto
  decía «Expediente/Solicitud/trámites/tareas»; añado **Fase**, que es nivel propio en el
  modelo.)*
- **Minimalismo estructural:** la semántica vive en los tipos (tipo de expediente, de
  solicitud, de fase, de trámite), configurables como catálogo.
- Solo **cuatro tareas**: ANALIZAR, ELABORAR, NOTIFICAR y ESPERAR PLAZO (eran siete).
- Varias fases pueden avanzar **en paralelo**.

**Animación:** el árbol crece nivel a nivel; luego las siete tareas antiguas se
funden en cuatro (ficha 5b de octubre).

**Fuente:** ficha 1 (minimalismo), 5 y 5b de `estado_oct_2026`; ADR-003, ADR-004,
ADR-037 (vocabulario ESFTT vs. permiso del motor). Captura: árbol de AT-3.

---

## 6. Prohibiciones: Normas → Contexto de tramitación → Reglas → Prohibiciones → Escape — [Carlos]

**Idea fuerza:** cada prohibición se puede rastrear hasta la norma que la justifica,
y siempre tiene salida justificada.

- **Normas:** catálogo de normas y sus variables; la vigencia es de la regla, no de
  la variable.
- **Contexto de tramitación:** dónde estoy (el sujeto ESFTT, p. ej.
  `Distribución/AAP/RESOLUCIÓN`) y qué es cierto ahora (variables: datos del proyecto,
  calculadas del árbol y de plazos).
- **Reglas:** condiciones que, si se cumplen y ninguna excepción las neutraliza,
  disparan.
- **Prohibición:** bloquear o advertir, citando la norma.
- **Escape:** el tramitador puede seguir justificándolo; queda en la bitácora.
- **Tres modos del motor:** inactivo, avisa, bloquea (despliegue progresivo: los
  usuarios aprenden el sistema antes de que el sistema los controle).

**Animación:** cinco cajas en cadena; una acción del tramitador entra por la
izquierda y se ilumina caja a caja hasta la decisión; luego la misma acción sale
por la puerta del escape con su justificación.

**Fuente:** ficha 1 de `estado_oct_2026`; ADR-001 (motor agnóstico), ADR-026
(vigencia de la regla); `INVENTARIO_BACKEND.md` §3.1–3.4.

---

## 7. Invariantes estructurales — [Carlos]

**Idea fuerza:** el motor cubre la **norma**, que cambia; los invariantes protegen la
**integridad** de BDDAT, que no cambia.

- Son reglas fijas en el código, previas al motor.
- Ejemplos: no borrar lo que tiene hijos; no borrar una tarea con documentos; una
  fase cerrada queda **sellada** (reabrirla es un acto propio); toda notificación
  tiene destinatario.
- En general **tienen escape**; los que no: la **evidencia irreversible** (lo ya
  notificado al exterior). Eso se arregla con actos posteriores, no deshaciendo.
- Tres sitios para una salvaguarda: invariante (fijo), regla del motor (modelo
  legal) o dato de catálogo.

**Animación:** dos tipos de barrera: las del motor, móviles y con su norma colgada;
los invariantes, fijos; uno de ellos sin puerta (lo notificado).

**Fuente:** ficha 1 de `estado_oct_2026` (nuevo: invariantes); ADR-036 (sellado de
fase cerrada), ADR-051 §E; `INVENTARIO_BACKEND.md` §3.5.

---

## 8. Entidades — [Carlos]

**Idea fuerza:** una sola tabla de entidades; el papel que hace cada una depende del
trámite.

- Una organización puede ser titular en un expediente y organismo consultado en
  otro: una tabla con **roles** (titular, consultado, publicador), no una tabla por tipo.
- **Representación:** una entidad puede actuar en nombre de otra.
- **Direcciones de notificación por rol:** la misma empresa recibe en tramitaciones
  como titular y en su área técnica como consultada.
- Al solicitante se le notifica en la sede que indicó en su solicitud.

**Animación:** una misma organización que se pone distintos «sombreros» según el
trámite y cambia de buzón.

**Fuente:** ficha 6 de `estado_oct_2026`. Captura: buscador con «Jerez».

---

## Temas añadidos — [propuesta, a depurar]

### 9. Una sola fuente de la verdad y datos separados de reglas

Cada dato existe en un único lugar; las tablas guardan hechos y las reglas viven
aparte, como registros. Cambiar el comportamiento es cambiar registros, no código.
*Posible ficha de apertura o de cierre que agrupe los principios.* — Fuente: ficha 1.

### 10. Las cuatro tareas y su ciclo de vida

ANALIZAR produce un **diagnóstico** (con su checklist de requisitos documentales);
ELABORAR genera el escrito; NOTIFICAR lo hace llegar y se cierra con su justificante;
ESPERAR PLAZO vigila el tiempo. — Fuente: ADR-005, ADR-033, ADR-034.

### 11. Plazos

Catálogo **editable**: a qué se aplica, desde qué documento se cuenta, qué documento
acredita el cumplimiento y qué pasa si vence (silencio, caducidad…). Días hábiles y
suspensiones como una sola medida. El plazo de resolver de cada acto se ve en la
solicitud. — Fuente: ADR-041, ADR-048; catálogo de plazos y efectos (capturas de
gestión). *Animación:* un reloj que se para con la suspensión y se reanuda.

### 12. Notificaciones

Toda notificación tiene destinatario; el **canal no se elige**: se deduce del
justificante vinculado; fechas de notificación, de cumplimiento y de efectos;
notificación edictal. — Fuente: ADR-049, ADR-051, ADR-052, ADR-034.

### 13. Organismos consultados

Cada organismo es un sub-proceso dentro de la fase (separata, respuesta, traslado al
titular, silencio), con número variable de organismos. — Fuente: ADR-011, ADR-042;
expediente-tipo `CONSULTAS_VARIOS_ESTADOS`.

### 14. Reformados de proyecto

La **versión del proyecto** es el eje: un reformado corta las fases y estas se repiten
para la nueva versión, sin perder la historia. — Fuente: ADR-044; captura del árbol
de AT-3.

### 15. Certificados: la acción que toca

Lo que toca hacer se materializa como **petición de un certificado** (cierre de
fase, fin de instrucción, cierre de solicitud). El de fin de instrucción audita todas
las reglas antes de resolver. — Fuente: ADR-043; ficha 5 de octubre.

### 16. Escritos y plantillas

Plantillas `.odt` elegidas por el contexto ESFTT (con escape), rellenas con los datos
del expediente, con un código de trazabilidad en el pie. — Fuente: ADR-025, ADR-035;
fichas 8 y 8b de octubre.

### 17. Almacén documental

Los ficheros viven en un **almacén propio**, por contenido, al que los usuarios no
acceden directamente; cada expediente tiene un **manifiesto** que permite
reconstruir sus carpetas sin BDDAT. El pool ya no es una carpeta: son los documentos
sin vincular. — Fuente: ADR-050; ficha 7 de octubre.

### 18. Roles, vistas y trazabilidad

Cuatro roles con mínimo privilegio; cada rol tiene su «Mi trabajo»; patrón único
listado → inspector; el seguimiento se pinta solo desde el árbol (colores = qué toca);
bitácora de toda acción y de todo escape. — Fuente: ADR-012, ADR-013, ADR-023,
ADR-053; fichas 3, 4b y 9 de octubre. Capturas de la presentación de hoy.

### 19. Límites y camino a producción

Lo que no hace (portafirmas, Notifica) y lo que falta antes de producción (resto de
fases, importación de Access, ENS). Útil para que la ADA sepa qué asume. — Fuente:
fichas 2, 10, 11 y 12 de octubre; `ficha_bddat_borrador.md` §6–7.

### 20. Cierre

Los principios en una frase cada uno (recapitulación de 2 a 9).

---

## Para decidir

1. **Orden:** ¿se intercalan los temas añadidos en la línea (p. ej. 10 tras 5, 11–13
   tras 7, 14–15 tras 4) o van todos detrás de tus ocho puntos?
2. **Estado y límites (19):** ¿entran en esta presentación o se quedan en la de
   octubre?
3. **Capturas reales:** ¿se usan las de hoy dentro de las fichas, o solo esquemas
   animados?
4. **Nivel jurídico de la ficha 1:** ¿con referencias a la norma (RD 1955/2000…) o
   solo el proceso?
