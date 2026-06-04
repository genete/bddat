# ADR-021 — Operaciones externas: firma en BandeJA y notificación en Notifica-PNT

**Estado:** Adoptada — sujeta a refinamiento durante implementación
**Fecha:** 2026-06-04
**Issue:** pendiente

> **Nota de estabilidad:** Este ADR recoge la arquitectura acordada en sesión de diseño.
> Los campos concretos de las tablas nuevas, los intervalos de polling y los detalles
> de integración con BandeJA/Notifica-PNT se fijarán al implementar, conforme aparezcan
> los detalles reales. La decisión de diseño es firme; el detalle fino es abierto.

---

## Contexto

Varias tareas del flujo ESFTT tienen pasos que hoy ocurren **fuera de BDDAT**:

- **ELABORAR** (pasos 5-7): el usuario lleva el borrador generado a BandeJA, crea una
  comunicación, elige firmantes, y espera que Portafirmas complete la firma. El documento
  firmado vuelve por el canal de red compartido y el usuario lo sube manualmente al pool.
- **NOTIFICAR** (pasos 3-4): el usuario abre Notifica-PNT, rellena los campos de la
  notificación, obtiene un número de remesa, y más tarde descarga el justificante de
  entrega para subirlo como producido.

BDDAT solo ve el resultado de esas operaciones (el documento firmado subido, el
justificante registrado). No participa en la ejecución ni tiene trazabilidad de lo que
ocurrió en los sistemas externos.

Una prueba de concepto de inspección de estado en Notifica-PNT está disponible en
`D:\notifica-poc` y valida la viabilidad técnica del scraping.

---

## Decisión

### 1. Principio rector: solo adiciones, el dominio BDDAT no cambia

Ninguna tabla existente se altera en estructura. Ningún flujo ESFTT actual se modifica.
El subsistema de operaciones externas se construye como una capa adicional que interactúa
con BDDAT exactamente igual que lo haría un usuario humano: a través de los mismos
endpoints y modelos existentes.

### 2. Usuario virtual `BOT_BDDAT`

Se crea un registro en la tabla `usuarios` con un perfil especial (nombre, rol, flag
`es_bot=True` o similar). Es el actor que consta en la bitácora cuando una operación
externa actúa sobre BDDAT. No tiene sesión interactiva; el servicio receptor actúa en
su nombre mediante llamadas internas autenticadas.

Beneficios:
- La bitácora captura automáticamente toda acción del bot sin código especial.
- Los permisos del bot se gestionan con el sistema existente (ADR-013).
- Auditoría: filtrar bitácora por este usuario muestra toda la actividad automatizada.

### 3. Credenciales externas en la tabla `usuarios`

Cada usuario real que usará la automatización almacena sus credenciales de BandeJA y
Notifica-PNT en la tabla `usuarios` (columnas nuevas). El cifrado usa la misma librería
ya instalada en `requirements.txt` con la que se protegen las contraseñas actuales.

El bot actúa **en nombre del usuario real** (sus credenciales), no con una cuenta genérica.
Esto es correcto porque en BandeJA y Notifica las acciones quedan registradas bajo el
funcionario que las realiza.

Los campos concretos (nombre de columna, longitud, nulabilidad) se definen al implementar.

### 4. Tablas de datos comunes BandeJA / Notifica

Las aplicaciones externas tienen catálogos de opciones que el scraping necesita conocer:
tipos de procedimiento, unidades orgánicas, modelos de asunto, etc. Estos datos se
almacenan en tablas nuevas, compartidas, que alimentan tanto al scraper (para saber qué
opción elegir) como al formulario dual-use (para mostrar selectores al usuario).

Ejemplos de datos a catalogar (lista no exhaustiva, se cierra al implementar):
- Procedimientos disponibles en BandeJA para el tipo de expediente AT.
- Categorías y vías de notificación en Notifica-PNT.
- Identificadores de unidades firmantes en Portafirmas.

### 5. Cola de tareas (`cola_operaciones_externas`)

Tabla nueva en PostgreSQL. Cada fila representa una operación externa pendiente de
ejecución. Esquema conceptual — campos y tipos exactos se definen al implementar:

