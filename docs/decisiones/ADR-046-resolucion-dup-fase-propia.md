# ADR-046 — El acto de la DUP se modela como fase propia `RESOLUCION_DUP`

**Estado:** Adoptada
**Fecha:** 2026-09-12
**Depende de:** ADR-045 (DUP acto separado de las autorizaciones) · ADR-044 R5 (varias fases finalizadoras por solicitud) · ADR-010 (`documentos_tarea` N:M) · ADR-039 (órgano propio y firmantes)
**Enmienda:** ADR-045 §"Lo que este ADR no decide" (cierra la pregunta ahí dejada abierta) · `ESTRUCTURA_ESF.md`/`.json` · `ESTRUCTURA_FTT.md`/`.json` · `TIPOS_DOCUMENTOS_CATALOGO.md`
**Origen:** continuación de `docs/diseño/PRE-ADR-resolucion-doble-acto-dup.md` (alternativa 3.2, ya confirmada ahí) tras cerrar el issue #911. Sesión 2026-09-12. Detalle estructural completo en `docs/diseño/DISEÑO_RESOLUCION_DUP.md`.
**Issues:** ninguno abierto todavía — este ADR y su diseño asociado son el material de partida para abrirlos

---

## Contexto

ADR-045 §B estableció que una solicitud con DUP produce dos actos resolutorios que no pueden ser el mismo documento: uno de autorización (AAP y/o AAC, delegado por la Dirección General) y otro de declaración de utilidad pública (delegado por la Consejería, Orden 5/06/2013 art. 5.6). Dejó sin decidir **cómo se representa el doble acto en el modelo** — dos fases finalizadoras hermanas o dos solicitudes separadas —, remitiendo la decisión "cuando el foco llegue a la fase de resolución".

