# ADR-039 — Datos institucionales del órgano propio: unidades, firmantes y catálogo RPS

**Estado:** Adoptada — pendiente de implementación
**Fecha:** 2026-08-04
**Origen:** #728, informado por una sesión de estudio de campo en vivo del DOM de BandeJA/Port@firmas (`docs/referencia/ESTUDIO_DOM_BANDEJA.md`)
**Relacionado:** ADR-021 §4 (firmantes ya identificados como dato a catalogar), ADR-025 (Capa 1 vs Context Builder), ADR-035 §4 (origen del hueco de tokens), #757 (catálogo RPS), #758 (gemelo de #659, automatización de envío a Port@firmas)

---

## Contexto

#728 detectó que los escritos generados necesitan datos del órgano emisor (consejería, sede, firmantes) que hoy no existen en BDDAT. Antes de decidir modelo hacía falta saber **qué pide realmente el sistema externo al que estos datos alimentan** — BandeJA/Port@firmas —, así que se hizo un estudio de campo en vivo con navegador real (login, alta de comunicación, envíos de prueba reales, firma real de dos comunicaciones) en lugar de diseñar en abstracto. El estudio completo, con selectores y mecanismos verificados, vive en `docs/referencia/ESTUDIO_DOM_BANDEJA.md`.

Hallazgos que condicionan el modelo:

- **No existe ningún campo de provincia/unidad orgánica** ni en `Usuario` ni en `Expediente`. Lo único parecido, `Proyecto.provincias_afectadas`, refleja dónde está la instalación física, no qué servicio tramita.
- **El envío a Port@firmas usa el destino del usuario que envía** (su propio puesto de trabajo en BandeJA), no la provincia de la instalación — confirmado explícitamente por Carlos, y coherente con que BandeJA solo permite tener un puesto activo por sesión de login.
- **Buscar firmante por nombre en BandeJA da homónimos**; buscar por DNI da resultado único. Verificado en vivo con un caso real (dos personas distintas con el mismo nombre, en organismos distintos).
- **El firmante que de verdad firma un oficio/resolución puede no ser usuario de BDDAT** (Delegado/a Territorial, Consejero/a) — BDDAT lo usan tramitadores y técnicos, no necesariamente la autoridad firmante.
- **El RPS no es obligatorio en el formulario de BandeJA**, pero Carlos señala un antecedente real: una auditoría pasada detectó el mismo código de RPS reutilizado indiscriminadamente para todo. No es un campo que se pueda dejar sistemáticamente vacío o con un valor cualquiera sin riesgo de repetir ese hallazgo.
- `docs/referencia/DISEÑO_ANALISIS_SOLICITUD.md` §8 ya decidió **"no crear tabla de firmantes"** — pero es un concepto distinto (cómo queda el bloque de cierre en el *texto* del escrito, resuelto con fragmentos `.docx`). El firmante de este ADR es "qué persona con DNI se busca en el cuadro de Port@firmas" — un problema de automatización/integración, no de redacción. No es un precedente que bloquee esta decisión, solo comparte nombre.
- No existe tabla de catálogo DIR3 propia en BDDAT: el patrón más cercano (N081, organismos externos) vive en la tabla genérica `entidades`, poblada operativamente por el tramitador según aparecen interesados — no es un catálogo curado por el Supervisor, y modela organismos *externos*, no la propia casa. No es reutilizable tal cual para el órgano emisor propio.

---

## Decisión

### 1. `unidades_organo_propio`, atada a `Usuario` — no a `Expediente`

Tabla catálogo nueva, curada a mano por el Supervisor: nombre, provincia (nullable, para servicios centrales), sede_direccion, sede_telefono, sede_correo, consejeria_nombre, codigo_bandeja_texto (el rótulo tal cual aparece en BandeJA, para localizarlo por texto en la automatización — **no** su `id`, que en el árbol de BandeJA viene vacío en 7 de 73 nodos y no es fiable como clave).

Se puebla con **las 8 delegaciones territoriales (servicio de energía por provincia) + los centrales relevantes desde el principio** — no las 73 filas completas del árbol de BandeJA, pero tampoco solo la delegación del despliegue actual. El coste es marginal: el dato ya está extraído en `app/data/bandeja_destinos/`. Motivo: aunque BDDAT es hoy mono-provincial, `Usuario.unidad_organo_id` ya resuelve la unidad **por usuario**, no por instancia global — así que el día que haya un usuario de otra provincia, solo hace falta asignarle la fila que le corresponde, sin migración de repoblado.

`Usuario.unidad_organo_id` (FK, nullable hasta que se rellene). No se deriva de `Expediente`/`Proyecto` porque el destino real usado en BandeJA es el puesto del usuario que envía, no la ubicación de la instalación — confirmado en el estudio de campo.

### 2. `firmantes_portafirmas`, tabla separada y desacoplada de `usuarios`

