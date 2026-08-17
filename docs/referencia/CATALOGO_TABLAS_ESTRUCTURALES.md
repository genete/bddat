# Catálogo de tablas estructurales — clasificación y gestión

> Auditoría de las tablas estructurales (no operacionales) de BDDAT: qué son, de qué
> dependen, si tienen CRUD administrable hoy, y qué acoplamiento real tienen con el
> código. Sesión 2026-07-04/05. Fuentes: `app/models/`, `app/services/`,
> `app/checks/catalogo_requerido.py`.

---

## Criterio

- **Operacional** (fuera de este catálogo): instancia creada durante la tramitación de
  un expediente concreto — `expedientes`, `solicitudes`, `fases`, `tareas`,
  `documentos`, `certificados`, `notificaciones`, etc.
- **Fundacional**: tabla estructural sin ninguna FK (raíz de catálogo).
- **Derivada**: tabla estructural cuya única FK apunta a otra tabla estructural
  (nunca a una operacional).

Ninguna tabla estructural tiene FK hacia una tabla operacional — el catálogo está
limpio arquitectónicamente en ese sentido.

---

## Tablas fundacionales (sin FK)

| Tabla | Descripción | ¿CRUD hoy? |
|---|---|---|
| `tipos_documentos` | Clasificación semántica de documentos | ❌ No — solo seed/migración |
| `tipos_expedientes` | Clasificación normativa de expedientes | ❌ No |
| `tipos_fases` | Catálogo de fases procedimentales | ❌ No |
| `tipos_solicitudes` | Catálogo de actos administrativos solicitables | ❌ No |
| `tipos_tareas` | Catálogo de tareas atómicas | ❌ No |
| `tipos_tramites` | Catálogo de trámites | ❌ No |
| `tipos_resultados_fases` | Resultados posibles de una fase | ❌ No |
| `tipos_ia` | Instrumentos ambientales (AAI/AAU/AAUS/CA/NO_SUJETO) | ❌ No |
| `municipios` | Catálogo geográfico (INE) | ❌ No — solo lectura (`api_municipios.py`) |
| `ambitos_inhabilidad` | Ámbitos territoriales del calendario de festivos | ❌ No — se autocrea desde `flask inhabiles importar` (CLI) |
| `efectos_plazo` | Efectos del vencimiento de un plazo | ❌ No — su propio docstring dice que debería administrarlo el Supervisor; sin acoplamiento a código, CRUD-safe si se construye |
| `catalogo_requerimientos` | Defectos-tipo reutilizables en tarea ANALIZAR | ❌ No — issue #441 (seed) pendiente |
| `configuracion_sistema` | Config clave/valor genérica (#323) | ❌ No — acceso vía `ConfiguracionSistema.get(clave, default)`, tolera ausencia por diseño |
| `consultas_nombradas` | SQL predefinido para plantillas .docx | ❌ No |
| `normas` | Catálogo de normas legales de referencia | ❌ No |
| `roles` | RBAC: ADMIN/SUPERVISOR/TRAMITADOR/ADMINISTRATIVO | ❌ No — por diseño, ancladas en el dict `PERMISOS` (`app/utils/permisos.py`) |
| ~~`tabla_metadata`~~ | Permisos por tabla (issue #85) | — **Eliminada en #585** (modelo, tabla y migración de baja) |

## Tablas derivadas (FK solo a otras estructurales)

| Tabla | Depende de | ¿CRUD hoy? |
|---|---|---|
| `dias_inhabiles` | `ambitos_inhabilidad` | ❌ No — solo CLI |
| `catalogo_plazos` | `efectos_plazo` | ✅ Sí — `catalogo_plazos` (#632); identificación por camino SFTT desde #785 |
| `condiciones_plazo` | `catalogo_plazos`, `catalogo_variables` | ✅ Sí — anidado en el inspector de `catalogo_plazos` (#632) |
| `catalogo_variables` | `normas` | ❌ No — acoplada al Variable Registry (`app/services/variables/`), ver #587 |
| `reglas_motor` | `normas` | ❌ No |
| `condiciones_regla` | `reglas_motor`, `catalogo_variables` | ❌ No |
| `excepciones_motor` | `reglas_motor`, `normas` | ❌ No |
| `condiciones_excepcion` | `excepciones_motor`, `catalogo_variables` | ❌ No |
| `requisitos_documentales` | `tipos_documentos`, `normas` | ✅ Sí — `admin_requisitos` (#583) |
| `condiciones_requisito` | `requisitos_documentales`, `catalogo_variables` | ✅ Sí — mismo módulo |
| `plantillas` | `tipos_documentos/expedientes/solicitudes/fases/tramites` | ✅ Sí — `admin_plantillas` |
| `tramites_tareas` | `tipos_tramites`, `tipos_tareas` | ✅ Sí — `tablas_maestras` (#171 fase 2), editor de pasos anidado; seed inicial 1:1 desde `ESTRUCTURA_FTT.json` (migración 345) |
| `fases_tramites` | `tipos_fases`, `tipos_tramites` | ❌ No — pendiente, ver ADR-037; seed 1:1 desde `ESTRUCTURA_FTT.json` (migración 725) |
| `tramites_tareas_documentos` | `tipos_tramites`, `tipos_documentos` | ❌ No — mismo caso |

## Casos límite

| Tabla | Nota | ¿CRUD hoy? |
|---|---|---|
| `entidades` | Solo FK a `municipios` (estructural), pero es maestro de datos poblado operativamente (titulares, interesados, autorizados), no catálogo curado por el Supervisor | ✅ Sí — módulo `entidades` |
| `usuarios` | FK N:M a `roles` | ✅ Sí — módulo `usuarios` |

---

## Arquitectura en 3 capas — `tipos_fases`/`tramites`/`tareas` y motor de reglas

Lo que a primera vista parece una sola tabla de catálogo en realidad separa tres capas
independientes:

1. **Vocabulario** (la fila en la tabla) — genérico, sin lista blanca en código.
   `app/services/tipos_creables.py` itera `TipoFase.query.order_by(...).all()`
   completo para poblar las opciones del árbol; `mutaciones_arbol.crear_fase()` acepta
   cualquier `tipo_fase`. Una fila nueva es visible y creable sin tocar código.
2. **Reglas** (`reglas_motor` + `condiciones_regla` + `excepciones_motor`) — ya 100%
   dato, evaluadas por `_evaluar()`/`build_sujeto()` en cada mutación (`crear_fase`,
   `crear_tramite`...). Es la capa que las UIs pendientes #170/#171 expondrían al
   Supervisor sin programador.
3. **Casos especiales** (Python hardcodeado: `_FASES_QUE_REQUIEREN_CERT_IP_CONSULTAS`,
   ramas por `codigo ==` en `calculado.py`/`estado_dominio.py`) — esto sí requiere
   programador siempre, porque es comportamiento nuevo, no solo dato nuevo.

`docs/referencia/ESTRUCTURA_ESF.json` (qué fases corresponden a qué tipo_solicitud,
con sus condiciones legales) hoy no lo lee ningún servicio — es documentación para
humanos. Su propia cabecera dice que esas restricciones deben migrar a `reglas_motor`
(ADR-007): confirma que la capa 2 es el destino de diseño correcto, no una tabla nueva.

**Cómo aplicar:** ante "¿puede el Supervisor crear un tipo_X nuevo sin programador?",
la respuesta depende de en qué capa cae lo pedido.

---

## Acoplamiento código → catálogo: `app/checks/catalogo_requerido.py` (#347)

`REGISTROS_REQUERIDOS` es el manifiesto de qué códigos concretos de las tablas
`tipos_*` y `roles` están anclados en la capa 3 (Python hardcodeado). Se actualiza
**solo** cuando código nuevo empieza a asumir un código concreto — nunca cuando se
añade una fila nueva a un catálogo sin que el código dependa de ella.

`validar_catalogo()` se llama desde `create_app()` tras `db.init_app()`; nunca lanza
excepción, solo loguea si falta un registro. Cubierto por
`tests/test_347_defensividad_backend.py`.

### Qué no encaja en este mecanismo, por naturaleza

**A) Sin tabla de catálogo detrás** — el enum vive solo en Python (o reforzado por
`CheckConstraint` de columna), sin modelo que el checker pueda consultar:

- `_TIPOS_TITULAR_VALIDOS` (`api_seguimiento.py`)
- Operadores de condición (`EQ/NEQ/IN/...`) en `condiciones_regla`/`condiciones_plazo`/`condiciones_excepcion`/`condiciones_requisito`
- Vocabulario de `estado_dominio.py` (`PENDIENTE_TRAMITAR`, `PENDIENTE_FIRMA`, `FIN`...) — dicts `COLOR`/`PRIORIDAD`, sin tabla en absoluto
- `PISTAS`/`PISTAS_OBLIGATORIAS` de `seguimiento.py` — agrupación interna del módulo

**B) Con tabla real, pero dirección/filosofía inversa:**

- `catalogo_variables` — la **fila de BD** asume que existe una función Python en el
  Variable Registry, no al revés. Ver issue #587 (checker en dirección inversa).
- `configuracion_sistema` — tolera ausencia por diseño (`.get(clave, default)`); no es
  "debe existir para que el sistema funcione", es justo lo contrario.

---

## Hallazgos abiertos (ver GitHub para estado actualizado)

- **#586** — `CERT_FIN_INSTRUCCION` (#373, cerrado) nunca dispara: `generador_cert.py`
  existe pero `mutaciones_arbol.crear_fase()` solo genera `CERT_FIN_IP_CONSULTAS` al
  crear la fase RESOLUCION.
- **#587** — checker de consistencia `catalogo_variables` ↔ Variable Registry
  (dirección inversa a #347).

## Decisión aparcada

**Generalizar el Variable Registry** (`app/services/variables/`) para que variables
tipo "dato" (passthrough simple de un campo existente, ver `dato.py`) sean definibles
por el Supervisor vía ruta de atributo en texto, sin función Python. Evaluada y
descartada (2026-07-04): el ahorro es modesto (solo cubre "el dato ya existe, falta
exponerlo") y el coste es real — una ruta de atributo en texto no la detecta ningún
refactor/grep, a diferencia de la función Python actual.
