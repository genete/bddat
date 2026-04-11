---
name: gemini-share
description: Lee el contenido de una conversación pública compartida de Gemini y lo devuelve como texto plano para analizar.
argument-hint: "<URL_compartida_de_Gemini>"
allowed-tools: mcp__playwright__browser_navigate, mcp__playwright__browser_click, mcp__playwright__browser_evaluate
---

Lee el contenido de la conversación pública de Gemini en esta URL: `$ARGUMENTS`

Sigue estos pasos en orden:

## Paso 1 — Navegar a la URL

Navega a la URL proporcionada.

## Paso 2 — Gestionar la pantalla de consentimiento de Google

Si la URL de la página resultante contiene `consent.google.com`, busca el botón "Rechazar todo" en el snapshot y haz clic en él. Espera a que la página cargue la conversación.

Si la URL ya es `gemini.google.com/share/...`, salta al paso 3.

## Paso 3 — Extraer el texto

Evalúa este JavaScript para obtener el texto limpio de la conversación:

```javascript
() => document.body.innerText
```

## Paso 4 — Presentar el resultado

Muestra el contenido extraído directamente en el chat, omitiendo los elementos de navegación de la interfaz de Gemini (menú superior, pie de página, botones). Céntrate en los turnos de conversación: mensajes del usuario y respuestas de Gemini.
