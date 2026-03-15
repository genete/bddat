> **Indice:** [ANALISIS_167_INDICE.md](ANALISIS_167_INDICE.md)

## 2) Dependencias con otros modulos

Analisis sistematico de que componentes existentes se ven afectados por cada
decision del punto 1. Para cada componente se indica el origen (decision/necesidad)
que motiva el cambio y la naturaleza de la modificacion.

### 2.1 Matriz de impacto: Decision → Ficheros afectados

La siguiente tabla resume que decisiones del punto 1 impactan en cada fichero.
Las columnas usan codigos cortos: **R** = renombrar/restructurar, **A** = anadir campo/funcion,
**M** = modificar logica existente, **E** = eliminar campo/codigo, **N** = fichero nuevo.

| Fichero | C1D1 rename | C1D2 tipo_exp | C1D3 -campos | C1D4 origen | C3 nombres | C4 whitelist | C4 combinados | B1-B8 generacion | C1-C8 transversales |
|---------|:-----------:|:-------------:|:------------:|:-----------:|:----------:|:------------:|:-------------:|:----------------:|:------------------:|
| `models/tipos_escritos.py` | R | A | E | | A | | A | | |
| `models/tipos_documentos.py` | | | | A | | | | | |
| `models/tipos_expedientes.py` | | | | | A | | | | |
| `models/tipos_solicitudes.py` | | | | | A | | M | | |
| `models/tipos_fases.py` | | | | | A | | | | |
| `models/tipos_tramites.py` | | | | | A | | | | |
| `models/tipos_tareas.py` | | | | | A | | | | |
| `models/solicitudes.py` | | | | | | | A | | |
| `models/documentos.py` | | | | | | | | | M |
| `models/tareas.py` | | | | | | | | M | |
| `models/__init__.py` | R | | | | | N | | | |
| `models/` (NUEVOS) | | | | | | N×3 | | | |
| `modules/admin_plantillas/routes.py` | R | M | E | M | M | M | M | | |
| `modules/admin_plantillas/templates/` | R | M | E | | M | M | | | |
| `services/generador_escritos.py` | R | | | | M | | | M | M |
| `services/escritos.py` | | | | | | | | | |
| `services/motor_reglas.py` | | | | | | | M | | |
| `routes/vista3.py` | | | | | | | M | M | |
| `routes/wizard_expediente.py` | | | | | | | M | | |
| ~~`templates/vistas/vista3/`~~ | | | | | | | | | DEPRECADA |
| `config.py` | | | | | | | | | |

> **Clave:** C1D1 = Cabo1 Decision1, C3 = Cabo3, C4 = Cabo4, B1-B8 = necesidades tramitador, C1-C8 = transversales.

---

### 2.2 Base de datos — Migraciones necesarias

Todas las migraciones deben ser manuales (`flask db revision`). Nunca `flask db migrate`.

#### 2.2.1 ALTER TABLE sobre tablas existentes

| Tabla | Cambio | Origen | Detalle |
|-------|--------|--------|---------|
| `tipos_escritos` | RENAME TABLE → `plantillas` | C1D1 | Renombrar tabla, constraints, indices, FKs entrantes |
| `plantillas` (ex tipos_escritos) | ADD `tipo_expediente_id` FK nullable → `tipos_expedientes.id` | C1D2 | NULL = cualquier tipo expediente |
| `plantillas` (ex tipos_escritos) | DROP `campos_catalogo` | C1D3 | El catalogo de campos sera calculo dinamico |
| `plantillas` (ex tipos_escritos) | ADD `variante` TEXT nullable | C3 | Texto libre para distinguir plantillas del mismo contexto ESFTT |
| `tipos_documentos` | ADD `origen` VARCHAR(10) NOT NULL DEFAULT 'AMBOS' | C1D4 | CHECK (`origen` IN ('INTERNO','EXTERNO','AMBOS')). Seed: actualizar registros existentes |
| `tipos_solicitudes` | ADD ~6 filas combinadas | C4 | INSERT tipos combinados (AAP_AAC, AAP_AAC_DUP, etc.) |
| `solicitudes` | ADD `tipo_solicitud_id` FK NOT NULL → `tipos_solicitudes.id` | C4 | FK directa al tipo (atomico o combinado). NOT NULL — sin datos reales que migrar |
| `tipos_expedientes` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Texto corto para nomenclatura de ficheros |
| `tipos_solicitudes` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_fases` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_tramites` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `tipos_tareas` | ADD `nombre_en_plantilla` TEXT nullable | C3 | Idem |
| `solicitudes_tipos` | DROP TABLE | C4 | Reemplazada por `Solicitud.tipo_solicitud_id` directo. Sin datos reales que preservar |

