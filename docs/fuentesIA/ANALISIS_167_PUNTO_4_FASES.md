> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 4) Orden logico de decisiones de diseno

Plan de implementacion en fases. Cada fase es una rama independiente que deja
Flask funcional tras merge. Si hay que parar, el sistema queda operativo
con la funcionalidad completada hasta ese punto.

### 4.1 Principios de la planificacion

- **Cada fase = una rama** `feature/167-fase-N-*` → PR → merge a `develop`
- **Migracion + codigo van juntos** en la misma rama (atomicidad R2)
- **Tras merge de cada fase:** Flask arranca, las rutas existentes funcionan
- **Si hay que revertir:** `git revert` del merge commit devuelve `develop` al estado anterior
- **Fases 1, 2 y 3 son independientes** entre si — pueden hacerse en cualquier orden
- **Fases 4+ son secuenciales** — cada una depende de las anteriores

### 4.2 Diagrama de fases

```
                Fase 0: Decisiones + fix R6
                (commit directo en develop)
                         |
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
   Fase 1:          Fase 2:        Fase 3:
   Solicitudes      Plantillas     Nomenclatura
   (whitelist +     (rename +      (nombre_en_
    FK directa)     limpieza)      plantilla ×5)
          |              |              |
          └──────────────┼──────────────┘
                         ↓
                    Fase 4:
                    Admin plantillas
                    (cascada + form)
                         |
                         ↓
                    Fase 5:
                    Motor generacion
                    (B1-B8, UI tarea)
                         |
                         ↓
                    Fase 6:
                    Trazabilidad
                    (C3 + A1 + A3)
```

> Fases 1, 2 y 3 son **tres operaciones en distintas partes del cuerpo** —
> se pueden hacer en paralelo o en cualquier orden.
> Fases 4-6 operan en la misma zona y **requieren que cicatricen las anteriores**.

---

### 4.3 Fase 0 — Fix independiente + export

**No es rama.** Commits directos en develop.

#### Decisiones previas — TODAS RESUELTAS (sesion 4)

| ID | Decision | Resolucion (ver punto 5) |
|----|----------|--------------------------|
| R1 | Semantica `EXISTE_TIPO_SOLICITUD` | Comparacion exacta. Supervisor lista tipos aplicables en la regla (P1) |
| R5 | Mecanismo escape en selectores | Toggle "Solo aplicables al contexto". Defecto = todas las opciones (P5) |
| I1 | Ubicacion endpoints generacion | `routes/api_escritos.py` — fichero API dedicado (P6) |
| I3 | Secuencial automatico nombres | Comprobar filesystem, sufijo ` (2)` antes de `.docx` (P5/propuesta) |

#### Acciones pendientes (commit directo en develop, sin rama)

| Accion | Detalle |
|--------|---------|
| Fix R6 | `Documento.__str__`: reemplazar `self.nombre_display` por `(self.url or '').rsplit('/', 1)[-1] or f'Documento {self.id}'` |
| Export R7 | Consulta SQL: `SELECT codigo, nombre, campos_catalogo FROM tipos_escritos WHERE campos_catalogo IS NOT NULL` → guardar en `docs_prueba/temp/` como referencia |

**Criterio de avance:** Fix R6 mergeado. Export R7 guardado.

---

### 4.4 Fase 1 — Solicitudes: FK directa + whitelist ESFTT

**Rama:** `feature/167-fase-1-tipo-solicitud-directo`
**Decisiones aplicadas:** R1/P1 (comparacion exacta), R3 (backfill script), R8/P2 (seed ampliable)
**Gestiona:** R2 (atomicidad drop solicitudes_tipos)

#### Migracion (1 fichero, `flask db revision`)

| Paso | SQL | Nota |
|------|-----|------|
| 1 | CREATE TABLE `expedientes_solicitudes`, `solicitudes_fases`, `fases_tramites` | PK compuestas, sin datos aun |
| 2 | INSERT tipos combinados en `tipos_solicitudes` (~6 filas) | AAP_AAC, AAP_AAC_DUP, etc. |
| 3 | ADD `tipo_solicitud_id` INT nullable + FK en `solicitudes` | Nullable para permitir backfill |
| 4 | **Backfill:** para cada solicitud, deducir tipo desde `solicitudes_tipos` | Script Python en `op.execute()` o `op.get_bind()` |
| 5 | ALTER `tipo_solicitud_id` SET NOT NULL | Tras backfill exitoso |
| 6 | DROP TABLE `solicitudes_tipos` | Punto de no retorno para la tabla puente |
| 7 | INSERT seed en 3 tablas whitelist desde JSON de estructura | Parsear JSON → bulk insert |

> **Punto critico:** Los pasos 3-6 son la ventana de cirugia. Si el backfill (paso 4)
> falla, la migracion aborta limpiamente antes de hacer DROP.

