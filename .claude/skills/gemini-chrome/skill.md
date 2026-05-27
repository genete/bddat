---
name: gemini-chrome
description: Consulta a Gemini via Chrome (cuenta Google propia, gratuito). Alternativa a /gemini cuando se quiere evitar coste de API. Requiere Chrome abierto con sesión Google activa.
argument-hint: "<pregunta> [ruta_fichero_contexto]"
allowed-tools: mcp__claude-in-chrome__tabs_context_mcp, mcp__claude-in-chrome__tabs_create_mcp, mcp__claude-in-chrome__navigate, mcp__claude-in-chrome__javascript_tool, mcp__claude-in-chrome__computer, mcp__claude-in-chrome__find, mcp__claude-in-chrome__file_upload
---

Eres el intermediario entre el usuario y Gemini via navegador Chrome. Tu argumento es: `$ARGUMENTS`

**Nunca muestres la respuesta cruda de Gemini.** Sintetiza y razona sobre ella antes de responder al usuario.

---

## Prerequisitos (verificar antes de empezar)

- Chrome abierto con cuenta Google logueada en gemini.google.com
- Extensión "Allow access to file URLs" activada: `chrome://extensions/` → Claude in Chrome → activar opción
- Si se va a enviar fichero de contexto: debe existir en `docs_prueba/temp/` antes de invocar el skill

---

## Paso 1 — Cargar herramientas y obtener tab

Carga las herramientas necesarias con ToolSearch antes de usarlas:
- `select:mcp__claude-in-chrome__tabs_context_mcp`
- `select:mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__javascript_tool,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__find`
- `select:mcp__claude-in-chrome__file_upload` (solo si hay fichero)

Obtén los tabs disponibles con `tabs_context_mcp`.

Si ya hay un tab con `gemini.google.com`, úsalo. Si no, crea uno nuevo con `tabs_create_mcp` y navega a `https://gemini.google.com/app`.

**Si la extensión no está conectada** (error "Browser extension is not connected"): informa al usuario que debe tener Chrome abierto con la extensión activa.

---

## Paso 2 — Navegar a conversación nueva

Navega a `https://gemini.google.com/app` para partir de una conversación limpia. Verifica que el textarea está disponible buscando con `find`:

```
query: "Introduce una petición para Gemini"
```

---

## Paso 3 — Subir fichero de contexto (solo si se proporcionó ruta)

### 3a — Instalar interceptor de createElement (llamada JS separada)

**Importante:** usar `document.createElement` override, NO MutationObserver. El MO es asíncrono y llega tarde; el override de createElement es síncrono — añade el listener de click ANTES de que Angular llame a `.click()`.

```javascript
var _orig = document.createElement.bind(document);
document.createElement = function(tag) {
  var el = _orig(tag);
  if (tag.toLowerCase() === 'input') {
    el.addEventListener('click', function(e) {
      if (el.type === 'file') {
        e.preventDefault();
        e.stopImmediatePropagation();
        window.__interceptedFileInput = el;
        el.id = '__claude_file_input';
        // Garantizar que esté en el DOM para que file_upload lo encuentre
        if (!document.contains(el)) {
          el.style.cssText = 'position:fixed;top:-200px;left:0;opacity:0.01;width:1px;height:1px';
          document.body.appendChild(el);
        }
        console.log('interceptado - inDOM:', document.contains(el));
      }
    }, true);
  }
  return el;
};
'interceptor listo'
```

### 3b — Abrir menú y seleccionar "Subir archivos"

Usa `computer` para clicks reales (gesto de usuario requerido por Chrome):

1. Toma screenshot para ver coordenadas del botón `+`
2. Click en el botón `+` con `computer left_click`
3. Click en "Subir archivos" del menú desplegable con `computer left_click`

### 3c — Verificar intercepción

```javascript
var el = window.__interceptedFileInput;
el ? 'ok - inDOM:' + document.contains(el) : 'NO interceptado'
```

Si `inDOM:false`, añadirlo manualmente al body:

```javascript
var el = window.__interceptedFileInput;
el.style.cssText = 'position:fixed;top:-200px;left:0;opacity:0.01;width:1px;height:1px';
document.body.appendChild(el);
document.contains(el) + ''
```

