# ARQUITECTURA — Subsistema Documental

> **Sesión de diseño:** 2026-03-04 | **Actualizado:** 2026-03-05
> Decisiones tomadas antes de entrar en M1 sistema documental (#166) y M2 generación escritos (#167).
> Documentos relacionados: `MOTOR_REGLAS_arquitectura.md`, `GUIA_CONTEXT_BUILDERS.md`, `ROADMAP.md`

---

## Principios rectores

### 1. Documento como pool agnóstico — confirmado correcto

`Documento` mantiene un único FK: `expediente_id`. No conoce tareas, proyectos ni organismos.
Las relaciones viven fuera, en tablas de particularización. **No modificar esta filosofía.**

### 2. Particularización N:M — patrón estándar del proyecto

En lugar de herencia SQLAlchemy (STI/JTI), el proyecto usa **tablas puente con metadatos**
para añadir semántica específica a documentos genéricos.

**Precedente existente:** `DocumentoProyecto` — tabla puente con campo `tipo` (PRINCIPAL/MODIFICADO/REFUNDIDO/ANEXO).

**Regla:** NO usar `class DocumentoOrganismo(Documento)` — herencia SQLAlchemy prohibida para documentos.

**Razón:** Un documento puede tener múltiples roles simultáneamente (proyecto + organismo).
La herencia singulariza; la particularización N:M no lo hace.

### 3. Estado derivado de documentos — via service layer

El estado de entidades complejas (consultas a organismos, estado de expediente) se deriva
consultando documentos, no almacenando estado duplicado.

**Dónde vive esta lógica:** `app/services/seguimiento.py` (M2, issue #169).
No implementar como @property en `Documento` ni como Event Sourcing completo.

---

## GAP resuelto — #188 cerrado

`tipos_documentos` + FK `tipo_doc_id` en `documentos` implementados en commit `fbb006e`.
`OTROS` (id=1) es el cajón de sastre por defecto (`server_default='1'`).

---

## Revisión del modelo Documento — #191 cerrado (2026-03-05)

### Campos eliminados

| Campo | Motivo |
|---|---|
| `origen` | Semántica ambigua (mezclaba dirección flujo con emisor concreto). La procedencia del emisor va en columnas de las tablas cualificadoras según su contexto. |
| `nombre_display` | Deducible del último segmento de la URL. Una sola fuente de la verdad. La interfaz siempre muestra el nombre calculado. |

### `fecha_administrativa` → nullable

NULL tiene dos significados legítimos:
1. **Pendiente de revisión** — documento cargado al pool sin fecha asignada aún.
2. **Sin valor jurídico propio por diseño** — borradores (`REDACTAR`) e informes internos (`ANALISIS`); el efecto jurídico lo tiene el documento firmado sucesor.

La API de asignación a tareas debe rechazar documentos con NULL cuando el tipo de tarea lo requiera. Es validación de negocio en capa de servicio, no constraint de BD.

### Coexistencia fechas Tarea ↔ Documento — sin duplicación

Dos campos de fecha con semánticas distintas y complementarias:

| Campo | Rol | Quién lo introduce |
|---|---|---|
| `Tarea.fecha_inicio / fecha_fin` | Verdad legal: cómputo de plazos y efectos administrativos | Tramitador, manualmente |
| `Documento.fecha_administrativa` | Dato de origen: fecha objetiva del acto jurídico del archivo | Tramitador, al incorporar el documento |

La fecha del documento es **dato de origen** (cuándo se firmó, se notificó, se registró).
La fecha de la tarea es **dato de proceso** (cuándo empieza/termina el efecto procedimental).
No hay duplicación: una informa a la otra pero no son intercambiables.

`Documento.fecha_administrativa` sirve además para: ordenar la bandeja de entrada por antigüedad, sugerir fechas al crear tareas relacionadas.

### `prioridad` — semántica aclarada

`0` = no prioritario. `>0` = prioritario (recurso de alzada, respuesta desfavorable, alegación urgente).
Pseudo-booleano que deja margen para escalas futuras. Validación de rango solo en frontend.

---

## Dos vías de entrada al pool — decisión 2026-03-05

Las dos vías son completamente independientes y no deben confundirse:

**Vía 1 — Carga masiva de soporte (operación previa a tramitación)**
Pantalla de gestión documental (#180). Ejecutada por el administrativo antes o al margen
del flujo de tramitación. No genera tareas en el ESFTT.

**Vía 2 — Tarea INCORPORAR (durante tramitación activa)**
Solo para documentos externos que llegan mientras el expediente está en tramitación:
informes de organismos, alegaciones, respuestas del titular, justificantes de publicación.
El documento debe existir ya en el pool antes de ejecutar la tarea.
**No aplica a la recepción inicial de solicitudes.**

### RECEPCION_SOLICITUD sin INCORPORAR

`REGISTRO_SOLICITUD.RECEPCION_SOLICITUD` cambia a patrón A (solo `ANALISIS`).
Los documentos ya están en el pool. El `ANALISIS` verifica su presencia, los cualifica
con `tipo_doc_id` correcto y produce un acta de recepción que es presupuesto para
las fases `ADMISIBILIDAD` y `ANALISIS_TECNICO`.

### ZIP — no válido como unidad de trabajo

Un ZIP no permite verificar la presencia de tipos específicos exigidos por la legislación.
Los documentos deben incorporarse individualmente con su `tipo_doc_id`.
El ZIP puede conservarse como referencia histórica del paquete original de registro,
pero no como sustituto de los documentos individuales clasificados.

---

## Subsistema consultas a organismos

**Tabla `entidades_consultadas`** (issue #153, diseño pendiente):
- `solicitud_id` FK, `entidad_id` FK, `tipo_consulta` (SEPARATA, LISTA...), `fecha_inclusion`

**Tabla de particularización `documentos_organismo`** (nueva, cuando llegue SEPARATAS):
- `documento_id` FK UNIQUE → documentos
- `organismo_id` FK → entidades
- `tipo_rol` — DR_CONSULTA, TRASLADO, RESPUESTA_ORGANISMO, RESPUESTA_TITULAR...

**Estado de consulta** — derivado en `seguimiento.py`:
```python
tipos_presentes = {doc.tipo_doc.codigo for doc in docs_del_organismo}
if 'RESPUESTA_ORGANISMO' in tipos_presentes: return 'RESPONDIDA'
elif 'SEPARATA_ENVIADA' in tipos_presentes: return 'ENVIADA'
else: return 'PENDIENTE'
```

---

## Motor de reglas — dimensión temporal

**Decisión:** Los plazos legales NO se integran en `condiciones_regla` directamente.
Se implementan en `app/services/plazos.py` (M3, issues #172/#173).

El motor delegará via nuevo `tipo_criterio = 'PLAZO_ESTADO'`:
- `params: {plazo_codigo, estado_esperado}`
- Handler devuelve PERMITIDO hasta que M3 esté implementado (mismo patrón que Fase 2)

**Issue:** #190 (M3)

---

## Generación de escritos — arquitectura dos capas

Ver detalle completo en `docs/fuentesIA/GUIA_CONTEXT_BUILDERS.md`.

### Tabla `tipos_escritos`

```
tipos_escritos
  id                SERIAL PK
  codigo            TEXT UNIQUE NOT NULL
  nombre            TEXT NOT NULL
  descripcion       TEXT
  plantilla_url     TEXT            ← ruta al .docx plantilla
  contexto_clase    TEXT NULL       ← nombre clase Python; NULL = solo capa base
  campos_catalogo   JSONB NULL      ← {campo: descripcion_legible} para la UI
  activo            BOOLEAN DEFAULT TRUE
```

### Capa 1 — Contexto base (autoservicio Supervisor)

`app/services/escritos.py` → `ContextoBaseExpediente.get_contexto(expediente_id)`

Devuelve diccionario plano con todos los campos simples del expediente:
titular, proyecto, tipo, municipio, tensión, instrumento ambiental, fecha_hoy, etc.

El Supervisor prepara plantilla .docx con `{{campo}}` y la registra en `tipos_escritos`
sin intervención del gestor de sistemas.

### Capa 2 — Context Builder (con soporte técnico/AI)

Para escritos con campos calculados o cruzados. Clase Python que enriquece el contexto base.
Ver `GUIA_CONTEXT_BUILDERS.md` para crear uno nuevo.

**Issue:** #189 (M2)

---

## Resumen de decisiones

| Decisión | Elegida | Descartada |
|----------|---------|------------|
| Extensión de `Documento` | Particularización N:M | Herencia SQLAlchemy |
| Estado de consultas | Service layer (seguimiento.py) | Event Sourcing / campo persistido |
| Plazos en motor | Servicio separado (plazos.py) | Criterios temporales en condiciones_regla |
| Escritos simples | Contexto base + plantilla .docx | Hardcoded por tipo |
| Escritos complejos | Context Builder por tipo | Motor genérico de descubrimiento semántico |
| Campo `origen` | Eliminado; procedencia en tablas cualificadoras | Campo libre en Documento |
| Campo `nombre_display` | Eliminado; deducible de URL | Campo editable por usuario |
| `fecha_administrativa` | Nullable (dos semánticas de NULL documentadas) | NOT NULL con fecha placeholder |
| `prioridad` | Mantener, pseudo-bool, validación solo frontend | Eliminar / CHECK constraint BD |
| Carga inicial al pool | Pantalla de gestión (#180), sin tarea ESFTT | Tarea INCORPORAR |
| INCORPORAR | Solo externos durante tramitación activa | También para carga inicial |
| ZIP como documento | Solo referencia histórica, no unidad de trabajo | Documento clasificable |
| Requisitos documentales legales | Issue #192 (M5, futuro) | Sin soporte |