Campos: cargo, dni, nombre, unidad_organo_id (FK a §1), vigente/fecha_baja, `usuario_id` **nullable** (se rellena solo si el firmante también es usuario BDDAT; no es requisito).

Se descarta modelarlo como un simple checkbox en `Usuario` (alternativa considerada, ver §Alternativas) porque el firmante real de un oficio/resolución con frecuencia no tiene cuenta BDDAT — atarlo al login habría exigido re-modelar en cuanto apareciera el primer firmante sin cuenta, que es el caso típico, no la excepción.

El campo de búsqueda a exponer en cualquier automatización es el **DNI** — verificado en vivo que el nombre da homónimos y el DNI no.

### 3. RPS: catálogo + asociación simple, sin motor de reglas — issue separado (#757)

Tabla catálogo `rps_bandeja` (import de referencia, ~205 filas del grupo de nuestra consejería) + FK/asociación simple desde el trámite o expediente propio al `codigo_rpa` elegido, curada a mano por el Supervisor.

Se descarta el patrón de 3 capas (vocabulario/reglas_motor/casos especiales) que usa el motor de `tipos_fases`/`tramites`: ese patrón se justifica cuando hace falta lógica condicional evaluable, y aquí no la hay — elegir el RPS es una asociación editorial fija, no una regla que dependa de variables del expediente.

Se separa de #728 a su propio issue (#757) porque, aunque salió de la misma sesión de investigación, es un catálogo y una asociación de naturaleza distinta (procedimientos, no datos del órgano) — mezclarlo habría diluido el alcance que #728 pide mantener acotado.

### 4. Exposición: Capa 1 para escritos, lookup directo para la automatización

Dos consumidores distintos del mismo catálogo:

- **Escritos** (nombre/cargo visibles en el pie, consejería/sede en cabecera): tokens de **Capa 1** (`ContextoBaseExpediente`), no Context Builder. Son datos globales/estáticos, no calculados por expediente ni dependientes de `contexto_clase` — exactamente la frontera que separa Capa 1 de Context Builder en `DISEÑO_GENERACION_ESCRITOS.md`.
- **Automatización de envío a Port@firmas** (#758, gemelo de #659): lookup directo sobre `firmantes_portafirmas` para obtener DNI + tipo de firma + orden — no pasa por tokens de escrito en absoluto, es un consumo distinto del mismo dato.

---

## Issues de implementación

- **#728** — modelo mínimo viable (`unidades_organo_propio`, `firmantes_portafirmas`, FK en `Usuario`, exposición Capa 1) + pantalla de mantenimiento. Checklist actualizado con las decisiones de este ADR.
- **#757** — catálogo RPS y su asociación con trámites/expedientes AT.
- **#758** — automatización Playwright del envío a Port@firmas (gemelo de #659); consume el modelo de este ADR, no lo redefine.

## Pendiente (bajado del alcance, no bloquea el mínimo viable)

Movido al checklist de #728 para que quede visible sin depender de leer este ADR:

- Multi-consejería en cabecera: el texto original de #728 es *"Consejería (nombre completo,
  **y puede ser más de una**)"* — sobre la propia consejería (probablemente resoluciones
  conjuntas con otra consejería, p.ej. AAI/AAU integrada con Medio Ambiente), no sobre
  provincia. Sigue sin resolver.
- Histórico de quién ocupó cada cargo/firmante cuándo — no necesario para el alcance actual.

---

## Alternativas descartadas

### A. Firmante como checkbox en `Usuario`
Simple y coherente con "el firmante suele ser alguien que tramita". Descartada como modelo único: el firmante real de un oficio/resolución (Delegado/a, Consejero/a) frecuentemente no es usuario de BDDAT — un checkbox en `Usuario` no tiene dónde colgar ese caso, que es el habitual para la Firma final, no solo el Visto Bueno técnico.

### B. Unidad propia derivada de `Expediente`/`Proyecto` (provincia de la instalación)
Ya existe `Proyecto.provincias_afectadas`, así que parecía aprovechable. Descartada: el destino real que usa BandeJA para Port@firmas es el puesto del usuario que envía, no la ubicación de la instalación — confirmado explícitamente en el estudio de campo. Derivarlo del expediente habría sido plausible pero incorrecto en cuanto un expediente lo tramitara alguien fuera de la provincia de la instalación.

### C. RPS con motor de reglas de 3 capas (mismo patrón que `tipos_fases`/`tramites`)
Reutilizar el patrón ya existente en el motor. Descartada: ese patrón se justifica por la capa de reglas evaluables condicionalmente; aquí la elección de RPS es una asociación editorial fija sin lógica condicional real que la motive. Aplicar las 3 capas sería sobre-ingeniería para el problema actual.

### D. Datos del órgano vía Context Builder en vez de Capa 1
Descartada: Context Builder está pensado para datos calculados/cruzados dependientes del expediente concreto (`contexto_clase`); los datos de órgano/sede/firmante son globales y estáticos, no varían por expediente — encajan en la definición de Capa 1, no en la de Context Builder.
