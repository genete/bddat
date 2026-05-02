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

Chrome abre un diálogo nativo de selección de fichero cuando Gemini activa el `<input type=file>`. Para evitarlo, instala un interceptor JS **antes** de pulsar el menú:

```javascript
// Paso 3a — Interceptor: bloquea el click del input antes de que Chrome abra el diálogo
window.__fileInput = null;
var obs = new MutationObserver(function(muts) {
  muts.forEach(function(m) {
    m.addedNodes.forEach(function(n) {
      if (n.nodeName === 'INPUT' && n.type === 'file') {
        window.__fileInput = n;
        n.addEventListener('click', function(e) {
          e.stopImmediatePropagation(); e.preventDefault();
        }, true);
      }
    });
  });
});
obs.observe(document.body, { childList: true, subtree: true });
window.__fileObserver = obs;
'interceptor listo'
```

Luego el flujo de clicks (reales con `computer`):
1. Click en "Abrir menú para subir archivos" con `find` + `computer left_click`
2. Click en menuitem "Subir archivos" con `find` + `computer left_click`
3. Recupera el input interceptado y asígnale un id para localizarlo:

```javascript
window.__fileObserver.disconnect();
var el = window.__fileInput;
if (el) { el.id = '__claude_file_input'; 'ok: ' + el.accept; }
else 'no encontrado';
```

4. Localiza el ref con `find` (query: `"__claude_file_input"`) y sube con `file_upload`

```
paths: ["D:\\BDDAT\\docs_prueba\\temp\\contexto_reducido_historial.txt"]
```

⚠️ **Limitación conocida**: el interceptor puede no ser suficiente en todas las versiones de Chrome — el diálogo nativo puede abrirse igualmente. Si el usuario reporta que el diálogo está abierto, pedirle que lo cierre manualmente (botón Cancelar del diálogo) antes de continuar con el Paso 4.

Si `file_upload` falla con "Not allowed": activar "Permitir acceso a URL de archivo" en `chrome://extensions/` → extensión Claude in Chrome.

---

## Paso 4 — Inyectar pregunta, enviar y leer respuesta

### 4a — Inyectar texto (llamada JS separada)

Usa `execCommand('insertText')` — **no** `box.innerText =`, que no activa el estado interno de React de Gemini:

```javascript
var box = document.querySelector('div[contenteditable="true"]');
box.focus();
document.execCommand('selectAll', false, null);
document.execCommand('insertText', false, 'PREGUNTA_AQUI');
JSON.stringify({ texto: box.innerText.slice(0, 80) })
```

Verifica que el campo `texto` en el resultado contiene el inicio de la pregunta antes de continuar.

### 4b — Enviar y esperar respuesta (Promise)

⚠️ `await` de nivel raíz no está soportado en el evaluador de la extensión. Usa una `Promise` directa — el evaluador la resuelve antes de devolver el resultado:

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

- **Título de pestaña**: solo cambia en la primera pregunta de una conversación nueva. No usarlo como indicador de respuesta completada.
- **Indicador fiable**: `model-response` count + ausencia del botón "Detener".
- **Refs dinámicos**: los refs de `read_page`/`find` cambian entre interacciones. Usar siempre `find` para relocalizar elementos en vez de reutilizar refs viejos.
- **Streaming**: si se lee la respuesta demasiado pronto, está incompleta. El polling del Paso 4 garantiza que el streaming terminó.
- **Conversación existente**: si se reutiliza un tab con historial, `prevCount` captura el estado previo correctamente y la lógica funciona igual.
