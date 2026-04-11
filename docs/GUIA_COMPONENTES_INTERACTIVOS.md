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
| API mínima | `getValue()`, `setValue()`, `clear()`, `setOpciones()`, `enable()`, `disable()` |

---

## Toasts programáticos

Sistema de notificaciones para uso desde JavaScript. Definido en `app/static/css/custom.css`
y el contenedor vive en `app/templates/layout/base_fullwidth.html`.

**No confundir con los flash messages de Flask**, que se inyectan en Jinja al renderizar
la página. Los toasts programáticos se muestran como respuesta a acciones AJAX ya resueltas.

### CSS (custom.css)

Cuatro clases disponibles: `.toast-success`, `.toast-danger`, `.toast-warning`, `.toast-info`.
Cada una aplica color de fondo sutil, texto oscuro y un botón de cierre con el filtro de color
correspondiente. Sobreescribe el estilo base de Bootstrap.

### Estructura HTML

```html
<div class="toast toast-success" role="alert"
     aria-live="assertive" aria-atomic="true"
     data-bs-autohide="true" data-bs-delay="5000">
  <div class="d-flex align-items-center p-3">
    <div class="flex-grow-1">
      <i class="fas fa-check-circle me-2"></i>
      <strong>Correcto:</strong> El mensaje aquí.
    </div>
    <button type="button" class="btn-close ms-3"
            data-bs-dismiss="toast" aria-label="Cerrar"></button>
  </div>
</div>
```

| Tipo | Clase | Icono FA | Etiqueta |
|------|-------|----------|----------|
| `success` | `.toast-success` | `fa-check-circle` | Correcto |
| `danger` | `.toast-danger` | `fa-exclamation-circle` | Error |
| `warning` | `.toast-warning` | `fa-exclamation-triangle` | Atención |
| `info` | `.toast-info` | `fa-info-circle` | Información |

### Función JS reutilizable

Copiar esta función en cualquier `<script>` que necesite mostrar toasts.
Inyecta el elemento en el `.toast-container` ya presente en el base template
y replica el ciclo de vida (clases `showing`/`hide`, autodestrucción).

```javascript
function mostrar_toast(tipo, mensaje) {
  var iconos    = { success: 'fa-check-circle', danger: 'fa-exclamation-circle',
                    warning: 'fa-exclamation-triangle', info: 'fa-info-circle' };
  var etiquetas = { success: 'Correcto', danger: 'Error',
                    warning: 'Atención',  info: 'Información' };
  var id   = 'toast-js-' + Date.now();
  var html =
    '<div id="' + id + '" class="toast toast-' + tipo + '" role="alert"' +
    ' aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">' +
    '<div class="d-flex align-items-center p-3"><div class="flex-grow-1">' +
    '<i class="fas ' + (iconos[tipo] || iconos.info) + ' me-2"></i>' +
    '<strong>' + (etiquetas[tipo] || 'Aviso') + ':</strong> ' + mensaje +
    '</div><button type="button" class="btn-close ms-3"' +
    ' data-bs-dismiss="toast" aria-label="Cerrar"></button></div></div>';

  var container = document.querySelector('.toast-container');
  container.insertAdjacentHTML('beforeend', html);
  var el = document.getElementById(id);
  el.classList.add('showing');
  var t = new bootstrap.Toast(el);
  t.show();
  setTimeout(function () { el.classList.remove('showing'); }, 300);
  el.addEventListener('hide.bs.toast', function () { el.classList.add('hide'); });
  el.addEventListener('click', function (e) {
    if (!e.target.closest('.btn-close')) { t.hide(); }
  });
  el.addEventListener('hidden.bs.toast', function () { el.remove(); });
}
```

### Uso

```javascript
mostrar_toast('success', 'Cambios guardados correctamente.');
mostrar_toast('danger',  'Error al conectar con el servidor.');
mostrar_toast('warning', 'El documento no tiene fecha administrativa.');
mostrar_toast('info',    'Ruta copiada al portapapeles.');
```

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