### 3d — Subir fichero con file_upload

Localiza el input con `find` (query: `"file input button"`) — será el input sin nombre / unnamed:

```
paths: ["D:\\BDDAT\\docs_prueba\\temp\\FICHERO.txt"]
ref: <ref del input interceptado>
```

### 3e — Disparar evento change para que Angular procese el fichero

```javascript
var el = window.__interceptedFileInput;
el.dispatchEvent(new Event('change', {bubbles: true}));
'files=' + el.files.length
```

Toma un screenshot para confirmar que el chip del fichero aparece en la UI de Gemini antes de continuar.

---

## Paso 4 — Inyectar pregunta, enviar y leer respuesta

### 4a — Inyectar texto (llamada JS separada)

Gemini usa un editor Quill. Usar `quill.insertText(..., 'user')` con source `'user'` para que Angular detecte el cambio. **No usar `quill.setText()`** — usa source `'api'` y Angular lo ignora; el texto queda visible pero no se envía.

```javascript
var quill = document.querySelector('rich-textarea').__quill;
quill.focus();
quill.deleteText(0, quill.getLength(), 'user');
quill.insertText(0, 'PREGUNTA_AQUI', 'user');
JSON.stringify({ texto: quill.getText().slice(0, 80) })
```

Verifica que el campo `texto` en el resultado contiene el inicio de la pregunta antes de continuar.

### 4b — Enviar y esperar respuesta (Promise)

⚠️ `await` de nivel raíz no está soportado en el evaluador de la extensión. Usar `Promise` directa:

```javascript
new Promise(function(resolve, reject) {
  var prevCount = document.querySelectorAll('model-response').length;
  document.querySelector('button[aria-label*="Enviar"]').click();

  var start = Date.now();
  var check = setInterval(function() {
    var n = document.querySelectorAll('model-response').length;
    var sending = document.querySelector('button[aria-label*="Detener"]');
    if (n > prevCount && !sending) {
      clearInterval(check);
      var responses = document.querySelectorAll('model-response');
      resolve(responses[prevCount].querySelector('message-content')?.innerText || 'sin texto');
    }
    if (Date.now() - start > 180000) { clearInterval(check); reject('timeout'); }
  }, 800);
})
```

---

## Paso 5 — Formular la pregunta

Construye la pregunta antes de inyectarla. No uses `$ARGUMENTS` literalmente — elabora un prompt claro que incluya:
- Contexto técnico del proyecto si es relevante (stack, dominio)
- La pregunta concreta
- El tipo de respuesta esperada (análisis, validación, alternativas...)

Si se ha subido un fichero de contexto, la pregunta puede referirse a él directamente ("En el proyecto adjunto...").

---

## Paso 6 — Sintetizar y responder

Lee el resultado del script JS. **No lo muestres al usuario directamente.** Presenta:
- Tu conclusión sobre la respuesta de Gemini
- Si coincide o difiere de tu propio criterio, y por qué
- Matices o advertencias relevantes que Gemini haya señalado

---

## Notas de comportamiento conocido

- **Interceptor createElement vs MutationObserver**: el MO llega tarde (asíncrono); el override de createElement es síncrono y garantizado. Siempre usar createElement override.
- **`quill.insertText(0, text, 'user')` obligatorio**: `quill.setText()` usa source `'api'` y Angular lo ignora — el texto queda visible pero no se envía. Con source `'user'` Angular lo procesa correctamente.
- **inDOM del input interceptado**: Angular a veces appenda el input al documento directamente; otras veces lo deja en un DIV detached. Siempre verificar con `document.contains(el)` y hacer `appendChild` al body si es false.
- **Título de pestaña**: solo cambia en la primera pregunta de una conversación nueva. No usarlo como indicador de respuesta completada.
- **Indicador fiable**: `model-response` count + ausencia del botón "Detener".
- **Refs dinámicos**: los refs de `find` cambian entre interacciones. Usar siempre `find` para relocalizar elementos en vez de reutilizar refs viejos.
- **Streaming**: si se lee la respuesta demasiado pronto, está incompleta. El polling del Paso 4 garantiza que el streaming terminó.
- **Conversación existente**: si se reutiliza un tab con historial, `prevCount` captura el estado previo correctamente y la lógica funciona igual.
