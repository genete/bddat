# Guion — «Cómo funciona BDDAT» (borrador 2)

> **Para qué.** Presentación para el personal técnico de la ADA sobre los principios de
> funcionamiento de BDDAT. La tecnología queda en `../fundamentos/`.
>
> **Formato.** El de `../fundamentos/`: fichas HTML de 1280×720 en una sola línea, con
> esquemas animados por pasos. Cada ficha lleva un título y pocas frases: el resto lo
> cuenta Carlos.
>
> **Cómo leer cada ficha de este guion.**
> - **En pantalla:** lo único que se escribe en la ficha.
> - **Notas:** apoyo para hablar; no van en la ficha.
> - **Animación:** la define Carlos al hacer la ficha.
> - **Estado (interno):** cómo está en el código; no se muestra.
> - **[Carlos]** = punto pedido por Carlos; **[propuesta]** = añadido, a depurar.
>
> El orden se va ajustando ficha a ficha.

---

## 0. Portada

**En pantalla:** BDDAT · Cómo funciona

---

## 1. El procedimiento de autorización de instalaciones eléctricas — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_01_procedimiento.html`

**En pantalla:** una nube de conceptos, unos más grandes que otros, que da impresión de
complejidad. Principales en recuadro, secundarios en píldora. Los solapes son parte del
juego.

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | **Normativa** · RD 1955/2000 · LSE · RD 337/2014 · RD 223/2008 · decretos de simplificación · medidas urgentes |
| 3 | **Promotor** |
| 4 | **Distribuidora** |
| 5 | **Información pública** |
| 6 | **Organismos** |
| 7 | **Solicitudes** · AAP · AAC · DUP · AE · AAT · Modificación · Cierre · … |
| 8 | **Proyecto** · distribución · transporte · renovables |
| 9 | **Documentación** |
| 10 | **Recursos** |
| 11 | **Plazos** |
| 12 | **Excepciones** · suelo urbano · tensión |
| 13 | **Figura ambiental** · AAU · Licencia ambiental |
| 14–17 | Cuatro tandas de flechas curvas rotuladas que relacionan unos con otros (no pretenden ser exactas): requerimiento, requisitos, exime, separata, condicionados, espera de plazo, notificación, alegaciones, anuncio, informe, plazo, resolución, sin IP, exenta… Azul lo que va, verde lo que vuelve, morado lo que es tiempo |

**Notas:** Carlos narra cada concepto al aparecer.

**Estado (interno):** —

---

## 2. Flujo rígido frente a libertad total — [Carlos] ✔ hecha

**Fichero:** `fichas/ficha_02_rigido_libre.html`

| Paso | Aparece |
|---|---|
| 1 | Título |
| 2 | Izquierda, **Flujo rígido** («el sistema decide el siguiente paso»): Solicitud → Requerimiento → Información pública → Consultas → Resolución → Recursos, en cascada vertical con flechas |
| 3 | Derecha, **Libertad total** («todo cabe, nada se controla»): los mismos seis elementos sin conexión, equidistantes en círculo y en otro orden |
| 4 | En medio, **BDDAT** · «se sitúa en un punto intermedio» |

**Notas:** en el flujo rígido lo imprevisto no cabe y el tramitador acaba trabajando
fuera; en la libertad total el estado depende de que alguien lo apunte. En BDDAT la
estructura legal guía, el tramitador tiene la iniciativa, el sistema prohíbe lo que no
debe pasar y siempre hay salida justificada.

**Fuente:** ficha 1 de octubre; `docs/historial/DISEÑO_MOTOR_REGLAS.md` §Principio de escape.

**Estado (interno):** hecho.

---

## 3. Todo vale mientras no esté prohibido — [Carlos]

**En pantalla:**
- ¿Está esto prohibido ahora?

**Notas:** lista negra, no lista blanca. El motor no genera el flujo: solo responde a esa
pregunta. No hay que modelar todos los caminos, solo los que la norma veda. Por eso se
quitaron las listas blancas de combinaciones de la estructura.

**Fuente:** `DISEÑO_MOTOR_REGLAS.md` §Principio rector; ADR-007.

**Estado (interno):** hecho.

---

## 4. El documento, núcleo del dato. El expediente — [Carlos]