| Campo conceptual | Descripción |
|---|---|
| tipo | `FIRMA_BANDEJA` \| `NOTIFICACION_PNT` \| `COMPROBACION_FIRMA` \| `COMPROBACION_NOTIFICACION` |
| estado | `PENDIENTE` \| `EN_EJECUCION` \| `COMPLETADA` \| `ERROR` \| `RECHAZADO` \| `RESULTADO_NEGATIVO` |
| usuario_real_id | FK a `usuarios` — de quién son las credenciales externas |
| tarea_bddat_id | FK a la tarea ESFTT asociada |
| payload | JSON — datos del formulario dual-use + metadatos necesarios para el scraping |
| resultado_payload | JSON — respuesta íntegra del servicio (número de remesa, motivo rechazo, etc.) |
| disponible_desde | TIMESTAMP — cuándo puede ser procesada (noche por defecto, NOW() si "ahora") |
| intentos | INTEGER |
| referencias adicionales | (a definir: expediente_id, fase, trámite, documento_id, etc.) |

### 6. Servicios de scraping: `BandejaService` y `NotificaService`

Dos módulos Python independientes. Cada uno:
- Recibe un payload con los datos necesarios para ejecutar la operación.
- Usa Playwright para interactuar con la aplicación externa.
- Devuelve un resultado estructurado (éxito + datos) o un error con detalle.
- No conoce nada de BDDAT — recibe datos, ejecuta, devuelve resultado.

La POC de `D:\notifica-poc` es la base de `NotificaService`.

### 7. Servicio receptor

Módulo Python que actúa como puente entre los servicios de scraping y BDDAT:

- Procesa el resultado devuelto por `BandejaService` o `NotificaService`.
- Ejecuta las operaciones BDDAT necesarias **en nombre del usuario virtual** `BOT_BDDAT`
  (subir documento al pool, vincular como producido, registrar en bitácora, etc.).
- Actualiza el estado de la tarea de cola con el resultado.
- Puede ser invocado por:
  - El **scheduler nocturno** (modo normal).
  - El **usuario directamente** desde la UI ("¡Enviar ahora!") — misma ruta de código.

Cuando la primera fase completa (envío a BandeJA / envío a Notifica), el servicio receptor
crea automáticamente la tarea de segunda fase en la cola (comprobación de firma /
comprobación de entrega). Si el usuario hizo la fase 1 a mano, también puede crear esa
tarea de segunda fase directamente desde el formulario.

### 8. Formulario dual-use

Isla React por tipo de operación externa. Contiene exactamente los campos que el usuario
necesitaría rellenar en BandeJA o Notifica-PNT si lo hiciera manualmente. Son los mismos
campos que se envían al servicio de scraping como payload.

Si el servicio no está disponible o el usuario prefiere hacerlo a mano, el formulario
sigue siendo útil: muestra los datos pre-cargados del expediente y la tarea para que el
usuario los copie en la aplicación externa, sin tener que buscarlo por su cuenta.

El formulario permite elegir entre:
- **Ejecutar esta noche** (encola con `disponible_desde` = próxima ventana nocturna).
- **Ejecutar ahora** (encola con `disponible_desde = NOW()` y dispara el servicio receptor inmediatamente).

### 9. Modos de ejecución

| Modo | Cuándo | Cómo |
|---|---|---|
| Normal (batch) | Noche, ventana horaria configurable | Scheduler revisa cola y procesa `PENDIENTE` donde `disponible_desde <= NOW()` |
| Inmediato | Usuario pulsa "¡Enviar ahora!" | Se encola con `disponible_desde = NOW()`, servicio receptor invocado al momento |

En condiciones normales todas las tareas (fase 1 y fase 2) deben resolverse dentro de la
ventana nocturna. El modo inmediato es la excepción, no la norma.

### 10. Tipos de resultado negativo

La cola distingue tres tipos de resultado no satisfactorio con semántica diferente:

