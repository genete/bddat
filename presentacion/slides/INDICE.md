# Índice de slides — BDDAT Presentación

> Documento de planificación y referencia para el desarrollo de la presentación Reveal.js.
> Cada slide tiene su propio fichero MD en esta carpeta.
> El HTML final se genera a partir de estos MDs una vez consensuado el contenido.

---

## Plan de trabajo

**Fase 1 — Contenido (actual)**
Escribir los MDs de cada slide uno a uno. Cada MD define: texto visible, bullets,
descripción del artefacto visual y notas del ponente. Se puede insertar, fusionar
o eliminar slides en este paso sin coste.

**Fase 2 — Validación visual de layouts (antes del HTML final)**
Construir un `index.html` de prueba con el tema CSS JA y todos los layouts del
índice rellenos con contenido placeholder. Sin contenido real. Objetivo: confirmar
que cada layout se ve bien en pantalla antes de volcar el contenido definitivo.
Iterar hasta aprobar cada layout.

**Fase 3 — HTML final**
Traducir los MDs aprobados al `index.html` definitivo usando los layouts validados.

**Nota sobre fragments (bullets):**
Todos los bullets se revelan uno a uno con clic de ratón (`class="fragment"`).
Anotarlo en cada MD cuando aplique. Es el comportamiento por defecto en slides
marcadas con fragments: Sí.

---

## Convenciones

- **Layout**: tipo de plantilla visual JA a aplicar (ver sección de layouts al final)
- **Fragments**: elementos que se revelan uno a uno con cada avance del presentador
- **Artefacto visual**: diagrama Miro (iframe), captura de pantalla, tabla, icono u otro elemento no-texto
- **Notas ponente**: texto para la vista de presentador (tecla `S` en Reveal.js, solo visible para el presentador)

---

## Tabla de slides

| ID  | Fichero                   | Título                              | Layout              | Fragments | Artefacto visual            |
|-----|---------------------------|-------------------------------------|---------------------|-----------|-----------------------------|
| S00 | s00_portada.md            | BDDAT — Gestión de expedientes AT   | Portada JA          | No        | Chevron verde + logo JA     |
| S01 | s01_problema.md           | El problema                         | Contenido 1 col     | Sí        | —                           |
| S02 | s02_que_es.md             | Qué es BDDAT                        | Contenido 1 col     | Sí        | —                           |
| S02.1 | s02_1_limites.md        | Qué no hace (todavía) y qué requiere | Contenido 1 col    | Sí        | —                           |
| S03 | s03_roles.md              | Quién lo usa                        | Contenido tabla     | Sí        | Tabla de roles              |
| S04 | s04_feat_interfaz.md      | Identidad corporativa y diseño      | Contenido img dcha  | Sí        | Captura pantalla app        |
| S05 | s05_feat_esftt.md         | Tramitación estructurada            | Contenido + iframe  | Sí        | Diagrama Miro ESFTT         |
| S06 | s06_feat_documental.md    | Sistema documental                  | Contenido img dcha  | Sí        | Captura gestor documentos   |
| S07 | s07_feat_escritos.md      | Generación de escritos              | Contenido img dcha  | Sí        | Captura generación escrito  |
| S08 | s08_feat_listado.md       | Listado inteligente y control       | Contenido img dcha  | Sí        | Captura listado/dashboard   |
| S09 | s09_demo.md               | Demo en vivo                        | Portadilla interior | No        | —                           |
| S10 | s10_roadmap.md            | Lo que viene                        | Línea de tiempo     | Sí        | —                           |
| S11 | s11_feedback.md           | Lo que necesitamos de vosotros      | Contenido 1 col     | Sí        | —                           |
| S12 | s12_gracias.md            | Gracias                             | Portada JA          | No        | —                           |
| SA1 | sa1_arquitectura.md       | Arquitectura técnica *(apéndice)*   | Contenido 2 col     | No        | Diagrama Miro arquitectura  |
| SA2 | sa2_context.md            | ContextAssembler *(apéndice)*       | Contenido código    | No        | Ejemplo JSON real           |

---

## Notas de estructura

- **S04–S08** forman el bloque "características implementadas". Son el núcleo de venta del proyecto.
  Cada una sigue el mismo patrón: título de la característica → bullets revelados uno a uno → artefacto visual.
- **S09** es portadilla de transición pura. Sin bullets ni artefactos. Marca el paso a la demo en vivo.
- **S10** usa el layout de línea de tiempo JA con 3 columnas:
  `Disponible ya | Próxima fase (M2/M3) | Más adelante (M4/M5)`
- **SA1 y SA2** son apéndice: en Reveal.js llevarán `data-visibility="uncounted"`,
  no aparecen en el contador de páginas ni en la barra de progreso.
  Se accede a ellas solo si alguien pregunta por la arquitectura.

---

## Layouts JA disponibles

| Nombre            | Descripción                                                      | Slides que lo usan     |
|-------------------|------------------------------------------------------------------|------------------------|
| Portada JA        | Fondo blanco, chevron verde dcha, título bold negro, logo JA    | S00                    |
| Portadilla int.   | Igual que portada pero sin número ni pie de navegación          | S09                    |
| Contenido 1 col   | Barra top verde, sección+línea, título, subtítulo verde, body   | S01, S02, S11          |
| Contenido img dcha| Igual + imagen o captura ocupando mitad derecha                 | S04–S08                |
| Contenido tabla   | Igual + tabla con header verde sólido                           | S03                    |
| Línea de tiempo   | Igual + bloques numerados en verde, 3 columnas                  | S10                    |
| Contenido 2 col   | Igual + dos columnas de texto o elementos                       | SA1                    |
| Contenido código  | Igual + bloque de código o JSON con fondo gris suave            | SA2                    |
