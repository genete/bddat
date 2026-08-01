---
name: cobertura
description: Revisa los issues cerrados desde la última actualización de MATRIZ_COBERTURA_BDDAT.md y prepara una propuesta de actualización, delegando la investigación a un agente en background. Filas que solo suben/bajan por cierre normal se aplican tras un visto bueno único; hallazgos que corrigen algo que la matriz ya afirmaba se señalan aparte y exigen confirmación explícita fila a fila.
argument-hint: ""
allowed-tools: Agent, Bash(git *), Bash(gh *), Read, Edit, Write
---

Ejecuta (o retoma) el ciclo de actualización de `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` para BDDAT.

## Contexto actual

- Último commit que tocó la matriz: !`git -C /d/BDDAT log -1 --format="%H %ad %s" -- "docs/diseño/MATRIZ_COBERTURA_BDDAT.md"`
- Rama actual: !`git -C /d/BDDAT branch --show-current`
- Propuestas ya generadas en temp: !`ls /d/BDDAT/docs_prueba/temp/ 2>/dev/null | grep -i propuesta_matriz`

## Pasos a seguir

### 0. Si ya hay una propuesta esperando revisión

Si el contexto de arriba muestra un `propuesta_matriz_*.md` que aún no le has presentado a
Carlos en esta conversación, ve directo al paso 3 — no relances el agente de investigación.

### 1. Lanzar el agente de investigación (background)

No investigues tú mismo el histórico de issues — es agregación mecánica (git log, `gh issue
list/view`, cruce de labels), perfecta para delegar. Lanza un agente `general-purpose` con
`Agent`, en **background** (no pases `run_in_background: false`), con un prompt autocontenido
— el agente arranca sin memoria de esta conversación — que incluya como mínimo:

- Hash y fecha del último commit que tocó la matriz (del contexto de arriba) y el working
  directory (`D:\BDDAT`).
- **Investigar:** listar issues cerrados desde esa fecha
  (`gh issue list --state closed --search "closed:>=<fecha>"`), leer cuerpo y labels
  `necesidad:N0XX` de cada uno, y el/los commits que lo cierran (`git log <hash>..HEAD`) para
  entender qué cambió de verdad en el código — el mensaje de commit de este proyecto suele ser
  suficiente, pero si la duda es sobre una fila que la matriz ya daba por cerrada, hay que leer
  el diff real (`git show <hash> -- <fichero>`), no fiarse solo de la prosa del issue.
- **Contrastar, no solo sumar:** para cada `N0XX` afectada, leer su fila actual en
  `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` y comprobar si lo que dice sigue siendo cierto — no
  asumir que un cierre de issue solo añade cobertura. Si el código real contradice algo que la
  fila ya afirmaba (un mecanismo que la matriz da por activo y no lo está, o al revés), es un
  **hallazgo de máxima prioridad**, distinto de una actualización rutinaria — típicamente
  aparece cuando un issue investiga un camino "vivo" y encuentra que no lo es (ver el propio
  historial de la matriz: N003 tras #722 es el caso de referencia).
- Leer la cabecera de la matriz (primeras ~17 líneas) para el estilo y la filosofía ("Fuente
  del %: código real... nunca issues", sin filas "pendiente de verificar") y las labels
  `necesidad:N0XX` abiertas de cada necesidad tocada, para no dar por cerrado un frente que
  sigue en cola.
- **Nunca tocar ficheros versionados del repo ni hacer commit.** El entregable es un fichero
  nuevo en `docs_prueba/temp/propuesta_matriz_<fecha-ISO>.md` — comprobar antes que el nombre
  no colisiona con uno existente (si colisiona, sufijo `-v2`, `-v3`...; nunca leer ni
  sobrescribir un temp existente sin comprobar antes) — con esta estructura:
  1. Tabla resumen: `Necesidad | % actual | % propuesto | Motivo (una línea)`.
  2. Propuesta fila a fila, con el texto completo listo para pegar tal cual en la tabla real
     (mismo tono conciso y denso en datos/referencias a issues que las filas existentes).
  3. Sección aparte **"Hallazgos que requieren confirmación explícita"** — solo lo que
     contradice algo que la matriz ya afirmaba (no una subida/bajada normal), con cita de
     código (fichero + función/línea) e issue que lo sostiene.
  4. Nota de coordinación: qué issues abiertos comparten necesidad con lo cerrado y podrían
     dejar la fila desactualizada otra vez pronto.

Informa a Carlos de que el agente está investigando en background y que avisarás al terminar.

### 2. Cuando el agente termine

Lee el fichero de propuesta que ha escrito.

### 3. Presentar a Carlos

- Enseña primero la tabla resumen del §1 de la propuesta.
- Las filas que solo suben o bajan por cierre normal de issues se aplican tras un único visto
  bueno genérico ("adelante", "aplica") — no hace falta confirmarlas una a una.
- La sección "Hallazgos que requieren confirmación explícita" **nunca se aplica sin que Carlos
  la confirme explícitamente**, fila a fila o en bloque pero de forma consciente — no vale un
  "sí" genérico a toda la propuesta. La cabecera de la propia matriz declara que su fuente es
  "código real, verificado, sin filas pendientes de verificar": una corrección de ese tipo
  pesa más que una actualización rutinaria y merece que Carlos la lea, no solo que la apruebe
  de pasada.

### 4. Aplicar y commitear

Tras la confirmación de Carlos:

- Edita `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` fila a fila con la tool `Edit` (nunca
  reescribas el fichero entero).
- Comprueba integridad de la tabla antes de dar por bueno el cambio: cada fila `| N0XX | ... |`
  debe tener el mismo número de `|` que las demás (un script rápido en `docs_prueba/temp/`
  basta, igual que en la sesión de referencia del 2026-08-01).
- `git add "docs/diseño/MATRIZ_COBERTURA_BDDAT.md"` — solo ese fichero, nunca `-A` ni `.`.
- Mensaje de commit: `[DOCS] Actualizar matriz de cobertura tras cierre de #<issues>` —
  escríbelo en un fichero único de `docs_prueba/temp/` y commitea con `git commit -F` (nunca
  `-m` con `$(cat ...)`, lo bloquea el guard de `REGLAS_BASH.md`).
- No borres el fichero de propuesta de `docs_prueba/temp/` — lo gestiona Carlos manualmente.

## Notas

- Este skill asume que ya existe `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` con su formato
  habitual (tabla por bloque, columna "Qué falta" densa en referencias a issues). Si el
  fichero cambia de estructura, actualiza este skill a la vez (es un derivado de facto de su
  formato, aunque no esté registrado en la tabla de `REGLAS_ARQUITECTURA.md` — no es un
  documento de diseño, es una convención de skill).
- Si Carlos pide "aplica ya todo, sin pasar por confirmación de hallazgos", recuérdale en una
  frase que eso contradice la garantía de la propia matriz antes de hacerlo — y hazlo solo si
  insiste.