| Estado | Significado | Reintento automático | Acción requerida |
|---|---|---|---|
| `ERROR` | Fallo técnico — bot no pudo ejecutar (timeout, DOM cambió, red) | Sí, hasta N intentos | Si persiste: usuario interviene |
| `RECHAZADO` | Firma rechazada deliberadamente por el firmante en Portafirmas | No | Tramitador revisa documento, decide si reenvía |
| `RESULTADO_NEGATIVO` | Notificación rehusada, devuelta, sin efecto (Notifica devuelve código de estado) | No | Tramitador decide si aplica notificación edictal u otra vía |

`RECHAZADO` y `RESULTADO_NEGATIVO` son eventos de negocio — no tiene sentido reintentar
automáticamente. El scheduler los deja quietos; el tramitador actúa.

El `resultado_payload` guarda íntegramente lo que devolvió el servicio: motivo de rechazo,
nombre del firmante que rechazó, código de estado de Notifica, etc. Ese dato es el insumo
para la decisión humana.

En la bitácora (bajo el usuario virtual) queda un registro de texto legible:
*"Firma rechazada — [nombre] — motivo: [X]"* o *"Notificación devuelta — código: [Y]"*.

El árbol del expediente (ADR-016) mostrará el estado de la operación externa en el
inspector de la tarea asociada — detalle visual a diseñar al implementar.

---

## Por qué

- **Solo adiciones**: el motor ESFTT, los modelos existentes y las vistas actuales no se
  tocan. El riesgo de regresión es mínimo.
- **Usuario virtual**: hace innecesario un API privado para el bot. El bot es un usuario
  más; la trazabilidad, los permisos y la bitácora funcionan sin código extra.
- **Formulario dual-use**: la automatización no crea dependencia — si el bot falla, el
  usuario tiene los datos delante para hacerlo a mano. El dato introducido nunca se
  desperdicia.
- **Cola en PostgreSQL**: sin infraestructura adicional (Redis, Celery). Suficiente para
  el volumen de un equipo pequeño, y el batch nocturno reduce la presión de latencia.
- **Distinción ERROR / RECHAZADO / RESULTADO_NEGATIVO**: evita que el sistema reintente
  en bucle situaciones que requieren decisión humana, y da al tramitador información
  accionable en lugar de un genérico "ha fallado".

---

## Cómo implementar (esbozo — orden orientativo)

1. Crear usuario virtual `BOT_BDDAT` en la BD.
2. Añadir columnas de credenciales externas a `usuarios` (cifradas).
3. Crear tablas de catálogos BandeJA / Notifica y seed inicial de opciones.
4. Crear tabla `cola_operaciones_externas` con los campos del §5.
5. Implementar `NotificaService` partiendo de la POC en `D:\notifica-poc`.
6. Implementar `BandejaService`.
7. Implementar servicio receptor (lógica de actualización BDDAT + creación de fase 2).
8. Implementar scheduler nocturno (APScheduler o similar integrado en Flask).
9. Implementar formulario dual-use para NOTIFICAR (isla React).
10. Implementar formulario dual-use para ELABORAR / firma (isla React).
11. Integrar indicador de estado de operación externa en el inspector del árbol (ADR-016).
12. Smoke tests: cola encola, scheduler procesa, servicio receptor actualiza tarea BDDAT.

Los campos exactos de las tablas nuevas, los intervalos del scheduler, el diseño fino
del indicador de estado en el árbol y los detalles del formulario dual-use se cierran
durante la implementación según lo que aparezca al ver los sistemas reales.

---

## Alternativas descartadas

### A. Modificar el modelo de tareas con nuevos estados intermedios

Añadir `PENDIENTE_FIRMA`, `EN_FIRMA`, `FIRMADO`, etc. al tipo o estado de la tarea ESFTT.
Descartada porque altera el dominio existente, complica el motor de reglas y acopla la
lógica de automatización al núcleo. La cola externa es un plano separado que no contamina
el modelo de tareas.

### B. Webhook / integración API nativa con BandeJA y Portafirmas

Si existiese una API oficial, sería preferible al scraping. Descartada en la práctica
porque BandeJA y Notifica-PNT no exponen API pública consumible desde aplicaciones de
terceros en el entorno de la Junta. El scraping con Playwright es el único camino viable
confirmado por la POC.

