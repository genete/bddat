# DISEÑO — `RESOLUCION_DUP` y `DATOS_CATASTRALES`: detalle estructural

> **Naturaleza de este documento:** desarrollo estructural de ADR-046 (trámites, tareas,
> documentos, precedencia). El ADR fija la decisión y su porqué; este documento es el que
> se revisa cuando cambie un detalle de catálogo, sin tocar el ADR ya adoptado. Mismo rol
> que `DISEÑO_CONSULTAS_ORGANISMOS.md` o `DISEÑO_ANALISIS_SOLICITUD.md` para sus fases.

**Estado:** Llevado a `ESTRUCTURA_ESF.md`/`.json` y `ESTRUCTURA_FTT.md`/`.json` (#914, v2.4/v6.4). Pendiente de abrir issues de implementación (migraciones y código).
**Fecha:** 2026-09-12

---

## 1. Fase `RESOLUCION_DUP`

Finalizadora. Sustituye a `RESOLUCION` en la solicitud `DUP` sola; convive como hermana en `AAC+DUP`, `AAP+AAC+DUP` y también en `AAP+DUP`. En `AAP+DUP` la fase existe desde el principio — lo diferido no es su existencia, es la *emisión* del acto: la tarea `ELABORAR` de su trámite `ELABORACION` queda bloqueada por la regla de orden (#891, ADR-045 §C) hasta que conste AAC otorgada en solicitud posterior del mismo expediente. Sin la fase no habría tarea `ELABORAR` sobre la que anclar ese bloqueo.

| Trámite | Patrón | Tareas | Destinatario / nota |
|---|---|---|---|
| `REQUERIMIENTO_RBDA_DEFINITIVA` | C | ELABORAR→NOTIFICAR→EP | Obligatorio y exclusivo de esta fase, previo a `ELABORACION`. Plazo 10 días (genérico LPACAP, procedimiento interno del servicio). Requiere al promotor la RBDA definitiva — solo parcelas a expropiar, propietarios, DNI, direcciones — o confirmación de la ya publicada en el anuncio de IP |
| `ELABORACION` | B (sin NOTIFICAR) | ELABORAR | Consume `RBDA_DEFINITIVA`. Mismo `tipo_tramite` código `ELABORACION` que `RESOLUCION` — colisión de nombre de fichero resuelta vía `_SUSTITUCIONES` (PRE-ADR §4.1.1) |
| `NOTIFICACION` | B (solo NOTIFICAR) | NOTIFICAR | Solicitante |
| `NOTIFICACION_ORGANISMOS` | B (solo NOTIFICAR) | NOTIFICAR | `interesados_expediente.tipo_origen IN ('ORGANISMO_CONSULTADO', 'MEDIO_AMBIENTE')` |
| `NOTIFICACION_INTERESADOS` | B (solo NOTIFICAR) | NOTIFICAR | `interesados_expediente.tipo_origen IN ('DUP', 'INTERESADO_RECONOCIDO')` |
| `PUBLICACION_BOP` | F+F | NOTIFICAR→EP→EP | Una instancia por provincia afectada |
| `PUBLICACION_BOJA` | F+F | NOTIFICAR→EP→EP | Instrucción 1/2016 DG Industria, DÉCIMO |
| `PUBLICACION_BOE` | F+F | NOTIFICAR→EP→EP | Art. 148.2 RD 1955/2000. La Instrucción 1/2016 no lo cita para la resolución (sí para la IP, SÉPTIMO) — se interpreta como omisión, prevalece el RD por rango |

**Especialización de inspector — `NOTIFICACION_ORGANISMOS`/`NOTIFICACION_INTERESADOS`:** whitelist por código de trámite, mismo mecanismo que `_TRAMITES_CON_SECCIONES_ANALISIS` (`app/routes/api_expedientes.py:68`) aplicado a `NOTIFICAR`:

```python
_TRAMITES_CON_NOTIFICACION_MULTIPLE = {'NOTIFICACION_ORGANISMOS', 'NOTIFICACION_INTERESADOS'}
```

Activa una vista de sub-lista de destinatarios (uno por fila, con su propio justificante) en vez del estado único pendiente/hecha. No afecta a `NOTIFICACION` (titular) ni a ningún otro `NOTIFICAR` del sistema. La pantalla de gestión de interesados (#431) es independiente y a nivel de expediente; el inspector reutiliza solo su consulta filtrada por `tipo_origen`, la representación es propia de cada trámite.

**`REQUERIMIENTO_RBDA_DEFINITIVA`:** su `ESPERAR_PLAZO` recibe directamente `RBDA_DEFINITIVA` (aportada por el promotor, o su confirmación de la ya publicada) sin anexos que incorporar — no exige `ANALIZAR` posterior (mismo caso que `TABLON_AYUNTAMIENTOS` de `INFORMACION_PUBLICA`). El documento producido lo consume `ELABORACION.ELABORAR` para redactar la resolución con los datos de expropiación definitivos.

**Bloqueos de motor (duplicado quirúrgico de los 5 de `RESOLUCION`, sujeto `ANY/ANY/RESOLUCION_DUP`):** `organismos_todos_terminados`, `fase_ip_finalizada`, `tramite_requerimiento_sin_respuesta`, `instrumento_ambiental=AAU`, `solicitud_tiene_cert_fin_instruccion`. Más la regla de orden de #891 (no resolver sin AAC previa aprobada), que ahora tiene dónde enganchar: `ELABORACION.ELABORAR`.

**Plazo:** propio, 6 meses (art. 148.1 RD 1955/2000) — converge con #892, no se resuelve aquí.

---

## 2. Fase `DATOS_CATASTRALES`

De la propia solicitud DUP (sin tasa). Obligatoria antes de `INFORMACION_PUBLICA`/`CONSULTAS` de esa solicitud. Dos caminos, elegidos hoy libremente por el tramitador (sin regla de motor):

### Camino con mediación catastral

| Trámite | Tareas | Consume | Produce |
|---|---|---|---|
| `SOLICITUD_CATASTRALES` | ANALIZAR | `SOLICITUD` (tipo genérico, polivalente) + `XML_PARA_CATASTRO` + `DR_DATOS_CATASTRALES` (si se aportó en origen) | `DIAGNOSTICO` (genérico) |
| `REQUERIMIENTO_CATASTRALES` (n, repetible) | ELABORAR→NOTIFICAR→EP→ANALIZAR | El `DIAGNOSTICO` de `SOLICITUD_CATASTRALES` (si desfavorable) o de la ronda anterior | `OFICIO_REQUERIMIENTO_CATASTRALES` (nuevo) + justificante genérico + `DIAGNOSTICO` de la ronda |
| `REMISION_ACUERDO_DATOS` | ELABORAR→NOTIFICAR→EP | `XML_DE_CATASTRO` + `DR_DATOS_CATASTRALES` conforme + el `DIAGNOSTICO` **favorable** que habilita el trámite (de `SOLICITUD_CATASTRALES` si no hubo defectos, o de la última ronda de `REQUERIMIENTO_CATASTRALES`) | `ACUERDO_CESION_CATASTRALES` (ELABORAR); EP espera la RBDA remitida por el promotor |

### Siempre (con o sin mediación previa)

| Trámite | Tareas | Consume | Produce |
|---|---|---|---|
| `ANALISIS_RBDA` | ANALIZAR | El producido único de `ESPERAR_PLAZO` de `REMISION_ACUERDO_DATOS` (registro de entrada que trae `RBDA` + `RBDA_DIRECCIONES` como anexos — mismo patrón v6.3 de `ESPERAR_PLAZO`, §"regla de recepción") | `DIAGNOSTICO` (genérico) |
| `TOMA_RAZON_RBDA` | ELABORAR→NOTIFICAR | — | `OFICIO_TOMA_RAZON_RBDA` (nuevo) — cierra la fase, anuncia inicio de IP/consultas + justificante genérico |

**Regla de negocio, no de motor (por ahora):** `REMISION_ACUERDO_DATOS` siempre consume un `DIAGNOSTICO` favorable — si `SOLICITUD_CATASTRALES` sale desfavorable, el camino pasa obligatoriamente por `REQUERIMIENTO_CATASTRALES` antes de llegar aquí.

**Camino sin mediación** (el promotor ya dispone de la RBDA, p. ej. operadoras con acceso directo al Catastro): se salta `SOLICITUD_CATASTRALES`/`REQUERIMIENTO_CATASTRALES`/`REMISION_ACUERDO_DATOS` — la RBDA llega ya con la documentación de la solicitud, y solo corren `ANALISIS_RBDA` → `TOMA_RAZON_RBDA`.

**Regla de motor futura, no implementada:** bloquear `CREAR ANALISIS_RBDA` si no constan `RBDA` y `RBDA_DIRECCIONES` en el pool de documentos del expediente.

---

## 3. Documentos nuevos

| Código | E/I | Producido por | Consumido por | Nota |
|---|---|---|---|---|
| `RBDA` | Externo | Registro de entrada (anexo del `ESPERAR_PLAZO` de `REMISION_ACUERDO_DATOS`, o aportado con la solicitud si no hay mediación) | `ANALISIS_RBDA.ANALIZAR` | Planos + afecciones por titular + valor. NIF/DNI (física) o NIF+nombre (jurídica). Contenido no evaluado por BDDAT. **Se publica** |
| `RBDA_DIRECCIONES` | Externo | Igual que `RBDA` | `ANALISIS_RBDA.ANALIZAR` | Mismo listado, sin planos, con dirección de notificación. **No se publica** |
| `XML_PARA_CATASTRO` | Externo | Aportado por el promotor | `SOLICITUD_CATASTRALES.ANALIZAR` | XML que la Administración introduce en el Catastro |
| `XML_DE_CATASTRO` | Interno | Elaboración propia (los datos vienen del Catastro, el fichero es artefacto de la Administración) | `REMISION_ACUERDO_DATOS.ELABORAR` | Resultado de la consulta al Catastro |
| `DR_DATOS_CATASTRALES` | Externo | Aportado por el promotor (origen o subsanación) | `REMISION_ACUERDO_DATOS.ELABORAR` | Declaración responsable de tratamiento de datos personales |
| `ACUERDO_CESION_CATASTRALES` | Interno | `REMISION_ACUERDO_DATOS.ELABORAR` | — (se notifica) | Firmado por el/la Delegado/a; fija las obligaciones LOPD |
| `OFICIO_REQUERIMIENTO_CATASTRALES` | Interno | `REQUERIMIENTO_CATASTRALES.ELABORAR` | — (se notifica) | Requerimiento de subsanación |
| `OFICIO_TOMA_RAZON_RBDA` | Interno | `TOMA_RAZON_RBDA.ELABORAR` | — (se notifica) | Cierra `DATOS_CATASTRALES`, anuncia inicio de IP |
| `OFICIO_REQUERIMIENTO_RBDA_DEFINITIVA` | Interno | `REQUERIMIENTO_RBDA_DEFINITIVA.ELABORAR` | — (se notifica) | Requerimiento previo a `RESOLUCION_DUP.ELABORACION` |
| `RBDA_DEFINITIVA` | Externo | Registro de entrada (`ESPERAR_PLAZO` de `REQUERIMIENTO_RBDA_DEFINITIVA`) | `RESOLUCION_DUP.ELABORACION.ELABORAR` | Solo parcelas a expropiar, con propietarios, DNI y direcciones — o confirmación de la `RBDA` ya publicada en IP. Mismo tipo en ambos casos |

Los `DIAGNOSTICO` de `SOLICITUD_CATASTRALES.ANALIZAR`, `REQUERIMIENTO_CATASTRALES.ANALIZAR` y `ANALISIS_RBDA.ANALIZAR` reutilizan el tipo genérico ya existente (`DIAGNOSTICO`, INTERNO, producido por cualquier `ANALIZAR` — ver `TIPOS_DOCUMENTOS_CATALOGO.md`); no hace falta código propio por trámite. Los justificantes de `NOTIFICAR` reutilizan igualmente el tipo genérico ya existente (p. ej. `JUSTIFICANTE_POSTAL`).

---

## 4. Pendiente de llevar a catálogo

- ~~`ESTRUCTURA_FTT.md`/`.json`: añadir ambas fases con este contenido.~~ Hecho (#914, v6.4; `REQUERIMIENTO_RBDA_DEFINITIVA` añadido después en v6.5).
- ~~`ESTRUCTURA_ESF.md`/`.json`: `RESOLUCION_DUP` y `DATOS_CATASTRALES` en las tablas de `DUP`, `AAC+DUP`, `AAP+AAC+DUP`, `AAP+DUP`; sustituir `RESOLUCION` por `RESOLUCION_DUP` en `DUP` sola.~~ Hecho (#914, v2.4).
- `TIPOS_DOCUMENTOS_CATALOGO.md`: las 10 filas nuevas de §3 (8 + `OFICIO_REQUERIMIENTO_RBDA_DEFINITIVA` + `RBDA_DEFINITIVA`).
- Issues de implementación (#914 continúa con esto): `tipos_solicitudes` (fila `AAP+DUP`, ex-#911), `tipos_fases` (nuevas filas), `tipos_tramites`/`tipos_tareas` (nuevas filas), `tipos_documentos` (10 filas), `reglas_motor` (duplicado + CREAR/82.1 + #891), `_FASE_FINALIZADORA_POR_SIGLAS` a listas, `_SUSTITUCIONES` en `nombres_documentos.py`, `_TRAMITES_CON_NOTIFICACION_MULTIPLE` en `api_expedientes.py`, `catalogo_plazos` (converge con #892).