#### 2.2.2 Tablas nuevas

| Tabla | Origen | Columnas | PK |
|-------|--------|----------|-----|
| `expedientes_solicitudes` | C4 | `tipo_expediente_id` FK, `tipo_solicitud_id` FK | PK compuesta (ambas FK) |
| `solicitudes_fases` | C4 | `tipo_solicitud_id` FK, `tipo_fase_id` FK | PK compuesta (ambas FK) |
| `fases_tramites` | C4 | `tipo_fase_id` FK, `tipo_tramite_id` FK | PK compuesta (ambas FK) |

Las tres tablas son whitelists editables por supervisor. Seed inicial desde
`Estructura_fases_tramites_tareas.json`.

#### 2.2.3 Datos maestros (seed)

| Tabla | Accion | Origen |
|-------|--------|--------|
| `tipos_solicitudes` | INSERT 6 tipos combinados | C4 |
| `tipos_documentos` | UPDATE `origen` por cada tipo existente | C1D4 |
| `expedientes_solicitudes` | INSERT seed desde JSON de estructura | C4 |
| `solicitudes_fases` | INSERT seed desde JSON de estructura | C4 |
| `fases_tramites` | INSERT seed desde JSON de estructura | C4 |
| 5 tablas tipos_ | UPDATE `nombre_en_plantilla` para cada tipo existente | C3 |

---

### 2.3 Modelos Python — Cambios por fichero

#### `app/models/tipos_escritos.py` → renombrar a `app/models/plantillas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar clase `TipoEscrito` → `Plantilla` | C1D1 | `__tablename__ = 'plantillas'` |
| Renombrar fichero → `plantillas.py` | C1D1 | Coherencia nombre-clase |
| Anadir `tipo_expediente_id` + relationship | C1D2 | FK nullable a `TipoExpediente` |
| Eliminar `campos_catalogo` | C1D3 | Columna y comment |
| Anadir `variante` | C3 | `db.Column(db.Text, nullable=True)` |
| Actualizar constraints (uq, fk names) | C1D1 | Prefijo `plantillas_` en vez de `tipos_escritos_` |

#### `app/models/tipos_documentos.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `origen` | C1D4 | `db.Column(db.String(10), nullable=False, default='AMBOS')` con CHECK |

#### `app/models/tipos_solicitudes.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `nombre_en_plantilla` | C3 | `db.Column(db.Text, nullable=True)` |
| Considerar campo `es_combinado` (bool) | C4 | Opcional: distinguir tipos atomicos de combinados para UI |

#### `app/models/tipos_expedientes.py`, `tipos_fases.py`, `tipos_tramites.py`, `tipos_tareas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `nombre_en_plantilla` | C3 | `db.Column(db.Text, nullable=True)` en cada uno |

#### `app/models/solicitudes.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Anadir `tipo_solicitud_id` FK NOT NULL | C4 | FK directa a `tipos_solicitudes.id`. Reemplaza la tabla puente `solicitudes_tipos` |
| Anadir relationship `tipo_solicitud` | C4 | `db.relationship('TipoSolicitud')` |

#### `app/models/__init__.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar import `TipoEscrito` → `Plantilla` | C1D1 | Cambiar `from app.models.tipos_escritos` → `from app.models.plantillas` |
| Anadir imports de 3 modelos whitelist | C4 | `ExpedienteSolicitud`, `SolicitudFase`, `FaseTramite` |
| Actualizar `__all__` | C1D1, C4 | Reemplazar `TipoEscrito` por `Plantilla`, anadir 3 nuevos |
| Respetar orden de capas | todos | Las 3 whitelist son maestras (sin FKs operacionales) — van al inicio |

#### Nuevos ficheros de modelo (3)

| Fichero | Clase | Origen |
|---------|-------|--------|
| `app/models/expedientes_solicitudes.py` | `ExpedienteSolicitud` | C4 |
| `app/models/solicitudes_fases.py` | `SolicitudFase` | C4 |
| `app/models/fases_tramites.py` | `FaseTramite` | C4 |

Cada uno con PK compuesta y sin columnas adicionales salvo las dos FK.

---

### 2.4 Servicios — Cambios por fichero

