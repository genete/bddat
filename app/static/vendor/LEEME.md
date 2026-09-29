# app/static/vendor/ — componentes de terceros

Copia local de lo que la app cargaba de CDN externos (#984). **No se edita a mano:**
lo genera `scripts/vendorizar_jda.py`, que es también la vía para actualizar de versión.

## Qué hay y de dónde viene

Descargado el **2026-09-29**.

| Ruta | Componente | Origen | Licencia |
|---|---|---|---|
| `jda/css/custom-jda-bootstrap.css` | Tema Bootstrap de la Junta de Andalucía v1.2.5 (Bootstrap 5.3.3 compilado con la identidad corporativa) | `https://cdn.juntadeandalucia.es/components/sass/1.2.5/css/` | Titularidad de la Junta de Andalucía, sin licencia propia declarada en el fichero (ver «Licencia del tema»). Núcleo Bootstrap: MIT |
| `jda/css/fonts.css` | `@font-face` de Montserrat, Source Sans Pro y Font Awesome, de la misma versión | ídem | ídem |
| `jda/css/all.css` | Font Awesome Free 6.5.1 | ídem | Iconos CC BY 4.0, tipografías OFL 1.1, código MIT |
| `jda/js/bootstrap.bundle.min.js` | Bootstrap 5.3.3 JS (idéntico byte a byte al de npm) | `…/sass/1.2.5/js/` | MIT |
| `jda/fonts/montserrat/` | Montserrat 400 y 700 | `…/sass/1.2.5/fonts/` | OFL 1.1 |
| `jda/fonts/sourceSansPro/` | Source Sans Pro (12 variantes) | ídem | OFL 1.1 |
| `jda/fonts/fa-webfonts/` | Webfonts de Font Awesome Free 6.5.1 | ídem | OFL 1.1 |
| `bootstrap-icons/` | Bootstrap Icons 1.11.1 | `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/` | MIT |
| `licencias/` | Textos de licencia de lo anterior | npm y GitHub (ver el script) | — |

## Qué es literal y qué no

Todo es copia literal **salvo una modificación**: en `jda/css/fonts.css` y
`bootstrap-icons/bootstrap-icons.css` cada `src:` se reduce al formato **woff2**
(se quitan las referencias a `.woff`, `.ttf` y `.otf`, y esos ficheros no se
versionan). Los navegadores actuales solo piden woff2. Ambos ficheros lo dicen en
su primera línea.

## Licencia del tema de la Junta

Los ficheros del CDN solo declaran la licencia MIT de Bootstrap; no traen ninguna
para los valores del tema. BDDAT es de la misma titularidad (Junta de Andalucía,
EUPL v1.2, ver `LICENSE`), y el tema se redistribuye con BDDAT bajo los términos con
que la Junta publica su CDN y, a falta de otros expresos, bajo la EUPL v1.2.

## Particularidades del original (no se corrigen: es copia literal)

- `fonts.css` línea 19 dice `font-face{` en vez de `@font-face{`: la variante
  ExtraLight (peso 200) de Source Sans Pro no llega a declararse. Ninguna pantalla
  la usa.
- El tema cambia los puntos de corte de Bootstrap: `xl` = 1300 px y **no hay punto
  de corte `xxl`** (solo queda `--bs-border-radius-xxl`). Ningún template ni CSS
  de la app usa clases `*-xxl-*`.

## Cómo actualizar

1. Cambiar las versiones al inicio de `scripts/vendorizar_jda.py`.
2. `python scripts/vendorizar_jda.py`
3. Revisar el diff, pasar las capturas de #984 (login, listados, árbol, modal, 1920 y
   1280 px) y comparar con las anteriores.
4. Actualizar la fecha y las versiones de esta tabla y de `LICENSE`.
