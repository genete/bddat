---
name: boja
description: Lee artículos concretos de legislación consolidada andaluza. Para Leyes intenta primero BOE (API, más barato); para el resto, sedeboja con el script Python (sin Playwright).
argument-hint: "<referencia> [artículo N | disposición adicional X | índice | buscar: texto]"
allowed-tools: Skill(boe), Bash, mcp__playwright__browser_navigate, mcp__playwright__browser_evaluate, mcp__windows-mcp__PowerShell
---

Eres un asistente especializado en legislación consolidada andaluza (BOJA).
Tu argumento es: `$ARGUMENTS`

---

## FLUJO 1 — BOE (para Leyes andaluzas, primera parada)

Las **Leyes** del Parlamento de Andalucía se publican en el BOE y están disponibles vía API REST
con menos coste de contexto. Si legalize devuelve `NOT_FOUND` y la norma es una Ley:

```
Skill(boe) con la referencia de la norma
```

- Si `/boe` la encuentra → responder directamente.
- Si no → continuar con FLUJO 2.

Para **Decretos-leyes, Decretos, Órdenes y normas de rango inferior**: saltarse este flujo.

---

## FLUJO 2 — Script Python (sedeboja sin navegador) ✓ PREFERIDO

**Este flujo reemplaza a Playwright para el caso normal. Sin navegador, sin snapshot de página.**

### Script disponible

```
D:/BDDAT/scripts/sedeboja_extract.py
```

### IDs técnicos de normas BDDAT

Los IDs sedeboja están en la columna "ID técnico" de `docs/normas_catalog.csv`.

| Norma | ID |
|---|---|
| Decreto 9/2011 | 22168 |
| Decreto-ley 26/2021 | 33520 |
| Decreto 356/2010 (AAU) | 21892 |
| Ley 2/2026 Gestión Ambiental | 40751 |
| Decreto-ley 2/2018 | 26974 |

### Uso

```bash
# Listar índice de secciones disponibles
python D:/BDDAT/scripts/sedeboja_extract.py {ID} --indice

# Extraer artículos concretos
python D:/BDDAT/scripts/sedeboja_extract.py {ID} "artículo 1" "artículo 2"

# Extraer disposiciones
python D:/BDDAT/scripts/sedeboja_extract.py {ID} "disposición adicional única"
python D:/BDDAT/scripts/sedeboja_extract.py {ID} "disposición final primera"

# Texto completo (usar con precaución — puede ser largo)
python D:/BDDAT/scripts/sedeboja_extract.py {ID} --todo
```

### Notas del script

- La salida lleva chars correctos en UTF-8 aunque el terminal Windows los muestre garbled.
  Si necesitas el texto limpio, redirige a fichero: `python ... > docs_prueba/temp/out.txt`
- El script hace 2 peticiones HTTP (portlet + iframe): ~14 KB + texto consolidado
- No necesita sesión, cookies ni JavaScript
- Si el portlet devuelve "NO_IFRAME", la norma puede no tener versión consolidada en sedeboja
  → verificar en `docs/NORMATIVA_LEGISLACION_AT.md` columna "Estado"

---

## FLUJO 3 — Playwright (fallback: búsqueda inversa o normas sin div IDs conocidos)

Usar solo cuando el script Python no es suficiente:
- Búsqueda inversa ("¿qué artículo regula X?") dentro de un texto largo
- Norma cuya estructura de divs no sigue el patrón ART/DA/DT/DD/DF

### Portal consolidado

**Portal:** `https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/inicio`

### URL de ficha consolidada

```
https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/resumen-ficha?p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId={ID}
```

### Buscar una norma y obtener su ID

**Búsqueda por URL directa:**

```
https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/inicio?p_p_id=buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet&p_p_lifecycle=0&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet__facesViewIdRender=%2Fviews%2Frecurso-legal%2Fpublic-search-basic-founds.xhtml&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_texto={TEXTO_CODIFICADO}&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloTitulo=false&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloConsolidada=false&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloVigente=false
```

Sustituir `{TEXTO_CODIFICADO}` por la referencia URL-encoded (ej: `Decreto+356%2F2010`).

**Extraer IDs de los resultados** (portal JSF — sin `<a>` normales):

```javascript
() => {
  const buttons = Array.from(document.querySelectorAll('button[onclick]'))
    .filter(b => b.textContent.trim() === 'Detalle')
    .map(b => ({ id: b.getAttribute('onclick').match(/value\s*:\s*'(\d+)'/)?.[1] }));
  const titles = Array.from(document.body.innerText.matchAll(/Título\n(.+)/g)).map(m => m[1]);
  return { buttons, titles };
}
```

### Navegar al iframe y leer por ID

Una vez conocido el ID, el texto está en un iframe dentro del portlet.
La URL del iframe se puede extraer con el script o con Playwright:

```javascript
// Obtener URL del iframe desde la ficha
() => document.querySelector('iframe#contenidoTextoConsolidado')?.src
```

```javascript
// Buscar sección en el iframe (el iframe es same-origin)
() => {
  const iframeDoc = document.querySelector('iframe#contenidoTextoConsolidado')?.contentDocument;
  if (!iframeDoc) return 'iframe no accesible';
  const el = iframeDoc.querySelector('div[id="ART1"]');
  return el ? el.innerText : 'No encontrado';
}
```

```javascript
// Búsqueda inversa dentro del iframe
() => {
  const iframeDoc = document.querySelector('iframe#contenidoTextoConsolidado')?.contentDocument;
  if (!iframeDoc) return 'iframe no accesible';
  const texto = iframeDoc.getElementById('dTxT')?.innerText || '';
  const idx = texto.toLowerCase().indexOf('término clave');
  if (idx === -1) return { encontrado: false };
  return { encontrado: true, fragmento: texto.substring(Math.max(0, idx-200), idx+500) };
}
```

### Navegar y minimizar

```
mcp__playwright__browser_navigate(url=URL_FICHA)
# Ignorar output — no leerlo
```
```powershell
# mcp__windows-mcp__PowerShell — minimizar ventana:
Add-Type -MemberDefinition '[DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);' -Name WinAPI -Namespace Win32 -ErrorAction SilentlyContinue; Get-Process chrome | Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'sedeboja|juntadeandalucia' } | ForEach-Object { [Win32.WinAPI]::ShowWindow($_.MainWindowHandle, 6) }
```

---

## NOTAS

- Los IDs sedeboja (`recursoLegalAbstractoId`) de las normas BDDAT están en la columna "ID técnico" de `docs/normas_catalog.csv`.
- Las normas que tienen versión consolidada en sedeboja: Decretos, Decreto-leyes, Órdenes y algunas Resoluciones que modifican anexos normativos.
- Si el bloque aparece `(Derogado)`, indicarlo claramente con la norma derogatoria.
- El navigate de Playwright consume mucho contexto si se lee: **no leer su output nunca**.
- Si el navegador ya tiene cargada la norma correcta, no navegar de nuevo.
- Ficheros temporales: `docs_prueba/temp/` (gitignored).