#### `app/services/generador_escritos.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar parametro `tipo_escrito` → `plantilla` | C1D1 | En `generar_escrito()` y helpers |
| Implementar `_ejecutar_consultas()` | C1 | Stub actual devuelve `{}`. Debe: parsear plantilla → detectar `{%tr for row in X %}` → ejecutar `ConsultaNombrada.query.filter_by(nombre=X)` → pasar resultado a contexto |
| Validacion de sintaxis pre-registro | A1 | Nueva funcion `validar_plantilla(ruta)` → intenta `DocxTemplate(ruta)` + parsear tokens |
| Inyeccion de metadatos (custom properties + QR) | C3 | Llamar a `python-docx` para escribir custom properties + generar QR con `qrcode` |
| Composicion de nombre de fichero | C3, B4 | Nueva funcion que construye nombre desde `nombre_en_plantilla` de cada nivel ESFTT |
| Guardado en FILESYSTEM_BASE | B4 | Escribir bytes a ruta dentro del arbol del expediente |
| Registro opcional en pool | B4 | Crear `Documento` con metadatos segun C4 |
| Asignacion opcional como doc producido | B4 | Asignar `tarea.documento_producido_id` |
| Auto-inicio de tarea REDACTAR | B8 | Si `tarea.fecha_inicio is None`: asignar `date.today()` |
| Gestion de errores con detalle | C7 | Try/catch Jinja2, campos inexistentes, consultas fallidas → mensaje legible |

> **Nota:** `app/services/escritos.py` (ContextoBaseExpediente) no requiere cambios
> estructurales. Sus 12 campos base permanecen estables. La unica modificacion posible
> es anadir al contexto los datos del tipo de solicitud combinado cuando este disponible.

#### `app/services/motor_reglas.py`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Reescribir `_criterio_existe_tipo_solicitud` | C4 | Actualmente usa `SolicitudTipo` (tabla puente N:M). Con la eliminacion de la tabla puente, consultar directamente `Solicitud.tipo_solicitud_id` |
| Stubs de EXISTE_DOCUMENTO_TIPO | B4, C3 | Los stubs actuales (`lambda: False`) deben implementarse cuando el pool reciba documentos generados con tipo correcto |

---

### 2.5 Rutas / Endpoints — Cambios por fichero

#### `app/modules/admin_plantillas/routes.py` — IMPACTO ALTO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Renombrar imports y referencias `TipoEscrito` → `Plantilla` | C1D1 | Todo el fichero |
| Anadir `TipoExpediente` a `_selects_context()` | C1D2 | Nuevo selector en formulario |
| Filtrar `TipoDocumento` por `origen != 'EXTERNO'` en `_selects_context()` | C1D4 | Solo mostrar tipos internos o ambos |
| Eliminar parsing/validacion de `campos_catalogo` en `_form_data_to_tipo()` | C1D3 | Eliminar textarea JSON del formulario |
| Anadir campo `variante` al formulario | C3 | Texto libre |
| Anadir campo `tipo_expediente_id` al formulario | C1D2 | Selector |
| Implementar selectores en cascada (AJAX) | A0 | Nuevos endpoints: `GET /api/admin/plantillas/solicitudes?tipo_expediente_id=X`, etc. |
| Validacion sintaxis .docx al registrar | A1 | Llamar a `validar_plantilla()` antes de `db.session.add()` |
| Parseo automatico del .docx | A3 | Tras subir, detectar campos/consultas/fragmentos usados |
| Actualizar `_build_tokens()` | C1D3, A0 | Eliminar referencia a `campos_catalogo`. Los tokens de Capa 2 se determinan por `contexto_clase`, no por datos estaticos |

#### `app/routes/vista3.py` — IMPACTO ALTO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Nuevo endpoint `POST /api/vista3/tarea/<id>/generar` | B1 | Orquesta la generacion: seleccion plantilla → preview → generar → guardar |
| Nuevo endpoint `GET /api/vista3/tarea/<id>/plantillas` | B2 | Devuelve plantillas aplicables al contexto ESFTT de la tarea, con logica NULL-comodin |
| Nuevo endpoint `GET /api/vista3/tarea/<id>/preview-campos` | B3 | Devuelve campos de la plantilla seleccionada con valores del expediente |
| Simplificar `_get_solicitudes_con_stats()` | C4 | Actualmente obtiene tipos via `SolicitudTipo` JOIN. Sustituir por acceso directo a `Solicitud.tipo_solicitud_id` |
| Simplificar `crear_solicitud()` | C4 | Aceptar `tipo_solicitud_id` unico en vez de `tipo_solicitud_id[]` |

#### `app/routes/wizard_expediente.py` — IMPACTO MEDIO

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Paso 3: cambiar selector de solicitudes | C4 | De multiselect checkboxes (tipos atomicos + tabla puente) a selector unico (tipo combinado). Solo rellena `Solicitud.tipo_solicitud_id`; `SolicitudTipo` se elimina |

