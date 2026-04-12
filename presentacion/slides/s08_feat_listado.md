# S08 — Listado inteligente y control

## Metadatos

- **Layout:** Contenido img dcha
- **Fragments:** Sí — cada bullet se revela con un clic
- **Artefacto visual:** Captura del listado de expedientes con pistas de estado visibles

---

## Contenido visible

**Número de sección:** 8

**Título** *(extrabold negro):*
> El estado de todos los expedientes, de un vistazo

**Subtítulo** *(bold verde):*
> Sin abrir ninguno

**Bullets** *(italic gris, se revelan uno a uno):*

1. Cada fila es una solicitud en tramitación. Cada columna es una pista del procedimiento: Análisis, Consultas, Medio Ambiente, Información Pública, Resolución

2. El estado de cada pista se calcula automáticamente del árbol del expediente — el listado siempre refleja la realidad sin que nadie lo actualice a mano

3. Los colores dicen qué toca: rojo = hay que actuar, amarillo = en firma, azul = esperando respuesta externa, verde = terminado

   - 3.1 *(fragment)* Si hay varios elementos en el mismo estado, el sistema los cuenta: *`TRAMITAR (3)`* — cuántas cosas esperan en esa pista

4. *(fragment)* El tramitador filtra por estado y trabaja por lotes — todos los que hay que firmar hoy, todos los que están esperando respuesta de organismos...

5. *(fragment)* La jefatura ve el estado global de todos los expedientes y de todos los tramitadores — sin preguntar, sin esperar informe

   - 5.1 *(fragment)* 🚧 *Pendiente de implementar*

6. *(fragment)* Los administrativos disponen de una vista propia con todos los expedientes y solicitudes: fechas y plazos de información pública, respuestas de titulares y organismos. Pueden acceder directamente a la tarea concreta — publicación, subsanación, consulta — sin pasar por el expediente completo

   - 6.1 *(fragment)* 🚧 *Pendiente de implementar*

---

## Artefacto visual

🎨 *Captura: listado de expedientes con varias filas y las columnas de pistas visibles.*

*Debe mostrar:*
- *Al menos 4-5 filas con solicitudes en distintos estados*
- *Las columnas de pistas (ANÁLISIS, CONSULTAS, MA, IP, RESOLUCIÓN) con colores*
- *Al menos un contador visible (ej. `TRAMITAR (2)`)*
- *Sin datos sensibles de personas reales*

*Ruta a definir: `presentacion/assets/cap_listado.png`*

---

## Notas ponente

Esta slide cierra el bloque de características. El tono es de síntesis — "todo lo que hemos visto hasta ahora se resume aquí".

Bullet 1: aclarar que la unidad es la solicitud, no el expediente — un mismo número AT puede tener varias filas si hay varias solicitudes activas simultáneamente. La audiencia lo reconocerá.

Bullet 2: este es el argumento de la disciplina de datos de S02.1 hecho realidad. Si los datos se rellenan bien, este listado es fiable. Si no, no lo es. No hace falta decirlo explícitamente — la conexión es obvia.

Bullet 3 + 3.1: señalar los colores en la captura mientras se habla. El contador es especialmente útil para detectar cuellos de botella — si una pista tiene `TRAMITAR (5)`, hay acumulación ahí.

Bullet 4: el trabajo por lotes es el cambio de flujo más práctico para el tramitador. En lugar de ir expediente a expediente, se agrupa por estado y se barre de una vez.

Bullet 5: este bullet es para la jefatura. Decirlo mirando a quien corresponda. "Sin preguntar, sin esperar informe" es el mensaje — la visibilidad es inmediata y objetiva.

Transición a S09 (portadilla demo): "Y ahora os lo enseñamos en vivo."