#### Codigo (ver punto 2.3-2.5 para detalle de cada fichero)

| Accion | Ficheros |
|--------|----------|
| Crear 3 modelos whitelist | `models/expedientes_solicitudes.py`, `solicitudes_fases.py`, `fases_tramites.py` (NUEVOS) |
| Actualizar modelo Solicitud | `models/solicitudes.py` — añadir `tipo_solicitud_id` + relationship |
| Reescribir queries (4 ficheros) | `services/motor_reglas.py`, `routes/vista3.py`, `routes/wizard_expediente.py`, `routes/api_expedientes.py` |
| Actualizar template wizard | `templates/expedientes/wizard_paso3.html` — multiselect → selector unico |
| Eliminar modelo obsoleto | `models/solicitudes_tipos.py` → BORRAR |
| Actualizar barrel | `models/__init__.py` — añadir 3, eliminar SolicitudTipo |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Flask arranca | ✓ | |
| Wizard crear expediente | ✓ | Selector tipo unico (atomico o combinado) |
| Vista3 solicitudes | ✓ | FK directa en vez de JOIN a tabla puente |
| Motor de reglas | ✓ | Reescrito segun decision R1 |
| API expedientes | ✓ | |
| Admin plantillas | ✓ | Sin cambios — sigue usando `TipoEscrito` (nombre antiguo) |
| CRUD whitelist (UI) | ✗ | Tablas existen pero sin interfaz (diferido) |

#### Verificacion

- `flask run` arranca
- Crear expediente via wizard con tipo de solicitud combinado (AAP_AAC)
- Abrir expediente existente → solicitud muestra tipo correcto (backfill ok)
- Motor de reglas: verificar que evalua solicitudes correctamente
- `grep -ri "SolicitudTipo\|solicitudes_tipos" app/` → cero resultados

---

### 4.5 Fase 2 — Plantillas: rename + limpieza + nuevos campos

**Rama:** `feature/167-fase-2-rename-plantillas`
**Gestiona:** R4 (amplitud rename), R7 (campos_catalogo), R9 (downgrade Alembic)

#### Migracion (1 fichero, `flask db revision`)

| Paso | SQL | Nota |
|------|-----|------|
| 1 | ALTER TABLE `tipos_escritos` RENAME TO `plantillas` | Tabla base |
| 2 | RENAME constraints FK y UQ | `fk_tipos_escritos_*` → `fk_plantillas_*`, idem UQ |
| 3 | ADD `tipo_expediente_id` FK nullable → `tipos_expedientes.id` | NULL = cualquier tipo |
| 4 | DROP COLUMN `campos_catalogo` | Export previo en Fase 0 |
| 5 | ADD `variante` TEXT nullable | Texto libre (ej: "Favorable", "Denegatoria") |
| 6 | ADD `origen` VARCHAR(10) NOT NULL DEFAULT 'AMBOS' en `tipos_documentos` | CHECK: INTERNO/EXTERNO/AMBOS |
| 7 | UPDATE `tipos_documentos` SET `origen` para tipos existentes | Clasificar cada tipo |

#### Codigo (ver punto 2.3-2.5 para detalle)

| Accion | Ficheros |
|--------|----------|
| Renombrar fichero + clase | `models/tipos_escritos.py` → `models/plantillas.py` (`Plantilla`, `__tablename__='plantillas'`) |
| Añadir campos al modelo | `tipo_expediente_id`, `variante` en `models/plantillas.py` |
| Añadir campo a TipoDocumento | `origen` en `models/tipos_documentos.py` |
| Actualizar barrel | `models/__init__.py` — `Plantilla` en vez de `TipoEscrito` |
| Actualizar admin routes | `modules/admin_plantillas/routes.py` — imports, queries, form, tokens |
| Actualizar admin templates (×4) | `listado.html`, `form.html`, `detalle.html`, `_panel_tokens.html` |
| Actualizar generador | `services/generador_escritos.py` — import, docstrings, mensajes |

> **Punto critico:** TODOS estos cambios deben ser coherentes. Si falta uno,
> Flask no arranca (`ImportError` o `AttributeError`). Hacer todos los cambios
> en la rama, probar, y solo entonces crear PR.

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Flask arranca | ✓ | |
| Admin plantillas: listado | ✓ | Usa `Plantilla`, muestra variante y tipo expediente |
| Admin plantillas: crear/editar | ✓ | Form con variante, tipo_expediente, sin campos_catalogo |
| Admin plantillas: detalle | ✓ | Panel tokens solo Capa 1 (12 campos base) |
| Tipos documentos | ✓ | Campo `origen` visible |
| Generador escritos | ✓ | Usa `Plantilla` (stub sin cambios funcionales) |
| Selectores cascada en admin | ✗ | Aun no implementados (Fase 4) |
| Filtrado por origen en admin | ✗ | Columna existe pero form no filtra aun (Fase 4) |

