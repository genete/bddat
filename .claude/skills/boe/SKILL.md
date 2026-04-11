---
name: boe
description: Lee artículos concretos de legislación consolidada del BOE estatal usando la API REST o Playwright. Para legislación andaluza (BOJA) usar /boja.
argument-hint: "<ELI_URL_o_referencia> [artículo N | disposición adicional X | índice | buscar: texto]"
allowed-tools: Bash, WebFetch, mcp__playwright__browser_navigate, mcp__playwright__browser_evaluate, mcp__windows-mcp__PowerShell
---

Eres un asistente especializado en navegar la legislación consolidada del BOE **estatal** de forma eficiente.
Tu argumento es: `$ARGUMENTS`

---

## CONOCIMIENTO DEL BOE

### Formato ELI (European Legislation Identifier)
```
https://www.boe.es/eli/{país}/{tipo}/{año}/{mes}/{día}/{número}/con
```
- `con` al final = versión consolidada
- Tipos: `l`=Ley, `lo`=Ley Orgánica, `rd`=Real Decreto, `rdl`=Real Decreto-ley, `rdleg`=Real Decreto Legislativo, `o`=Orden ministerial, `res`=Resolución

### API REST de datos abiertos

**Base:** `https://www.boe.es/datosabiertos/api/legislacion-consolidada`
**Cabecera obligatoria:** `Accept: application/xml` (WebFetch no sirve — no soporta cabeceras custom; usar `curl`)

| Endpoint | Resultado | Formato |
|---|---|---|
| `/id/{BOE-ID}/texto/indice` | Índice con ids y títulos de todos los bloques | XML, JSON |
| `/id/{BOE-ID}/texto/bloque/{id_bloque}` | Un único bloque (artículo, sección...) con todas sus versiones históricas | XML |
| `/id/{BOE-ID}/metadatos` | Metadatos de la norma | XML, JSON |

- `{BOE-ID}` = identificador tipo `BOE-A-2000-24019`
- `{id_bloque}` = mismo id que el ancla HTML: `a52`, `a123`, `ir-20`, `ti`, `daprimera`...

### IDs de bloque — mismos que anclas HTML

| Sección | id_bloque | Notas |
|---|---|---|
| Preámbulo | `preambulo` o `pr` | |
| Título I, II... | `ti`, `tii`, `tiii`... | Romanos en minúscula |
| Capítulo I (1ª aparición) | `ci` | |
| Capítulo I (2ª aparición) | `ci-2` | Sufijo incremental, no predecible → consultar índice |
| Sección 1 (1ª) | `s1` | |
| Artículo 52 | `a52` | |
| Artículo 59 bis | `a59bis` | |
| Artículo 110 ter | `a110ter` | |
| Disposición Adicional 1ª | `daprimera` | |
| Disposición Transitoria 1ª | `dtprimera` | |
| Disposición Derogatoria única | `ddunica` o `dd` | |
| Disposición Final 1ª | `dfprimera` o `df` | |
| Firma | `firma` o `fi` | |
| Anexo | `an` | |
| ITC-RAT N (reglamentos técnicos) | `ir-N` | No predecible → consultar índice |

**Ordinal → texto:** primera, segunda, tercera, cuarta, quinta, sexta, séptima, octava, novena, décima, undécima, duodécima, decimotercera...

### Reglamentos con ITCs (ej: RD 337/2014 — RAT)
- Cada ITC tiene id `ir-N` — no predecible sin consultar el índice primero
- Una ITC entera puede estar en un único bloque grande → búsqueda de texto interna con Playwright

---

## COSTE DE CONTEXTO — CUÁNDO USAR QUÉ

| Caso | Herramienta | Coste en contexto |
|---|---|---|
| Artículo(s) conocido(s), 1-2 artículos | **curl \| python** (API) | ~7 KB por artículo |
| Artículo(s) conocidos, 3+ artículos de la misma ley | **Playwright** (navegar una vez, evaluar N veces) | ~7 KB × N (navigate amortizado) |
| Índice de la ley | **curl** (API `/texto/indice`) | pequeño |
| Búsqueda inversa (no sé qué artículo) | **Playwright** (buscar en DOM) | navigate + pequeño |
| Búsqueda dentro de bloque grande (ITC) | **Playwright** (evaluate + indexOf) | pequeño |

---

## FLUJO A — API REST con curl (artículos concretos)

### Paso 1 — Obtener el BOE-ID desde la URL ELI

La URL ELI no contiene el BOE-ID. Obtenerlo con WebFetch:
```
WebFetch(url="https://www.boe.es/eli/es/rd/2000/12/01/1955/con",
         prompt="Extrae el identificador con formato BOE-A-XXXX-XXXXX del enlace canonical")
```
La página HTML contiene `<link rel="canonical" href="...act.php?id=BOE-A-2000-24019">`.

### Paso 2 — Obtener artículo con curl | python (piped — XML nunca toca el contexto)

