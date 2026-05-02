---
name: gemini
description: Consulta a Gemini 2.5 Flash como asesor externo y sintetiza su respuesta. Úsalo cuando necesites una segunda opinión sobre diseño, arquitectura o decisiones técnicas del proyecto.
argument-hint: "<pregunta_o_tema>"
allowed-tools: Bash, Write
---

Eres el intermediario entre el usuario y Gemini. Tu argumento es: `$ARGUMENTS`

**Nunca muestres la respuesta cruda de Gemini.** Lee la respuesta, razona sobre ella y presenta al usuario tu síntesis y conclusiones.

---

## Paso 1 — Decidir el contexto a enviar

Evalúa qué contexto necesita Gemini para responder bien:

**Contexto completo del proyecto** — cuando la pregunta afecta a la arquitectura global, modelos, flujos o algo que requiere visión de conjunto. Ejecuta el script y usa el fichero generado:

```bash
venv/Scripts/python.exe scripts/preparar_contexto.py
```
Fichero resultante: `D:\BDDAT\contexto_completo_gemini.txt`

⚠️ **Límite del modelo:** `gemini-2.5-flash` acepta hasta 1M tokens (~750 KB de texto puro; menos con código mezclado). El contexto completo del proyecto supera habitualmente ese límite. **Si el fichero resultante supera 3 MB, usa siempre contexto reducido.**

**Contexto reducido** — primera opción para preguntas sobre un subconjunto de ficheros (auditorías de docs, análisis de un módulo, revisiones de historial…). Compila un fichero temporal con solo lo relevante:
- Escribe a `docs_prueba/temp/contexto_gemini_reducido.txt` los fragmentos pertinentes
- Úsalo como fichero de contexto

Antes de llamar a `generateContent` con cualquier fichero grande, verifica que cabe con `countTokens`:

```python
count_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:countTokens?key=" + key
count_payload = {"contents": [{"parts": [
    {"file_data": {"file_uri": file_uri, "mime_type": "text/plain"}},
    {"text": "x"}
]}]}
req = urllib.request.Request(count_url, data=json.dumps(count_payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    tokens = json.load(r)["totalTokens"]
if tokens > 950_000:
    raise SystemExit(f"Contexto demasiado grande: {tokens:,} tokens. Reduce el fichero.")
```

**Sin fichero** — cuando la pregunta es conceptual o general y no requiere código del proyecto.

---

## Paso 2 — Formular el prompt para Gemini

Construye tú el prompt. No uses literalmente `$ARGUMENTS` como prompt — elabora una pregunta clara que incluya:
- El contexto técnico necesario (stack, dominio del proyecto si es relevante)
- La pregunta concreta
- Qué tipo de respuesta buscas (alternativas, validación, crítica...)

---

## Paso 3 — Llamar a la API

Escribe `docs_prueba/temp/gemini_ask.py` y ejecútalo con `python3 docs_prueba/temp/gemini_ask.py`.

**Sin fichero de contexto:**

```python
import os, urllib.request, json, sys

key = os.environ["GEMINI_API_KEY"]
prompt = """PROMPT_ELABORADO_AQUI"""

payload = {"contents": [{"parts": [{"text": prompt}]}]}
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + key
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    resp = json.load(r)
sys.stdout.buffer.write(resp["candidates"][0]["content"]["parts"][0]["text"].encode("utf-8"))
sys.stdout.buffer.write(b"\n")
```

**Con fichero de contexto (contexto completo o reducido):**

```python
import os, urllib.request, json, sys

key = os.environ["GEMINI_API_KEY"]
fichero = r"RUTA_ABSOLUTA_AL_FICHERO"
pregunta = """PREGUNTA_ELABORADA_AQUI"""

with open(fichero, "rb") as f:
    data = f.read()
upload_url = "https://generativelanguage.googleapis.com/upload/v1beta/files?key=" + key
req = urllib.request.Request(upload_url, data=data, headers={"Content-Type": "text/plain", "X-Goog-Upload-Protocol": "raw"})
with urllib.request.urlopen(req) as r:
    file_uri = json.load(r)["file"]["uri"]

payload = {"contents": [{"parts": [
    {"file_data": {"file_uri": file_uri, "mime_type": "text/plain"}},
    {"text": pregunta}
]}]}
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + key
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    resp = json.load(r)
sys.stdout.buffer.write(resp["candidates"][0]["content"]["parts"][0]["text"].encode("utf-8"))
sys.stdout.buffer.write(b"\n")
```

---

## Paso 4 — Sintetizar y responder

Lee la salida del script. **No la muestres al usuario.** Presenta:
- Tu conclusión sobre la respuesta de Gemini
- Si coincide o difiere de tu propio criterio, y por qué
- Si hay matices o advertencias relevantes que Gemini haya señalado

Si la llamada falla (429, 404, error de key), informa al usuario del error técnico.