**En pantalla:**
- Las fechas son del documento
- El estado se deriva
- Expediente = documentos vinculados

**Notas:** fecha administrativa, la que cuenta legalmente, no la del fichero; la
estructura no guarda fechas; nadie actualiza el estado a mano. Un documento sin
vincular no es del expediente (huérfano del pool).

**Fuente:** ADR-002, ADR-027; fichas 5 y 7 de octubre.

**Estado (interno):** hecho.

---

## 5. Expediente · Solicitud · Fase · Trámite · Tarea — [Carlos]

**En pantalla:**
- Cinco niveles fijos
- La semántica vive en los tipos

**Notas:** el punto pedido decía «Expediente/Solicitud/trámites/tareas»; la **Fase**
es nivel propio en el modelo. Los tipos (de expediente, solicitud, fase, trámite) son
catálogo. Fases en paralelo.

**Fuente:** fichas 1 y 5 de octubre; ADR-037; `docs/referencia/ESTRUCTURA_FTT.md`.

**Estado (interno):** hecho; la tabla de trámites por fase existe pero aún no se edita
desde la interfaz.

---

## 6. Cuatro tareas — [propuesta]

**En pantalla:**
- ANALIZAR · ELABORAR · NOTIFICAR · ESPERAR PLAZO

**Notas:** eran siete: REDACTAR y FIRMAR se funden en ELABORAR; PUBLICAR es una
NOTIFICAR; INCORPORAR desaparece porque incorporar es vincular un documento. ANALIZAR
siempre produce un diagnóstico.

**Fuente:** `ESTRUCTURA_FTT.md` §Tareas atómicas; ADR-003, ADR-004, ADR-005; ficha 5b
de octubre.

**Estado (interno):** hecho.

---

## 7. Las tareas se encadenan por documentos — [propuesta]

**En pantalla:**
- Cada tarea consume documentos y produce uno
- Lo que produce una lo consume la siguiente

**Notas:** ANALIZAR → diagnóstico → ELABORAR → escrito → NOTIFICAR → justificante →
ESPERAR PLAZO → documento recibido → ANALIZAR. Patrones combinables: A (analizar),
B (elaborar y notificar), C (con espera), F (espera pasiva). Toda espera que pueda
recibir documentación de terceros exige un ANALIZAR después.

**Fuente:** `ESTRUCTURA_FTT.md` §Tareas atómicas y §Patrones de flujo; ADR-010.

**Estado (interno):** hecho.

---

## 8. Entidades — [Carlos]

**En pantalla:**
- Una sola tabla
- El papel depende del trámite

**Notas:** titular en un expediente, organismo consultado en otro: roles, no una tabla
por tipo, para no duplicar datos (una sola fuente de la verdad). Representación.
Direcciones de notificación por rol. Al solicitante, la sede de su solicitud.

**Fuente:** fichas 1 y 6 de octubre.

**Estado (interno):** hecho; el tipo de titular aún solo sirve para filtrar.

---

## 9. Normas → Contexto → Reglas → Prohibición → Escape — [Carlos]

**En pantalla:**
- Normas
- Contexto de tramitación
- Reglas
- Prohibición
- Escape

**Notas:** las reglas son registros, no código, y citan su norma; la vigencia es de la
regla. Contexto: dónde estoy en la estructura y qué es cierto ahora (datos del
proyecto, calculados, plazos). Regla con excepciones. Prohibición: bloquear o advertir.
Escape: seguir justificándolo, queda en la bitácora. Tres modos del motor: inactivo,
avisa, bloquea.

**Fuente:** ficha 1 de octubre; ADR-001, ADR-026; `docs/diseño/INVENTARIO_BACKEND.md` §3.

**Estado (interno):** hecho.

---

## 10. Invariantes estructurales — [Carlos]

**En pantalla:**
- La norma cambia: reglas
- La estructura no: invariantes
- Lo notificado no se deshace

**Notas:** fijos en el código y previos al motor. No borrar lo que tiene hijos ni una
tarea con documentos; fase cerrada sellada (reabrir es un acto propio); toda
notificación tiene destinatario. Casi todos tienen escape; lo ya notificado al exterior
no: se corrige con actos posteriores.

