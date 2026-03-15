> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 5) Preguntas sin respuesta

Preguntas que requieren respuesta del usuario antes de implementar.
Organizadas por fase — solo bloquean la fase indicada, no las anteriores.

Cada pregunta incluye una recomendacion. Si la recomendacion es correcta,
basta con "OK" o "de acuerdo". Solo hace falta respuesta extendida si
la recomendacion no encaja.

---

### Para Fase 1 (solicitudes + whitelist)

#### P1. Semantica de `EXISTE_TIPO_SOLICITUD` con tipos combinados (R1)

Actualmente una solicitud AAP+AAC tiene DOS filas en la tabla puente
(una para AAP, otra para AAC). La regla `EXISTE_TIPO_SOLICITUD:AAP`
devuelve True.

Tras el cambio, la solicitud tiene un FK directo al tipo combinado `AAP_AAC`.
La comparacion `siglas == 'AAP'` devuelve False.

**Pregunta:** Cuando se escriban reglas en el motor, se referiran a tipos
atomicos (`AAP`) o a tipos combinados (`AAP_AAC`)?

**Recomendacion:** Usar siglas combinadas. Una solicitud AAP_AAC es un
procedimiento distinto de AAP puro — tiene fases, plazos y texto de
resoluciones distintos. Las reglas deben reflejar esa realidad.
Si puntualmente se necesita "cualquier solicitud que incluya AAP",
se puede crear un criterio adicional `INCLUYE_TIPO_SOLICITUD` que
descomponga las siglas.

---

#### P2. Completitud de tipos combinados a crear

Los 6 tipos combinados definidos son:

| Siglas | Descripcion |
|--------|-------------|
| AAP_AAC | Autorizacion Administrativa Previa y de Construccion |
| AAP_AAC_DUP | AAP + AAC + Declaracion de Utilidad Publica |
| AAP_AAC_AAU | AAP + AAC + Autorizacion Ambiental Unificada |
| AAP_AAC_AAU_DUP | AAP + AAC + AAU + DUP |
| AAC_DUP | AAC + Declaracion de Utilidad Publica |
| AAE_DEFINITIVA_AAT | Explotacion Definitiva + Transmision de Titularidad |

**Pregunta:** Falta algun tipo combinado que exista en la practica?

**Recomendacion:** Si faltan, mejor anadirlos ahora en el seed que
crear una migracion posterior. Si no estas seguro, estos 6 son suficientes
para empezar — se pueden anadir mas con un simple INSERT.

---

### Para Fase 2 (plantillas + tipos_documentos)

#### P3. Clasificacion de tipos de documentos por `origen`

La migracion necesita UPDATE para cada tipo de documento existente.
El seed inicial contiene al menos OTROS y DR_NO_DUP. Puede haber
mas si los has creado manualmente.

**Pregunta:** Para cada tipo de documento, clasificar como
INTERNO (generado por BDDAT), EXTERNO (recibido de fuera), o AMBOS.

**Propuesta inicial:**

| Codigo | Propuesta `origen` | Razon |
|--------|--------------------|-------|
| OTROS | AMBOS | Cajon de sastre, puede ser cualquier cosa |
| DR_NO_DUP | EXTERNO | La presenta el solicitante |
| *(otros que existan)* | *Clasificar* | |

> Necesito que confirmes esta tabla con todos los tipos que existan
> en tu BD de desarrollo. Si no recuerdas cuales hay, puedo consultar
> cuando tenga permisos SELECT o puedes ejecutar:
> `SELECT id, codigo, nombre FROM public.tipos_documentos ORDER BY id;`

---

### Para Fase 3 (nomenclatura)

#### P4. Valores de `nombre_en_plantilla` para tipos existentes

La migracion necesita UPDATE para cada registro en 5 tablas tipos_.
Estos valores aparecen en los nombres de fichero generados.

**Pregunta:** Revisar los valores propuestos tras generarlos. No necesito
respuesta ahora — preparare la lista completa al escribir la migracion
de Fase 3 y te la presento para revision.