```bash
curl -s -H "Accept: application/xml" \
  "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2000-24019/texto/bloque/a115" \
| python - << 'EOF'
import xml.etree.ElementTree as ET, sys
tree = ET.parse(sys.stdin)
root = tree.getroot()
bloque = root.find('.//bloque')
versiones = bloque.findall('version')
ultima = versiones[-1]  # versión más reciente
lines = [f"# {bloque.get('titulo','')}", f"*Vigente desde: {ultima.get('fecha_vigencia') or ultima.get('fecha_publicacion')}*", ""]
for elem in ultima:
    if elem.tag == 'blockquote': continue  # omitir notas al pie
    texto = ''.join(elem.itertext()).strip()
    cls = elem.get('class','')
    if not texto: continue
    if cls == 'articulo': lines.append(f"## {texto}")
    elif cls == 'parrafo_2': lines.append(f"  {texto}")
    else: lines.append(texto)
    lines.append("")
print('\n'.join(lines))
EOF
```

**IMPORTANTE:** En Windows el heredoc `<< 'EOF'` puede fallar con bash. Si falla, escribir el script a `docs_prueba/temp/parse.py` con la tool `Write` y usar `curl ... | python docs_prueba/temp/parse.py`. Eliminar temp tras uso.

### Paso 3 — Índice de la ley (cuando no se conoce el id del bloque)

```bash
curl -s -H "Accept: application/xml" \
  "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/BOE-A-2000-24019/texto/indice" \
| python - << 'EOF'
import xml.etree.ElementTree as ET, sys
root = ET.parse(sys.stdin).getroot()
for b in root.findall('.//bloque'):
    print(f"{b.findtext('id'):20} {b.findtext('titulo')}")
EOF
```

---

## FLUJO B — Playwright (búsqueda inversa / múltiples artículos / bloques grandes)

### Navegar y minimizar

```
mcp__playwright__browser_navigate(url=ELI_URL_consolidada)
# Ignorar output — guardado en fichero automáticamente, no leerlo
```
```powershell
# mcp__windows-mcp__PowerShell — minimizar ventana BOE:
Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);' -Name WinAPI -Namespace Win32 -ErrorAction SilentlyContinue; Get-Process chrome | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'boe\.es|BOE-A-' } | ForEach-Object { [Win32.WinAPI]::ShowWindow($_.MainWindowHandle, 6) }
```

### Leer artículo conocido

```javascript
() => { const el = document.getElementById('a115'); return el ? el.innerText : 'No encontrado'; }
```

### Varios artículos a la vez

```javascript
() => ['a115','a116','a117'].map(id => { const el = document.getElementById(id); return { id, texto: el ? el.innerText : 'No encontrado' }; })
```

### Búsqueda inversa — encontrar qué artículo regula algo

```javascript
() => {
  const resultados = [];
  document.querySelectorAll('#textoxslt .bloque').forEach(b => {
    const t = b.innerText.toLowerCase();
    if (t.includes('término1') && t.includes('término2')) {
      const h = b.querySelector('h4,h5');
      resultados.push({ id: b.id, titulo: h?.innerText.trim(), fragmento: b.innerText.substring(0,300) });
    }
  });
  return resultados;
}
```

### Búsqueda dentro de bloque grande (ITC completa en un solo div)

```javascript
() => {
  const el = document.getElementById('ir-20');
  const texto = el?.innerText || '';
  const idx = texto.toLowerCase().indexOf('palabra clave');
  if (idx === -1) return { encontrado: false };
  return { encontrado: true, fragmento: texto.substring(Math.max(0, idx-300), idx+600) };
}
```

### Índice via DOM (si Playwright ya está abierto)

```javascript
() => [...document.getElementById('lista-marcadores').querySelectorAll('a')]
  .map(a => ({ id: a.getAttribute('href').replace('#',''), texto: a.textContent.trim() }))
```

---

## CONSTRUCCIÓN DEL id_bloque DESDE REFERENCIA TEXTUAL

| Referencia | id_bloque |
|---|---|
| "artículo 52" | `a52` |
| "art. 59 bis" | `a59bis` |
| "artículo 110 ter" | `a110ter` |
| "artículo 132 quater" | `a132quater` |
| "DA 1ª" / "disposición adicional primera" | `daprimera` |
| "DT 3ª" | `dttercera` |
| "DF 5ª" | `dfquinta` |
| "título IV" | `tiv` |
| "capítulo II del título III" | Consultar índice (sufijo `-N` no predecible) |
| "ITC-RAT 20" | `ir-20` (confirmar en índice) |

---

## NOTAS

- El BOE indexa legislación andaluza **de rango de Ley** (Leyes del Parlamento de Andalucía) pero no la de rango inferior (Decretos, Decreto-leyes, Órdenes) — para esas, usar `/boja`.
- Si el bloque aparece `(Derogado)`, indicarlo claramente con la norma derogatoria.
- La API devuelve versiones históricas — usar siempre la última `<version>` (la más reciente).
- El navigate de Playwright consume mucho contexto si se lee: **no leer su output nunca**.
- Si el navegador ya tiene cargada la ley correcta, no navegar de nuevo.
- Ficheros temporales: `docs_prueba/temp/` (gitignored). Borrar tras uso.
