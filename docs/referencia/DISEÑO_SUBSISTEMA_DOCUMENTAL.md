# ARQUITECTURA — Subsistema Documental

> **Sesión de diseño:** 2026-03-04 | **Actualizado:** 2026-03-18
> Decisiones tomadas antes de entrar en M1 sistema documental (#166) y M2 generación escritos (#167).
> Documentos relacionados: `DISEÑO_MOTOR_REGLAS.md`, `GUIA_CONTEXT_BUILDERS.md`, `PLAN_ROADMAP.md`

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

### Fechas de tarea — única fuente de verdad (#310)

`Tarea.fecha_inicio` y `Tarea.fecha_fin` fueron eliminadas en #310.
`Documento.fecha_administrativa` es la única fuente de verdad para la fecha del acto jurídico
asociado a una tarea: cuándo se firmó, se notificó, se registró.

La completitud de una tarea se deduce de documentos, no de fechas:
`tarea.ejecutada` ↔ `documento_producido_id IS NOT NULL`.

`Documento.fecha_administrativa` sirve además para: ordenar la bandeja de entrada por antigüedad,
sugerir fechas al crear tareas relacionadas, y como referencia temporal para plazos
(ver `DISEÑO_FECHAS_PLAZOS.md`).

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

Ver detalle completo en `docs/GUIA_CONTEXT_BUILDERS.md`.

### Tabla `plantillas` (renombrada desde `tipos_escritos` en #167 Fase 2)

Modelo: `app/models/plantillas.py`

```
plantillas
  id                    SERIAL PK
  codigo                TEXT UNIQUE NOT NULL      ← slug estable (REQUERIMIENTO_SUBSANACION)
  nombre                TEXT NOT NULL             ← nombre legible para la UI
  descripcion           TEXT NULL
  ruta_plantilla        TEXT NOT NULL             ← ruta relativa a PLANTILLAS_BASE/plantillas/
  variante              TEXT NULL                 ← distingue plantillas del mismo contexto (Favorable, Denegatoria)
  tipo_documento_id     FK tipos_documentos NOT NULL  ← tipo que se asignará al Documento generado
  tipo_expediente_id    FK tipos_expedientes NULL ← NULL = aplica a cualquier tipo de expediente
  tipo_solicitud_id     FK tipos_solicitudes NULL ← NULL = aplica a cualquier solicitud
  tipo_fase_id          FK tipos_fases NULL       ← NULL = aplica a cualquier fase
  tipo_tramite_id       FK tipos_tramites NULL    ← NULL = aplica a cualquier trámite
  contexto_clase        TEXT NULL                 ← nombre clase Python; NULL = solo capa base
  filtros_adicionales   JSONB DEFAULT '{}'        ← variables de negocio futuras (tensión, tecnología…)
  activo                BOOLEAN DEFAULT TRUE      ← FALSE = oculta en REDACTAR, conservada para histórico
```

**Cambios respecto al diseño original (`tipos_escritos`):**
- Renombrada a `plantillas` por claridad semántica
- Añadidas 4 FKs ESFTT nullable (tipo_expediente, tipo_solicitud, tipo_fase, tipo_tramite) para filtrado por contexto de tarea — NULL = comodín
- `plantilla_url` → `ruta_plantilla` (relativa a `PLANTILLAS_BASE/plantillas/`)
- Añadido `tipo_documento_id` (NOT NULL): tipo semántico que se asigna al Documento generado
- Añadido `variante`: texto libre para distinguir escritos del mismo contexto ESFTT
- Añadido `filtros_adicionales`: JSON extensible para criterios futuros
- Eliminado `campos_catalogo`: reemplazado por `consultas_nombradas` (tabla independiente)

### Tabla `consultas_nombradas` (nueva, #167 Fase 3)

Modelo: `app/models/consultas_nombradas.py`

Consultas SQL predefinidas para tablas dinámicas en plantillas .docx.
El supervisor referencia la consulta por nombre en el marcador: `{%tr for row in municipios_afectados %}`.

```
consultas_nombradas
  id          SERIAL PK
  nombre      TEXT UNIQUE NOT NULL     ← slug usado en plantilla (municipios_afectados)
  descripcion TEXT NOT NULL            ← texto legible para supervisor en UI
  sql         TEXT NOT NULL            ← SQL parametrizado con :expediente_id
  columnas    JSONB NOT NULL           ← [{campo, descripcion}] para UI supervisor
  activo      BOOLEAN DEFAULT TRUE
```

### Capa 1 — Contexto base (autoservicio Supervisor)

`app/services/escritos.py` → `ContextoBaseExpediente(expediente).get_contexto()`

Devuelve diccionario plano con los campos directos del expediente:
numero_at, titular (nombre/NIF/dirección), proyecto (título/finalidad/emplazamiento),
instrumento ambiental, responsable, municipios, fecha_hoy.

El Supervisor prepara plantilla .docx con `{{campo}}` y la registra en `plantillas`
sin intervención del gestor de sistemas.

### Capa 2 — Context Builder (con soporte técnico/AI)

Para escritos con campos calculados o cruzados. Clase Python que enriquece el contexto base.
Ver `GUIA_CONTEXT_BUILDERS.md` para crear uno nuevo.

### Capa 3 — Consultas nombradas (autoservicio Supervisor)

Tablas dinámicas ejecutadas sobre el expediente. Se ejecutan todas las activas y se pasan
al contexto Jinja2; las no referenciadas en la plantilla se ignoran silenciosamente.
Si una consulta falla, se pasa como lista vacía (log warning, no rompe generación).

### Motor de generación (Fase 5 #167)

`app/services/generador_escritos.py` orquesta el flujo:
1. Carga plantilla .docx desde `PLANTILLAS_BASE/plantillas/`
2. Capa 1: `ContextoBaseExpediente`
3. Capa 2: Context Builder opcional (`plantilla.contexto_clase`)
4. Capa 3: Consultas nombradas activas
5. Renderiza con `python-docx-template` (Jinja2)

API REST: `app/routes/api_escritos.py` — endpoints `/api/escritos/plantillas`, `/preview`, `/generar`.

**Issue:** #167

---

## Resumen de decisiones

| Decisión | Elegida | Descartada |
|----------|---------|------------|
| Extensión de `Documento` | Particularización N:M | Herencia SQLAlchemy |
| Estado de consultas | Service layer (seguimiento.py) | Event Sourcing / campo persistido |
| Plazos en motor | Servicio separado (plazos.py) | Criterios temporales en condiciones_regla |
| Escritos simples | Contexto base + plantilla .docx (tabla `plantillas`) | Hardcoded por tipo |
| Escritos complejos | Context Builder por tipo + consultas nombradas | Motor genérico de descubrimiento semántico |
| Catálogo de escritos | `plantillas` con 4 FKs ESFTT nullable (comodín) | `tipos_escritos` sin filtrado por contexto |
| Tablas dinámicas en plantillas | `consultas_nombradas` (SQL + :expediente_id) | `campos_catalogo` JSONB en tipos_escritos |
| Campo `origen` | Eliminado; procedencia en tablas cualificadoras | Campo libre en Documento |
| Campo `nombre_display` | Eliminado; deducible de URL | Campo editable por usuario |
| `fecha_administrativa` | Nullable (dos semánticas de NULL documentadas) | NOT NULL con fecha placeholder |
| `prioridad` | Mantener, pseudo-bool, validación solo frontend | Eliminar / CHECK constraint BD |
| Carga inicial al pool | Pantalla de gestión (#180), sin tarea ESFTT | Tarea INCORPORAR |
| INCORPORAR | Solo externos durante tramitación activa | También para carga inicial |
| ZIP como documento | Solo referencia histórica, no unidad de trabajo | Documento clasificable |
| Requisitos documentales legales | Issue #192 (M5, futuro) | Sin soporte |