El PRE-ADR (`docs/diseño/PRE-ADR-resolucion-doble-acto-dup.md`) retomó la pregunta, evaluó ambas vías y **eligió la alternativa 3.2** (dos fases finalizadoras reales, cada una con su propio ciclo de vida) por reutilizar mecanismos ya construidos y verificados (`Solicitud.estado` de ADR-044 R5/#901, `Fase.documento_resultado_id`, `catalogo_plazos` por tipo de fase) en vez de inventar un ciclo de vida de "subfase" nuevo. Quedó pendiente el diseño estructural (trámites, tareas, documentos) — es lo que este ADR formaliza.

Al bajar al detalle aparecieron dos huecos adicionales, no anticipados por ADR-045 ni por el PRE-ADR:

- La **Instrucción 1/2016 de la Dirección General de Industria, Energía y Minas** (BOJA), que rige en la práctica cómo se reparten las inserciones de boletín entre Delegación Territorial y Dirección General, añade el **BOJA** a la publicidad de la DUP (tanto en información pública como, salvo silencio de la propia Instrucción, en la resolución) — algo que ni el RD 1955/2000 ni ADR-045 mencionan porque es de rango autonómico.
- Para poder redactar el `RBDA` (relación de bienes y derechos afectados, art. 143.3.e RD 1955/2000) el promotor necesita en muchos casos datos catastrales de titularidad que solo la Administración puede mediar (protección de datos personales, Ley Orgánica de Protección de Datos) — un procedimiento propio, sin cobertura hasta ahora en ningún documento de referencia.

---

## Decisión

### A — `RESOLUCION_DUP` es fase finalizadora propia, no subfase de `RESOLUCION`

Confirma la alternativa 3.2 del PRE-ADR. Cada acto (autorización, DUP) es una fase real con su propio `documento_resultado_id`, su propia fecha de cierre y su propio plazo en `catalogo_plazos`. `Solicitud.estado` (ADR-044 R5) ya exige que todas las finalizadoras estén cerradas y ya sabe decir `RESUELTA_DISCREPANTE` si difieren — funciona sin tocarlo.

### B — Para DUP sola, `RESOLUCION_DUP` sustituye a `RESOLUCION`; en las combinadas conviven como hermanas

Una solicitud `DUP` (autónoma, posterior a AAP o AAC ya obtenida) no tiene autorización que resolver en esa solicitud — su única finalizadora es `RESOLUCION_DUP`. En `AAC+DUP` y `AAP+AAC+DUP`, ambas fases conviven como hermanas: una resuelve la autorización, otra la DUP. En `AAP+DUP`, por el corolario diferido de ADR-045 §C, hoy solo aplica `RESOLUCION` (AAP); `RESOLUCION_DUP` queda para cuando llegue una solicitud posterior con AAC.

Motivo, no solo coherencia terminológica: los bloqueos de motor que gobiernan quién puede resolver qué (§E) se anclan al código de fase, y `DUP` sola nunca debería poder resolverse por el camino de `RESOLUCION` genérica.

### C — Notificaciones de `RESOLUCION_DUP`: un trámite por grupo de destinatario, no una única multi-instancia

Art. 148.2 RD 1955/2000 distingue tres grupos además del solicitante: Administraciones/organismos que informaron, titulares de bienes y derechos, y demás interesados. Se modelan como tres trámites:

- `NOTIFICACION` — al solicitante (patrón ya existente en `RESOLUCION`)
- `NOTIFICACION_ORGANISMOS` — filtra `interesados_expediente.tipo_origen IN ('ORGANISMO_CONSULTADO', 'MEDIO_AMBIENTE')`
- `NOTIFICACION_INTERESADOS` — filtra `tipo_origen IN ('DUP', 'INTERESADO_RECONOCIDO')`

No hace falta ninguna tabla nueva: `interesados_expediente` (#374) ya tiene estos cinco `tipo_origen` reservados desde su diseño original; hoy solo `TITULAR` está poblado por código. Los dos trámites nuevos son dos *consumidores* que filtran el mismo almacén, no una fusión de datos.

La cardinalidad alta de `NOTIFICACION_INTERESADOS` (decenas de parcelas, varios titulares cada una) no se resuelve duplicando trámites por destinatario (patrón de `CONSULTA_SEPARATA`, inadecuado aquí): se resuelve extendiendo el mecanismo de whitelist por código de trámite que ya usa `ANALIZAR` (`app/routes/api_expedientes.py:68`, `_TRAMITES_CON_SECCIONES_ANALISIS`) con un equivalente para `NOTIFICAR` (`_TRAMITES_CON_NOTIFICACION_MULTIPLE = {'NOTIFICACION_ORGANISMOS', 'NOTIFICACION_INTERESADOS'}`) que active una vista de sub-lista de destinatarios en el inspector, sin afectar a ningún otro `NOTIFICAR` del sistema. La pantalla de gestión de interesados (#431) es independiente, a nivel de expediente; el inspector solo reutiliza su consulta filtrada, la representación es propia de cada uno.

### D — Publicaciones de `RESOLUCION_DUP`: un trámite por boletín, no un `PUBLICACION` genérico

Mismo patrón que ya usa `INFORMACION_PUBLICA` (`ANUNCIO_BOE`, `ANUNCIO_BOP`, `ANUNCIO_BOJA`) en vez de repetir el `PUBLICACION` único de `RESOLUCION` genérica. Tres trámites: `PUBLICACION_BOP`, `PUBLICACION_BOJA`, `PUBLICACION_BOE`.

`PUBLICACION_BOJA` la añade la Instrucción 1/2016 DG Industria (BOJA), apartado SÉPTIMO (información pública) y DÉCIMO (resolución) — no está en el RD 1955/2000, que es de 2000 y no conocía el BOJA como boletín autonómico separado. `PUBLICACION_BOE` se mantiene pese a que el apartado DÉCIMO de esa misma Instrucción no lo cita para la resolución (solo lo cita para la información pública, apartado SÉPTIMO): prevalece el art. 148.2 RD 1955/2000, de rango superior, que sí exige BOE para la resolución. Se interpreta el silencio de la Instrucción como omisión, no como excepción — publicar de más nunca es un defecto; si el servicio lo desmiente, se ajusta la regla o el catálogo entonces, no antes.

Nota fuera de alcance: el mismo rework (trámite por boletín en vez de uno genérico) previsiblemente le tocará a `RESOLUCION` genérica (AAP/AAC) más adelante — no se aborda en este ADR.

### E — Los bloqueos de motor de `RESOLUCION_DUP` se duplican quirúrgicamente, no se heredan

`RESOLUCION` hoy bloquea su `ELABORACION.ELABORAR` con cinco reglas de motor (`organismos_todos_terminados`, `fase_ip_finalizada`, `tramite_requerimiento_sin_respuesta`, `instrumento_ambiental=AAU`, `solicitud_tiene_cert_fin_instruccion`), todas con `sujeto='ANY/ANY/RESOLUCION'` literal. `RESOLUCION_DUP` necesita las mismas condiciones de instrucción completa, pero se decide **no** construir un mecanismo de herencia genérico entre tipos de fase finalizadora: futuros tipos de resolución (p. ej. cambio de titular) no compartirán necesariamente estos bloqueos, y una herencia ciega los arrastraría sin control. Se duplican las filas de `reglas_motor` con `sujeto='ANY/ANY/RESOLUCION_DUP'`.

A esto se suma la regla de orden ya prevista en #891 (ADR-045 §C: la DUP no se resuelve antes que el proyecto de ejecución aprobado), que ahora tiene dónde enganchar: la tarea `ELABORAR` de `RESOLUCION_DUP.ELABORACION`.

### F — `DATOS_CATASTRALES`: fase propia de la solicitud DUP, no solicitud aparte

Para que el promotor pueda redactar el `RBDA` necesita en algunos casos que la Administración medie el acceso a datos catastrales de titularidad (protección de datos personales). Se modela como fase de la propia solicitud DUP (no lleva tasa, no es un acto administrativo autónomo) con dos caminos posibles:

- **Con mediación catastral** (el promotor no tiene acceso directo al Catastro): `SOLICITUD_CATASTRALES` → `REQUERIMIENTO_CATASTRALES` (repetible) → `REMISION_ACUERDO_DATOS` → `ANALISIS_RBDA` → `TOMA_RAZON_RBDA`.
- **Sin mediación** (el promotor ya dispone de la RBDA, p. ej. operadoras con acceso directo al Catastro): solo `ANALISIS_RBDA` → `TOMA_RAZON_RBDA`.

`DATOS_CATASTRALES` es obligatoria antes de cualquier fase posterior de la solicitud (`INFORMACION_PUBLICA`, `CONSULTAS`). Qué camino se sigue lo decide hoy el tramitador libremente, sin regla de motor — igual que el resto de creación de fases/trámites en el árbol. Candidato de regla futura, no implementado ahora: bloquear `CREAR ANALISIS_RBDA` si no constan `RBDA` y `RBDA_DIRECCIONES` en el pool de documentos del expediente. Detalle completo de trámites, tareas y documentos en `docs/diseño/DISEÑO_RESOLUCION_DUP.md`.

### G — Dos documentos nuevos: `RBDA` y `RBDA_DIRECCIONES`

Ambos externos (aportados por el promotor; su contenido no lo evalúa BDDAT, es responsabilidad del promotor):

| Documento | Contenido | ¿Se publica? |
|---|---|---|
| `RBDA` | Planos + afecciones por titular/propietario (no necesariamente parcela catastral) + valor numérico. Identificación NIF/DNI (persona física) o NIF+nombre (persona jurídica) | Sí — es lo que se inserta en el anuncio de información pública (art. 144 RD 1955/2000) |
| `RBDA_DIRECCIONES` | Mismo listado de afecciones, sin planos, con la dirección de notificación de cada titular | No — datos de contacto |

Se registran como un único producido de la tarea `ESPERAR_PLAZO` de `REMISION_ACUERDO_DATOS` (el registro de entrada de ambos documentos, patrón ya establecido en `ESTRUCTURA_FTT.md` v6.3 §"regla de recepción en `ESPERAR_PLAZO`": un único producido que acredita el hecho, los anexos entran al pool para el `ANALIZAR` siguiente). Los consume `ANALISIS_RBDA.ANALIZAR`.

---

## Consecuencias

**Documentos de referencia a actualizar:**
- `ESTRUCTURA_ESF.md`/`.json` — añadir `RESOLUCION_DUP` (y `DATOS_CATASTRALES`) a las tablas de `DUP`, `AAC+DUP`, `AAP+AAC+DUP`, `AAP+DUP`; sustituir `RESOLUCION` por `RESOLUCION_DUP` en `DUP` sola.
- `ESTRUCTURA_FTT.md`/`.json` — nuevas fases `RESOLUCION_DUP` y `DATOS_CATASTRALES` con sus trámites y tareas (detalle en `DISEÑO_RESOLUCION_DUP.md`).
- `TIPOS_DOCUMENTOS_CATALOGO.md` — `RBDA`, `RBDA_DIRECCIONES`, `XML_PARA_CATASTRO`, `XML_DE_CATASTRO`, `DR_DATOS_CATASTRALES`, `ACUERDO_CESION_CATASTRALES`, `OFICIO_REQUERIMIENTO_CATASTRALES`, `OFICIO_TOMA_RAZON_RBDA`.
- `NORMATIVA_MAPA_PROCEDIMENTAL.md`/`NORMATIVA_PLAZOS.md` — bloque de la DUP que ADR-045 §Consecuencias ya pedía (#894), ahora con `RESOLUCION_DUP` y `DATOS_CATASTRALES` incluidos.

**Código a tocar (issues por abrir, no implementado en este ADR):**
- `informe_instruccion.py:_FASE_FINALIZADORA_POR_SIGLAS` — de mapa 1:1 a listas.
- `reglas_motor` — nueva fila CREAR/82.1 para `RESOLUCION_DUP` (guardián `catalogo_requerido.py` la reclama en cuanto `es_finalizadora=True`); duplicado quirúrgico de las 5 reglas de §E; regla de orden de #891.
- `nombres_documentos.py:_SUSTITUCIONES` — entrada para `('RESOLUCION_DUP', 'ELABORACION')`.
- `app/routes/api_expedientes.py` — `_TRAMITES_CON_NOTIFICACION_MULTIPLE` análogo a `_TRAMITES_CON_SECCIONES_ANALISIS`.
- `catalogo_plazos` — plazo propio de `RESOLUCION_DUP` (6 meses, art. 148.1) — converge con #892.

---

## Lo que este ADR no decide

- Mecanismo exacto de la regla de motor que en el futuro condicione el camino de `DATOS_CATASTRALES` (§F, candidato anotado, no diseñado).
- Plantillas y contenido de los escritos nuevos (`OFICIO_REQUERIMIENTO_CATASTRALES`, `ACUERDO_CESION_CATASTRALES`, `OFICIO_TOMA_RAZON_RBDA`).
- Régimen de recursos (pie de recurso por acto) — deuda ya destapada por ADR-045 §Consecuencias, sigue sin asumirse aquí.

---

## Alternativas descartadas

Heredar automáticamente en `RESOLUCION_DUP` los bloqueos de motor de `RESOLUCION` (por tipo de fase o por marca "es finalizadora"). Descartada (§E): generalizaría de más sobre la base de un solo caso — futuros tipos de resolución no comparten necesariamente estos bloqueos, y una herencia ciega complica revertir un bloqueo que no debería aplicar a un tipo nuevo.

Fusionar organismos consultados e interesados en un único trámite de notificación. Descartada (§C): el propio art. 148.2 los distingue como grupos separados, y mezclarlos en la vista del inspector complica la especialización de cada uno sin ganar nada a cambio.
