---
id: ADR-009
título: Incrustación de imágenes en plantillas mediante función img() en contexto Jinja2
fecha: 2026-05-16
estado: decidida — implementada (#297)
---

## Decisión

Las imágenes (logotipos, sellos, firmas…) se incrustan en los escritos generados mediante
una función `img()` inyectada en el contexto Jinja2 de cada renderizado.

Uso en plantilla `.docx`:

```
{{ img('logo_portada.png', '3.5', '1.98') }}   — ancho y alto en cm
{{ img('firma_director.png', '4.0') }}          — solo ancho; alto proporcional
{{ img('sello.png') }}                          — tamaño original del fichero
```

Los ficheros de imagen se almacenan en `PLANTILLAS_BASE/recursos/` y se referencian
por nombre desde la plantilla. El posicionamiento (inline, dentro de cuadro de texto
anclado, etc.) lo define la propia plantilla, no el código.

## Por qué

**Problema previo:** las plantillas heredadas (.doc, Word 2000) tenían los logotipos
incrustados directamente. Al cambiar la identidad corporativa de la Junta (2017) fue
necesario actualizar más de 30 plantillas manualmente.

**Por qué no variables hardcodeadas** (`ctx['logo_portada'] = InlineImage(...)`):
ata el nombre del fichero y las dimensiones al código Python. Añadir un nuevo logotipo
o usarlo en otro lugar requeriría cambio de código.

**Por qué no fragmentos subdoc** (`{{r Logo}}`): docxtpl/docxcompose no reasigna
correctamente los `rId` de imagen al mezclar subdocumentos — las imágenes quedan
como referencias rotas en el output.

**Por qué `img()` callable en contexto:** Jinja2 evalúa la llamada en tiempo de
renderizado, `InlineImage` queda embebida en el `.docx` resultante, y no existe
dependencia entre el nombre de la variable y el código del generador. Cualquier imagen
en `PLANTILLAS_BASE/recursos/` es incrustable desde cualquier plantilla y en cualquier
posición sin modificar código.

## Anclaje

El token `{{ img(...) }}` produce contenido **inline** (anclado como carácter).
El posicionamiento real en el documento lo controla la plantilla:

- **Cabecera páginas 2+:** token en párrafo de cabecera → imagen inline en el flujo de texto.
- **Logos de primera página:** token dentro de un cuadro de texto (`wps:txbx`) que está
  anclado con posición absoluta a la página. La imagen es inline dentro del cuadro;
  el cuadro provee el anclaje absoluto.
- **Pie de primera página:** ídem cuadro de texto anclado.

Esta separación de responsabilidades (el código embebe, la plantilla posiciona) permite
que el diseñador de plantillas controle la maquetación sin intervención del desarrollador.

## Cómo implementar

- `app/services/generador_escritos.py`: función `_fn_imagen(tpl, recursos_dir)` que
  devuelve el callable `img()`. Se inyecta como `ctx['img']` antes de `tpl.render(ctx)`.
- Directorio de recursos: `PLANTILLAS_BASE/recursos/` (misma variable de entorno que
  las plantillas, sin variable adicional).
- Plantilla base de carta: `plantilla_base_297.docx` con los tres tokens ya configurados.

## Alternativas descartadas

- **Variables hardcodeadas por nombre** (`logo_portada`, `logo_cabecera`, `logo_pie`):
  descartada por acoplar nombres de fichero al código.
- **Fragmentos subdoc** (`{{r Logo}}`): descartada por bug de reasignación de `rId`
  en docxtpl/docxcompose que deja imágenes sin resolver.
- **Logo vinculado en plantilla + incrustado en generador**: descartada por fragilidad
  de rutas absolutas en vínculos de plantilla y complejidad de la cirugía ZIP necesaria.