#### Nuevos endpoints necesarios (API)

| Endpoint | Origen | Descripcion |
|----------|--------|-------------|
| `GET /api/admin/plantillas/tipos-solicitud?tipo_expediente_id=X` | A0, C4 | Tipos de solicitud validos para un tipo de expediente (via whitelist `expedientes_solicitudes`) |
| `GET /api/admin/plantillas/tipos-fase?tipo_solicitud_id=X` | A0, C4 | Fases validas para un tipo de solicitud (via `solicitudes_fases`) |
| `GET /api/admin/plantillas/tipos-tramite?tipo_fase_id=X` | A0, C4 | Tramites validos para una fase (via `fases_tramites`) |
| `POST /api/vista3/tarea/<id>/generar` | B1 | Genera escrito desde tarea REDACTAR |
| `GET /api/vista3/tarea/<id>/plantillas` | B2 | Plantillas aplicables al contexto de la tarea |
| CRUD consultas nombradas (4-5 endpoints) | A4 | CRUD basico de `ConsultaNombrada` para el supervisor |

---

### 2.6 Templates / Vistas — Cambios necesarios

#### `app/modules/admin_plantillas/templates/admin_plantillas/`

| Template | Cambio | Origen |
|----------|--------|--------|
| `form.html` | Anadir selector `tipo_expediente_id` | C1D2 |
| `form.html` | Anadir campo `variante` | C3 |
| `form.html` | Eliminar textarea `campos_catalogo` | C1D3 |
| `form.html` | Implementar selectores en cascada con JS | A0 |
| `form.html` | Filtrar tipos de documento (excluir EXTERNO) | C1D4 |
| `detalle.html` | Mostrar tipo de expediente y variante | C1D2, C3 |
| `listado.html` | Anadir columna tipo expediente / variante | C1D2, C3 |
| `_panel_tokens.html` | Eliminar seccion campos_catalogo | C1D3 |
| Todas | Renombrar variables `tipo`/`tipo_escrito` → `plantilla` | C1D1 |

#### ~~`app/templates/vistas/vista3/`~~ — DEPRECADA

La vista de acordeones (vista3) se va a deprecar. Los cambios de B1-B6 (generacion
desde tarea REDACTAR) y C4 (tipo solicitud directo) se implementaran en la vista
breadcrumb BC (`app/templates/vistas/vista3_bc/`) o su sucesora.

#### `app/templates/expedientes/wizard_paso3.html`

| Cambio | Origen | Detalle |
|--------|--------|---------|
| Cambiar multiselect tipos atomicos → selector tipo combinado | C4 | El selector muestra tipos atomicos Y combinados. `SolicitudTipo` desaparece; solo se usa `Solicitud.tipo_solicitud_id` |

#### Templates nuevos necesarios

| Template | Origen | Descripcion |
|----------|--------|-------------|
| Parcial de generacion en vista tarea (BC) | B1-B6 | UI de seleccion plantilla + preview + checkboxes + resultado |
| CRUD consultas nombradas (listado, form, detalle) | A4 | 3-4 templates |
| CRUD whitelist ESFTT (opcional fase 1) | C4 | Si se implementa admin de whitelists, 3 listados editables |

---

### 2.7 JavaScript afectado

| Componente | Cambio | Origen |
|------------|--------|--------|
| Admin plantillas: formulario | Selectores en cascada AJAX (E→S→F→T) | A0, C4 |
| Admin plantillas: formulario | Refrescar panel tokens segun contexto (preparado, no implementado aun) | A0 |
| Vista tramitacion BC: tarea | Logica boton "Generar escrito" → AJAX al endpoint de generacion | B1 |
| Vista tramitacion BC: tarea | Selector plantilla filtrado + preview campos | B2, B3 |
| Vista tramitacion BC: tarea | Checkboxes pool/doc_producido/abrir_carpeta + submit | B4, B5 |
| Wizard paso 3 | Cambiar de multiselect a selector unico (o selector con buscador) | C4 |

> **Consultar `docs/GUIA_COMPONENTES_INTERACTIVOS.md`** antes de implementar cualquier JS.
> Componentes existentes reutilizables: `SelectorBusqueda` (para selectores con busqueda),
> `ScrollInfinito` (no aplica aqui), `FiltrosListado` (no aplica aqui).

---

### 2.8 Dependencias externas (pip)

