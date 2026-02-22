# Guía de Componentes Interactivos

Referencia de los componentes JS reutilizables de la aplicación.
Complementa `GUIA_VISTAS_BOOTSTRAP.md` (que cubre layout y vistas).

---

## Principios del sistema

- Cada componente es una **clase JS** que construye su propio HTML internamente.
  El template solo necesita un `<div>` vacío con un `id`.
- El CSS asociado contiene **únicamente estructura** (posicionamiento, z-index, overflow).
  Cero colores, cero tipografía: todo se hereda del tema Bootstrap activo (`v2-theme.css`).
- Los componentes que participan en formularios incluyen un
  `<input type="hidden" name="...">` interno que lleva el valor al submit.
- Los botones auxiliares (×, ▾) llevan `tabindex="-1"`: accesibles por ratón, invisibles al Tab.
- El foco de teclado vive siempre en el elemento principal del componente.

---

## Convenciones para nuevos componentes

| Aspecto | Convención |
|---|---|
| Nombre de clase JS | `PascalCase` en español (ej: `SelectorBusqueda`, `SelectorMultiple`) |
| Prefijo CSS | Iniciales del componente + guion (ej: `sb-` para `SelectorBusqueda`) |
| Fichero JS | `app/static/js/nombre_componente.js` |
| Fichero CSS | `app/static/css/nombre_componente.css` |
| Colores en CSS | Prohibidos. Usar `inherit` o `currentColor` |
| Tipografía en CSS | Prohibida. Heredada del tema |
| API mínima | `getValue()`, `setValue()`, `clear()` |

---

## Catálogo

### SelectorBusqueda

Control de selección única con filtrado por texto. Alternativa al `<select>` nativo
cuando se necesita buscar dentro de la lista.

**Ficheros:**
- `app/static/js/selector_busqueda.js`
- `app/static/css/selector_busqueda.css`

**Mockup de referencia:** `docs/mockups/select-mockup.html`

#### Uso en Jinja2

```html
{# 1. Cargar en el bloque head (o en base_fullwidth.html si se usa globalmente) #}
<link rel="stylesheet" href="{{ url_for('static', filename='css/selector_busqueda.css') }}">

{# 2. Contenedor vacío donde vivirá el componente #}
<div id="sel-provincia"></div>

{# 3. Instanciar al final del body o en el bloque scripts #}
<script src="{{ url_for('static', filename='js/selector_busqueda.js') }}"></script>
<script>
  new SelectorBusqueda('#sel-provincia', {{ opciones|tojson }}, {
    placeholder: '— Seleccione una provincia —',
    name: 'provincia'   // atributo name del input hidden para el formulario
  });
</script>
```

El array `opciones` debe tener la forma `[{ "v": "valor", "t": "texto visible" }, ...]`.
Desde Flask se puede construir así:

```python
opciones = [{"v": p.codigo, "t": p.nombre} for p in provincias]
return render_template('mi_vista.html', opciones=opciones)
```

#### API pública

```javascript
const sel = new SelectorBusqueda('#mi-div', opciones, config);

sel.getValue()        // → string con el valor seleccionado, '' si vacío
sel.setValue('GRA', 'Granada')  // selecciona programáticamente
sel.clear()           // limpia la selección
```

#### Comportamiento

| Acción | Resultado |
|---|---|
| Foco en el input | Abre la lista completa |
| Escribir texto | Filtra la lista (contiene, insensible a mayúsculas) |
| Clic en opción | Selecciona y cierra |
| Clic en placeholder | Limpia la selección |
| Clic fuera | Cierra sin cambiar la selección |
| Botón × | Limpia y devuelve el foco al input |
| Botón ▾ | Alterna abrir / cerrar |
| `↓` / `↑` | Navegan la lista (nunca el historial del navegador) |
| `Enter` | Confirma el ítem resaltado |
| `Escape` | Limpia la selección |
| `Tab` | Cierra y pasa al siguiente control; × y ▾ no reciben foco |

#### Estructura HTML generada

```html
<div id="mi-div" class="sb-wrap">
  <input type="text"   class="form-control sb-input" autocomplete="off">
  <input type="hidden" name="provincia">
  <button class="sb-btn-x" tabindex="-1">×</button>
  <button class="sb-btn-v" tabindex="-1">▾</button>
  <ul class="sb-lista dropdown-menu">
    <li class="sb-placeholder dropdown-item">— Seleccione una provincia —</li>
    <li class="dropdown-item" data-v="ALM">Almería</li>
    ...
  </ul>
</div>
```

#### Notas de implementación

- `autocomplete="off"` impide que el navegador muestre su propio historial al pulsar `↓`.
- Los ítems de la lista usan las clases Bootstrap `dropdown-menu` / `dropdown-item`,
  por lo que heredan automáticamente los colores del tema (incluyendo el estado `active`).
- El botón ▾ usa `mousedown` + `preventDefault()` para no disparar el `blur` del input
  antes de procesar la acción de toggle.
- El botón × usa el mismo patrón para la limpieza.

---

## Próximos componentes (pendientes)

- `SelectorMultiple` — selección acumulable con badges (variante del anterior)
- `SelectorRemoto` — opciones cargadas desde API REST al escribir (mínimo 2 caracteres)