### C. Celery + Redis como cola de tareas

Más potente y probado en producción a escala. Descartado porque introduce infraestructura
adicional (Redis) innecesaria para el volumen del equipo. Una cola en PostgreSQL con
scheduler nocturno cubre el caso sin añadir complejidad operacional.

---

## Anexo — Flujo manual actual por tipo de tarea

Este anexo describe los pasos físicos que realiza el usuario hoy, antes de cualquier
automatización. Sirve de referencia para entender qué operaciones son internas a BDDAT
y cuáles ocurren en sistemas externos. Las marcas **[IN]** y **[EX]** indican si el paso
ocurre dentro o fuera de BDDAT.

### ANALIZAR

1. [IN] Crear tarea en BDDAT.
2. [IN] Tomar documento(s) del pool del expediente y asignarlos como consumido.
3. [IN/EX] Leer los documentos (en BDDAT si se ofrece vista PDF; fuera si no).
4. [IN] Elaborar diagnóstico mediante la operación "generar documento" o rellenando el
   formulario de diagnósticos.
5. [IN] Asignar documento producido a la tarea.

> Todos los pasos son internos o potencialmente internos. ANALIZAR no entra en el
> alcance de este ADR.

---

### ELABORAR

1. [IN] Crear tarea en BDDAT.
2. [IN] Tomar documentos del pool (diagnóstico y otros) y asignarlos como consumido.
3. [IN] Elaborar borrador mediante "generar documento" vía plantilla.
4. [IN] El PDF generado se incorpora al pool y a la tarea como consumido (automatizable).
5. **[EX]** El usuario abre BandeJA, crea una comunicación nueva, rellena campos (asunto,
   procedimiento, expediente, destino, etc.), sube documentos, elige firmantes (vºbº y
   firma) y envía. BandeJA se comunica internamente con Portafirmas y crea entradas de
   firma y visto bueno para los firmantes elegidos.
6. **[EX]** Los firmantes firman en Portafirmas.
7. **[EX]** El usuario revisa Portafirmas, comprueba que está firmado, descarga el PDF
   firmado y lo coloca en el directorio del expediente en la red.
8. [IN] El usuario sube el documento firmado al pool del expediente. BDDAT lo reconoce
   automáticamente por las trazas dejadas en el borrador (issue pendiente — si no está
   implementado, el usuario lo clasifica manualmente) y lo asigna como producido.

> Los pasos 5, 6 y 7 son los que este ADR busca automatizar para ELABORAR.
> El paso 8 depende de un issue separado; si no está implementado, el usuario lo hace
> a mano sin impacto en la automatización de los pasos anteriores.

---

### NOTIFICAR

1. [IN] Crear tarea en BDDAT.
2. [IN] Tomar el documento firmado (y otros) del pool y asignarlos como consumido.
   Opcionalmente concatenar PDFs según la vía de notificación.
3. **[EX]** El usuario abre Notifica-PNT, rellena los campos de la notificación
   (destinatario, asunto, número de expediente, datos de contacto, etc.), sube el
   documento y envía. Notifica devuelve un **número de remesa** para seguimiento.
   El usuario anota ese número (habitualmente en un fichero de texto dentro de la
   carpeta del expediente en red).
4. **[EX]** Notifica envía un correo al usuario cuando el estado de la notificación
   cambia. El usuario descarga el justificante desde Notifica y lo incorpora al
   expediente junto con el número de remesa.
5. [IN] El tramitador, al revisar la vista de seguimiento, comprueba que la tarea está
   notificada porque ya tiene el documento producido (justificante) registrado.

> Los pasos 3 y 4 son los que este ADR busca automatizar para NOTIFICAR.
> El resultado de la notificación puede ser entrega, rehúso, devolución o falta de
> efecto — cada uno con implicaciones legales distintas (ver §10, `RESULTADO_NEGATIVO`).

---

### ESPERAR_PLAZO

Las casuísticas son muy variadas según el tipo de documento consumido que se espera
o si es simplemente un plazo per se. Queda fuera del alcance de este ADR; se analizará
en una sesión posterior para determinar qué puede automatizarse.