| Paquete | Estado | Necesidad | Origen |
|---------|--------|-----------|--------|
| `docxtpl` (python-docx-template) | Instalado | Generacion .docx | Ya presente (#189) |
| `python-docx` | Instalado | Custom properties, inspeccion | Ya presente (#189) |
| `qrcode` | **NUEVO** | QR de clasificacion en pie de pagina | C3 |
| `Pillow` | Probablemente instalado | Dependencia de `qrcode` para generar imagen | C3 |

---

### 2.9 Configuracion

| Fichero | Cambio | Origen |
|---------|--------|--------|
| `app/config.py` | Sin cambios estructurales | — |
| `FILESYSTEM_BASE` (env) | Ya existe. Usado para guardar .docx generados | B4 |
| `PLANTILLAS_BASE` (env) | Ya existe. Directorio de plantillas .docx | — |

> No se necesitan nuevas variables de configuracion.

---

### 2.10 Modulos no afectados

Los siguientes modulos/componentes **no requieren cambios** por las decisiones del punto 1:

| Componente | Motivo de no afectacion |
|------------|-------------------------|
| `app/modules/expedientes/` | Las rutas de expediente no referencian plantillas ni tipos_escritos |
| `app/modules/entidades/` | Sin relacion con generacion de escritos |
| `app/modules/proyectos/` | Sin relacion directa (Proyecto se consume via ContextoBaseExpediente, que no cambia) |
| `app/modules/usuarios/` | Sin relacion |
| `app/routes/auth.py` | Sin relacion |
| `app/routes/dashboard.py` | Sin relacion |
| `app/routes/perfil.py` | Sin relacion |
| `app/routes/api_entidades.py` | Sin relacion |
| `app/routes/api_expedientes.py` | Sin relacion |
| `app/routes/api_municipios.py` | Sin relacion |
| `app/routes/api_proyectos.py` | Sin relacion |
| `app/models/municipios.py` | Sin relacion |
| `app/models/proyectos.py` | Sin relacion |
| `app/models/entidad.py` | Sin relacion |
| `app/models/direccion_notificacion.py` | Sin relacion |
| `app/models/autorizados_titular.py` | Sin relacion |
| `app/models/historico_titular_expediente.py` | Sin relacion |
| `app/models/municipios_proyecto.py` | Sin relacion |
| `app/models/documentos_proyecto.py` | Sin relacion |
| `app/models/motor_reglas.py` (modelo) | El modelo no cambia; la logica que cambia esta en el servicio |
| `app/services/escritos.py` (ContextoBaseExpediente) | Los 12 campos base no cambian. Posible extension menor para incluir tipo solicitud combinado |

---

### 2.11 Resumen cuantitativo

| Categoria | Ficheros existentes modificados | Ficheros nuevos | Tablas ALTER | Tablas nuevas |
|-----------|:-------------------------------:|:---------------:|:------------:|:-------------:|
| Modelos | 9 | 3 | 8 | 3 |
| Servicios | 2 | 0 | — | — |
| Rutas | 3 | ~1 (API cascada) | — | — |
| Templates | ~8 | ~5 | — | — |
| JS | ~3 bloques | — | — | — |
| **Total** | **~25** | **~9** | **8** | **3** |

---

### 2.12 Grafo de dependencias entre cambios

Algunos cambios son prerequisitos de otros. Este grafo define el orden minimo:

```
[C4: Tablas whitelist + seed]
    ↓
[C4: Tipos combinados en tipos_solicitudes]
    ↓
[C4: FK tipo_solicitud_id en solicitudes]       [C1D1: Rename tipos_escritos → plantillas]
    ↓                                                ↓
[C1D2: FK tipo_expediente_id en plantillas]     [C1D3: DROP campos_catalogo]
    ↓                                                ↓
[C3: nombre_en_plantilla en 5 tablas tipos_]    [C1D4: origen en tipos_documentos]
    ↓                                                ↓
[C3: variante en plantillas]                    [Modelo TipoDocumento actualizado]
    ↓                                                ↓
 ─────────────── convergen ──────────────────────────
                    ↓
            [Admin plantillas: selectores cascada + formulario]
                    ↓
            [A1: Validacion sintaxis .docx]
                    ↓
            [A3: Parseo automatico]
                    ↓
            [C1: _ejecutar_consultas()]
                    ↓
            [B1-B6: Flujo generacion en Vista 3]
                    ↓
            [C3: Codigo embebido + QR]
                    ↓
            [B8: Auto-inicio tarea REDACTAR]
```

> **Nota:** Los bloques sin flechas entre ellos pueden ejecutarse en paralelo.
> En particular, el rename C1D1 y las tablas whitelist C4 son independientes entre si.

---
