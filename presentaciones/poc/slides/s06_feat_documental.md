# S06 — Sistema documental

## Metadatos

- **Layout:** Contenido img dcha
- **Fragments:** Sí — cada bullet se revela con un clic
- **Artefacto visual:** Captura del gestor de documentos de un expediente

---

## Contenido visible

**Número de sección:** 6

**Título** *(extrabold negro):*
> Todos los documentos, en su sitio

**Subtítulo** *(bold verde):*
> Un pool único por expediente, ligado al procedimiento

**Bullets** *(italic gris, se revelan uno a uno):*

1. Todos los documentos de un expediente enlazados a su número de AT. BDDAT sabe la ruta donde se guarda cada documento en el servidor de archivos.

   - 1.1 *(fragment)* Se puede localizar de inmediato para ver o editar.

2. Cada documento tiene una fecha administrativa — la que cuenta legalmente, no la del archivo en disco

3. Los documentos se vinculan a las tareas que los generan o consumen: el sistema sabe qué borrador produjo qué resolución firmada

   - 3.1 *(fragment)* 🎨 *Tabla inline: consumo y producción de documentos por tipo de tarea atómica.*
     | Tarea | Consume | Produce |
     |-------|---------|---------|
     | REDACTAR | Informe/nota *(opcional)* | Borrador |
     | ANALIZAR | Documento a analizar | Informe / nota interior |
     | FIRMAR | Borrador | Documento firmado |
     | NOTIFICAR | Documento firmado | Justificante de notificación |
     | PUBLICAR | Documento firmado | Justificante de publicación |
     | INCORPORAR | — | Documentos externos registrados en el pool *(entrada N:M)* |
     | ESPERAR PLAZO | — | — |

4. El administrativo puede cargar documentos al pool pendiente y marcarlos como prioritarios — el tramitador los incorpora al flujo cuando toca

---

## Artefacto visual

🎨 *Captura: vista del gestor de documentos de un expediente con varios documentos listados.*

*Debe mostrar:*
- *Lista de documentos con nombre, tipo, fecha administrativa y estado (prioritario / normal)*
- *Al menos un documento prioritario visible (badge o indicador de prioridad)*
- *Sin datos sensibles de personas reales*

*Ruta a definir cuando se tome la captura: `presentacion/assets/cap_documental.png`*

---

## Notas ponente

Bullet 1: el mensaje es de localización, no de reconstrucción de estado (eso lo hace el ESFTT). BDDAT mantiene el vínculo entre el número AT y la ruta física en el servidor — el tramitador no tiene que buscar carpetas manualmente. El sub-bullet 1.1 remata con el beneficio práctico inmediato.

Bullet 2: la fecha administrativa es un concepto que la audiencia conoce bien. El sistema la distingue de la fecha del fichero porque lo que importa es cuándo tiene efectos, no cuándo se guardó. No insistir demasiado — la audiencia lo entenderá enseguida.

Bullet 3: conectar con S05 sin decir "como visteis antes". Basta con "el sistema sabe de dónde viene cada documento y qué tareas lo han usado". Esto es lo que permite trazabilidad real.

Bullet 4: el rol del administrativo aparece aquí de forma natural. Recordar que está en la sala — es un caso de uso que les afecta directamente. La prioridad les da visibilidad antes de que el tramitador revise.

Transición a S07: "Y si el documento hay que redactarlo desde cero, el sistema también ayuda."
