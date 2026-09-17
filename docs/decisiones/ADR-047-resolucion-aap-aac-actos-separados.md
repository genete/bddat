# ADR-047 — AAP y AAC pueden resolverse en actos separados dentro de una misma solicitud

**Estado:** Adoptada — el modelado queda pendiente de implementación (issue nuevo, prerrequisito de #891)
**Fecha:** 2026-09-17
**Depende de:** ADR-044 R5 (`Solicitud.estado` admite varias finalizadoras y `RESUELTA_DISCREPANTE`) · ADR-045 (mismo principio — solicitar junto no obliga a resolver junto — aplicado antes a la DUP) · ADR-046 (patrón de fase propia + duplicado quirúrgico de reglas de motor)
**Enmienda:** `ESTRUCTURA_ESF.md`/`.json` (tabla `AAP+AAC` y `AAP+AAC+DUP`) · `ESTRUCTURA_FTT.md`/`.json` (fases nuevas) · `NORMATIVA_PLAZOS.md` (plazo partido) · `NORMATIVA_MAPA_PROCEDIMENTAL.md`
**Origen:** Detectado durante el diseño de #891 (la regla de orden de la DUP necesita responder "¿está la AAC resuelta?", y eso reveló que la fase única `RESOLUCION` no contempla que AAP y AAC puedan resolverse en momentos distintos). Sesión 2026-09-17.
**Issues:** #891 (bloqueado por este ADR hasta que se implemente) · #918 (implementación)

---

## Contexto

`tipos_solicitudes` admite `AAP+AAC` (y `AAP+AAC+DUP`) como solicitud conjunta, tramitada con una
única fase finalizadora `RESOLUCION` (`tipo_fase` id 8) que resuelve las dos autorizaciones —AAP,
art. 53.1.a LSE / arts. 122-128 RD 1955/2000; AAC, art. 53.1.b LSE / arts. 130-131— en un solo acto.

Tramitar junto no obliga a resolver junto. En la práctica, sobre todo en renovables, a veces **es
necesario** resolver por separado: la AAP puede llegar a su plazo (art. 128, 3 meses) con la AAC
todavía pendiente —organismos reticentes en las consultas propias de la AAC, con más plazo (art.
131.7)—, y forzar un acto único obligaría a elegir entre retrasar indebidamente la AAP o resolver la
AAC sin contenido. Ninguna de las dos es correcta, y ninguna la exige la norma: son dos
autorizaciones distintas que solo comparten tramitación por conveniencia procedimental.

**Cita normativa confirmada** (leída en sesión 2026-09-17): LSE art. 53.1, párrafo de cierre — "La
tramitación y resolución de autorizaciones definidas en los párrafos a) y b) del apartado 1 del
presente artículo **podrán** efectuarse de manera consecutiva, coetánea o conjunta." Es una facultad,
no un mandato, y "consecutiva" es precisamente resolver AAP y AAC por separado. El RD 1955/2000
confirma la misma lectura por estructura: AAP (Sección 1.ª, resolución propia en art. 128) y AAC
(Sección 2.ª, resolución propia en art. 131.7) son dos procedimientos con acto resolutorio distinto,
y su art. 131.1 párr. 2 contempla expresamente el caso de una instalación con AAP ya resuelta cuya
AAC se tramita solo bajo la Sección 2.ª. Ninguna de las dos normas exige resolución única ni ata la
tramitación/resolución al modo en que se presentó la solicitud.

El modelo de hoy no lo permite representar. Los tres sitios que asumen acto único:

- `reglas_motor`: 5 filas con `sujeto='ANY/ANY/RESOLUCION'` (ids 36, 37, 38, 1718, 1787).
- `catalogo_plazos`: `camino='ANY/AAP+AAC'` (id 1855) y `'ANY/AAP+AAC+DUP'` (id 1856), cada una con
  un único plazo de 3 meses (art. 131.7) para toda la solicitud.