#### Verificacion

- `flask run` arranca
- Admin plantillas: CRUD completo funcional (listar, crear, editar, ver)
- `grep -ri "TipoEscrito\|tipo_escrito\|tipos_escritos" app/` → cero resultados
- Verificar en BD: `\dt public.plantillas` existe, `\dt public.tipos_escritos` no

---

### 4.6 Fase 3 — Nomenclatura: `nombre_en_plantilla` en 5 tablas

**Rama:** `feature/167-fase-3-nombre-en-plantilla`
**Fase mas segura.** Solo ADD COLUMN nullable × 5.

#### Migracion (1 fichero)

ADD `nombre_en_plantilla` TEXT nullable en: `tipos_expedientes`, `tipos_solicitudes`,
`tipos_fases`, `tipos_tramites`, `tipos_tareas`. UPDATE seed con valores legibles
para los tipos existentes.

#### Codigo

Añadir `nombre_en_plantilla = db.Column(db.Text, nullable=True)` en los 5 modelos.
Sin mas cambios — la columna no se consume hasta Fase 5.

#### Flask tras merge

**Todo funciona identicamente.** 5 columnas nuevas nullable sin codigo que las lea.

#### Verificacion

- `flask run` arranca
- Consulta BD: verificar columnas y valores seed

---

### 4.7 Fase 4 — Admin plantillas: selectores en cascada + form completo

**Rama:** `feature/167-fase-4-admin-cascada`
**Requiere:** Fases 1 + 2 + 3 completadas (las tres convergen aqui)
**Decisiones aplicadas:** R5/P5 (toggle "Solo aplicables al contexto", defecto=todas)

#### Contenido

| Bloque | Detalle |
|--------|---------|
| Endpoints AJAX cascada | `GET /api/admin/plantillas/tipos-solicitud?tipo_expediente_id=X` (y analoga para fases y tramites). Sin filtro devuelve todas; con `?filtrar=1` solo whitelist |
| JS selectores cascada | E → filtra S → filtra F → filtra T. Toggle "Solo aplicables al contexto" (defecto=todas) |
| Filtrar tipos_documentos | Excluir `origen='EXTERNO'` en el selector del form |
| Actualizar panel tokens | Preparar endpoint AJAX para refresco futuro (Capa 2). Hoy solo muestra Capa 1 |
| Validacion sintaxis (A1) | `validar_plantilla(ruta)` — try `DocxTemplate(ruta)` antes de registrar |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Admin plantillas: form | ✓ | Selectores en cascada E→S→F→T con escape |
| Admin plantillas: validacion | ✓ | Error claro si plantilla .docx tiene sintaxis Jinja2 rota |
| Tipos documentos: filtro | ✓ | Solo internos/ambos en selector |
| Panel tokens | ✓ | Capa 1 fija, AJAX preparado para Capa 2 |
| Generacion desde tarea | ✗ | Aun no implementada (Fase 5) |

#### Verificacion

- Crear plantilla nueva → selectores filtran en cascada
- Toggle "Solo aplicables": al activar, se ocultan opciones fuera de whitelist
- Subir .docx con token mal escrito → error de validacion
- Subir .docx correcto → registro exitoso

---

### 4.8 Fase 5 — Motor de generacion (B1-B8)

**Rama:** `feature/167-fase-5-generacion`
**Requiere:** Fase 4 completada
**Decisiones aplicadas:** I1/P6 (`routes/api_escritos.py`), I3 (sufijo ` (N)` en filesystem)

#### Contenido

| Bloque | Necesidades cubiertas |
|--------|----------------------|
| Endpoint generacion | B1. `POST /api/escritos/generar` en `routes/api_escritos.py` (nuevo) |
| Selector plantilla filtrado | B2. Plantillas aplicables al contexto ESFTT de la tarea, con NULL-comodin |
| Preview campos | B3. Valores del expediente para tokens de la plantilla seleccionada |
| Guardado + checkboxes | B4. Nombre sistematizado (Cabo 3), ruta en FILESYSTEM_BASE, checkboxes pool/doc_producido |
| Abrir carpeta | B5. Checkbox → protocolo `bddat-explorador://` |
| Regeneracion | B6. Sobrescritura transparente si misma ruta y nombre |
| Auto-inicio tarea | B8. Si `fecha_inicio is None`: asignar `date.today()` |
| Ejecutar consultas | C1. Implementar `_ejecutar_consultas()` (stub actual) |
| Errores | C7. Try/catch Jinja2 → toast con detalle |
| Nombre sistematizado | C8. Composicion desde `nombre_en_plantilla` de cada nivel ESFTT |