#### Config

| Opción | Tipo | Descripción |
|---|---|---|
| `placeholder` | string | Texto del estado vacío |
| `name` | string | Atributo `name` del `<input hidden>` para submit |
| `onChange` | `(v, t) => {}` | Callback ejecutado al seleccionar o limpiar. `v` = valor, `t` = texto. Se llama con `('', '')` al limpiar. |

#### API pública

```javascript
const sel = new SelectorBusqueda('#mi-div', opciones, config);

sel.getValue()              // → string con el valor seleccionado, '' si vacío
sel.setValue('GRA', 'Granada')  // selecciona programáticamente (dispara onChange)
sel.clear()                 // limpia la selección (dispara onChange con v='')
sel.setOpciones(nuevas)     // reemplaza la lista de opciones y limpia el valor
                            //   sin disparar onChange — usar para selectores encadenados
sel.enable()                // habilita el control
sel.disable()               // deshabilita el control y cierra la lista
```

#### Selectores encadenados (provincia → municipio)

Patrón usado en el wizard paso 2 y en la edición de expediente:

```javascript
// El selector dependiente empieza deshabilitado
const muniSel = new SelectorBusqueda('#sb-municipio', [], {
  placeholder: '— Seleccione primero una provincia —',
  name: 'municipio_id',
  onChange: (v, t) => {
    if (!v) return;
    // hacer algo con la selección, p.ej. añadir a una lista
    muniSel.clear();  // clear() llama onChange('','') → el guard !v lo descarta
  }
});
muniSel.disable();

// El selector padre carga las opciones del dependiente al cambiar
const provSel = new SelectorBusqueda('#sb-provincia', [], {
  placeholder: '— Seleccione una provincia —',
  onChange: async (v, t) => {
    muniSel.setOpciones([]);          // limpia sin disparar onChange del hijo
    if (!t) { muniSel.disable(); return; }
    const resp = await fetch(`/api/municipios?provincia=${encodeURIComponent(t)}`);
    const data = await resp.json();
    muniSel.setOpciones(data.map(m => ({ v: String(m.id), t: m.nombre })));
    muniSel.enable();
  }
});

// Cargar las opciones del selector raíz desde API
fetch('/api/provincias')
  .then(r => r.json())
  .then(lista => provSel.setOpciones(lista.map(n => ({ v: n, t: n }))));
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

### EntradaFecha

Campo de texto con parser inteligente de fechas. Acepta formatos abreviados y normaliza
al perder el foco. Sin dependencias externas.

**Ficheros:**
- `app/static/js/entrada_fecha.js`
- `app/static/css/entrada_fecha.css`

**Mockup de referencia:** `docs/mockups/fecha-mockup.html` (Control 4)

#### Uso en Jinja2

```html
{# 1. Cargar en el bloque head #}
<link rel="stylesheet" href="{{ url_for('static', filename='css/entrada_fecha.css') }}">

{# 2. Contenedor vacío donde vivirá el componente #}
<div id="ef-fecha-inicio"></div>

{# 3. Instanciar al final del body o en el bloque scripts #}
<script src="{{ url_for('static', filename='js/entrada_fecha.js') }}"></script>
<script>
  new EntradaFecha('#ef-fecha-inicio', {
    name: 'fecha_inicio',   // atributo name del input hidden para el formulario
    onChange: (iso) => { console.log(iso); }  // opcional
  });
</script>
```

#### Config

| Opción | Tipo | Descripción |
|---|---|---|
| `name` | string | Atributo `name` del `<input hidden>` para submit |
| `placeholder` | string | Texto de ayuda (por defecto `dd/mm/aaaa`) |
| `onChange` | `(iso) => {}` | Callback al confirmar fecha válida o al limpiar. `iso` = `'yyyy-mm-dd'` o `''`. |

#### API pública

```javascript
const ef = new EntradaFecha('#mi-div', { name: 'fecha_inicio' });

ef.getValue()              // → 'yyyy-mm-dd' o ''
ef.setValue('2025-02-10')  // muestra 10/02/2025, dispara onChange
ef.clear()                 // limpia campo y hidden, dispara onChange('')
ef.enable()
ef.disable()
```

#### Comportamiento

| Acción | Resultado |
|---|---|
| Escribir `10/2/25` y pulsar Tab | Normaliza a `10/02/2025`, hidden = `2025-02-10` |
| Separadores aceptados | `/` `-` `.` espacio |
| Año de 2 dígitos | `25` → `2025`, `99` → `2099` |
| Fecha imposible (`31/02/2025`) | Borde rojo, hidden vacío |
| Campo vacío al salir | Sin error, hidden vacío |
| `Escape` | Limpia campo y hidden |
| Botón `×` | Limpia y devuelve el foco al input |
| Hover sobre el input | Tooltip "Escape para borrar" |

#### Estructura HTML generada

```html
<div id="mi-div" class="ef-wrap">
  <input type="text"   class="form-control ef-input" placeholder="dd/mm/aaaa"
         data-bs-toggle="tooltip" title="Escape para borrar">
  <input type="hidden" name="fecha_inicio" class="ef-hidden">
  <button class="ef-btn-x" tabindex="-1">×</button>
</div>
```

---

### SelectorFiltro

Selector de filtro con etiqueta contextual y estado activo visual. Diseñado para
usarse en la barra de filtros de los listados V2. Internamente usa un `<select>` nativo,
por lo que `FiltrosListado` lo detecta y gestiona automáticamente.

**Ficheros:**
- `app/static/js/selector_filtro.js`
- `app/static/css/selector_filtro.css`

Cargados automáticamente en `lista_v2_base.html` — no hace falta incluirlos manualmente
en templates que extiendan ese base.

#### Uso en Jinja2

```html
{# En el bloque filtros_extra del template de listado #}
{% block filtros_extra %}
<div id="sf-tipo-exp"></div>
{% endblock %}

{% block extra_js %}
{{ super() }}
<script>
  new SelectorFiltro('#sf-tipo-exp', {{ tipos_exp | tojson }}, {
    label: 'Tipo expediente',
    name: 'tipo_expediente_id'
  });
  const scrollInfinito = new ScrollInfinito({ ... });
  const filtros = new FiltrosListado(scrollInfinito);
</script>
{% endblock %}
```

El array de opciones tiene la forma `[{ "v": "valor", "t": "texto visible" }, ...]`.

#### Config

| Opción | Tipo | Descripción |
|---|---|---|
| `label` | string | Texto de la etiqueta. El placeholder será `"Label (todos)"`. |
| `name` | string | Atributo `name` del `<select>` nativo interno |
| `onChange` | `(v, t) => {}` | Callback al seleccionar o limpiar. `v` = valor, `t` = texto. Se llama con `('', '')` al limpiar. |

#### API pública

```javascript
const sf = new SelectorFiltro('#mi-div', opciones, config);

sf.getValue()               // → valor seleccionado o ''
sf.setValue('3')            // selecciona programáticamente (dispara onChange)
sf.clear()                  // vuelve al estado "todos" (dispara onChange)
sf.setOpciones(nuevas)      // reemplaza opciones y limpia — sin disparar onChange
sf.enable() / sf.disable()
```

#### Comportamiento

| Estado | Apariencia |
|---|---|
| Sin filtro | Fondo blanco, texto `"Label (todos)"`, sin botón × |
| Con filtro | Fondo `var(--primary-lighter)` (#f7fbf8, verde muy claro — igual que hover de fila de tabla), borde `var(--primary)`, botón × visible |
| Clic en × | Limpia la selección, devuelve el foco al select, dispara recarga del listado |
| Btn Limpiar (FiltrosListado) | Resetea el select y actualiza el estado visual |

#### Notas de implementación

- El color de fondo activo se aplica al **wrapper** `.sf-wrap` (div), **no** al `<select>`.
  El select usa `background: transparent` para que el dropdown nativo no herede el tinte verde.
- El focus ring usa `:focus-within` en el wrapper en vez de `outline` en el `<select>`:
  el wrapper no sufre el layout shift al aparecer el botón `×` (fix #268).
- `clear()` despacha un evento `change` con `bubbles:true` para que `FiltrosListado` recargue
  el listado, igual que haría una selección manual del usuario.
- `FiltrosListado._limpiar()` usa el flag `_limpiando` para suprimir los eventos de cambio
  durante el reset masivo y evitar recargas múltiples.

#### Estructura HTML generada

```html
<div id="mi-div" class="sf-wrap [sf-activo]">
  <select class="sf-select" name="tipo_expediente_id">
    <option value="">Tipo expediente (todos)</option>
    <option value="1">Legalización</option>
    ...
  </select>
  <button class="sf-btn-x" tabindex="-1">×</button>
</div>
```

---

### InputFiltro

Campo de texto para filtros con icono de lupa y estado activo visual. Compañero de
`SelectorFiltro`. Compatible con `FiltrosListado` (v2.2+): los inputs `.if-input`
se detectan automáticamente y se gestionan con debounce.

**Ficheros:**
- `app/static/js/input_filtro.js`
- `app/static/css/input_filtro.css`

Cargados automáticamente en `lista_v2_base.html`.

#### Uso en Jinja2

```html
{% block filtros_extra %}
<div id="if-nif"></div>
{% endblock %}

{% block extra_js %}
{{ super() }}
<script>
  new InputFiltro('#if-nif', {
    placeholder: 'Filtrar por NIF...',
    name: 'nif'
  });
  const scrollInfinito = new ScrollInfinito({ ... });
  const filtros = new FiltrosListado(scrollInfinito);
</script>
{% endblock %}
```

#### Config

| Opción | Tipo | Descripción |
|---|---|---|
| `placeholder` | string | Texto de ayuda mostrado en el input |
| `name` | string | Atributo `name` del `<input>` interno |
| `onChange` | `(v) => {}` | Callback en cada pulsación de tecla. `v` = valor actual. |

#### API pública

```javascript
const inf = new InputFiltro('#mi-div', config);

inf.getValue()          // → string con el valor actual o ''
inf.setValue('12345')   // establece el valor (dispara onChange)
inf.clear()             // limpia el campo (dispara onChange con '')
inf.enable() / inf.disable()
```

#### Comportamiento

| Estado | Apariencia |
|---|---|
| Vacío | Fondo blanco, icono lupa gris (`var(--text-secondary)`), sin botón × |
| Con texto | Fondo `var(--primary-lighter)` (#f7fbf8, igual que `SelectorFiltro` y hover de fila), borde `var(--primary)`, lupa verde (`var(--primary)`), botón × visible |
| Clic en × | Limpia el campo, devuelve el foco al input, dispara recarga del listado |
| Btn Limpiar (FiltrosListado) | Vacía el input y actualiza el estado visual |

#### Notas de implementación

- El buscador principal (`input[type="search"]` en `lista_v2_base.html`) también muestra
  estado activo con el mismo color, pero vía CSS puro: `.filters input[type="search"]:not(:placeholder-shown)`.
  No requiere componente JS.
- `clear()` despacha un evento `input` con `bubbles:true` para que `FiltrosListado`
  inicie su debounce y recargue el listado.

#### Estructura HTML generada

```html
<div id="mi-div" class="if-wrap [if-activo]">
  <span class="if-icon" aria-hidden="true"><i class="fas fa-search"></i></span>
  <input type="text" class="if-input" placeholder="Filtrar por NIF...">
  <button class="if-btn-x" tabindex="-1">×</button>
</div>
```

---

## Próximos componentes (pendientes)

- `SelectorMultiple` — selección acumulable con badges (variante del anterior)
- `SelectorRemoto` — opciones cargadas desde API REST al escribir (mínimo 2 caracteres)