**No es bloqueante para el analisis** — solo para la migracion concreta.

---

### Para Fase 4 (admin plantillas + cascada)

#### P5. Mecanismo del principio de escape en selectores (R5)

Los selectores en cascada ESFTT filtran opciones segun las tablas whitelist.
El principio de escape exige que no haya callejones sin salida.

**Pregunta:** Como se presenta la via de escape en la interfaz?

**Recomendacion:** Toggle "Mostrar todos" en cada selector:
- **Normal:** solo opciones de la whitelist
- **Mostrar todos:** aparecen todas las opciones, con las de fuera de
  whitelist marcadas con badge de advertencia (ej: icono + color distinto)
- El endpoint AJAX devuelve `{compatibles: [...], otros: [...]}`
- Si el usuario elige un "otro", se registra en bitacora

Alternativas descartadas:
- Entrada "Otros..." al final → requiere segundo selector, mas complejo
- Bypass global → demasiado coarse-grained, se pierde la advertencia por selector

---

### Para Fase 5 (motor de generacion)

#### P6. Ubicacion de endpoints de generacion (I1)

La vista de acordeones (Vista 3) esta deprecada. Los endpoints de generacion
no deben ir en `routes/vista3.py`.

**Pregunta:** Donde se implementan?

**Opciones:**

| Opcion | Fichero | Pros | Contras |
|--------|---------|------|---------|
| A | `routes/api_escritos.py` (NUEVO) | Separacion clara, reutilizable | Un fichero mas |
| B | Dentro del futuro fichero de vista BC | Cohesion con la UI que lo consume | Acoplado a la vista |
| C | `modules/admin_plantillas/routes.py` | Ya existe el modulo | Mezcla admin + tramitacion |

**Recomendacion:** Opcion A. Un fichero API dedicado a la generacion de
escritos. Los endpoints son API pura (JSON in, JSON/file out) y los
puede consumir cualquier vista futura. Mantiene separacion limpia.

---

### No bloqueantes (pueden decidirse durante implementacion)

#### P7. FK `plantilla_id` en tabla `documentos` (I4)

**Pregunta:** Anadir FK nullable `plantilla_id` en documentos para
trazabilidad directa plantilla→documento?

**Recomendacion:** Si. Coste minimo (1 columna). Aporta verificacion
cruzada con el codigo embebido (C3). Se anade en la migracion de Fase 6.

---

#### P8. Checkboxes de generacion: estado por defecto

Al generar un escrito, hay 3 checkboxes opcionales:
- Registrar en pool
- Asignar como documento producido
- Abrir carpeta contenedora

**Pregunta:** Marcados o desmarcados por defecto?

**Recomendacion:**
- Registrar en pool: **marcado** (es lo esperable en el 90% de casos)
- Asignar como doc producido: **marcado** (idem)
- Abrir carpeta: **desmarcado** (es conveniencia, no necesidad)

El usuario siempre puede cambiarlos antes de generar.

---

### Resumen

| # | Pregunta | Fase | Tipo |
|---|----------|:----:|:----:|
| P1 | Semantica EXISTE_TIPO_SOLICITUD | 1 | Confirmacion |
| P2 | Completitud tipos combinados | 1 | Revision |
| P3 | Clasificacion tipos_documentos por origen | 2 | Datos necesarios |
| P4 | Valores nombre_en_plantilla | 3 | Revision (diferida) |
| P5 | Mecanismo escape selectores | 4 | Confirmacion |
| P6 | Ubicacion endpoints generacion | 5 | Decision |
| P7 | FK plantilla_id en documentos | 6 | Confirmacion |
| P8 | Checkboxes por defecto | 5 | Confirmacion |

> **Si todas las recomendaciones son correctas**, las unicas respuestas
> que necesito antes de empezar son P2 (lista completa) y P3 (clasificacion).
> El resto son confirmaciones de "OK, adelante con lo propuesto".