#### Flask tras merge

| Componente | Estado | Nota |
|------------|:------:|------|
| Tarea REDACTAR: boton generar | ✓ | Visible en vista BC |
| Selector plantilla | ✓ | Filtrado por contexto ESFTT |
| Preview antes de generar | ✓ | Campos con valores reales |
| Generacion .docx | ✓ | Sustitucion de campos, consultas, fragmentos |
| Guardado en disco | ✓ | Nombre sistematizado, ruta dentro de FILESYSTEM_BASE |
| Registro en pool (opcional) | ✓ | Via checkbox |
| Trazabilidad: codigo embebido | ✗ | Aun no (Fase 6) |
| Validacion pre-generacion | ✗ | La validacion de registro es Fase 4. Pre-generacion es redundante (C5 eliminada) |

#### Verificacion

- Abrir tarea REDACTAR → boton "Generar escrito" visible
- Seleccionar plantilla → preview de campos con valores del expediente
- Generar → .docx creado en ruta correcta con nombre sistematizado
- Marcar checkbox pool → documento registrado en pool del expediente
- Regenerar con misma plantilla → aviso sobrescritura → binario reemplazado
- Tarea sin fecha_inicio → tras generar, fecha_inicio = hoy

---

### 4.9 Fase 6 — Trazabilidad y parseo (C3, A3)

**Rama:** `feature/167-fase-6-trazabilidad`
**Requiere:** Fase 5 completada
**Decisiones aplicadas:** R10 (probar pipeline antes), P7 (NO FK — trazabilidad en metadatos del .docx)

#### Contenido

| Bloque | Detalle |
|--------|---------|
| Custom properties | Inyectar metadatos BDDAT en el .docx generado (python-docx), incluyendo plantilla ID |
| QR clasificacion | Generar QR con codigo estructurado. Insertar en pie de pagina (o donde `{{qr_clasificacion}}`) |
| Texto pie discreto | `Template ID: NNN` en pie de pagina — trazabilidad visible que sobrevive impresion |
| Parseo automatico (A3) | Al registrar plantilla: detectar campos, consultas, fragmentos usados |

> **Prerequisito R10:** Antes de implementar custom properties, probar manualmente
> si sobreviven el pipeline .docx → portafirmas → PDF. Si no sobreviven,
> priorizar QR como via principal.

#### Flask tras merge

Feature #167 completamente funcional. Ciclo completo:
crear plantilla → generar escrito → codigo embebido → reincorporar con clasificacion.

---

### 4.10 Resumen: estado de Flask en cada punto de parada

Si se para el trabajo tras completar la fase N, este es el estado del sistema:

| Parada tras | Admin plantillas | Wizard solicitudes | Motor reglas | Generacion escritos | Trazabilidad |
|-------------|:----:|:----:|:----:|:----:|:----:|
| Fase 0 | ✓ (sin cambios) | ✓ (sin cambios) | ✓ (sin cambios) | ✗ | ✗ |
| Fase 1 | ✓ (sin cambios) | ✓ (selector unico) | ✓ (FK directa) | ✗ | ✗ |
| Fases 1+2 | ✓ (rename + campos) | ✓ | ✓ | ✗ | ✗ |
| Fases 1+2+3 | ✓ | ✓ | ✓ | ✗ | ✗ |
| Fase 4 | ✓✓ (cascada + escape) | ✓ | ✓ | ✗ | ✗ |
| Fase 5 | ✓✓ | ✓ | ✓ | ✓ | ✗ |
| Fase 6 | ✓✓ | ✓ | ✓ | ✓ | ✓ |

> **Clave:** ✓ = funcional, ✓✓ = funcional con mejoras de #167, ✗ = no implementado aun.
> En ningun punto de parada hay funcionalidad ROTA. Lo que no esta implementado
> simplemente no existe aun — el sistema funciona con lo que tiene.

### 4.11 Estimacion de complejidad por fase

| Fase | Migracion | Codigo | Complejidad | Dependencias |
|------|:---------:|:------:|:-----------:|:------------:|
| 0 | — | 1 fix trivial | Baja | Ninguna |
| 1 | 1 (7 pasos) | ~10 ficheros | **Alta** | Fase 0 (decisiones resueltas) |
| 2 | 1 (7 pasos) | ~8 ficheros | **Alta** | Fase 0 (export R7) |
| 3 | 1 (simple) | 5 ficheros | Baja | Ninguna |
| 4 | — | ~4 ficheros + JS | Media-Alta | Fases 1+2+3 |
| 5 | — | ~6 ficheros + JS + templates | **Alta** | Fase 4 |
| 6 | — | ~3 ficheros + dependencia pip | Media | Fase 5, verificacion R10 |

---
