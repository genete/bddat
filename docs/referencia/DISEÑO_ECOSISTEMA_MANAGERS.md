# Ecosistema de Managers externos — Diseño conceptual

> Documento semilla. Los proyectos aquí descritos (bandeja-manager, ptwanda-manager)
> son futuros repositorios independientes. Este fichero recoge las decisiones de
> integración con BDDAT para que sean coherentes desde el inicio.
>
> **Estudio de campo del DOM de PTWANDA** (acceso, flujo de scraping, descarga de documentos):
> [ESTUDIO_DOM_PTWANDA.md](ESTUDIO_DOM_PTWANDA.md).

---

## Contexto

BDDAT recibe documentación a través de aplicaciones externas de registro:

- **Bandeja** — plataforma corporativa de entrada de comunicaciones (Junta de Andalucía)
- **PTWANDA** — plataforma de tramitación de procedimientos, solicitudes vía VEAJA

Ambas requieren acceso manual: login, descarga de documentos, clasificación, asignación.
El objetivo del ecosistema de managers es automatizar ese proceso con Python + Playwright
y exponer una UI web para la jefatura de servicio/departamento que realiza el reparto.

---

## Arquitectura general

```
Aplicación externa (Bandeja / PTWANDA)
        ↓  Playwright scraping (scheduler nocturno)
  [manager-db]  ←→  Flask :500X  (UI jefatura)
        ↓  decisión jefatura
    ┌───┴─────────────────────────────────┐
    │ No es BDDAT                         │ Es BDDAT
    │ Playwright asigna en app externa    │ descomprime ZIP
    │ Registra asignación + nota          │ mueve carpeta al pool de BDDAT
    └─────────────────────────────────────┘ INSERT docs con plataforma_codigo
```

Cada manager es un proyecto independiente con su propia BD PostgreSQL y su propio
proceso Flask. Comparten el mismo servidor físico que BDDAT.

---

## Infraestructura compartida (mismo servidor)

```
PC servidor
├── PostgreSQL
│   ├── bddat               ← BDDAT (Flask :5000)
│   ├── bandeja_manager     ← bandeja-manager (Flask :5001)
│   └── ptwanda_manager     ← ptwanda-manager (Flask :500X)
└── schedulers              ← APScheduler dentro de cada Flask
```

---

## Flujo bandeja-manager

### Scheduler nocturno (APScheduler)

1. Playwright obtiene listado actual de entradas PENDIENTE de Bandeja.
2. Compara con `entrada_bandeja.id_bandeja` ya registrados en la BD local.
3. Solo descarga las entradas nuevas → INSERT con `estado=PENDIENTE`.
4. Los documentos se guardan en disco local (carpeta propia del manager).

### UI jefatura — reparto

- Lista de entradas PENDIENTE descargadas.
- El manager pre-procesa el contenido (nombre de ficheros, texto extraíble).
- El usuario puede abrir el documento ya descargado para más detalle (sin llamadas HTTP frágiles).
- **Concurrencia**: `SELECT FOR UPDATE SKIP LOCKED` evita que dos jefes gestionen la misma entrada simultáneamente.

### Decisión: no es BDDAT

1. Jefatura selecciona usuario asignable (tabla `UsuarioBandeja` gestionable desde UI).
2. Playwright abre Bandeja y asigna la comunicación al usuario seleccionado.
3. Se registra asignación + nota opcional en la BD del manager.
4. La entrada desaparece del listado de pendientes.

### Decisión: es BDDAT

1. Jefatura consulta y selecciona el expediente en BDDAT (via acceso directo a PostgreSQL o mediante los templates de búsqueda de BDDAT). Si corresponde a una solicitud nueva, deja el expediente sin asignar. El documento requiere el `id` del expediente para la inserción.
2. El manager descomprime el ZIP y mueve la carpeta descomprimida al **pool de BDDAT**.
3. INSERT de cada documento en la BD de BDDAT con:
   - `expediente_id` = id del expediente si la jefatura lo localizó, o `NULL`
   - `plataforma_codigo` = código de la entrada (p.ej. `"BJ-2026-00423"`)
4. La entrada queda registrada como `estado=TRASLADADA_BDDAT` en la BD del manager.

---

## Flujo ptwanda-manager

> Detalle técnico del DOM y del scraping en [ESTUDIO_DOM_PTWANDA.md](ESTUDIO_DOM_PTWANDA.md).
> Esta sección recoge el flujo de negocio y la integración con BDDAT.

PTWANDA es la plataforma de entrada de solicitudes telemáticas (VEAJA). El manager opera sobre la
cola de solicitudes en estado **"solicitud telemática (firmada)"** (procedimiento `ENERG_INST`,
fase `SOLICITUD TELEMATICA`): las solicitudes nuevas presentadas y firmadas, aún sin tramitar.

### Visión de integración (objetivo — aún NO integrable)

1. ptwanda-manager **descarga** automáticamente la documentación de toda solicitud firmada.
2. BDDAT ofrece a los **administrativos avanzados** una interfaz a esos ficheros descargados.
3. Los **administrativos avanzados** (los más antiguos del servicio — **no es un rol nuevo**)
   asumen la **nueva labor** de crear en BDDAT el expediente correspondiente (huérfano, sin
   asignar) a partir de esos ficheros. BDDAT es solo **una parte** del trabajo del servicio:
   sigue habiendo carga administrativa relevante (Notifica, etc.); esta labor se integra en ese
   conjunto, no lo sustituye.
