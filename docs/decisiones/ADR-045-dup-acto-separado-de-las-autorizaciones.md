# ADR-045 — La DUP se resuelve en acto separado de las autorizaciones

**Estado:** Adoptada en el plano jurídico — el modelado queda abierto (ver §Lo que este ADR no decide)
**Fecha:** 2026-09-09
**Depende de:** ADR-039 (datos del órgano propio y firmantes) · ADR-041 (plazos, y §D bis anclas documentales) · ADR-044 (varias fases del mismo tipo por solicitud ya son posibles)
**Enmienda:** `ESTRUCTURA_ESF.md` §`DUP` · `NORMATIVA_SOLICITUDES.md` §Tipos combinados · `NORMATIVA_PLAZOS.md` §2.2 · `NORMATIVA_MAPA_PROCEDIMENTAL.md` §2
**Origen:** revisión de un documento externo sobre las combinaciones AAP/AAC/DUP, contrastado artículo a artículo con el RD 1955/2000 y con las dos órdenes de delegación andaluzas. Sesión del 2026-09-09.
**Issues:** #891 (§C) · #892 (§D) · #893 (colateral del catálogo) · #894 (§Consecuencias) · #431 (§F, ya abierto)

---

## Contexto

Tres figuras que el promotor puede pedir juntas:

| Sigla | Figura | Base |
|---|---|---|
| AAP | Autorización administrativa previa (sobre **anteproyecto**) | Art. 53.1.a LSE · arts. 122-128 RD 1955/2000 |
| AAC | Autorización administrativa de construcción (sobre **proyecto de ejecución**) | Art. 53.1.b LSE · arts. 130-131 RD 1955/2000, que aún la llaman «aprobación del proyecto de ejecución» |
| DUP | Declaración, en concreto, de utilidad pública | Arts. 54-56 LSE · arts. 140-152 RD 1955/2000 |

**Lo que la norma permite pedir.** Art. 143.2 RD 1955/2000, literal: la solicitud de DUP
«podrá efectuarse bien de manera simultánea a la solicitud de autorización administrativa
**y/o** de aprobación del proyecto de ejecución, o bien con posterioridad a la obtención de
la autorización administrativa». Es decir: AAP+DUP, AAC+DUP, AAP+AAC+DUP y DUP sola son
todas solicitudes admisibles.

**Lo que la norma y la jurisprudencia impiden resolver.** La DUP no es una declaración
abstracta: lleva implícita la necesidad de ocupación y la **urgente ocupación** a efectos
del art. 52 LEF (art. 149.1), y opera sobre la relación concreta e individualizada de bienes
y derechos del art. 143.3.e). Esa relación solo es definitiva cuando lo es la implantación,
y la implantación no lo es hasta que el proyecto de ejecución incorpora los condicionados de
la información pública, del instrumento ambiental y de los organismos consultados. De ahí la
doctrina del grupo de sentencias del TS sobre la central de Morata de Tajuña (22, 23, 24 de
marzo y 25 de mayo de 2010): **no cabe declarar la utilidad pública sin aprobar previa o
simultáneamente el proyecto ejecutivo**.

El propio reglamento ya presupone ese acoplamiento sin necesidad de jurisprudencia: el
art. 146.2 da por realizado el trámite de informe a otras Administraciones «en el supuesto de
haberse solicitado conjuntamente la declaración de utilidad pública **con la aprobación de
proyecto de ejecución**».

La **STS de 28 de mayo de 2026** (ROJ STS 2449/2026, ECLI:ES:TS:2026:2449, casación contra
STSJ Andalucía de 25-04-2024) completa la doctrina por el otro extremo: las modificaciones
posteriores del proyecto **no** obligan a repetir la DUP mientras no alteren la relación de
bienes y derechos ni sus elementos definitorios —fincas, titulares, referencias catastrales,
superficie, naturaleza del terreno, tipo de afección—. En el caso resuelto, cambios de
geometría y ubicación **dentro de la misma finca** no exigieron nueva declaración.

### La particularidad andaluza: dos cadenas de delegación

Aquí está el dato que reordena todo lo anterior, y que no aparece en ningún análisis del
procedimiento hecho solo sobre el RD 1955/2000. En Andalucía **la autorización y la DUP no
pueden ir en el mismo acto**, porque no las dicta el mismo órgano ni agotan la misma vía.