**Fuente:** ficha 1 de octubre; ADR-036, ADR-051 §E; `INVENTARIO_BACKEND.md` §3.5.

**Estado (interno):** hecho.

---

## 11. Certificados: lo que toca hacer — [propuesta]

**En pantalla:**
- Cierre de fase · Fin de instrucción · Cierre de solicitud

**Notas:** la acción siguiente se presenta como petición de un certificado. El de fin
de instrucción revisa todas las reglas antes de resolver.

**Fuente:** ADR-043; ficha 5 de octubre.

**Estado (interno):** hecho.

---

## 12. Plazos — [propuesta]

**En pantalla:**
- Catálogo editable
- Días hábiles y suspensiones
- Efecto del vencimiento

**Notas:** cada plazo dice a qué se aplica, desde qué documento se cuenta, qué
documento acredita el cumplimiento y qué pasa si vence (silencio, caducidad…).
Suspensión como medida única. Plazo de resolver de cada acto.

**Fuente:** ADR-041, ADR-048.

**Estado (interno):** hecho; pendiente mostrar el plazo de resolver en el árbol y la
proyección de plazos.

---

## 13. Notificaciones — [propuesta]

**En pantalla:**
- Siempre a un destinatario
- El canal lo dice el justificante

**Notas:** el canal no se elige: se deduce del justificante vinculado. Fechas de
notificación, de cumplimiento y de efectos. Notificación edictal.

**Fuente:** ADR-034, ADR-049, ADR-051, ADR-052; `ESTRUCTURA_FTT.md` §Trámites transversales.

**Estado (interno):** modelo hecho; falta la interfaz de varios destinatarios (#929).

---

## 14. Organismos consultados — [propuesta]

**En pantalla:**
- Un sub-proceso por organismo

**Notas:** separata, respuesta, traslado al titular, silencio. Número variable de
organismos por fase.

**Fuente:** ADR-011, ADR-042; expediente-tipo `CONSULTAS_VARIOS_ESTADOS`.

**Estado (interno):** hecho (fase de consultas completa).

---

## 15. Reformados de proyecto — [propuesta]

**En pantalla:**
- La versión del proyecto es el eje

**Notas:** un reformado corta las fases, que se repiten para la nueva versión sin perder
la historia.

**Fuente:** ADR-044; expediente-tipo `REFORMADO_ANALISIS_Y_CONSULTAS`.

**Estado (interno):** hecho.

---

## 16. Escritos y plantillas — [propuesta]

**En pantalla:**
- La plantilla según el contexto
- Los datos salen del expediente

**Notas:** plantillas `.odt`, elegidas por la posición en la estructura (con escape),
con código de trazabilidad en el pie.

**Fuente:** ADR-025, ADR-035; fichas 8 y 8b de octubre.

**Estado (interno):** generación hecha; plantillas al almacén, edición y PDF para firma
pendientes.

---

## 17. Almacén documental — [propuesta]

**En pantalla:**
- Los ficheros, fuera de BDDAT
- Un manifiesto por expediente

**Notas:** almacén propio por contenido, sin acceso directo de los usuarios; el
manifiesto permite reconstruir las carpetas sin BDDAT. El pool son los documentos sin
vincular.

**Fuente:** ADR-050; ficha 7 de octubre.

**Estado (interno):** almacén hecho; ZIP del expediente, papelera y limpieza pendientes.

---

## 18. Roles, vistas y bitácora — [propuesta]

**En pantalla:**
- Cuatro roles, cada uno con su trabajo
- Listado → inspector
- Todo queda en la bitácora

**Notas:** tramitador, administrativo, supervisor, administrador; mínimo privilegio.
El seguimiento se calcula del árbol: el color dice qué toca. Bitácora de toda acción y
de todo escape.

**Fuente:** ADR-012, ADR-013, ADR-023, ADR-053; fichas 3, 4b y 9 de octubre.

**Estado (interno):** hecho; revisión de coherencia de la interfaz en curso (ADR-053).

---

## 19. Estado de desarrollo (una o dos fichas)

**En pantalla:** hecho · en curso · antes de producción · después de producción.

**Notas:** incluye los límites (portafirmas, Notifica). Se redacta al final, a partir de
los «Estado (interno)» de este guion y de las fichas 10 a 12 de octubre.
