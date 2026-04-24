# DISEÑO — Generación de escritos administrativos

> **Issue principal:** #167
> **Fecha análisis:** 2026-03-15 (3 sesiones)
> **Estado:** Análisis completo. Cabos 1-5 cerrados. Implementación pendiente → #277 (M2).
> **Issues relacionados:** #189 (cerrado), #181 y #182 (vinculados via C3)

---

## Lo implementado (#189 cerrado)

| Componente | Estado | Ubicación |
|---|---|---|
| Modelo `Plantilla` (renombrado desde `TipoEscrito` en #167 Fase 2) | HECHO | `app/models/plantillas.py` |
| Modelo `ConsultaNombrada` | HECHO | `app/models/consultas_nombradas.py` |
| Migración BD (ambas tablas) | HECHO | `migrations/versions/20c5d1e9d782*.py` |
| `ContextoBaseExpediente` (Capa 1) | HECHO | `app/services/escritos.py` |
| `generar_escrito()` (orquestador) | HECHO (parcial) | `app/services/generador_escritos.py` |
| Dependencia `docxtpl` | HECHO | `requirements.txt` (commit 6b85fcf) |
| Admin plantillas — CRUD 4 pantallas | HECHO | `app/modules/admin_plantillas/` |
| Panel de tokens copiables | HECHO | `_panel_tokens.html` |
| Protocolo URI `bddat-explorador://` | HECHO | Issue #231 |
| Config `PLANTILLAS_BASE` | HECHO | `app/config.py` |
| Guía Context Builders | HECHO (doc) | `docs/GUIA_CONTEXT_BUILDERS.md` |

**Stubs pendientes:**
- `_ejecutar_consultas()` devuelve `{}` — no ejecuta consultas nombradas aún
- Context Builders (Capa 2): arquitectura lista, cero implementaciones
- Sin endpoint que dispare la generación desde la UI de tramitación

---

## Modelo plantillas — decisiones (Cabo 1+2 cerrado)

| # | Decisión | Motivo |
|---|----------|--------|
| 1 | **Renombrar `tipos_escritos` → `plantillas`** | El nombre actual induce a confusión; es un registro de plantillas concretas |
| 2 | **Añadir `tipo_expediente_id` FK nullable a `plantillas`** | Completa la E que falta en ESFTT. NULL = cualquier tipo de expediente |
| 3 | **Eliminar `campos_catalogo` de `plantillas`** | Cálculo dinámico según contexto, no dato estático — evita inconsistencias |
| 4 | **Añadir `origen` (INTERNO/EXTERNO/AMBOS) a `tipos_documentos`** | Impide que una plantilla apunte a un tipo de documento externo |
| 5 | **Mantener `contexto_clase`** | Necesario para Capa 2 (Context Builders) |
| 6 | **Mantener `filtros_adicionales` JSONB** | Absorbe futuro sin migración |
| 7 | **Añadir campo `variante` TEXT nullable a `plantillas`** | Texto libre para distinguir plantillas del mismo contexto ESFTT ("Favorable", "Denegatoria") |

**Implementación:** Issue #167 Fase 2.

---

## Nomenclatura de ficheros (Cabo 3 cerrado)

### Nombre de plantilla (sistema lo construye, supervisor lo acepta o ajusta)

```
{tarea} {tramite} {fase} {solicitud} {expediente} [V {variante}].docx
```

Requiere campo `nombre_en_plantilla` en las 5 tablas tipo_ (tipos_tareas, tipos_tramites,
tipos_fases, tipos_solicitudes, tipos_expedientes).

**Reglas para NULLs (comodines):**
- NULL al final de la cadena → se omite
- NULL en medio de dos valores reales → se sustituye por `ANY`

### Nombre de documento generado

Los niveles que eran NULL/ANY en la plantilla se rellenan con datos reales del expediente.

**Ejemplos:**

| Plantilla | Documento generado |
|---|---|
| `Redactar Elaboracion Resolucion V Favorable.docx` | `Redactar Elaboracion Resolucion AAP+AAC AT-13465-24 V Favorable.docx` |
| `Redactar Requerimiento subsanacion.docx` | `Redactar Requerimiento subsanacion AAP+AAC AT-13465-24.docx` |
| `Notificar Traslado condicionados Consultas ANY Transporte.docx` | `Notificar Traslado condicionados Consultas AAP+AAC+DUP AT-13465-24.docx` |

**TODO:** Secuencial automático (sufijo ` (2)`, ` (3)`...) cuando ya existe un documento
con el mismo nombre para el mismo expediente.

**Almacenamiento:** Directorio plano en `PLANTILLAS_BASE/`. El contexto ESFTT vive en BD,
no en el filesystem. La convención de nombres evita colisiones sin subdirectorios.

**Implementación:** Issue #167 Fase 3 (`nombre_en_plantilla` × 5 tablas).

---

## Filtrado dinámico de tokens por contexto ESFTT (Cabo 4 cerrado)

- **3 tablas whitelist** E→S→F→T. Ver `docs/DISEÑO_MOTOR_REGLAS.md`.
- **Tipos de solicitud combinados** como entidades propias en `tipos_solicitudes`. Ver `docs/NORMATIVA_SOLICITUDES.md`.
- **Tokens Capa 1** son siempre los mismos (12 campos base del expediente).
- La dinamicidad de tokens llega con Capa 2 / Context Builders (diferible).
- **Toggle "Solo aplicables al contexto"** (principio de escape). Defecto = todas las opciones.

**Implementación:** Issue #167 Fase 4 (admin plantillas en cascada).

---

## Trazabilidad — códigos embebidos (C3, vincula #182 y #181)

Al generar el .docx, el sistema inyecta automáticamente metadatos de clasificación:

**Ciclo de vida del documento generado:**
```
GENERAR (#167)       → .docx con código embebido (#182)
   ↓
Usuario edita en Writer → el código sobrevive
   ↓
Portafirmas          → PDF firmado, código intacto
   ↓
INCORPORAR al pool   → inspección automática (#181) lee el código
   ↓
Clasificación sin intervención manual
```

**Doble vía de trazabilidad:**
1. **Custom properties del .docx** — invisible, lectura programática directa
2. **QR en pie de página** — resistente a impresión, escaneo, conversión PDF.
   El supervisor puede ubicarlo con `{{qr_clasificacion}}`; si no lo pone, el sistema lo añade al final.

**Código estructurado:**
`BDDAT|AT-12345|AAP_AAC|RESOLUCION|ELABORACION|RES_FAVORABLE|2026-03-15`

**Prerequisito R10:** Antes de implementar custom properties, probar manualmente
si sobreviven el pipeline .docx → portafirmas → PDF.

**Implementación:** Issue #167 Fase 6.

---

## Necesidades por actor (resumen de decisiones)

### A. Supervisor — al crear/gestionar plantillas

| ID | Necesidad | Decisión |
|----|-----------|----------|
| A0 | Filtrado dinámico de tokens por contexto ESFTT | Whitelist 3 tablas + toggle escape (Fase 4) |
| A1 | Validación de sintaxis del .docx subido | `DocxTemplate(ruta)` antes de registrar (Fase 4) |
| A2 | Probar plantilla con datos reales | DIFERIBLE |
| A3 | Parseo automático del .docx (detectar campos/consultas/fragmentos) | Necesario parcial (Fase 6) |
| A4 | CRUD de consultas nombradas | Necesario (Fase 5) |
| A5 | Versionado de plantillas | DIFERIBLE |

### B. Tramitador — al usar la plantilla en tarea REDACTAR

| ID | Necesidad | Decisión |
|----|-----------|----------|
| B1 | Botón "Generar escrito" en tarea REDACTAR | Botón en la card de tarea (Fase 5) |
| B2 | Selección de plantilla filtrada por contexto ESFTT | Lista con NULLs como comodines (Fase 5) |
| B3 | Preview de campos antes de generar | Valores del expediente + alerta si vacío (Fase 5) |
| B4 | Guardado con nombre sistematizado + checkboxes | Checkboxes: registrar pool + asignar doc_producido (Fase 5) |
| B5 | Abrir carpeta contenedora tras generar | Checkbox → protocolo `bddat-explorador://` (Fase 5) |
| B6 | Regeneración: sobrescritura transparente | Aviso + reemplazo binario en disco (Fase 5) |
| B8 | Generar = iniciar tarea | Si `fecha_inicio is None` → asignar `date.today()` (Fase 5) |

### C. Transversales

| ID | Necesidad | Decisión |
|----|-----------|----------|
| C1 | Ejecución de consultas nombradas | Implementar stub `_ejecutar_consultas()` (Fase 5) |
| C2 | Context Builders (Capa 2) | DIFERIBLE — bajo demanda del primer tipo complejo |
| C3 | Trazabilidad y código embebido | Código en custom properties + QR (Fase 6) |
| C4 | Metadatos del documento generado | `fecha_administrativa=NULL`, `prioridad=0`, `asunto=` descripción plantilla + ESFTT real |
| C7 | Gestión de errores de generación | Toast con detalle del error Jinja2 (Fase 5) |

---

## Fases de implementación

Ver `docs/PLAN_ROADMAP.md` — issue #167 para el detalle completo de cada fase.

| Fase | Contenido | Complejidad | Dependencias |
|------|-----------|:-----------:|:------------:|
| 0 | Fix R6 + export `campos_catalogo` | Baja | Ninguna |
| 1 | Solicitudes: FK directa + whitelist ESFTT | Alta | Fase 0 |
| 2 | Plantillas: rename + limpieza + nuevos campos | Alta | Fase 0 |
| 3 | Nomenclatura: `nombre_en_plantilla` × 5 tablas | Baja | Ninguna |
| 4 | Admin plantillas: selectores en cascada + form completo | Media-Alta | Fases 1+2+3 |
| 5 | Motor de generación (B1-B8) | Alta | Fase 4 |
| 6 | Trazabilidad y parseo (C3, A3) | Media | Fase 5 |

Las fases 1, 2 y 3 son **independientes entre sí** y pueden ejecutarse en cualquier orden.
Las fases 4-6 son secuenciales y requieren que cicatricen las anteriores.

---

## Actualizaciones pendientes tras ejecutar migraciones (Cabo 6)

Renombrado ejecutado en #167 Fase 2. Actualización de docs completada en #278.

| Fichero | Estado |
|---------|--------|
| `docs/GUIA_CONTEXT_BUILDERS.md` | ✅ actualizado (#278) |
| `docs/PLAN_ROADMAP.md` | ✅ actualizado (#278) |
| `docs/DISEÑO_SUBSISTEMA_DOCUMENTAL.md` | ✅ ya actualizado |