**Orden de 5 de junio de 2013** (BOJA 114), art. 5.6 — delegación del **Consejero** en las
Delegaciones Territoriales:

> «En materia de expropiación forzosa, la competencia para declarar la utilidad pública y
> necesidad de ocupación de los bienes y derechos a expropiar en materia de energía,
> hidrocarburos y minas, **salvo que la expropiación afecte a bienes en dos o más
> provincias**, en cuyo caso la competencia será de la Dirección General…»

Y su art. 9:

> «Conforme a lo dispuesto en el artículo 112.c) de la Ley 9/2007 […] **ponen fin a la vía
> administrativa** las resoluciones, actos o acuerdos que se dicten en el ejercicio de las
> competencias delegadas por la presente Orden.»

**Resolución de 11 de marzo de 2022** de la Dirección General de Energía (BOJA 52, efectos
18/03/2022) — resuelvo 2.º delega las autorizaciones del art. 53 LSE para instalaciones
intraprovinciales; resuelvo 7.º:

> «…se considerarán dictadas por la persona titular de la **Dirección General** competente en
> materia de energía.»

Su resuelvo 10.º deja sin efecto la Resolución de 9 de marzo de 2016, **no** la Orden de 2013:
su propia exposición de motivos las describe como dos instrumentos separados y vivos.

| | Autorizaciones (AAP/AAC/AE/AAT) | DUP |
|---|---|---|
| Norma de delegación | Resolución DG Energía 11/03/2022 | Orden de la Consejería 05/06/2013, art. 5.6 |
| Órgano delegante | Dirección General (órgano intermedio) | **Consejería** |
| Acto considerado dictado por | Dirección General | Consejería |
| Vía administrativa | **No la agota** → alzada | **La agota** → reposición potestativa / contencioso |
| Instalación interprovincial | AAP/AAC no delegadas: resuelve la DG | La DT solo **tramita**; resuelve la DG |

### Lo que BDDAT tenía interiorizado

Lo sustantivo era correcto y llegó por el camino equivocado. El catálogo `tipos_solicitudes`
tiene `AAP+AAC`, `AAP+AAC+DUP` y `AAC+DUP`, y **no** tiene `AAP+DUP` — que es justo la
combinación que no puede resolverse en bloque. Pero esa ausencia no responde a ninguna regla:
nada impide un `INSERT` que la reintroduzca, y ninguna regla del motor impide resolver una DUP
sin AAC. `ESTRUCTURA_ESF.md` §`DUP` afirma además que la DUP autónoma es «posterior a AAP **o**
AAC ya obtenida», lo que contradice la doctrina: tras la AAP sola es **solicitable**, no
resoluble.

Y en ningún sitio del sistema constaba que la resolución de la DUP fuera un acto distinto:
`NORMATIVA_PLAZOS.md` §2.2 y `NORMATIVA_MAPA_PROCEDIMENTAL.md` §2 no tienen bloque de la DUP
pese a documentar AAP, AAC, AE, transmisión y cierre.

---

## Decisión

### A — Solicitar y resolver son dos planos distintos, y el catálogo es del primero

`tipos_solicitudes` cataloga lo que el promotor **pide**, no lo que la Administración resuelve
en un acto. Las cuatro formas del art. 143.2 son solicitudes legítimas. Lo que está reglado no
es qué se puede pedir junto, sino en qué orden pueden dictarse los actos.

### B — En Andalucía, toda solicitud que incluya DUP produce **dos** actos resolutorios

Uno de autorización (AAP y/o AAC), dictado por delegación de la Dirección General, que no agota
la vía. Otro de declaración de utilidad pública, dictado por delegación de la Consejería, que la
agota. Pueden llevar la misma fecha; no pueden ser el mismo acto ni compartir pie de recurso.

Esto vale igual para `AAP+AAC+DUP`, `AAC+DUP` y `AAP+DUP`: la diferencia entre ellas no es
cuántos actos hay, sino si el segundo puede dictarse ya.

### C — Regla de orden: el acto de DUP no puede preceder al que aprueba el proyecto de ejecución

Formulación operativa, comprobable sobre fechas de actos y no sobre la redacción de un texto:

> Una solicitud no puede resolverse favorablemente en su parte de DUP si no consta aprobado el
> proyecto de ejecución —AAC otorgada en la misma solicitud, o en solicitud anterior del mismo
> expediente— con fecha igual o anterior a la del acto de DUP.

Es **modelo legal**, no invariante: va a `reglas_motor` con su cita normativa, no hardcodeada.
El efecto (bloquear con justificación o advertir) se decide en el issue, no aquí.

Corolario que enmienda `ESTRUCTURA_ESF.md`: `AAP+DUP` y `DUP` tras AAP sola son tramitables;
su acto de DUP queda a la espera de la AAC. No es un caso prohibido, es un caso **diferido**.

### D — La DUP tiene plazo propio, y hoy no lo tiene

Son dos procedimientos con dos plazos que corren desde la misma fecha de entrada y vencen en
momentos distintos: 3 meses la autorización (arts. 128 y 131.7), y el que corresponda a la DUP
—el art. 148.1 RD 1955/2000 dice seis meses «en todo caso»—.

Hoy `catalogo_plazos` hace dos cosas incompatibles con eso: consolida `AAP+AAC+DUP` y `AAC+DUP`
en la entrada de 3 meses del art. 131.7 (con lo que **el plazo de la DUP desaparece en las
combinadas**), y para `DUP` sola registra 3 meses citando un «art. 145.4 RD 1955/2000» que no
existe —el art. 145 es «Alegaciones» y no tiene apartados—. La cita errónea viene del seed
`448_seed_plazos_resolucion`.

### E — La interprovincialidad cambia el órgano que resuelve

Que la instalación discurra por más de una provincia, o que la expropiación afecte a bienes de
dos o más, mueve la competencia resolutoria a la Dirección General en ambos actos. BDDAT tiene
la unidad territorial propia (ADR-039, #728) pero no el dato de la instalación. Es dato del
proyecto, no regla.

### F — La DUP se notifica a los titulares de bienes y derechos

Art. 148.2: la resolución se notifica al solicitante, a las Administraciones y organismos que
informaron o debieron informar, **a los titulares de bienes y derechos afectados** y a los
demás interesados. Es el enganche natural de #431 (registro de propietarios de fincas afectadas
en `interesados_expediente`), y la razón de que el cierre del plazo de la DUP no pueda anclarse
en la misma notificación que el de la autorización.

---

## Consecuencias

Las dos listas siguientes son el alcance de **#894**.

**Lo que hay que corregir porque afirma algo falso:**

- `ESTRUCTURA_ESF.md` §`DUP`, encabezado: «posterior a AAP o AAC ya obtenida» → distinguir
  solicitable de resoluble.
- `ESTRUCTURA_ESF.md` §`DUP` nota ³: cita «art. 143.4» para la IP conjunta; es el **art. 144
  párrafo final**. Y su «PENDIENTE CONFIRMACIÓN NORMATIVA» sobre si la IP de la AAP sustituye a
  la de la DUP puede cerrarse en el sentido que ya afirma §`AAC+DUP` nota ²: no la sustituye,
  porque la relación de bienes solo es definitiva con el proyecto de ejecución.
- `catalogo_plazos`: cita inexistente y plazo de la DUP ausente en las combinadas (§D).

**Lo que hay que añadir porque falta:**

- Bloque de la DUP (arts. 143-152) en `NORMATIVA_PLAZOS.md` §2.2 y en
  `NORMATIVA_MAPA_PROCEDIMENTAL.md` §2.
- El cuadro de delegación de este ADR en `NORMATIVA_MAPA_PROCEDIMENTAL.md` §1 «Competencia
  (Andalucía — BDDAT)», que hoy no distingue las dos cadenas.
- Reglas `RD1955-12` (orden de resolución) y `RD1955-13` (modificación posterior sin nueva DUP)
  en `docs/referencia/normas/hallazgos_nblm/BOE-A-2000-24019_reglas.md`.

**Deuda que este ADR destapa pero no asume:** el régimen de recursos no está modelado en
ninguna parte. No hay dónde registrar si un acto agota la vía ni qué pie de recurso lleva, y es
un dato que la plantilla de la resolución necesita. `GUIA_RECURSOS_JUNTA.md` no cubre esto —es
un catálogo de recursos técnicos de la ADA, no administrativos.

