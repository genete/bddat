# S07 — Generación de escritos

## Metadatos

- **Layout:** Contenido img dcha
- **Fragments:** Sí — cada bullet y sub-bullet se revela con un clic
- **Artefacto visual:** Captura del flujo de generación de escrito desde una tarea REDACTAR

---

## Contenido visible

**Número de sección:** 7

**Título** *(extrabold negro):*
> El borrador, sin copiar y pegar

**Subtítulo** *(bold verde):*
> Plantillas que ya conocen el expediente

**Bullets** *(italic gris, se revelan uno a uno):*

1. En una tarea REDACTAR, el sistema propone las plantillas disponibles para ese contexto — tipo de solicitud, fase y trámite — y genera el borrador con los datos del expediente ya rellenos

   - 1.1 *(fragment)* Si hay campos vacíos en el expediente, el sistema avisa antes de generar — no aparecen huecos en el documento

2. *(fragment)* El documento se guarda con nombre sistematizado y queda registrado en el pool del expediente, vinculado a la tarea que lo originó

3. *(fragment)* El documento lleva embebido un código estructurado de trazabilidad, visible en el pie de página — cuando vuelve firmado al pool, el sistema lo clasifica automáticamente sin intervención manual

   - 3.1 *(fragment)* El código es legible por el tramitador: confirma visualmente que el sistema lo ha identificado correctamente. *Ejemplo: `BDDAT | AT-13465-24 | AAP | RESOLUCIÓN | ELABORACIÓN | Favorable`*

4. *(fragment)* Las plantillas las gestiona el supervisor: se adaptan cuando cambia un modelo oficial sin tocar el código de la aplicación

5. *(fragment)* Las plantillas admiten campos simples, campos calculados, tablas dinámicas, fragmentos de texto y condiciones — todo en función de los datos reales del expediente

   - 5.1 *(fragment)* **Campo simple** — *Ejemplo: `{{expediente.numero_at}}` → `AT-13465-24`*
   - 5.2 *(fragment)* **Campo calculado / consulta** — *Ejemplo: tabla de municipios afectados generada automáticamente desde la base de datos*
   - 5.3 *(fragment)* **Fragmento condicional** — *Ejemplo: párrafo de resolución favorable o desfavorable según el resultado de la fase*

6. *(fragment)* El documento generado es un `.docx` editable en LibreOffice Writer — si la situación lo requiere, el tramitador puede ajustarlo de forma autónoma antes de firmarlo

---

## Artefacto visual

🎨 *Captura: pantalla de generación de escrito desde una tarea REDACTAR.*

*Debe mostrar idealmente:*
- *Selector de plantilla filtrado por contexto (tipo solicitud / fase / trámite)*
- *Preview de campos del expediente a insertar*
- *Botón "Generar escrito"*

*Nota: la funcionalidad está implementada (rutas `api_escritos`, UI en `tramitacion_bc_tarea.html`, panel de admin en `admin_plantillas/`). No hay plantillas de producción todavía — solo plantillas de prueba. La captura se puede tomar con una plantilla de prueba real.*

*Ruta a definir: `presentacion/assets/cap_escritos.png`*

---

## Notas ponente

Esta es una de las características más valoradas — darle tiempo y dejarlo respirar.

Bullet 1: el mensaje central es que no hay que abrir el escrito anterior, cambiar el número de AT y rezar. El sistema pone los datos.
Sub-bullet 1.1: si la audiencia pregunta qué pasa si falta algo, la respuesta es que el sistema avisa — no se generan documentos con huecos en blanco.

Bullet 2: el documento generado entra ya clasificado y vinculado a su tarea — la trazabilidad funciona desde el origen.

Bullet 3 + 3.1: el código estructurado en el pie de página no es técnico ni confidencial — es la identidad del documento expresada de forma legible. El tramitador puede verificar que el sistema lo ha clasificado bien. Cuando ese documento regresa firmado al pool, el sistema lo lee y lo clasifica sin intervención manual.

Bullet 5 + sub-bullets: mostrar los ejemplos uno a uno. No apresurarse — esta es la parte que más impresiona a quien ha maquetado escritos a mano. Los fragmentos condicionales (5.3) son el argumento más potente: la plantilla ya sabe qué párrafo poner según el resultado.

Bullet 6: dejar claro que no es una caja negra. Si el tramitador necesita ajustar algo, abre el .docx en Writer y listo. La autonomía no desaparece.

Transición a S08: "Con todo esto en marcha, el listado de expedientes es donde se ve el estado de todo de un vistazo."