4. Creado el expediente en BDDAT, ptwanda-manager **finaliza automáticamente** el expediente en
   PTWANDA (paso aún no explorado en el DOM; se prevé sencillo). Así deja de aparecer como
   "solicitud firmada" en la siguiente iteración del scraping.

### Por qué todavía no se puede integrar

La finalización automática (paso 4) no puede activarse mientras siga vigente el **flujo de
producción actual sin BDDAT**: hoy son los técnicos quienes finalizan a mano. Integrarla ahora
colisionaría con ese trabajo. La integración completa queda condicionada a que BDDAT esté en
producción.

### Flujo manual actual (vigente hoy)

1. Un **técnico avanzado con labores extra** entra en PTWANDA, lee de qué trata cada solicitud firmada y la **asigna** a un técnico.
2. El **técnico**, periódicamente, entra en PTWANDA, **descarga** la documentación y **finaliza** el expediente.
3. Ese técnico avanzado **itera** buscando nuevas solicitudes firmadas y repite el ciclo.

### Paso intermedio inmediato (app autónoma — repositorio aparte)

Mientras la integración con BDDAT no es posible, una **aplicación Python autónoma** automatiza el
trabajo del técnico (paso 2 del flujo manual), sin depender de BDDAT:

- Recibe el **DNI del técnico** al que la jefatura ha asignado los expedientes.
- Descarga **todos los expedientes a su cargo** en estado solicitud firmada.
- **Finaliza** cada uno tras la descarga.

El código de descarga y finalización será reutilizable por ptwanda-manager cuando llegue la
integración completa.

---

## Integración con BDDAT — campo `plataforma_codigo`

Nuevo campo `plataforma_codigo VARCHAR` (nullable) en la tabla `documentos` de BDDAT.
El valor es el código único de la entrada en la plataforma externa de origen:

| valor de `plataforma_codigo` | significado |
|---|---|
| `NULL` | documento generado internamente en BDDAT |
| `"BJ-2026-00423"` | documento externo, entrada de Bandeja |
| `"PTW-2026-00891"` | documento externo, entrada de PTWANDA |

**Desacoplamiento deliberado:**
- BDDAT no sabe ni necesita saber qué sistema generó el código.
- El código es opaco para BDDAT pero legible por humanos: identifica a la vez la plataforma y la entrada concreta.
- Si mañana aparece un tercer sistema, BDDAT no cambia.
- No hay FK ni lectura inversa de BDDAT hacia ningún manager.

> **Nota:** `tipos_documentos` ya tiene un campo llamado `origen` con valores
> `INTERNO / EXTERNO / AMBOS`. Son conceptos distintos: ese campo describe la naturaleza
> del *tipo* de documento (quién lo genera habitualmente), no la procedencia de una
> instancia concreta. Ese campo tiene además una deuda de diseño pendiente: el valor
> `AMBOS` es ambiguo y el nombre `origen` no refleja bien su semántica. Se anota como
> refactorización futura independiente de este diseño.

### Documentos huérfanos (solicitud nueva)

Cuando `expediente_id = NULL`, todos los documentos con el mismo `plataforma_codigo`
forman un conjunto coherente: llegaron juntos, son la misma solicitud.

En BDDAT el administrativo ve **"lote BJ-2026-00423 sin expediente"** como grupo,
no como documentos sueltos. Desde el wizard de nuevo expediente puede auto-asignar
todo el lote a la nueva solicitud de una sola acción.

---

## Tabla `UsuarioBandeja` (bandeja-manager)

Gestionable desde la UI del manager. Playwright usa `login_bandeja` para ejecutar
la asignación en la aplicación externa.

| campo         | tipo    | notas                        |
|---------------|---------|------------------------------|
| id            | int PK  |                              |
| nombre        | varchar | nombre visible en la UI      |
| login_bandeja | varchar | login en la aplicación externa |
| activo        | bool    | filtra la lista de asignables |

---

## Ventajas sobre el flujo manual anterior

| Aspecto | Flujo anterior | Con managers |
|---|---|---|
| Descarga | Técnico entra en Bandeja y descarga | Automática, nocturna |
| Reparto | Jefatura asigna en Bandeja uno a uno | UI centralizada con pre-análisis |
| Concurrencia | Sin control (duplicados posibles) | Bloqueo optimista por BD |
| Trazabilidad | Hoja de cálculo | BD auditada con notas |
| Ingesta en BDDAT | Manual por técnico | Automática desde jefatura |
| Acceso técnico a Bandeja | Necesario para BDDAT | Innecesario para asignaciones BDDAT |

---

## Pendiente de definir

- Criterios de pre-análisis automático del contenido (clasificador simple por nombre de fichero vs. NLP).
- Formato exacto del código `plataforma_codigo` por sistema (prefijo + año + secuencial).
- Política de retención de ficheros descargados en el manager tras traslado a BDDAT.
- Migración BDDAT: añadir columna `plataforma_codigo VARCHAR` nullable a la tabla `documentos`.
- Refactorización futura: renombrar/rediseñar `tipos_documentos.origen` (INTERNO/EXTERNO/AMBOS) cuyo nombre es ambiguo y `AMBOS` no tiene criterio claro para el supervisor del catálogo.