---

## Lo que este ADR no decide

**Cómo se representa el doble acto en el modelo.** Hoy `Solicitud` tiene un único
`documento_cierre_id` (ADR-041 §D bis). Desde ADR-044 R5 (#901), `Solicitud.estado` ya no toma
"la primera" ni "la última" fase finalizadora que encuentra: exige que **todas** las que tenga la
solicitud estén cerradas, y si sus resultados no coinciden dice `RESUELTA_DISCREPANTE` en vez de
mentir con un `RESUELTA` mudo — pero sigue sin poder expresar **cuáles** son los dos resultados, ni
sus dos fechas de cierre; ese arreglo evitó que el sistema mintiera mientras tanto, no resolvió la
representación. Lo que sí está preparado, y hace que el problema siga siendo de representación y no
de estructura: varias fases del mismo tipo por solicitud ya son posibles —`crear_fase` no comprueba
duplicidad (ADR-044 §Contexto)—.

Las dos vías evaluadas, sin elegir:

1. **Dos fases finalizadoras** sobre la misma solicitud, con resultado, ancla de cierre y plazo
   propios. Conserva que el promotor presentó una sola solicitud y que la instrucción —IP
   conjunta, consultas— es común.
2. **Dos solicitudes hermanas**, retirando del catálogo las combinadas con DUP. Más simple
   estructuralmente, pero duplica la instrucción compartida y falsea el número de solicitudes
   presentadas.

La decisión se toma cuando el foco llegue a la fase de resolución, no aquí.

---

## Alternativas descartadas

**Modelarlo como orden interno de una resolución única**, que es como lo plantea el análisis
del RD 1955/2000 aislado del derecho andaluz de organización: bastaría con que dentro del texto
se aprobara primero el proyecto y después se declarara la utilidad pública. **Descartada por
imposible aquí**: distinto órgano delegado y distinta vía. Se deja anotado porque es la lectura
a la que se llega leyendo solo la norma sectorial, y volverá a aparecer.

**Prohibir `AAP+DUP` en el catálogo** para que la combinación no resoluble en bloque no exista.
Descartada: el art. 143.2 la admite expresamente, y con dos actos separados no hay nada
patológico en ella —el acto de DUP simplemente espera—.

---

## Issues

Ninguno de los tres toca el modelado del doble acto; son correcciones sobre lo que ya existe.

### #891 — Regla de motor: la DUP no se resuelve antes que el proyecto de ejecución

Variable nueva del tipo `tiene_aac_previa` (hoy solo existe `tiene_aap_previa`) más la fila en
`reglas_motor` con la cita de §C. Decidir en el issue si el efecto es bloqueo con justificación
o advertencia.

### #892 — Plazo de resolución de la DUP

Corregir la cita inexistente y dar plazo propio a la parte DUP de las combinadas (§D). Requiere
confirmar con el servicio qué plazo aplica la Delegación.

### #893 — `nombre_en_plantilla` desplazado en `tipos_solicitudes`

Colateral, detectado al revisar el catálogo. La migración `c3d4e5f6a7b8_fase3_nombre_en_plantilla`
sembró nombres de un catálogo de combinaciones anterior: id 19 (`AAP+AAC+DUP`) → «AAP+AAC+DUP+AAE»,
id 20 (`AAC+DUP`) → «AAP+AAC+RAIPEE+RADNE», id 21 (`AE_DEFINITIVA+AAT`) → «AAT+Ampliación Plazo».
Afecta al nombre de los documentos generados.

### #894 — Alinear los documentos de referencia con este ADR

Las dos listas de §Consecuencias: `ESTRUCTURA_ESF.md`, `NORMATIVA_SOLICITUDES.md`,
`NORMATIVA_MAPA_PROCEDIMENTAL.md` §1 y §2, `NORMATIVA_PLAZOS.md` §2.2 y el hallazgo NBLM del
RD 1955/2000. Sin volver a las fuentes: las citas literales están en este ADR.

### Ya abierto, fuera de este ADR

- **#431** — flujo UI para registro de propietarios de fincas afectadas (DUP) en
  `interesados_expediente`. Conecta con §F.