- La regla §F de ADR-044 ("se prohíbe crear una fase que cubra una versión ya cubierta por otra fase
  del mismo tipo") impediría hoy crear una segunda `RESOLUCION` en la misma solicitud aunque se
  quisiera partir la resolución, porque no ha mediado ningún reformado entre las dos.

Esto es un problema anterior e independiente de #891 —un técnico ya puede encontrarse hoy con la AAP
lista y la AAC atascada, sin DUP de por medio, y no tiene dónde formalizar la primera— pero #891 no
puede escribir `tiene_aac_previa` de forma correcta mientras `RESOLUCION` sea el único código
posible: no hay manera de expresar "la AAC está resuelta, la AAP no" ni al revés.

---

## Decisión

### A — `RESOLUCION` sigue siendo el acto conjunto; dos códigos nuevos para el acto partido

`RESOLUCION_AAP` y `RESOLUCION_AAC`: mismo tipo de fase (finalizadora, trámite `ELABORACION` +
`NOTIFICACION` calcado de `RESOLUCION`), para cuando el técnico decide resolver por separado.
`RESOLUCION` conserva su código y su significado para el caso conjunto — ningún expediente ni regla
existente cambia. En `AAP` o `AAC` solas (no combinadas) tampoco cambia nada: ahí nunca hay nada que
partir, y `RESOLUCION` nunca ha sido ambigua.

### B — Resolver conjunto o partido es elección del técnico, declarada en catálogo, no en regla de motor

Mismo patrón que `DATOS_CATASTRALES` (ADR-046 §F): `fases_tramites` declara los dos caminos
posibles para `AAP+AAC`(`+DUP`) —una fase `RESOLUCION`, o dos fases `RESOLUCION_AAP` +
`RESOLUCION_AAC`— y el árbol permite crear cualquiera de los dos. Ninguna regla de motor fuerza una
u otra; el mecanismo exacto de exclusión mutua entre ambos caminos se decide en el issue de
implementación (§Lo que este ADR no decide).

### C — Duplicado quirúrgico de las reglas de motor de `RESOLUCION`

Las 5 reglas con `sujeto='ANY/ANY/RESOLUCION'` (36, 37, 38, 1718, 1787) se duplican para
`RESOLUCION_AAP` y `RESOLUCION_AAC` — 10 filas nuevas, sin herencia (mismo criterio que ADR-046 §E:
un tipo de fase nuevo no hereda ciegamente los bloqueos de otro, porque no tiene por qué compartirlos
siempre).

### D — `catalogo_plazos`: el plazo conjunto se divide cuando se resuelve partido

Hoy `camino='ANY/AAP+AAC'` da un único plazo de 3 meses (art. 131.7) para toda la solicitud. Si se
resuelve partido, cada acto lleva su propio plazo desde la misma fecha de entrada: 3 meses para la
parte AAP (art. 128) y 3 meses para la parte AAC (art. 131.7). Mismo problema estructural que #892 ya
documentó para AAC/DUP —`solicitudes.documento_cierre_id` es una FK única, no dos— y que
`DISEÑO_RESOLUCION_DUP.md` §1 dejó abierto sin resolver. No se resuelve en este ADR: converge con esa
misma pieza pendiente, ahora con un tercer caso que la necesita.

### E — `tiene_aac_previa` (#891) mira los dos códigos

La variable de la regla de orden de la DUP considera favorable tanto una `RESOLUCION` conjunta como
una `RESOLUCION_AAC` partida — el requisito legal (proyecto de ejecución aprobado) es el mismo acto
sustantivo; solo cambia el envoltorio de fases que lo representa.

### F — Regla de orden: si se resuelve partido, la AAC no puede emitirse antes que la AAP

Mismo principio que #891 aplica a la DUP, un nivel antes: el proyecto de ejecución que aprueba la
AAC tiene que ser coherente con lo que la AAP ya fijó (emplazamiento, características básicas), así
que abrir la posibilidad de resolver partido obliga a imponer el orden entre las dos mitades.
Formulación operativa, calcada de ADR-045 §C:

> Cuando una solicitud `AAP+AAC`(`+DUP`) se resuelve partida, la fase `RESOLUCION_AAC` no puede
> elaborarse sin que conste `RESOLUCION_AAP` de la misma solicitud finalizada con resultado
> favorable.

Es regla de motor, no invariante — mismo razonamiento que #891: admite escape con justificación.
Ancla en `RESOLUCION_AAC.ELABORACION.ELABORAR`, igual patrón que #891 ancla en
`RESOLUCION_DUP.ELABORACION.ELABORAR`.

**No aplica** a `RESOLUCION` conjunta (un solo acto, no hay orden que imponer entre sus dos mitades)
ni a una solicitud `AAC` pura (no hay AAP que esperar en esta solicitud; una AAP favorable previa en
otra solicitud del expediente ya tiene su propio efecto —sin bloqueo, solo reduce el plazo de
consultas— vía la condición existente `tiene_solicitud_aap_favorable`, art. 131.1 párr. 2). El
`sujeto='ANY/ANY/RESOLUCION_AAC'` ya acota esto por construcción: esa fase solo existe cuando se ha
elegido el camino partido.

**Variable nueva** (nombre a decidir en el issue): existe una fase con `tipo_fase.codigo ==
'RESOLUCION_AAP'` en la **misma solicitud**, finalizada con resultado favorable. A diferencia de
`tiene_solicitud_aap_favorable`, debe incluir la solicitud actual — mismo motivo que llevó a no
reutilizar `tiene_aac_resuelta_favorable` para #891 (§E): AAP y AAC son ahora fases hermanas de la
misma solicitud cuando se resuelve partido.

**Cita normativa confirmada** (leída en sesión 2026-09-17): RD 1955/2000 arts. 128.4, 130.1 y 131.1
párr. 2. La Sección 2.ª del Título VII (aprobación de proyecto de ejecución, AAC) está construida
normativamente como una fase que sigue a la AAP ya resuelta, no paralela a ella: el art. 128.4 fija
el plazo, contado desde el otorgamiento de la AAP, dentro del cual debe solicitarse la aprobación del
proyecto de ejecución, con caducidad de la AAP si no se solicita a tiempo; el art. 130.1 atribuye esa
solicitud a "el peticionario o **el titular de la autorización**" (la AAP ya otorgada); y el art.
131.1 párr. 2 regula expresamente el caso de tramitación bajo la Sección 2.ª cuando "la instalación
**cuenta con una resolución de autorización administrativa previa**". No hace falta acudir a LPACAP
art. 88.2 — el fundamento sectorial específico basta.

---

## Consecuencias

**Documentos a actualizar:**
- `ESTRUCTURA_ESF.md`/`.json` — tablas de `AAP+AAC` y `AAP+AAC+DUP`: fase `RESOLUCION` como camino
  alternativo a `RESOLUCION_AAP` + `RESOLUCION_AAC`.
- `ESTRUCTURA_FTT.md`/`.json` — las dos fases nuevas, con sus trámites y tareas calcados de
  `RESOLUCION`.
- `NORMATIVA_PLAZOS.md` — plazo partido cuando aplique.
- `NORMATIVA_MAPA_PROCEDIMENTAL.md` — si documenta el camino de resolución de `AAP+AAC`.

**Código a tocar (issue de implementación, no en este ADR):**
- `tipos_fases` — 2 filas nuevas (`RESOLUCION_AAP`, `RESOLUCION_AAC`).
- `fases_tramites` — entradas para `AAP+AAC` y `AAP+AAC+DUP` con los dos caminos declarados.
- `reglas_motor` — 10 filas (duplicado de las 5 de `RESOLUCION`, ×2 códigos) **+ 1 fila más** para la
  regla de orden de §F sobre `RESOLUCION_AAC` (11 filas en total).
- `catalogo_variables` — variable nueva de §F (AAP previa en la misma solicitud).
- `catalogo_plazos` — filas del plazo partido; converge con #892.
- `app/services/informe_instruccion.py` — `_FASE_FINALIZADORA_POR_SIGLAS`: ADR-046 ya señaló que
  debía pasar "de mapa 1:1 a listas"; este ADR es un motivo más para no aplazarlo.
- `app/services/generador_cert.py` — verificar que no asuma una única `RESOLUCION` por solicitud
  combinada al redactar el certificado de fin de instrucción.
- `app/services/variables/calculado.py` — `tiene_aac_previa` (#891) comprueba `tipo_fase.codigo IN
  ('RESOLUCION', 'RESOLUCION_AAC')`.

**#891 queda bloqueado** por la implementación de este ADR: `tiene_aac_previa` no se puede escribir
de forma correcta mientras "AAC resuelta sin AAP" no sea representable en el árbol.

---

## Lo que este ADR no decide

- **El mecanismo exacto de exclusión mutua en el árbol** entre crear `RESOLUCION` o crear
  `RESOLUCION_AAP`+`RESOLUCION_AAC` — análogo al control excluyente de anclaje de proyecto principal
  de #887, pero se decide en el issue de implementación.
- **Si otras combinaciones de `tipos_solicitudes` tienen el mismo problema.** No se ha encontrado
  ninguna otra en esta sesión, pero no se ha hecho un barrido exhaustivo de todo el catálogo.

---

## Alternativas descartadas

**`RESOLUCION_AAP_AAC`** (renombrar el código conjunto en vez de mantener `RESOLUCION`). Descartada:
migraría datos de expedientes ya existentes y las 5 reglas + 2 filas de plazo activas hoy, sin
ganancia sustantiva sobre mantener `RESOLUCION` para el caso mayoritario — mismo criterio de coste
que llevó a ADR-046 a no tocar `RESOLUCION` al introducir `RESOLUCION_DUP`.

**Forzar siempre la resolución partida** (retirar la conjunta). Descartada: sería una regresión — la
conjunta sigue siendo válida y es el caso mayoritario.

---

## Issues

- **#918** — implementación, alcance de §Consecuencias, prerrequisito de #891.
- **#891** — pasa a depender de #918; su variable `tiene_aac_previa` se apoya en §E.
- **#892** — ya documentaba el mismo hueco de plazo/cierre único para AAC/DUP; con §D converge un
  tercer caso que lo necesita.
