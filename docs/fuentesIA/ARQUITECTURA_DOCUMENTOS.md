# ARQUITECTURA — Subsistema Documental

> **Sesión de diseño:** 2026-03-04
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

## GAP detectado — BLOQUEANTE para M1 #166

### `Documento` no tiene tipo de negocio

El motor de reglas ya usa `tipo_doc_codigo` en criterios `EXISTE_DOCUMENTO_TIPO`.
Pero `Documento.tipo_contenido` es el tipo MIME (application/pdf), no el tipo de negocio.

**Solución requerida antes de #166:**
- Tabla maestra `tipos_documentos` (`id`, `codigo`, `nombre`, `descripcion`, `requiere_doc_producido`)
- FK `tipo_doc_id` en `documentos` → `tipos_documentos`

**Issue:** #188 (M1)

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
