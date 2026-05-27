---
id: ADR-009
título: Estrategia de imágenes en plantillas — logotipos estáticos vs. imágenes dinámicas
fecha: 2026-05-16
revisado: 2026-05-17
estado: decidida — implementada (#297); logotipos reformulados tras reflexión post-cierre
---

## Decisión

Se distinguen dos categorías de imagen con estrategias distintas:

### 1. Logotipos corporativos — incrustados de fábrica en la plantilla

Los logotipos (escudo de la Junta, marca del organismo…) se incrustan directamente
en cada plantilla `.docx` en el momento de su diseño. No llevan token `{{ img() }}`.

**Actualización de logotipo (caso excepcional):** se ejecuta un script de sustitución
que opera sobre el ZIP interno del `.docx` — localiza la imagen por su `rId` en
`word/_rels/document.xml.rels`, reemplaza el fichero en `word/media/` y, si las
dimensiones cambian, actualiza `word/document.xml`. El script se aplica una vez
sobre cada plantilla afectada, no en tiempo de renderizado.

### 2. Imágenes dinámicas por expediente — función `img()` en contexto Jinja2

Las imágenes cuyo contenido varía por documento (firmas, sellos, diagramas, mapas
de emplazamiento, QR codes…) se incrustan mediante la función `img()` inyectada en
el contexto Jinja2.

Uso en plantilla `.docx`:

```
{{ img('firma_director.png', '4.0') }}   — solo ancho; alto proporcional
{{ img('sello.png') }}                   — tamaño original del fichero
```

Los ficheros se almacenan en `PLANTILLAS_BASE/recursos/`. El posicionamiento lo
define la plantilla (cuadro de texto anclado, párrafo de cabecera, etc.), no el código.

## Por qué

**Logotipos no son contenido dinámico.** El logotipo de la Junta lleva más de 40 años
sin cambiar de imagen. Si cambiase de imagen manteniendo posición y tamaño, el script
de sustitución basta. Si cambiase también de posición o tamaño habría que modificar
la plantilla igualmente — lo que invalida la ventaja del token dinámico en ese escenario.

El token `{{ img(...) }}` solo controla ancho/alto de la imagen, no su posición en la
página. El posicionamiento real ya debe estar resuelto en el diseño de la plantilla
mediante cuadros de texto anclados. Por tanto, el token no aporta nada al caso del
logotipo que no esté ya resuelto de fábrica.

Usar `img()` para logotipos introduce overhead en cada renderizado para un contenido que
nunca varía por expediente.

**Por qué no variables hardcodeadas** (`ctx['logo_portada'] = InlineImage(...)`):
ata el nombre del fichero y las dimensiones al código Python. Añadir un nuevo logotipo
o usarlo en otro lugar requeriría cambio de código.

**Por qué no fragmentos subdoc** (`{{r Logo}}`): docxtpl/docxcompose no reasigna
correctamente los `rId` de imagen al mezclar subdocumentos — las imágenes quedan
como referencias rotas en el output.

## Anclaje de imágenes dinámicas (img())

El token `{{ img(...) }}` produce contenido **inline** (anclado como carácter).
El posicionamiento real en el documento lo controla la plantilla:

- **Cabecera páginas 2+:** token en párrafo de cabecera → imagen inline en el flujo de texto.
- **Imágenes en cuerpo del escrito:** token dentro de un cuadro de texto (`wps:txbx`)
  anclado con posición absoluta. La imagen es inline dentro del cuadro; el cuadro
  provee el anclaje absoluto.

## Cómo implementar

**Función `img()`:**
- `app/services/generador_escritos.py`: función `_fn_imagen(tpl, recursos_dir)` que
  devuelve el callable `img()`. Se inyecta como `ctx['img']` antes de `tpl.render(ctx)`.
- Directorio de recursos: `PLANTILLAS_BASE/recursos/` (misma variable de entorno que
  las plantillas, sin variable adicional).

**Script de sustitución de logotipo:**
- Pendiente de implementar si se necesita; operará sobre el ZIP del `.docx`:
  leer `word/_rels/document.xml.rels` para localizar el `rId` del logotipo,
  reemplazar el fichero en `word/media/`, actualizar dimensiones en `word/document.xml`
  si procede.
- Se ejecuta manualmente sobre las plantillas afectadas, no en tiempo de render.

## Alternativas descartadas

- **Variables hardcodeadas por nombre** (`logo_portada`, `logo_cabecera`, `logo_pie`):
  descartada por acoplar nombres de fichero al código.
- **Fragmentos subdoc** (`{{r Logo}}`): descartada por bug de reasignación de `rId`
  en docxtpl/docxcompose que deja imágenes sin resolver.
- **Token `img()` para logotipos:** descartada post-implementación (#297). El token no
  controla posición — que ya está en la plantilla — y añade overhead por render para
  contenido estático. El script de sustitución cubre el caso de cambio de logotipo
  con menor coste operacional.
