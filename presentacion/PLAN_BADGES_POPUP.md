# Plan: Badges SVG + Popups en S05

## Objetivo
Sustituir los `<strong>` de la sublista ESFTT por mini-badges SVG clicables
que abren un popup con detalle de cada nivel. La frase "Estructura en capas"
también clicable → popup con SVG completo (a preparar por el usuario).

---

## Lo que implementa Claude (ya hecho o pendiente)

### 1. CSS — en `tema-ja.css`
- `.esftt-badge` — cursor pointer, inline-flex, alineación vertical
- `.esftt-popup-overlay` — fondo semitransparente full-screen, z-index alto
- `.esftt-popup-box` — caja centrada, blanca, sombra, título + cuerpo + botón cerrar
- Animación entrada suave (opacity + scale)

### 2. HTML — en `index.html` S05
Sustituir en la sublista:
```
<strong>Expediente</strong>  →  <span class="esftt-badge" data-popup="expediente">[SVG_EXPEDIENTE]</span>
<strong>Solicitud</strong>   →  <span class="esftt-badge" data-popup="solicitud">[SVG_SOLICITUD]</span>
<strong>Fase</strong>        →  <span class="esftt-badge" data-popup="fase">[SVG_FASE]</span>
<strong>Trámite / Tarea</strong> →  <span class="esftt-badge" data-popup="tramite">[SVG_TRAMITE]</span>
                                 +  <span class="esftt-badge" data-popup="tarea">[SVG_TAREA]</span>
```

Frase "Estructura en capas":
```
<span class="esftt-badge esftt-capas" data-popup="capas">Estructura en capas</span>
```

Popups (divs ocultos al final de la sección):
```html
<div id="popup-expediente" class="esftt-popup-data" hidden>
  <h4>Expediente</h4>
  <p>El contenedor único ligado a un proyecto físico. Tipos: Transporte, Distribución, Renovable…</p>
</div>
<!-- ídem para solicitud, fase, tramite, tarea -->
<div id="popup-capas" class="esftt-popup-data" hidden>
  [SVG_CAPAS — a proporcionar por el usuario]
</div>
```

### 3. JS — bloque al final de `index.html`
- Al hacer clic en `.esftt-badge` → leer `data-popup` → mostrar overlay con contenido del popup correspondiente
- Cerrar al pulsar ESC, clic en overlay, o botón ×
- `stopPropagation` para que Reveal.js no capture el clic
- Reset del popup al cambiar de slide (`Reveal.on('slidechanged')`)

---

## Lo que hace el usuario

### SVG badges inline (pequeños, ~80×24px)
Uno por cada nivel, para sustituir los placeholders `[SVG_X]` en los `<span>`:
- `[SVG_EXPEDIENTE]` — rect blanco borde negro
- `[SVG_SOLICITUD]` — píldora azul claro `#c6dcff`
- `[SVG_FASE]` — rect melocotón `#f8d3af`
- `[SVG_TRAMITE]` — rect lavanda `#dedaff`
- `[SVG_TAREA]` — chevron/flecha verde `#adf0c7`

### SVG popup "Estructura en capas"
SVG completo (tamaño libre) para el popup de la frase introductoria.
Sustituye el placeholder `[SVG_CAPAS]` en `#popup-capas`.

---

## Orden de trabajo al retomar
1. Claude implementa CSS + JS + HTML con placeholders `[SVG_X]`
2. Usuario entrega los 6 SVGs (5 badges + 1 popup capas)
3. Claude sustituye los placeholders por los SVGs reales
4. Commit y push → GitHub Pages actualiza
