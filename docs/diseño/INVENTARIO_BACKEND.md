# Inventario de backend — Fase 2.5

> Insumo neutro para la fase 3 del revamping de UI. Datos objetivos sobre modelos, motor, servicios, ADRs e issues abiertos. Sin propuestas de cambio.
> Fecha del corte: 2026-05-28.

---

## 1. Mapa del dominio

49 ficheros en `app/models/` con 54 clases ORM totales (algunos ficheros agrupan varias). Resumen por familia conceptual:

### 1.1 Árbol ESFTT (núcleo)

| Modelo | Tabla | Propósito | FKs principales |
|---|---|---|---|
| Expediente | `expedientes` | Raíz administrativa única por instalación | `responsable_id`→usuarios, `tipo_expediente_id`, `proyecto_id` (1:1), `titular_id`→entidades |
| Solicitud | `solicitudes` | Acto administrativo individual (AAP, AAC, DUP, AE…) | `expediente_id`, `entidad_id`, `tipo_solicitud_id`, `solicitud_afectada_id`, `documento_solicitud_id` |
| Fase | `fases` | Contenedor temporal de trámites con resultado | `solicitud_id`, `tipo_fase_id`, `resultado_fase_id`, `documento_resultado_id` |
| Tramite | `tramites` | Contenedor organizativo de tareas | `fase_id`, `tipo_tramite_id` |
| Tarea | `tareas` | Unidad de trabajo con entrada/salida documental | `tramite_id`, `tipo_tarea_id` |
| DocumentoTarea | `documentos_tarea` | Vínculo N:M tarea↔documento con `rol`=CONSUMIDO/PRODUCIDO (ADR-010) | `tarea_id`, `documento_id` |

### 1.2 Catálogos de tipos ESFTT

| Modelo | Tabla | Propósito |
|---|---|---|
| TipoExpediente | `tipos_expedientes` | Distribucion / Transporte / Renovable / Convencional |
| TipoSolicitud | `tipos_solicitudes` | AAP, AAC, DUP, AE_PROVISIONAL, AAP+AAC, AAP+AAC+DUP, CIERRE, MOD… (atómicos y combinados) |
| TipoFase | `tipos_fases` | ANALISIS_SOLICITUD, CONSULTAS, INFORMACION_PUBLICA, RESOLUCION, COMPATIBILIDAD_AMBIENTAL, etc. |
| TipoTramite | `tipos_tramites` | CONSULTA_SEPARATA, REQUERIMIENTO_SUBSANACION, PUBLICACION, etc. |
| TipoTarea | `tipos_tareas` | 4 valores: ANALIZAR, ELABORAR, NOTIFICAR, ESPERAR_PLAZO (ADRs 003, 004) |
| TipoResultadoFase | `tipos_resultados_fases` | FAVORABLE, FAVORABLE_CONDICIONADO, DESFAVORABLE, DESISTIDO… |
| TipoDocumento | `tipos_documentos` | Clasificación semántica de documentos (INFORME_ORGANISMO, RESOLUCION, DIAGNOSTICO, JUSTIFICANTE_*…) |
| TipoIA | `tipos_ia` | Instrumentos ambientales (AAI, AAU, EXENTO…) |
| TramiteTarea | `tramites_tareas` | Patrón de tareas obligatorias por tipo de trámite (seed estructural) |
| TramiteTareaDocumento | `tramites_tareas_documentos` | Tipos de documento esperados por patrón |

### 1.3 Documentos y vínculos

| Modelo | Tabla | Propósito |
|---|---|---|
| Documento | `documentos` | Pool puro de archivos del expediente. URL puede ser ruta local, http(s) o `bddat://` (ADR-006). Único FK = `expediente_id`. `tipo_doc_id`, `fecha_administrativa` (nullable), `prioridad` |
| DocumentoProyecto | `documentos_proyecto` | Vinculación documento↔proyecto (cualificador) |
| DocumentoTarea | `documentos_tarea` | Vínculo N:M con rol (ver §1.1) |
| Notificacion | `notificaciones` | "Documento vitaminado" para tarea NOTIFICAR (ADR-008): `resultado` (CORRECTA/INCORRECTA/INDIFERENTE), `numero_intento`, `fecha_intento` |
| Diagnostico | `diagnosticos` | "Documento vitaminado" para tarea ANALIZAR (ADR-005): `resultado` (favorable/condicionado/desfavorable), `defectos` (JSONB) |
| Resolucion | `resoluciones` | Documento de resolución (formaliza cierre de fase RESOLUCION) |
| Certificado | `certificados` | Certificados internos generados por el motor (CERT_PLAZO_CUMPLIDO, CERT_FIN_INSTRUCCION, CERT_FIN_IP_CONSULTAS). URL `bddat://certificados/<id>` |
| CertificadoFase | `certificados_fase` | Variante por fase |

### 1.4 Motor de reglas

