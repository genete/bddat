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

Si el argumento incluye una ruta de fichero, sigue este flujo exacto. Los clicks deben ser **reales** (con `computer`), no JavaScript — Chrome requiere gesto de usuario real para activar el file picker.

1. Haz click en el botón "Abrir menú para subir archivos" con `find` + `computer left_click`
2. Haz click en el menuitem "Subir archivos" con `find` + `computer left_click`
3. Localiza el `input[type=file]` generado con `find` (query: "file input")
4. Sube el fichero con `file_upload` usando la ruta absoluta

```
# Ejemplo de ruta válida:
paths: ["D:\\BDDAT\\docs_prueba\\temp\\contexto_reducido_historial.txt"]
```

Si `file_upload` falla con "Not allowed": la opción "Allow access to file URLs" no está activada en la extensión (ver prerequisitos).

---

## Paso 4 — Inyectar pregunta, enviar y leer respuesta (una sola llamada JS)

Usa `javascript_tool` con este script. Captura `prevCount` antes de enviar para saber cuál es la respuesta nueva:

```javascript
await (async () => {
  // 1. Inyectar texto en el contenteditable
  const box = document.querySelector('div[contenteditable="true"]');
  box.focus();
  box.innerText = `PREGUNTA_AQUI`;
  box.dispatchEvent(new Event('input', { bubbles: true }));

  // 2. Contar respuestas actuales y pulsar enviar
  const prevCount = document.querySelectorAll('model-response').length;
  document.querySelector('button[aria-label*="Enviar"]').click();

  // 3. Polling: esperar nueva respuesta completa (botón Stop desaparece)
  await new Promise((resolve, reject) => {
    const start = Date.now();
    const check = setInterval(() => {
      const n = document.querySelectorAll('model-response').length;
      const sending = document.querySelector('button[aria-label*="Detener"]');
      if (n > prevCount && !sending) { clearInterval(check); resolve(); }
      if (Date.now() - start > 120000) { clearInterval(check); reject('timeout'); }
    }, 800);
  });

  // 4. Extraer la nueva respuesta
  const responses = document.querySelectorAll('model-response');
  return responses[prevCount].querySelector('message-content')?.innerText || 'sin texto';
})()
```

Sustituye `PREGUNTA_AQUI` por la pregunta elaborada (ver Paso 5).

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
