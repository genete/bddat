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

## Contrato de un selector

Un selector es cualquier control del que se elige un valor de una lista: el `<select>` nativo, los
componentes de este catálogo y sus equivalentes de React. Hay **dos tipos, que se distinguen por el
tamaño de la lista y no por la tecnología**, y **un único contrato de comportamiento** para los dos
(#1038). No se busca un componente único: se busca que ninguno decida por su cuenta qué hace en los
bordes, que es donde se pierden datos sin que nadie lo vea.

| Tipo | Cuándo | Jinja | React |
|---|---|---|---|
| **Corto** | Hasta unas 12 opciones | `<select class="form-select">`; `SelectorFiltro` en las barras de filtros | `ControlCampo` (el del esquema editable) o un `<select>` |
| **Con búsqueda** | Más de 12, o una lista que crece con el uso | `SelectorBusqueda` | No hay equivalente; `SelectorEntidad` es un híbrido (desplegable y, desde 12 opciones, filtro de texto) |

**Las cuatro reglas** (valen para los dos tipos):

1. **La opción vacía dice qué implica no elegir**, cuando no elegir tiene consecuencias: «Sin
   representante: se notifica al solicitante», no «—». Es `texto_vacio` en el esquema editable,
   `textoVacio` en React, el `placeholder` de `SelectorBusqueda` y el texto de la `<option value="">` del
   `<select>` nativo. Si nada depende de no elegir, vale «—». El mismo texto sale en lectura, para que lo
   que se ve en lectura se vea en edición.
2. **Un valor guardado que no está entre las opciones no se oculta ni se da por válido.** El selector se
   ve vacío, junto a él sale un «!» con el motivo en el tooltip, y el «!» desaparece en cuanto el usuario
   cambia el selector, a otra opción o a la vacía. Sin tocarlo, el valor guardado se conserva: lo
   decide el usuario, no el control. El motivo lo da el servidor (`aviso`), porque solo él sabe por qué
   ya no vale; sin motivo, el control pone uno genérico. Vale para cualquier causa: una revocación, una
   baja, un valor puesto por un script.
3. **Elegir «nada» de nuevo tiene que poder cambiar algo.** Un `<select>` nativo no dispara `change` al
   elegir lo que ya se ve elegido, y con un valor fuera de las opciones la opción vacía ya parece elegida.
   Mientras dure ese estado, el elegido por dentro es una opción oculta con el mismo texto que la vacía.
   El selector no se remonta al aparecer o quitarse el «!» (mismo envoltorio siempre), o se pierde el foco.
4. **Las formas de las opciones no se unifican; se adaptan en la frontera.** `{v, t}` en los componentes
   de Jinja y en los endpoints hechos para ellos (`/sedes`); `{valor, texto}` en el esquema editable y en
   React; `{id, text}` en el autocompletado de entidades y en `/autorizados`. Una lista de la que se elige se define **una vez en el
   servicio** y cada puerta la formatea, y **el validador que la acepta usa esa misma lista**: lo que se
   ofrece y lo que se acepta no pueden discrepar (`notificaciones.representantes_posibles` y
   `sedes_posibles`, que usan los endpoints, el esquema y `validar_representante` / `validar_sede`).

**Por qué importa la regla 2.** Con un `<select>` de Jinja cuya opción `selected` no coincide con ninguna
de la lista, el navegador muestra la primera opción y, si esa es la vacía, al guardar el formulario
entero se envía vacío: el campo se borra en silencio. `SelectorBusqueda.setValue(v, t)` falla al revés: no comprueba que `v` esté en
la lista y pinta como válido lo que no lo es.

**Cómo lo declara el esquema editable** (`esquema_editable._campo_select`): `texto_vacio` y `aviso` solo
salen cuando hay algo que decir, así que los select que no lo necesitan conservan su forma. El detalle de
lectura lleva el mismo `aviso` en el campo (`detalle_nodo._campo`).

```python
{'campo': 'representante_entidad_id', 'etiqueta': 'Representante', 'control': 'select',
 'valor': 12,                                    # lo guardado, tal cual, aunque ya no sea una opción
 'opciones': [{'valor': 7, 'texto': 'Gestoría Ejemplo S.L. (B11223344)'}],
 'texto_vacio': 'Sin representante: se notifica al solicitante',
 'aviso': '«Gestoría Vieja S.L. (B99887766)»: El representante no figura como autorizado…'}
```

**Dónde está implementado hoy:** solo en `ControlCampo` (React, `expediente-arbol/components/TarjetaDatos.jsx`),
que lo aplica a todos los select del esquema editable. Pendiente de alinear: `SelectorBusqueda.setValue`
(que valide contra la lista), `SelectorEntidad` y los `<select>` de los formularios Jinja. Un caso
concreto del riesgo, leído en el código y sin reproducir en la aplicación: el desplegable de responsable
del formulario de expediente solo lista tramitadores activos (`usuarios_tramitadores`) y el guardado hace
`aplicar_fk(request.form, 'responsable_id', …)`, que convierte «vacío» en `NULL`. Un responsable dado de
baja, o que ya no es tramitador, se vería como «Sin asignar» y quedaría sin responsable al guardar
cualquier otro campo.

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

---

## APIs de shell — Inspector y Modal grande (ADR-023)

Disponibles como globals en `window` desde `inspector-overlay.js`, cargado en `base_app.html`.

### `window.AppInspector`

Control del inspector overlay de shell. Funciona en cualquier vista (Jinja o React).

```javascript
AppInspector.open({ selId, title, fragmentUrl })
// Abre o hace swap del inspector. Si fragmentUrl: carga el fragmento en el panel.
// Si ya está abierto con el mismo selId: no-op (retención, §7 ADR-023).
// `title` es la cabecera de reserva del marco (la que pasa el listado): el fragmento puede
// sustituirla con data-title. refresh() la conserva.

AppInspector.mountReact({ selId })
// Variante para islas React: abre el panel sin tocar el body
// (la isla pinta por portal en #app-inspector-body).

AppInspector.close()
// Popdown + limpia selId + emite CustomEvent 'inspector:closed'.

AppInspector.refresh()
// Re-fetch del último fragmentUrl (usar tras guardar en el modal grande).

AppInspector.setLocked(bool)
// true → backdrop bloqueante (modo edición); false → lectura.
// Sustituye/coexiste con el body.arbol-lock del árbol. Con un fragmento Jinja con marco,
// el propio marco lo gobierna (bloqueado en edición, libre en lectura).

AppInspector.setFrame(descriptor | null)
// Marco que alimenta una isla React (el puente del árbol). Ver «Marco único del inspector».

AppInspector.isOpen()        // → boolean
AppInspector.currentSel()   // → selId actual o null
```

**Eventos CustomEvent emitidos** (escuchables en `document`):

| Evento | `detail` | Cuándo |
|---|---|---|
| `inspector:opened` | `{ selId }` | Popup (cerrado → abierto) |
| `inspector:swapped` | `{ selId }` | Cambio de ítem in-place |
| `inspector:closed` | — | Popdown |

**Clases de estado** (sobre `.app-shell` / `<body>`):

| Clase | Significado |
|---|---|
| `.app-shell.is-inspector-open` | Inspector visible |
| `.app-shell.is-inspector-locked` | Edición — backdrop bloqueante |

#### Marco único del inspector (ADR-053 §A y §B, #1042)

El shell pinta **una sola barra** (`#app-inspector-bar`, fuera del scroll del cuerpo) con la
cabecera y los gestos de ver / editar / guardar / cancelar / cerrar. Ni los fragmentos Jinja ni
el árbol pintan ya la suya. Hay dos fuentes:

**1. Un fragmento Jinja**, con atributos en su raíz (el DOM que hay en el cuerpo es la verdad):

```html
<!-- lectura -->
<div class="p-3" data-inspector-frame="ver" data-title="…"
     {% if puede_editar %}data-edit-url="{{ url_for('modulo.editar_fragmento', id=x.id) }}"{% endif %}>
<!-- edición -->
<div class="p-3" data-inspector-frame="editar" data-title="…">
  <form data-inspector-form data-action="{{ url_for('modulo.editar', id=x.id) }}"> … </form>
</div>
```

| Atributo | Dónde | Qué hace |
|---|---|---|
| `data-inspector-frame` | raíz | `ver` o `editar`. Sin él, el fragmento no tiene barra (cola, seguimiento y huérfanos, de solo lectura) |
| `data-edit-url` | lectura | URL del fragmento de edición. Sin él no hay «Editar» (es el antiguo `{% if puede_editar %}`) |
| `data-title` | ambas | Sustituye al título del listado. **Ponerlo cuando el título sale de un campo editable**; si no, la cabecera queda desactualizada tras guardar. Con el nombre o el código inmutable basta el del listado |
| `data-edit-label` | lectura | Rótulo de «Editar» (p. ej. «Resolver» en mensajes internos, donde editar es resolver) |
| `data-save-label` | edición | Rótulo de «Guardar» (p. ej. «Resolver petición») |
| `data-min-width` | ambas | Ancho mínimo del cuerpo en px (ver abajo) |

Reglas del contrato:

- **El fragmento no lleva botones de editar, cancelar ni guardar.** El formulario de edición es
  el **único** `form[data-inspector-form]` del fragmento; «Guardar» lo envía con `requestSubmit()`
  (pasa por la validación HTML5 y por el envío XHR de siempre). Con dos formularios o con
  ninguno, «Guardar» queda deshabilitado y el shell avisa en consola. Intro en un campo de
  texto guarda si hay cambios.
- Las **acciones propias** de la lectura (activar, eliminar, «Gestionar»…) se quedan en el
  cuerpo: el marco solo se lleva «Editar».
- **«Guardar» gris y «Cerrar» con el formulario limpio; «Guardar» activo y «Cancelar» cuando se
  ha tocado.** Tocar es un `input` o un `change` dentro del formulario. **Todo script que cambie
  campos sin que el usuario teclee** (añadir, quitar o mover una fila, escribir un campo oculto,
  elegir un fichero en un modal) **tiene que disparar un `change` que burbujee**
  (`el.dispatchEvent(new Event('change', { bubbles: true }))`): si no, «Guardar» no se enciende y
  el cambio no se puede guardar, sin ningún aviso. Lo hacen `requisitos-inspector.js`,
  `tablas-maestras-pasos.js` y el explorador de plantillas.
- Los botones del marco **no llevan icono** junto al verbo (estilo de la Junta): «Editar»,
  «Guardar», «Cancelar/Cerrar». Orden: «Cancelar/Cerrar» a la izquierda y la acción principal a la
  derecha, y «Editar» y «Guardar» ocupan el mismo sitio (al pulsar «Editar» el puntero cae sobre
  «Guardar» deshabilitado).
- En vista **no hay cruz**: se cierra con clic exterior, `Escape` o un clic en la franja de
  redimensionado. (`_inspector_cola.html` conserva la suya hasta que adopte el marco, #1039.)
- El **interior no cambia**: «Guardar» del marco es el del formulario entero. Lo que un bloque
  interior guarda por su cuenta (en el árbol: ítems técnicos, shuttles, vincular documento…)
  no enciende la barra (ADR-023 §5 bis, rev. 2026-07-29).

**2. El árbol del expediente (React)**, con `AppInspector.setFrame(descriptor)`, que lo llama
`usePuenteInspector` (`react-src/src/expediente-arbol/puenteInspector.js`) cada vez que cambia el
estado:

```javascript
AppInspector.setFrame({
  modo: 'ver' | 'editar', tipo, titulo, estado, candado,        // cabecera
  semaforo: { color, titulo },                                  // semáforo del nodo (o null)
  puedeEditar, hayCambios, interiorSucio, guardando, minWidth,
  onEditar, onGuardar, onSalir,                                 // los tres gestos
})
```

Los gestos ejecutan las acciones del store (`entrarEdicion`, `pedirGuardar()` —nunca `guardar` con el
evento del clic: su primer argumento es la justificación del escape— y `cancelar`). `hayCambios` es el
del borrador global del store. `interiorSucio` (#1055) es texto sin guardar en un bloque que guarda por
su cuenta: no enciende «Guardar» pero hace que el botón de salida diga «Cancelar». Los fragmentos Jinja
no lo declaran. Cómo avisa un bloque: `useInteriorSucio` en `GUIA_REACT_ISLAS.md`.

**Ancho mínimo (D11).** El cuerpo hace scroll vertical y horizontal; la barra queda fuera. Cada
caso declara el ancho por debajo del cual su contenido no se encoge más (`data-min-width`, o
`minWidth` en el descriptor) y el shell lo vuelca en `--inspector-min`. Sin declarar, el cuerpo se
encoge hasta el mínimo del shell (320 px). Las cifras de cada fragmento se midieron con este
criterio: barrido de 320 a 960 px de 20 en 20, en lectura y en edición, con scrollbars clásicos
activos; el caso «cabe» cuando el cuerpo no desborda y ningún control visible queda por debajo
de su umbral (texto, textarea y fecha 110 px; select 80; número 56). Para un fragmento nuevo,
medirlo igual en vez de estimarlo. La señal del scroll horizontal es la barra nativa; con barras
superpuestas se oculta sola y eso no está medido en el navegador de la Consejería.

---

### `window.AppModalLarge`

Modal Bootstrap maximizado (`.modal-app-xl`) para gestión compleja desde el inspector (capa 3, ADR-023 §6).

```javascript
AppModalLarge.open(fragmentUrl, { title, onSaved })
// Carga el fragmento en el modal y lo muestra.
// onSaved (opcional): callback al guardar — por defecto AppInspector.refresh() + cierre.
```

`.modal-app-xl` se define en `app-shell.css`: maximizado con margen (~`calc(100% - 3rem)`), casi pantalla completa. Es un modal Bootstrap estándar (backdrop bloqueante, `z-index` > inspector).

---

## Próximos componentes (pendientes)

- `SelectorMultiple` — selección acumulable con badges (variante del anterior)
- `SelectorRemoto` — opciones cargadas desde API REST al escribir (mínimo 2 caracteres)