| Modelo | Tabla | Propósito |
|---|---|---|
| Norma | `normas` | Norma legal de referencia (DL26_2021, LPACAP, RD337_2014…) con URL ELI |
| CatalogoVariable | `catalogo_variables` | Registro de variables disponibles (clave, etiqueta, tipo_dato, activa) |
| ReglaMotor | `reglas_motor` | Regla: `(accion, sujeto, efecto)`. accion=CREAR/BORRAR, sujeto=patrón ESFTT con `/` y comodín `ANY`, efecto=BLOQUEAR/ADVERTIR |
| CondicionRegla | `condiciones_regla` | Condición AND (variable, operador, valor) |
| ExcepcionMotor | `excepciones_motor` | Excepción anclada a una regla por FK |
| CondicionExcepcion | `condiciones_excepcion` | Condición de excepción |
| RequisitoDocumental | `requisitos_documentales` | Requisito de documento por procedimiento (#192) |
| CondicionRequisito | `condiciones_requisito` | Condición AND aplicada al requisito |
| DocumentoRequisito | `documentos_requisito` | Asignación documento↔requisito por solicitud |

### 1.5 Plazos e inhabilidad

| Modelo | Tabla | Propósito |
|---|---|---|
| CatalogoPlazo | `catalogo_plazos` | Plazo legal por camino SFTT (admin por supervisor). `camino` con comodín ANY (#785), campo_fecha JSONB, plazo_valor + plazo_unidad |
| CondicionPlazo | `condiciones_plazo` | Condiciones AND de supuesto legal (no de posición en el árbol — eso va en `camino`) |
| EfectoPlazo | `efectos_plazo` | Efecto del vencimiento: SILENCIO_ESTIMATORIO, SILENCIO_DESESTIMATORIO, CADUCIDAD_PROCEDIMIENTO… |
| DiaInhabil | `dias_inhabiles` | Calendario de festivos por ámbito |
| AmbitoInhabilidad | `ambitos_inhabilidad` | Nacional, regional, local |

### 1.6 Entidades y representación

| Modelo | Tabla | Propósito |
|---|---|---|
| Entidad | `entidades` | Personas físicas y jurídicas. Titulares, peticionarios, organismos consultados |
| AutorizadoTitular | `autorizados_titular` | Relación entidad↔entidad con autorización de representación |
| DireccionNotificacion | `direcciones_notificacion` | Direcciones de notificación con rol (TITULAR, REPRESENTANTE…) |
| HistoricoTitularExpediente | `historico_titulares_expediente` | Histórico completo de cambios de titular del expediente |
| InteresadoExpediente | `interesados_expediente` | Sujetos interesados (TITULAR, REPRESENTANTE, ALEGANTE, organismos) |
| Alegante | `alegantes` | Alegantes con su tramitación |
| OrganismoExpediente | `organismos_expediente` | Organismos consultados por expediente (estado: pendiente_inicio / en_tramitacion / cerrado_favorable…) |
| TramiteOrganismo | `tramites_organismos` | Vinculación N:1 trámite→organismo (ADR-011) |
| InformacionPublica | `informaciones_publicas` | Datos cualificadores de fase IP |
| Municipio | `municipios` | Catálogo de municipios |
| MunicipioProyecto | `municipios_proyecto` | Municipios afectados por proyecto |

### 1.7 Usuarios, permisos, bitácora

| Modelo | Tabla | Propósito |
|---|---|---|
| Usuario | `usuarios` | Usuarios del sistema (Flask-Login). siglas, email, activo, password_hash |
| Rol | `roles` | Catálogo de roles: ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO |
| usuarios_roles | `usuarios_roles` | Tabla puente N:M usuario↔rol |
| Bitacora | `bitacora` | Cuaderno de actuaciones. usuario_id, operacion, tabla, registro_id, columna, created_at, detalle (JSON) |

### 1.8 Proyecto y otros

| Modelo | Tabla | Propósito |
|---|---|---|
| Proyecto | `proyectos` | Proyecto técnico de la instalación (1:1 con expediente) |
| Plantilla | `plantillas` | Catálogo de plantillas .docx con contexto ESFTT y `contexto_clase` (CB) |
| ConsultaNombrada | `consultas_nombradas` | SQL nombrado parametrizable por `:expediente_id` para alimentar plantillas |
| ConfiguracionSistema | `configuracion_sistema` | Valores de configuración runtime |
| CatalogoRequerimiento | `catalogo_requerimientos` | Catálogo de defectos tipificados para requerimientos |
| RequerimientoTarea | `requerimientos_tarea` | Defectos seleccionados por tarea ANALIZAR (#440 pendiente UI) |
| ~~TablaMetadata~~ | ~~`tabla_metadata`~~ | **Dada de baja en #585** — permisos de lectura/escritura por tabla y rol (#85). Nunca tuvo consumidores y su premisa contradice ADR-013 (la visibilidad no se restringe por rol). El control de acceso vivo es el dict `PERMISOS` de `app/utils/permisos.py` |

---

## 2. Modelo de estado y trazabilidad

### 2.1 Estado del expediente — **se deduce, no se almacena**

ADR-002 establece que ESFTT **no tiene campos `estado` ni `fecha_*` materializados**. El estado es siempre una `@property` calculada a partir de hijos y documentos:

| Nivel | Property | Estados |
|---|---|---|
| Solicitud | `estado` | `EN_TRAMITE` \| `RESUELTA` \| `RESUELTA_FAVORABLE` \| `RESUELTA_DESFAVORABLE` \| etc. (cualificado por la fase finalizadora) |
| Fase | `estado` | `PLANIFICADA` \| `EN_CURSO` \| `PDTE_CIERRE` \| `FINALIZADA` |
| Tramite | `estado` | `PLANIFICADO` \| `EN_CURSO` \| `FINALIZADO` |
| Tarea | `estado` | `PLANIFICADA` \| `EN_CURSO` \| `EJECUTADA` |

La cascada de la deducción:
- Tarea EJECUTADA ⇔ tiene vínculo `documentos_tarea` con `rol='PRODUCIDO'`.
- Trámite FINALIZADO ⇔ todas las tareas con tipo `ANALIZAR/ELABORAR/NOTIFICAR/ESPERAR_PLAZO` están ejecutadas; NOTIFICAR debe tener resultado `CORRECTA` (ADR-008).
- Fase FINALIZADA ⇔ tiene `documento_resultado_id`. Para llegar ahí: todos los trámites FINALIZADOS + técnico formaliza con `resultado_fase_id` + documento.
- Solicitud RESUELTA ⇔ todas las fases finalizadas Y existe la fase finalizadora exigida por el motor.

Existe además un **expediente.heredado** booleano que marca expedientes legacy con datos incompletos (decoupling del motor).

### 2.2 Estado por pista del listado de seguimiento (`services/seguimiento.py`)

Proyección por **pista** (SOL, CONSULTAS, MA, IP, RES) del núcleo `services/estado_dominio.py` (#558). Cada pista devuelve un `EstadoPista(codigo, color, count, nota)`. Vocabulario y prioridad canónicos (1 = más urgente, coherente con el color):
`PENDIENTE_TRAMITAR` (🔴) > `PENDIENTE_ESTUDIO` (🔴) > `PENDIENTE_REDACTAR` (🔴) > `NOTIFICACION_AGOTADA` (🔴) > `PENDIENTE_CERRAR` (🟠) > `NOTIFICACION_FALLIDA` (🟠) > `PENDIENTE_FIRMA` (🟡) > `PENDIENTE_NOTIFICAR` (🔵) > `PENDIENTE_PLAZOS` (⚪) > `FIN` (🟢).
La familia de notificar comparte la etiqueta "NOTIFICAR" (lo que escala es el color). `PENDIENTE_SUBSANAR` es el relabel de `PENDIENTE_PLAZOS` en la pista SOL.

Insumo directo para reemplazar la hoja Calc "pendiente de *".

### 2.3 Bitácora

Tabla genérica `bitacora`: usuario_id, operacion (10 chars), tabla, registro_id, columna (opcional), created_at, detalle (JSON). No tiene seed inicial — se rellena al uso. Granularidad: cualquier servicio invoca `bitacora.registrar(...)`.

Casos de uso actuales:
- ADR-012: `verificar_acceso_expediente(accion='editar')` registra `operacion='ALTERAR', detalle={'actuacion_fuera_asignacion': True}` cuando un TRAMITADOR edita expediente ajeno.
- Otros casos no automatizados todavía.

Sin tabla específica de "diagnóstico de expediente" — el estado actual se reconstruye recorriendo el árbol cada vez.

---

## 3. Motor de reglas

Stack: motor agnóstico + assembler + variable registry.

### 3.1 Motor agnóstico (`services/motor_reglas.py`)

Recibe `(accion, sujeto, variables: dict)` y evalúa reglas en BD. No conoce dominio. Principio: todo PERMITIDO salvo lo expresamente prohibido.

- **Acciones soportadas:** `CREAR`, `BORRAR` (FINALIZAR se eliminó como verbo en ADR-007 — los invariantes lo cubren).
- **Sujeto:** patrón ESFTT compuesto separado por `/`: `Distribucion/AAP/RESOLUCION`. `ANY` en cualquier posición = comodín.
- **Efecto:** `BLOQUEAR` | `ADVERTIR`.
- **Evaluación en dos barridos:** condiciones AND de la regla → si dispara, condiciones AND de cada excepción → si alguna casa, prohibición neutralizada.
- **Función `evaluar`** devuelve `EvaluacionResult(permitido, nivel, variables_trigger, norma_compilada, url_norma, motivo, puede_escapar)`.
- **Función `auditar`** recorre TODAS las reglas sin short-circuit (insumo de `CERT_FIN_INSTRUCCION`).

### 3.2 Operadores (`services/operadores.py`)

12 operadores: `EQ`, `NEQ`, `IN`, `NOT_IN`, `IS_NULL`, `NOT_NULL`, `GT`, `GTE`, `LT`, `LTE`, `BETWEEN`, `NOT_BETWEEN`.

### 3.3 Assembler (`services/assembler.py`)

`build(expediente, objeto)` produce `(sujeto, variables)`. Acepta como `objeto`:
- instancia existente (Solicitud, Fase, Tramite, Tarea)
- dict para CREAR: `{'solicitud': s, 'tipo_fase': tf}`
- `None`

Helpers: `build_sujeto` (solo sujeto, barato), `evaluar_multi` y `auditar_multi` (para tipos combinados: AAP+AAC se evalúa una vez por tipo simple).

### 3.4 Variable Registry (`services/variables/`)

Decorador `@variable('nombre')` en módulos `dato.py`, `calculado.py`, `plazo.py`. Submódulos importados al arrancar para auto-registrar.

Variables registradas actualmente:
- **dato** (3): `sin_linea_aerea`, `max_tension_nominal_kv`, `solo_suelo_urbano_urbanizable`. Lectura directa de campos del Proyecto.
- **calculado** (15+): `fase_ip_finalizada`, `tramite_publicar_existe`, `existe_fase_finalizadora_cerrada`, `tiene_solicitud_aap_favorable`, `tipo_sujeto_solicitado`, `tipo_solicitud`, `es_solicitud_aac_pura`, `tramite_analisis_con_deficiencias`, `tramite_requerimiento_sin_respuesta`, `organismos_todos_terminados`, `organismo_supera_iteraciones`, `tipo_expediente`, `es_expediente_produccion`, `tiene_aac_resuelta_favorable`, `traslado_organismo_titular_vencido`.
- **plazo**: variables `estado_plazo` y `efecto_plazo` consumidas por reglas del motor — calculadas por `obtener_estado_plazo` y enlazadas al ciclo de vida del expediente.

### 3.5 Invariantes ESFTT (`services/invariantes_esftt.py`)

Checks BDDAT-aware que el motor agnóstico no puede evaluar (requieren queries al dominio). Se invocan ANTES de `motor_reglas.evaluar()` y bloquean acciones estructurales:

- **BORRAR**: no borrar SOLICITUD/FASE/TRAMITE si tiene hijos; no borrar TAREA con documentos.
- **FINALIZAR FASE**: bloqueada si hay tareas sin documento producido, NOTIFICAR con resultado INCORRECTA, o diagnóstico desfavorable sin consumir (#419).
- **FINALIZAR TRAMITE**: análogo.
- **FINALIZAR TAREA**: si tipo requiere documento producido/usado y falta.

### 3.6 Requisitos documentales (`services/requisitos.py`, modelo desde #192)

`evaluar_requisitos(solicitud, variables)` devuelve `{items, todos_cubiertos, error}`. Cada `RequisitoDocumental` tiene condiciones AND; sin condiciones = universal. La asignación documento↔requisito vive en `documentos_requisito` con `solicitud_id`. UI consumidora pendiente (#495).

---

## 4. Generación documental

Pipeline completo: plantilla `.docx` + 2 capas de contexto + consultas nombradas + fragmentos + sustituciones de imagen.

### 4.1 Plantillas (`models/plantillas.py`)

`Plantilla(codigo, nombre, ruta_plantilla, tipo_documento_id, tipo_expediente_id?, tipo_solicitud_id?, tipo_fase_id?, tipo_tramite_id?, variante, contexto_clase, activo)`.

Las 4 FKs ESFTT son nullable: NULL = aplica a cualquier valor de esa dimensión. `contexto_clase` referencia un Context Builder Capa 2.

### 4.2 Pipeline (`services/generador_escritos.py`)

```
generar_escrito(plantilla, expediente, db_session, tarea=None) → bytes
  1. ContextoBaseExpediente(expediente).get_contexto()           [Capa 1]
  2. Si tarea.documentos_consumidos → ctx['doc_entrada'] = primero
  3. Si plantilla.contexto_clase → Context Builder Capa 2        [Capa 2]
  4. Ejecuta TODAS las ConsultaNombrada activas con :expediente_id
  5. Inyecta función img() y carga fragmentos .docx referenciados
  6. DocxTemplate.render(ctx)
  7. Corrige párrafos anidados (body + headers/footers)
  8. Devuelve bytes (caller decide guardado)
```

Funciones auxiliares: `componer_nombre_documento(tarea, plantilla)`, `ruta_destino_documento(expediente, nombre)`, `guardar_docx(bytes, ruta)`.

### 4.3 Capa 1 — ContextoBaseExpediente (`services/escritos.py`)

Dict plano con datos básicos: `expediente_id`, `numero_at`, `titular_nombre`, `titular_nif`, `titular_dir` (subdict), `proyecto_titulo`, `proyecto_finalidad`, `proyecto_emplazamiento`, `instrumento_ambiental`, `responsable_nombre`, `municipios` (lista), `fecha_hoy`.

### 4.4 Capa 2 — Context Builders (`services/context_builders/`)

10 builders implementados:

| Builder | Propósito |
|---|---|
| `ContextoAnalisisAlegaciones` | Listado y análisis de alegaciones para escritos de respuesta |
| `ContextoAnalisisDocumental` | Análisis documental — pendiente integrar checklist requisitos (#495) |
| `ContextoNotificacionOrganismo` | Datos para notificación a organismo |
| `ContextoConsultaSeparata` | Consulta separata a organismo |
| `ContextoConsultaTrasladoTitular` | Traslado al titular del expediente |
| `ContextoConsultaTrasladoOrganismo` | Traslado al organismo |
| `ContextoSubsanacion` | Requerimiento de subsanación |
| `ContextoResolucion` | Datos para resolución (alegaciones, organismos+estado, condicionados) |
| `ContextoInformacionPublica` | Datos de fase IP |
| `ContextoRecepcionAlegacion` | Recepción de alegación |

### 4.5 Certificados internos (`services/cert_pdf.py`, `cert_fin_ip_consultas.py`, `generador_cert.py`)

Documentos `CERT_*` generados por el motor sin fichero físico (URL `bddat://certificados/<id>`). PDF on-demand vía endpoint `GET /expedientes/cert/<cert_id>/pdf`.

Tipos: `CERT_PLAZO_CUMPLIDO`, `CERT_FIN_INSTRUCCION`, `CERT_FIN_IP_CONSULTAS`.

### 4.6 Consultas nombradas

Tabla `consultas_nombradas`: SQL parametrizable por `:expediente_id` que se ejecuta en cada generación de escrito y se inyecta como variable de contexto. Las plantillas usan `{%tr for row in <nombre> %}…{%tr endfor %}` para iterar resultados.

---

## 5. Plazos e inhabilidad

### 5.1 Cálculo (`services/plazos.py`)

Dos entradas, una por nivel con plazo (#778):
`obtener_estado_plazo_tarea(tarea, ctx/variables) → EstadoPlazo(estado, efecto, fecha_limite, dias_restantes, fecha_disparo, fecha_cumplimiento, fecha_parada)` y
`obtener_estado_plazo_solicitud(sol, ctx/variables) → EstadoPlazoSolicitud(… + suspendido, suspendido_desde, dias_suspendidos, fecha_limite_sin_suspender)`.

Estados: `SIN_PLAZO` | `EN_PLAZO` | `PROXIMO_VENCER` (≤5 días hábiles) | `VENCIDO` | `CUMPLIDO`.

Efectos posibles: `NINGUNO`, `SILENCIO_ESTIMATORIO`, `SILENCIO_DESESTIMATORIO`, `CADUCIDAD_PROCEDIMIENTO`, `PERDIDA_TRAMITE`, `APERTURA_RECURSO`, `PRESCRIPCION_CONDICIONADO`, `CONFORMIDAD_PRESUNTA`, `RESPONSABILIDAD_DISCIPLINARIA`, `SIN_EFECTO_AUTOMATICO`.

`calcular_fecha_fin(fecha_acto, valor, unidad, inhabiles)` implementa art. 30 LPACAP para `DIAS_HABILES` | `DIAS_NATURALES` | `MESES` | `ANOS` (con prórroga al primer hábil siguiente).

### 5.2 Suspensiones

No hay motor aparte desde #778 (ADR-041): una suspensión es el plazo de un tercero visto desde la solicitud. `_causas_suspension(solicitud)` recorre `solicitud → fases → trámites → tareas` reteniendo las que tienen entrada con `suspende_plazo_solicitud`; cada una se mide igual que cualquier plazo y aporta el intervalo `[disparo, parada]`, con `parada = min(cumplimiento, vencimiento, hoy)`. Los intervalos se funden (`_fusionar_intervalos`) y sus días hábiles `(A, B]` empujan la fecha límite. Qué suspende es dato del catálogo, no una lista en el código.

### 5.3 Configuración (`models/catalogo_plazos.py`)

`CatalogoPlazo(tipo_elemento, camino, campo_fecha JSONB, campo_fecha_cumplimiento JSON, suspende_plazo_solicitud, plazo_valor, plazo_unidad, efecto_vencimiento_id, norma_origen, vigencia_desde, vigencia_hasta, activo, orden)`.

Selección (#785): de las entradas activas del nivel, se descartan las cuyo `camino` no casa con el del elemento (`plazos.compilar_camino` + `operadores.camino_casa`, comodín `ANY`); de las que casan, la primera cuyas `CondicionPlazo` (AND) se cumplen. Ordenadas por `orden ASC, id ASC`.

### 5.4 Calendario

`DiaInhabil(fecha, ambito_id, nombre)`. Catálogo `AmbitoInhabilidad` (nacional/regional/local). Comando CLI `inhabiles` para cargar año (`app/cli/inhabiles.py`).

---

## 6. APIs JSON

13 ficheros de routes. Los HTML los cubre la auditoría UI; aquí, los endpoints JSON.

### 6.1 `app/routes/api_*.py` (7 blueprints)

| Blueprint | Endpoints principales | Consumidor UI |
|---|---|---|
| `api_expedientes` | `/api/expedientes/` (listado paginado), filtros, búsqueda | `lista_v2_base.html` |
| `api_entidades` | `/api/entidades/` listado, `/api/entidades/candidatos_autorizacion` | `entidades/index.html`, `entidades/detalle.html` |
| `api_proyectos` | `/api/proyectos/` listado | `proyectos/index.html` |
| `api_seguimiento` | `/api/seguimiento/` agregación por solicitud con `estado_solicitud` | `seguimiento_y_huerfanos/index.html` (pestaña Seguimiento, #630 ADR-038) |
| ~~`api_bc`~~ | CRUDs para breadcrumbs: crear/editar/finalizar Fase/Tramite/Tarea con evaluación del motor en cada operación | **Retirado en #577** — sus consumidores (`tramitacion_bc_*.html` + `v3-breadcrumbs-*.js`) murieron en #519; el CRUD vivo del árbol es `api_expedientes` (`/nodo/…`) |
| `api_municipios` | Búsqueda y selector | `municipios_selector.js` |
| `api_escritos` | Generación de escritos: lista plantillas aplicables, genera .docx, guarda en pool | `generar_escrito.js` (huérfano en templates actuales) |

### 6.2 APIs en `app/modules/*/routes.py`

- `admin_plantillas`: 5 endpoints JSON (`/api/admin_plantillas/tipos-solicitud`, `/tipos-fase`, `/tipos-tramite`, `/fs`, `/tokens`).
- `expedientes` (pool documentos): `/expedientes/<id>/documentos/json`, `/explorador-fs`, `/registrar-rutas`, `/url-externa`, `/editar`, `/borrar`, `/abrir-en-carpeta`.

---

## 7. Permisos y auth

### 7.1 Modelo

- `Usuario` con N:M `Rol` vía `usuarios_roles`.
- 4 roles estándar definidos: `ADMIN`, `SUPERVISOR`, `TRAMITADOR`, `ADMINISTRATIVO`.
- Sin tabla de permisos en BD (decisión ADR-012).

### 7.2 PERMISOS dict (`utils/permisos.py`) — fuente única

```python
PERMISOS = {
    'acceder_expediente':   {ADMIN, SUPERVISOR, TRAMITADOR, ADMINISTRATIVO},
    'editar_expediente':    {ADMIN, SUPERVISOR, TRAMITADOR},
    'cambiar_responsable':  {ADMIN, SUPERVISOR},
    'ver_todos_proyectos':  {ADMIN, SUPERVISOR, ADMINISTRATIVO},
    'gestionar_usuarios':   {ADMIN, SUPERVISOR},
    'gestionar_plantillas': {ADMIN, SUPERVISOR},
}
```

**6 permisos**. Cambiar quién puede hacer qué = una línea. Añadir permiso nuevo = entrada en dict + check en endpoint.

### 7.3 Evaluación

- `tiene_permiso(nombre)` evalúa contra el **rol activo de sesión** (no contra todos los roles del usuario — clave para que el cambio de rol tenga efecto).
- `@require_permiso('nombre')` para endpoints administrativos.
- `@role_required('ADMIN', 'SUPERVISOR')` para casos donde el rol importa más que el permiso.
- `verificar_acceso_expediente(expediente, accion)`: gestiona el indicador de bombilla y, para `accion='editar'` sobre expediente ajeno por TRAMITADOR, registra en bitácora con `detalle={'actuacion_fuera_asignacion': True}`.

### 7.4 Permiso blando (ADR-012)

TRAMITADOR puede editar cualquier expediente, no solo el asignado. La traza queda en bitácora. Lógica acordada con jefatura en mayo 2026.

---

## 8. Migraciones

~85 ficheros Alembic en `migrations/versions/`. Agrupación por tema (no exhaustiva — solo bloques principales):

| Bloque | Tema |
|---|---|
| Setup inicial | `dfdeb43518d6_initial_schema_multi_schema_setup` |
| Tabla metadata (#85) | `12c75207263b`, `0f6a72b443e5` |
| Refactor entidades (#103) | `3f7071afb12d` |
| Numero AT correlativo | `606202414595_contador_gapless_numero_at` |
| Motor de reglas (paso a paso) | `5c4f7a4bf22d`, `a9cd38df8797_paso3`, `557859de1417_paso4a`, `f58e0e31f0b2_paso4b`, `e40ce8475305_paso6_5`, `d715b074b58c`, `1800b039663e`, `20e383031811`, `319_descripcion_regla`, `455_variables_motor_analisis`, `460_variables_motor_consultas`, `f0d0988bb956`, `f77b09ef7c1e`, `cae8e6d884af`, `bc4a9f1d8e02_190_variables_plazo` |
| Catálogo plazos (#341) | `c9379e09ae01_172_plazos_tablas_catalogo`, `6a9c2d5e0232_341_condiciones_plazo`, `2da48740db54_341_variables_art131`, `347_tipo_elemento_codigo`, `350_seed_catalogo_plazos`, `416_seed_plazos_tablon`, `448_seed_plazos_resolucion`, `463_seed_plazos_consultas`, `785_catalogo_plazos_camino_sftt` |
| Tipos documentos (#188) | `09855a1393f6`, `337_seed_tipos_documentos`, `377_seed_descripciones` |
| Plantillas (#167) | `b2c3d4e5f6a7_fase2_rename_plantillas`, `c3d4e5f6a7b8_fase3_nombre_en_plantilla`, `a1b2c3d4e5f6_fase1_tipo_solicitud_directo` |
| Eliminar whitelists (ADR-007) | `387_eliminar_whitelists_esft`, `e292f71a07a5_merge_heads_366_normas` |
| Sin fechas ESFTT (ADR-002) | `95c2e862e8d6`, `b7f95d61a7a9_add_documento_solicitud_id` |
| Tareas (ADRs 003, 004, 005) | `345_tramites_tareas`, `345_seed_tramites_tareas`, `346_tramites_tareas_documentos`, `370_actualizar_tipos_tareas`, `370_actualizar_tipos_tramites`, `370_seed_tramites_tareas`, `488_seed_tramites_tareas_registro_interesados` |
| Diagnósticos (ADR-005) | `392_diagnosticos` |
| Notificaciones (ADR-008) | `a4d067a1d5bf_418_tabla_notificaciones`, `402_notificacion_organismo` |
| Documentos↔Tareas N:M (ADR-010) | `420_modelo_nm_documento_tarea`, `a3f1c8e290bd_documentos_tarea` |
| Organismos (#391, ADR-011) | `391_organismos_expediente`, `449_grant_organismos_expediente`, `456_tramites_organismos`, `395_seed_organismos_consulta` |
| Certificados | `373_cert_fin_instruccion`, `425_certificados`, `470_cert_fin_ip_consultas` |
| Resolución (#403) | `a6fef197271a_403_resolucion` |
| Información pública | `404_informacion_publica`, `366_comunicacion_audiencia` |
| Catálogo requerimientos | `405_catalogo_requerimientos` |
| Interesados (#374) | `374_interesados_expediente` |
| Bitácora | `001_bitacora` |
| Compatibilidad tipos sol. (#410) | `410_compatibilidad_tipos_solicitud` |
| Requisitos documentales (#192) | `6a2e29774f16_192_requisitos_documentales` |
| Configuración | `323_configuracion_sistema` |
| Seeds varios | `348_seed_catalogo_base`, `348_seed_normas_base`, `451_seed_normas_ampliacion`, `477_fix_norma_origen_cierre`, `merge_heads_seed_catalogo_base` |
| Misceláneos | `4a972bf8399a` (alegantes), `bf66f512eaf4` (histórico titular), `0d6742443660` (fechas), `0869cda75380` (abrev), `45b0d1302dd4` (url_text), `39fccabb9426_296_senal_resultado`, `350_variable_tipo_tramite`, `388_tipo_sujeto_solicitado`, `393_alegantes`, `8deef1de808e_302_fase_finalizadora`, `90655e484fb2_341_seed_art131_informe_aapp`, `342a6f032b38_466_direccion_notificacion`, `fd2bc02d2474_revision_modelo_documento` |

---

## 9. Decisiones ADR

12 ADRs en `docs/decisiones/`. Todos aceptados/implementados (varios con ADR posterior que matiza).

| # | Título | Decisión clave | Estado |
|---|---|---|---|
| 001 | Motor de reglas agnóstico | El motor no conoce el dominio: recibe `(accion, sujeto, dict)` y evalúa. ContextAssembler ensambla aparte. | Implementado |
| 002 | ESFTT sin fechas | Ni ESFTT ni estados materializados — todo se deduce de documentos | Implementado (mig. 95c2e862e8d6) |
| 003 | ELABORAR fusiona REDACTAR+FIRMAR | Una sola tarea atómica para borrador+firma. Documento producido = el firmado | Implementado (#370) |
| 004 | Eliminación de INCORPORAR | ESPERAR_PLAZO recibe el documento externo directamente | Implementado (#370) |
| 005 | ANALIZAR siempre produce DIAGNOSTICO | Documento interno `bddat://diagnosticos/<id>` con resultado favorable/condicionado/desfavorable | Decidida — implementada en #392 |
| 006 | URI `bddat://` para documentos internos | `documentos.url` admite ruta local / http(s) / bddat://. `resolver_url()` devuelve dict ORM | Implementada (#365, enmendada #425) |
| 007 | Eliminar whitelists E-S-F-T | Eliminadas 3 tablas whitelist. Verbos INICIAR/FINALIZAR retirados del motor — invariantes los cubren | Adoptada (#387) |
| 008 | `notificaciones` como documento vitaminado | Tabla con `resultado`/`numero_intento`/`fecha_intento` para tarea NOTIFICAR | Adoptada (#418) |
| 009 | Imágenes en plantillas | Logotipos incrustados de fábrica; imágenes dinámicas con `img()` en Jinja2 | Implementada (#297) |
| 010 | N:M documento↔tarea con rol | Tabla `documentos_tarea` con `rol`=CONSUMIDO/PRODUCIDO sustituye 2 FK | Adoptada (#420) |
| 011 | `tramites_organismos` + completitud CONSULTAS | Nueva tabla N:1, criterios de cierre favorable de fase CONSULTAS | Adoptada (#456) |
| 012 | Permisos centralizados + permiso blando | `PERMISOS` dict como fuente única en código; TRAMITADOR puede tocar cualquier expediente, trazas en bitácora | Adoptada (#174) |

---

## 10. Otra documentación

### 10.1 Guías (`docs/guias/`)

| Fichero | Propósito |
|---|---|
| `REGLAS_DESARROLLO.md` | Reglas de codificación, commits, templates, migraciones; análisis de impacto previo |
| `REGLAS_BASH.md` | Anti-bloqueos del evaluador de Claude Code para shell |
| `GUIA_GENERAL.md` | Guía general del proyecto |
| `GUIA_ADMINISTRACION.md` | Tareas administrativas (BD, usuarios, plantillas) |
| `GUIA_COMPONENTES_INTERACTIVOS.md` | Cómo usar `selector_busqueda`, `entrada_fecha`, etc. |
| `GUIA_ROLES.md` | Definición funcional de roles |
| `GUIA_VISTAS_BOOTSTRAP.md` | Patrones visuales reutilizables |

### 10.2 Referencia (`docs/referencia/`) — diseños vivos

| Fichero | Propósito |
|---|---|
| `DISEÑO_CONTEXT_ASSEMBLER.md` | Arquitectura del Variable Registry, CBs y assembler |
| `DISEÑO_FECHAS_PLAZOS.md` | Cómputo de plazos, art. 30 LPACAP, suspensiones |
| `DISEÑO_GENERACION_ESCRITOS.md` | Pipeline de generación documental |
| `DISEÑO_SUBSISTEMA_DOCUMENTAL.md` | Pool, vínculos, roles, validaciones |
| `DISEÑO_ANALISIS_SOLICITUD.md` | Fase ANALISIS_SOLICITUD |
| `DISEÑO_CONSULTAS_ORGANISMOS.md` | Fase CONSULTAS y organismos |
| `ESTRUCTURA_ESF.md`, `ESTRUCTURA_FTT.md` | Catálogos estructurales (los JSON viven en `app/data/`) |
| `GUIA_CONTEXT_BUILDERS.md` | Cómo crear un nuevo CB |
| `GUIA_DIAGRAMAS_ESFTT.md` | Cómo leer/dibujar diagramas del flujo |
| `GUIA_NORMAS.md` | Catálogo de normas y su uso en motor |
| `GUIA_RECURSOS_JUNTA.md` | Recursos visuales/CDN de la JdA |
| `NORMATIVA_LEGISLACION_AT.md` | Mapa normativo legal AT |
| `NORMATIVA_PLAZOS.md`, `NORMATIVA_MAPA_PROCEDIMENTAL.md`, `NORMATIVA_SOLICITUDES.md`, `NORMATIVA_EXCEPCIONES_AT.md` | Recopilatorios normativos |
| `TIPOS_DOCUMENTOS_CATALOGO.md` | Catálogo de tipos de documento |
| `PLAN_ESTRATEGIA.md` | Estrategia del proyecto |
| `IMPLEMENTACION_341.md` + sesiones 1-6 | Implementación detallada del subsistema de plazos |
| `IMPLEMENTACION_347.md` | Refactor `tipo_elemento_codigo` |
| `normas/sedeboja_*.md`, `hallazgos_nblm/*.md`, `PROMPT_NBLM.md` | Extractos de normas BOJA y hallazgos de NotebookLM |

### 10.3 Historial (`docs/historial/`) — diseños y análisis pasados (varios pendientes de marcar obsoletos — #351)

| Fichero | Propósito |
|---|---|
| `DISEÑO_MOTOR_AGNOSTICO.md`, `DISEÑO_MOTOR_REGLAS.md` | Diseños del motor (el agnóstico es el vivo) |
| `DISEÑO_NUMERACION_AT.md` | Numeración AT correlativa |
| `ANALISIS_ESTADO_MAYO_2026.md` | Snapshot del estado del proyecto en mayo |
| `ANALISIS_LISTADO_INTELIGENTE.md` | Diseño del listado de seguimiento |
| `ANALISIS_HOMOGENEIZACION_UI.md` | Análisis de unificación UI (insumo del revamping) |
| `ANALISIS_TAREAS_INVERSO.md` | Análisis funcional inverso de tareas |
| `ANALISIS_GENERACION_DIAGRAMA_EXPEDIENTE.md` | Diagrama dinámico de expediente |
| `ANALISIS_CONSULTAS_ORGANISMOS_2026-05-24.md` | Análisis previo a ADR-011 |
| `REGLAS_ARQUITECTURA.md` | Reglas de arquitectura general |
| `REVISION_VALIDEZ_ISSUES_MAYO_2026.md` | Revisión validez de issues |
| `PROCEDIMIENTO_SETUP_PC.md` (#344 obsoleto), `PROCEDIMIENTO_MMD_DESDE_DOCUMENTACION.md`, `PROCEDIMIENTO_MMD_DESDE_IMAGEN.md` | Procedimientos operativos |

### 10.4 Otros

| Directorio | Contenido |
|---|---|
| `docs/supervisor/` | `GUIA_PLANTILLAS.md` para el supervisor |
| `docs/estilos/` | `README.md` + `guia_colores_junta_andalucia.html` |
| `docs/mockups/` | 3 ficheros HTML con iconos ESFTT/TAREAS/ESTADOS |
| `docs/normas/` | `sedeboja_34371.md` |
| `docs/diagramas_flujo/` | Diagramas del flujo (vacío o pendiente) |
| `docs/implementaciones/` | (vacío o pendiente) |

### 10.5 Presentación POC (`presentacion/` en la raíz, fuera de `docs/`)

Sistema Reveal.js con tema CSS propio de la Junta de Andalucía. **16 slides** organizadas en bloques (problema → qué es → roles → características implementadas → demo → roadmap → feedback) más 2 apéndices técnicos.

Contenidos clave para el revamping:

| Slide | Mensaje vendido | Implicación para el rediseño |
|---|---|---|
| S01 Problema | "Hojas Calc + Access + servidor — sin contexto unificado" | Confirma el dolor relatado en fase 2 |
| S02 Qué es | "Centraliza expediente, guía al tramitador, genera escritos, traza" | 4 pilares declarados — el revamping debe reforzarlos, no diluirlos |
| S04 Identidad | "Misma imagen JA — sin curva de aprendizaje" | **La identidad JA es compromiso intencional**, no inercia. El revamping debe mantenerla pero puede tensarla hacia "app profesional" |
| S08 Listado | "Estado de cada pista se calcula automáticamente. Colores dicen qué toca. Trabajo por lotes. Jefatura ve estado global sin preguntar" | Es exactamente la varita mágica nº 2 del estudio de usuario — **pero los bullets 5.1 y 6.1 ya están marcados "🚧 pendiente de implementar"** en la propia slide |
| S10 Roadmap | 3 columnas: disponible / próximamente / más adelante | Línea narrativa pública que el revamping debe respetar (orden y promesas) |
| S11 Feedback | 4 preguntas: ¿flujos útiles? ¿casuística no cubierta? ¿qué te preocupa del cambio? ¿cómo participar en pruebas? | Cuestionario explícito que el usuario lanzó a la audiencia — el estudio de usuario fase 2 contesta varias |

Assets (capturas reales del POC actual, útiles para el "antes" del revamping):
- `DetalleExpediente.png`, `GeneracionEscrito.png`, `GestorDocumentos.png`, `ListadoSeguimiento.png`
- `Diagrama_ESFTT.svg`, `Estructura_en_capas.svg`
- Logotipos JdA en CMYK (horizontal, vertical, positivo, negativo)

Otros: `diagrama.html` (visualización interactiva ESFTT, distinta de `app/templates/demo/diagrama.html`), `js/popups.js`, `PLAN_BADGES_POPUP.md`.

**Cruces relevantes con la fase 3:**
- S08 declara públicamente que la "vista jefatura" y la "vista administrativo propia" están pendientes — coherente con que las dos primeras varitas mágicas del estudio de usuario sigan sin soporte backend.
- S10 columna 2 menciona "Diagrama visual interactivo del árbol", "Auditoría de actividad por técnico" y "Vista del administrativo" como próximas — el revamping puede aterrizar esas promesas o redirigirlas si la fase 3 lo justifica.
- S04 cierra la puerta a un cambio visual radical: el compromiso "ya conocéis esta interfaz" obliga a evolución dentro del lenguaje JdA, no salto a otro sistema visual.

---

## 10.6 Otras carpetas del repositorio

### 10.6.1 `tests/` — 51 ficheros

`conftest.py` define 3 fixtures: `app` (session), `app_ctx` (function, con rollback nested automático) y `client`. 50 tests numerados por issue/feature:

| Bloque | Cobertura |
|---|---|
| Plazos | `test_172_plazos_computo`, `test_173_suspensiones`, `test_190_plazos_contrato`, `test_341_evaluador_plazo`, `test_341_modelo_condicion_plazo`, `test_341_operadores`, `test_341_e2e_art131`, `test_341_variables_art131`, `test_328_motor_estado_plazo_integracion`, `test_350_seguimiento_esperar_plazo`, `test_362_cert_plazo_cumplido`, `test_448_seed_plazos_resolucion`, `test_463_seed_plazos_consultas`, `test_475_traslado_titular_vencido` |
| Motor | `test_323_modo_global_motor`, `test_324_escape_motor`, `test_373_auditar`, `test_388_tipo_sujeto_solicitado`, `test_455_variables_motor_analisis`, `test_460_variables_motor_consultas` |
| Documentos / vínculos | `test_346_mapa_documentos`, `test_365_bddat_uri`, `test_420_documentos_tarea`, `test_392_diagnostico` |
| Trámites / tareas / estructura | `test_345_tramites_tareas`, `test_419_invariante_cierre_fase`, `test_405_requerimientos_tarea` |
| Organismos | `test_247_organismos_crud` *(roto, #487)*, `test_391_organismo_expediente`, `test_395_organismos_consulta`, `test_456_tramites_organismos`, `test_457_cbs_traslado`, `test_458_estado_organismo`, `test_461_entidades_consultables`, `test_462_enviar_consultas`, `test_471_crear_traslado` |
| Resolución / IP / alegaciones | `test_403_resolucion`, `test_404_informacion_publica`, `test_393_alegante`, `test_394_analisis_alegaciones`, `test_406_subsanacion`, `test_402_notificacion_organismo`, `test_470_cert_fin_ip_consultas` |
| Requisitos documentales | `test_192_requisitos_documentales` (#192 PR #496) |
| Certificados / fase | `test_373_cert_fase` |
| Bitácora | `test_001_bitacora` |
| Entidades / direcciones | `test_300_direccion_titular` |
| Misceláneos | `test_296_senal_resultado`, `test_347_defensividad_backend`, `test_348_instalacion_limpia` |

Cobertura amplia del backend de motor, plazos, ESFTT, documentos y CBs. La UI prácticamente sin tests automatizados.

### 10.6.2 `scripts/` — 22 ficheros

> **Aviso:** algunos scripts pueden estar desactualizados respecto al estado actual del modelo (seeds antiguos, rutas obsoletas, dependencias retiradas). No se ha auditado uno por uno — verificar antes de ejecutar cualquiera. Auditoría individual queda fuera del alcance de esta fase.

| Familia | Ficheros | Propósito |
|---|---|---|
| Seeds | `seed_demo.py`, `seed_listado.py`, `seed_motor_variables.py`, `verificar_seed.py` | Datos de prueba (incluye los 11 escenarios T01-T11 del listado inteligente) |
| SQL bootstrap | `crear_usuario_admin.sql`, `datos_roles.sql`, `data/municipios.sql` | Carga inicial fuera de Alembic |
| Normativa BOJA | `sedeboja_buscar.py`, `sedeboja_extract.py` | Scraping de BOJA sin navegador (2 peticiones HTTP). Genera `docs/referencia/normas/sedeboja_*.md` |
| Normativa BOE / cruce | `legalize_xref.py`, `legalize_compile.py`, `compile_hallazgos.py` | Integración con repo externo `legalize-es`; compilación para NotebookLM |
| Contexto IA | `preparar_contexto.py`, `preparar_contexto_nblm.py` | Volcado del proyecto a fichero único para Gemini/NotebookLM |
| Operativa | `flask_console.py` (GUI tkinter para servidor dev), `gen_issues.py` | |
| Cliente Windows | `cliente/install.bat`, `cliente/install.ps1`, `cliente/bddat-explorador-handler.ps1`, `cliente/bddat-explorador-launcher.vbs` | Instalador del handler URL `bddat://` para abrir documentos desde navegador remoto (referenciado en issue #195) |
| Build | `build_react.sh` | Compilación del bundle React (`react-diagramas/` → `app/static/js/react/diagrama-esftt.iife.js`) |

### 10.6.3 `react-diagramas/` — POC React aislado

Proyecto Vite/Rollup independiente del backend Flask. **3 ficheros fuente** en `src/`:

| Fichero | Rol |
|---|---|
| `DiagramaEsftt.jsx` | Componente principal. Usa `@xyflow/react` (ReactFlow) con `Background`, `Controls`, `MiniMap`. Layout fijo en 3 columnas (Solicitud/Fase/Trámite) con cálculo de Y centrado para evitar solapamientos. Hace toasts Bootstrap reusando `.toast-container` del layout Flask al hacer clic en nodos |
| `main.jsx` | Entry standalone (modo desarrollo) |
| `main.lib.jsx` | Bundle IIFE: expone `window.DiagramaEsftt.mount(element)` que el template Flask invoca |

Dependencias principales (de `package.json`): React 18, `@xyflow/react`, `d3-dispatch`, scheduler. Compilador: esbuild/Rollup.

**Estado**: POC con datos mockeados (`mockData.js`). El issue **#320** ("UI/BE Integrar diagrama ReactFlow en vista de tramitación — datos reales y comportamiento completo") es el que cierra el gap entre POC y producción. Solo aparece en `demo/diagrama.html`.

**Implicación para el revamping**: la decisión de subir React de "POC en una vista" a "componente productivo en tramitación" debe tomarse en fase 4 — define si el stack JS de BDDAT pasa a ser híbrido (Jinja + React por componente) o si el revamping consolida en uno solo.

---

## 11. Issues abiertos

67 issues abiertos agrupados por milestone (datos vía `gh issue list`):

### 11.1 M2 — Necesarios (workaround temporal, no escala) — 12 issues

| # | Título | Tipo |
|---|---|---|
| 436 | Despensa de condicionados para resoluciones | backend |
| 435 | Despensa de fundamentos de derecho para resoluciones | backend |
| 431 | Wizard registro propietarios fincas afectadas (DUP) | diseño |
| 430 | Proyección automática organismos→interesados al emitir CERT_FIN_INSTRUCCION | diseño |
| 428 | Wizard nuevo expediente: exigir doc de solicitud | diseño |
| 396 | UI gestión organismos_expediente | frontend |
| 354, 351 | Docs obsoletos en historial | docs |
| 332 | CI: tests en GitHub Actions | infra |
| 320 | Integrar diagrama ReactFlow en vista tramitación | UI/BE |
| 281 | Migrar vistas Plantillas y Usuarios a arquitectura listado V2 | UI/BE |
| 279 | Campo `tecnologia` en Proyecto + filtro seguimiento | BD/UI |
| 256 | Vista de auditoría de expedientes — agregados | UI |
| 213 | Auditoría datos asociados en detalles | UI |
| 182 | Códigos clasificación embebidos en PDFs firmados | docs |
| 181 | Inspección automática documentos — preclasificación | docs |

### 11.2 M3 — Motor de reglas y plazos — ~26 issues

| # | Título | Tipo |
|---|---|---|
| 495 | Integrar checklist requisitos en ContextoAnalisisDocumental | servicio/template |
| 489 | norma_origen catalogo_plazos desactualizada RD 88/2026 | bug seed |
| 487 | Tests rotos test_247 y test_341 | test |
| 479 | Selector modo global del motor en panel supervisor | UI |
| 442 | Formulario diagnóstico ANALIZAR (tabla diagnosticos) | UI |
| 441 | Seed inicial catalogo_requerimientos | BD |
| 440 | Selector de requerimientos en tarea ANALIZAR | UI/BE |
| 432 | Fase RECONOCIMIENTO_INTERESADO: cadena ESFTT | diseño |
| 429 | Cambio titularidad: guard + cadena ESFTT + interesados | diseño |
| 409 | Regla tasas: art. 45.1 Ley 10/2021 | motor |
| 408 | Diseño checklist documental (requisito_documental + checklist_asociacion) | diseño |
| 407 | Campo `siglas_escritos` en Usuario | modelo |
| 367 | Asociar documento a tarea al subir al pool | UX |
| 322 | Mensajes motor siempre via toast | UX |
| 306 | Helper cálculo tasa y extracción presupuesto | feature backend |
| 305 | Script detección tipo expediente por análisis proyecto | feature backend |
| 304 | Script detección tipo solicitud por análisis PDF | feature backend |
| 294 | Pivot normativa→motor: modo suave incremental | estrategia |
| 171 | CRUD tablas maestras (TipoFase/Tramite/Tarea) | admin |
| 170 | CRUD reglas motor para Supervisor | admin |
| 106 | Listado códigos DIR3 | (sin label) |

### 11.3 M4 — Pre-producción — ~17 issues

| # | Título | Tipo |
|---|---|---|
| 464 | Ampliar seed_demo con organismos_expediente reales | seed |
| 444 | Crear plantillas .docx definitivas y registrar en BD | servicio |
| 379 | Tipos documentos seleccionables al crear documento | UI |
| 344 | PROCEDIMIENTO_SETUP_PC.md desactualizado | docs |
| 330 | Estrategia de despliegue: WSL→Docker→Prod | infra/post-MVP |
| 317 | Testing con GitHub Actions | feature/infra |
| 295 | Cambios titularidad masivos (agrupaciones solares) | negocio |
| 243 | Metadatos estructurados en documentos | enhancement |
| 227 | Bug: SUPERVISOR puede desactivar ADMIN | bug |
| 193 | Detector URLs huérfanas en pool | docs |
| 178 | Política backup BD | infra |
| 177 | HTTPS y certificado digital en producción | infra |
| 176 | Adecuación al ENS | seguridad |
| 175 | Wizard importación expedientes legacy | datos |
| 151 | ⚠️ Infraestructura soporte producción | producción |
| 120 | Base numero_at antes producción (legacy/nuevos) | infra |
| 105 | Migración Access→PostgreSQL schema legacy | BD/legacy |
| 45 | ⚠️ Cambiar SECRET_KEY antes producción | crítico/seguridad |

### 11.4 M5 — Post-producción — ~12 issues

| # | Título | Tipo |
|---|---|---|
| 450 | Procedimiento CIERRE — fase CONSULTA_OPERADOR_SISTEMA | enhancement |
| 342 | Ideas proyectos y entidades | enhancement |
| 273 | Footer componente estadísticas globales | UI |
| 272 | Validación completa NIF/NIE algoritmo oficial | modelo |
| 249 | Diagramas ESFTT por capas (Mermaid) | enhancement |
| 246 | Incrustar documento entrada como subdoc en plantillas | enhancement |
| 240 | Centralizar tooltips con MutationObserver | UI |
| 228 | Sistema de ayuda/manual de usuario | docs |
| 195 | URI personalizado bddat:// para abrir desde navegador remoto | pool |
| 76 | Exportación listado expedientes (Excel/CSV) | enhancement/future/post-MVP |
| 75 | Búsqueda global expedientes (titular, AT, solicitante) | enhancement/future/post-MVP |
| 74 | Semáforos y alertas vencimientos en dashboard | enhancement/future/post-MVP UI |
| 28 | Sistema notificaciones internas + solicitudes cambio rol | feature |
| 27 | Visualización cartográfica PostGIS + Leaflet | enhancement |
| 4 | Permitir a usuarios no registrados solicitar acceso | enhancement |

### 11.5 Lectura rápida para el revamping

Issues UI/UX vivos que tocan al revamping directamente:
- **Búsqueda global** (#75) está en post-MVP — re-evaluar prioridad con lo que dijo el usuario en fase 2 (búsqueda por número de expediente es operación primaria).
- **Semáforos/alertas en dashboard** (#74) también post-MVP — pero el estudio de usuario lo apunta como crítico ("memoria externa").
- **Exportación listado** (#76) post-MVP — el caso de uso "compilar expediente para recurso" (varita mágica nº 3) **no tiene issue** específico; #76 solo cubre exportar listado, no compilar dossier.
- **Mensajes motor via toast** (#322) en M3 — coherente con cualquier rediseño.
- **Auditoría datos asociados** (#213, #256) en M2 — encaja con "estado del expediente de un vistazo".
- **CRUD reglas motor + tablas maestras** (#170, #171) en M3 — admin para supervisor, área específica.
- **Migrar Plantillas/Usuarios a V2** (#281) en M2 — pendiente unificación.

---

## 12. Cruce con las aspiraciones del usuario (varitas mágicas)

### A) Estadísticas automáticas para supervisor / servicios centrales

**Soporte actual: parcial-bajo.**

- ✅ `Bitacora` permite registrar actuaciones, pero **no se rellena salvo en ADR-012**.
- ✅ `seguimiento.py` calcula estado por solicitud (insumo agregable).
- ❌ **No hay endpoint ni servicio de agregaciones** (totales por tramitador, estados por pista, plazos vencidos, tiempos medios…). No hay "dashboard de jefatura".
- ❌ Sin tabla `diagnosticos`/snapshots periódicos que permita histórico.

Para implementar las varitas: añadir endpoints/servicios de agregación sobre seguimiento + completar puntos de escritura en bitácora + decidir si se persisten snapshots o se calculan on-demand.

### B) Estado del expediente accesible de un vistazo

**Soporte actual: parcial-medio.**

- ✅ Properties `estado` en cada nivel ESFTT deducen el estado al consultar.
- ✅ `seguimiento.estado_solicitud(id)` devuelve estado por pista listo para mostrar.
- ✅ `plazos.obtener_estado_plazo()` ya existe con semáforo de 5 días.
- ❌ **No hay vista de "expediente al volver" con resumen ejecutivo**: próximo hito, plazos vivos, última actuación, alertas. La UI actual (auditoría UI fase 1) tiene 5 vistas BC anidadas, pero sin cabecera de estado consolidada.
- ❌ Sin caché — recorrer el árbol cada vez para mostrar la cabecera podría ser caro a 15k expedientes.

Para implementar: nueva vista de "cabecera de expediente" con datos pre-calculados de seguimiento + plazos + última bitácora.

### C) Compilación de expediente para recurso de alzada / contencioso

**Soporte actual: muy bajo.**

- ✅ `Documento` ya tiene `prioridad` (campo previsto para señalar relevancia).
- ✅ El pool de documentos por expediente está completo.
- ✅ El pipeline de generación documental existe y maneja contextos complejos (Capa 2 CBs).
- ❌ **No hay servicio de "empaquetar expediente"** (índice + concatenación PDF + bitácora exportada + metadatos).
- ❌ No hay tipo de documento `EXPEDIENTE_COMPILADO` ni plantilla específica.
- ❌ Sin issue tracked (varita no descubierta hasta fase 2).

Para implementar: nuevo servicio + decisión sobre formato (PDF único con índice / ZIP / dossier docx) + caso de uso documentado.

---

## 13. Lagunas y deuda

### 13.1 TODOs/FIXME estructurales detectados al leer

- `motor_reglas.py` línea 30: `# TODO paso 5: variables = build(expediente_id)` (docstring ejemplo, no estructural).
- `plazos.py`: comentario "Stub hasta #173" en `_aplicar_suspensiones` — pero parece ya implementado (suma días hábiles).
- `services/escritos.py` ContextoBaseExpediente: contexto base con campos básicos solo. CBs Capa 2 cubren el resto.
- `expedientes.py` signal `after_insert`: `'fuente_doc_id': None  # transitorio — rellenar tras rediseño wizard`.

### 13.2 Servicios/modelos en estado parcial

- `CatalogoPlazo.tipo_elemento_id` marcado como DEPRECATED (sustituido por `tipo_elemento_codigo`); pendiente eliminar (#347 ya implementado el sustituto pero queda limpieza).
- `RequerimientoTarea` (modelo) — UI consumidora pendiente (#440, #442).
- `RequisitoDocumental` recién implementado (#192, PR #496) — integración con `ContextoAnalisisDocumental` pendiente (#495).
- `bitacora` solo se escribe en ADR-012 — el resto de puntos de escritura están sin instrumentar.

### 13.3 Seeds incompletas o conocidas como tales

- `catalogo_requerimientos` sin seed (#441).
- `organismos_expediente` `seed_demo` muy básico (#464).
- `catalogo_plazos.norma_origen` desactualizada tras RD 88/2026 (#489).
- Procedimiento CIERRE incompleto (#450 — post-MVP).

### 13.4 Tests rotos conocidos (#487)

- `test_247` — falta app context.
- `test_341` — URL de stub no válida en e2e art. 131.

---

## 14. Anomalías

- **`generar_escrito.js`** no está referenciado en ningún template actual aunque `api_escritos` existe — punto suelto entre backend y UI.
- **`v2-scroll-to-top.js` y `v2-tabla-scroll-to-top.js`** son redundantes (también detectado en auditoría UI).
- **`base_acordeon.html` y `_header.html`** huérfanos.
- **`proyectos.*` es alias de UI sobre `expedientes.*`** — no es anomalía del backend, sino decisión semántica pendiente (ver auditoría UI §4.2).
- **Algunos docs en `docs/historial/`** marcan diseños superados pero no están etiquetados como obsoletos (#351, #354).
- **`HistoricoTitularExpediente`** se rellena vía signal SQLAlchemy `after_insert` de `Expediente` — funciona pero usa `connection.execute` Core en lugar de session (correcto por diseño, pero atípico en este código).
- **`CatalogoPlazo` tiene dos campos `tipo_elemento_id` (deprecated) y `tipo_elemento_codigo` (vigente)** — convivencia transitoria.

---

## 15. Resumen de impacto para la fase 3 del revamping

Lecturas relevantes a llevar al cruce con la auditoría UI + estudio de usuario:

1. **El backend está mejor preparado para "memoria externa" de lo que la UI explota.** Properties de estado, `seguimiento.py`, `plazos.py` ya producen los datos para una cabecera de expediente útil. La UI actual no lo expone consolidado.
2. **El motor de reglas es un canal listo para alertas explicables al usuario** (`norma_compilada`, `url_norma`, `motivo`). Las "advertencias del sistema" pueden ser propagadas a UI con base normativa visible — coherente con el principio "no esconder restricciones" (ADR-007).
3. **Las dos "varitas mágicas" críticas no tienen servicio backend**: estadísticas agregadas (A) y compilación de expediente (C). Cualquiera de las dos implica nuevo desarrollo backend además de UI — no es solo rediseño.
4. **Permisos están centralizados en 6 entradas** (ADR-012). Cambiar UX de permisos = una línea en `PERMISOS`. Pero la UI no expone hoy de forma consistente "qué puedes y qué no" — todo se descubre al chocar.
5. **Bitácora subutilizada.** Si la "memoria externa" debe ser fiable, conviene instrumentar más puntos de escritura — la tabla y el servicio ya están.
6. **El `tipo_elemento_codigo` del catálogo de plazos**, la migración legacy y el manejo de `heredado` son zonas donde el backend va por delante de la UI o donde la UI tendrá que tratar estados especiales.
7. **Issues UI clave (#170, #171, #322, #281, #213, #256, #74, #75, #76, #320, #322, #396, #440, #442, #479, #495)** son candidatos directos a "rescatar o repensar durante la auditoría" — varios cubren cosas que el revamping ya iba a tocar.
8. **El árbol BC de 5 niveles está bien soportado** por el modelo, pero la API `api_bc` y los JS `v3-breadcrumbs-*` son la capa más pesada de la UI actual. Es el punto donde rediseño y backend tendrán que conversar más. *(Resuelto por la vía del rediseño: ambas capas se retiraron —#519 la UI, #577 la API— y el árbol vive hoy en `api_expedientes` + isla React.)*
