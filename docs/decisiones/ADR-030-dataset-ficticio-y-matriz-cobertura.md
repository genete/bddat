---
id: ADR-030
título: Dataset ficticio estable y matriz de cobertura para desarrollo y certificación pre-producción
fecha: 2026-07-07
estado: Adoptada
issue: pendiente de crear
relacionado con: ADR-001 (motor agnóstico) · ADR-002 (ESFTT sin fechas) · ADR-010 (documentos_tarea N:M) · ADR-019 (estrategia tests UI por fases) · ADR-025 (Context Builder) · ADR-026 (vigencia normativa es de la regla, no de la variable)
---

## Contexto

El desarrollo de BDDAT necesita datos en base de datos para dos usos distintos:

1. **Validar a mano** nuevas funcionalidades de interfaz, motor de reglas y plazos, en cualquier momento del desarrollo — pre o post producción.
2. **Servir de fixture** a la suite de tests, incluidos tests que todavía no existen.

Ambos usos comparten un problema de fondo: **la estabilidad temporal**. Por ADR-002, ningún elemento ESFTT almacena fechas propias — las fechas administrativas viven en `Documento.fecha_administrativa`, y `fecha_limite` de un plazo **nunca se guarda, se recalcula siempre contra `hoy()`** (`app/services/plazos.py::obtener_estado_plazo`). El envejecimiento, por tanto, no está en el motor de cálculo — está en las fechas semilla fijas que alimentan ese cálculo: un expediente sembrado hoy con un documento fechado "hace 3 días hábiles" deja de representar `PRÓXIMO_VENCER` en cuanto pasa el tiempo real.

Al estudiar el alcance, el objetivo se amplió de "comodidad de desarrollo" a **auditoría de completitud de cara a la puerta M4→M5**: qué mecanismos del sistema necesitan una forma de comprobar que "lo que se supone que funciona, funciona" antes de considerar el sistema listo para producción — aunque la implementación de esa comprobación pueda quedar como placeholder en una primera vuelta.

### Lo que ya existe (base parcial y fragmentada)

| Pieza | Qué hace | Problema |
|---|---|---|
| `scripts/seed_demo.py` | 7 entidades + 10 expedientes narrativos verosímiles, aditivo (`get_or_create` por clave de negocio) | Fechas fijas (2022-2024) — ya envejecidas |
| `scripts/seed_listado.py` | 11 escenarios exactos de estado (T01-T11) de `estado_solicitud()`/`seguimiento.py`, destructivo (`TRUNCATE ... RESTART IDENTITY CASCADE`) | Fechas fijas (2025) — mismo envejecimiento; borra todo lo operacional al reejecutar |
| `scripts/seed_motor_variables.py` | 5 variables del Variable Registry, upsert idempotente por nombre | Ninguno — es el patrón de catálogo a imitar |
| `scripts/verificar_seed.py` | Verifica a mano (framework casero `check()`/`sys.exit(1)`) los 11 escenarios contra `seguimiento.py` real | Duplica pytest fuera de la suite |
| Fixture `expediente_seed` (`tests/conftest.py`) | `Expediente.query.first()`, `pytest.skip` si no hay ninguno | Pasivo — no garantiza dato; depende de que alguien haya sembrado antes a mano |
| `REGISTROS_REQUERIDOS` (`app/checks/catalogo_requerido.py`, #347) | Manifiesto de códigos mínimos de catálogo de capa 1 (vocabulario) que el código hardcodeado da por hechos | Es el suelo de vocabulario, no dice nada de `catalogo_plazos` (capa 2) ni resuelve expedientes |

`seed_demo.py` y `seed_listado.py` comparten, sin ningún módulo común, ~150 líneas de funciones auxiliares casi idénticas (`cargar_ids`, `crear_exp`, `crear_sol`, `crear_doc`, `crear_fase`, `crear_tramite`, `crear_tarea`). Ninguna de las dos usa fechas relativas a `hoy()`. La anotación `notas='PLAZO_DIAS=N'` que ambas usan en tareas `ESPERAR_PLAZO` no la consume ningún servicio de `app/` — es anotación muerta.

ADR-019 (Fase 2) ya anticipaba, sin llegar a diseñarla, una "BD test con fixture sembrada (`scripts/seed_demo.py` extendido si hace falta)". Este ADR es, en gran parte, el diseño de esa pieza pendiente.

---

## Decisión

### 1. Sandbox completo — sin aislamiento entre catálogo real y ficticio

El dataset ficticio (estructural y operacional) **nunca convive con datos reales en la misma base de datos**; producción se siembra aparte, de cero, bajo control explícito del Supervisor/administrador del sistema en el momento del despliegue. No existe una ruta de herencia o promoción automática entre la BD de desarrollo y la de producción.

Consecuencia directa: **no hace falta ningún mecanismo de aislamiento entre "tipo real" y "tipo de prueba"** dentro del catálogo. Se reutilizan tipos reales (`tipos_fases`, `tipos_tramites`, `tipos_solicitudes`, `tipos_tareas`) o se crean nuevos indistintamente, y se cuelgan de ellos valores de `catalogo_plazos`/`reglas_motor` puramente convenientes para ejercitar el mecanismo (p. ej. un plazo de 45 días sin base normativa) sin que eso represente ningún riesgo para producción. La capa de vocabulario ya es abierta por diseño: `app/services/tipos_creables.py` itera `TipoFase.query.order_by(...).all()` sin lista blanca — una fila nueva es visible y usable sin tocar código.

La única distinción que sobrevive es de conveniencia documental, no arquitectónica: dejar constancia legible (p. ej. en `norma_origen` o `observaciones`) de qué filas de catálogo son cobertura de mecanismo y cuáles podrían reutilizarse tal cual al sembrar producción — decisión de estilo, no de diseño.

**Alternativa descartada:** vocabulario de catálogo dedicado a test (`tipos_fases`/`tramites`/`solicitudes` con prefijo `TEST_*`), separado del vocabulario real. Se descartó porque resolvía un problema inexistente: solo tendría sentido si el catálogo de desarrollo pudiera terminar, total o parcialmente, en producción por herencia — y esa ruta no existe.

### 2. Consolidar antes de extender

Extraer las funciones auxiliares duplicadas de `seed_demo.py`/`seed_listado.py` a un módulo compartido (p. ej. `scripts/seed_lib.py`). Ambos scripts existentes pasan a importarlo; cero cambio de comportamiento. Es prerequisito de todo lo demás — construir la pieza de fechas relativas encima de dos copias duplicadas dobla el mantenimiento.

**Regla de diseño de los builders:** nunca hardcodear un identificador autoincremental. Todo se resuelve en tiempo de ejecución por clave estable — catálogo por `codigo`/`siglas` (patrón `cargar_ids()`: un `SELECT codigo, id` a un dict), operacional por clave de negocio (`nif`, `numero_at`) con `get_or_create`. Es la técnica que ya hace funcionar a los dos scripts existentes sin que un borrado o una recreación rompa nada.

La librería soporta dos modos de orquestación sobre los mismos builders:
- **Aditivo** (`get_or_create` por clave de negocio) — para el dataset narrativo persistente de desarrollo, que no debe perderse entre ejecuciones.
- **Destructivo-reset** (`TRUNCATE ... RESTART IDENTITY CASCADE` sobre las tablas operacionales, nunca sobre catálogo/estructurales) — para la matriz de cobertura, que quiere partir de un estado conocido y reproducible. El `CASCADE` es imprescindible: sin él, truncar `expedientes` falla por las FKs vivas de `solicitudes`/`fases`/etc.

### 3. Motor de fechas relativas a `hoy()` — vive en el seed, nunca en producción

**Aclaración explícita, porque generó confusión en el diseño:** `app/services/plazos.py` no se modifica ni un carácter. La única pieza nueva es una función auxiliar que vive dentro del script de seed (no en `app/`) y que usa el propio `calcular_fecha_fin()` real **al revés**: en lugar de `fecha_acto → fecha_límite`, busca qué `fecha_acto` hay que escribir hoy en `Documento.fecha_administrativa` para que, al pasar por el cálculo real (sin reimplementar su lógica), el resultado caiga en el estado deseado (`EN_PLAZO` holgado, `PRÓXIMO_VENCER` dentro del umbral de 5 días hábiles, `VENCIDO` reciente o antiguo). Reejecutar el seed en cualquier momento futuro reproduce el mismo abanico de estados relativo al nuevo "hoy" — sin tocar producción, sin reimplementar su lógica, sin riesgo de divergencia.

**Corrección de alcance encontrada durante el diseño:** `DISEÑO_FECHAS_PLAZOS.md` §3.3 marca las suspensiones de plazo como "pendiente de estudio previo". Leyendo `plazos.py` directamente, **las suspensiones ya están implementadas** — no como tabla propia, sino por inferencia del árbol documental (`_obtener_suspensiones`, `_TRAMITES_SUSPENSION`, `_TRAMITES_CIERRE`): un trámite disparador con su tarea `NOTIFICAR` produciendo documento abre la suspensión; el cierre se resuelve vía `ANALIZAR`/`ESPERAR_PLAZO` del propio trámite o de un trámite hermano receptor. La documentación estaba desactualizada; el código manda. La matriz de cobertura de plazos (§5) incluye por tanto suspensión activa y cerrada, no solo estados simples.

### 4. Matriz de cobertura — motor de reglas (`reglas_motor` / `condiciones_regla` / `excepciones_motor`)

12 operadores en `app/services/operadores.py`, compartidos con `catalogo_plazos`: `EQ NEQ IN NOT_IN IS_NULL NOT_NULL GT GTE LT LTE BETWEEN NOT_BETWEEN`.

| Dimensión | Casos a cubrir |
|---|---|
| Operador | Uno por cada uno de los 12 |
| Condiciones por regla | Sin condición (dispara siempre) · una condición · varias (AND implícito) |
| Efecto | `BLOQUEAR` · `ADVERTIR` |
| Excepción | Sin condiciones (neutraliza siempre) · con condiciones · varias excepciones en la misma regla |
| Prioridad | ≥2 reglas casando el mismo (`accion`,`sujeto`) con `prioridad` distinta |
| Profundidad del sujeto | Distintas longitudes de segmento (Solicitud/Fase/Trámite) y comodín `ANY` en cada posición |
| Tipo combinado | Solicitud con tipo compuesto (p. ej. AAP+AAC) → `evaluar_multi`/`auditar_multi` evalúa cada tipo simple, bloquea si cualquiera bloquea |
| Variable ausente | Condición referencia una variable no presente en el dict → no dispara, no lanza excepción (`log.warning`) |
| Acción | `CREAR` y `BORRAR` |

### 5. Matriz de cobertura — plazos (`catalogo_plazos` / `condiciones_plazo` / `efectos_plazo`)

| Dimensión | Casos a cubrir |
|---|---|
| Unidad | `DIAS_HABILES` · `DIAS_NATURALES` (prorroga si cae inhábil) · `MESES` (recorte de mes corto) · `ANOS` |
| Estado | `SIN_PLAZO` · `EN_PLAZO` · `PROXIMO_VENCER` (≤5 días hábiles) · `VENCIDO` |
| Efecto | Los 9 valores no-nulos de `efectos_plazo` — al menos un `VENCIDO` por cada uno |
| `campo_fecha` (forma de resolución) | `{"fk":...}` directo · `{"via_tarea_tipo":X,"rol":"CONSUMIDO"}` · `{"via_tarea_tipo":X,"rol":"PRODUCIDO"}` (retroactivo) · `{"rol":...}` sobre la propia Tarea · fallback FASE→solicitud cuando la fase no tiene el FK propio |
| Suspensión | Activa (sin cierre, extiende hasta hoy) · cerrada (duración fija sumada) — una por cada uno de los 4 trámites disparadores |
| Selección de entrada | `_seleccionar_catalogo`: varias entradas para el mismo tipo con `orden` distinto y condiciones, con fallback sin condiciones |
| Vigencia | `vigencia_desde`/`vigencia_hasta` — entrada histórica vs. vigente para el mismo tipo |
| Nivel ESFTT | SOLICITUD · FASE · TRAMITE · TAREA |

### 6. Matriz de cobertura — Variable Registry (`app/services/variables/`)

~19-20 variables activas hoy en código (`dato.py`, `calculado.py`, `plazo.py`); cada una necesita un escenario que la haga `True` y otro que la haga `False`.

**Nota sobre `catalogo_variables.activa` (ADR-026):** el flag no codifica vigencia normativa ni es un interruptor de negocio — es la compuerta de implementación ("¿existe ya la función en el Variable Registry?"), y es portante de verdad (filtra `_compilar_variables()` en `app/services/assembler.py`). Las variables cuya función ya existe en código deben estar en `activa=True`; `scripts/seed_motor_variables.py` quedó desacompasado del código en este punto (algunas funciones que ya existen siguen con `activa=False`) — corregirlo es parte natural de la consolidación del §2, no una decisión nueva de este ADR. El futuro de la propia columna se decide en #561, no aquí.

### 7. Matriz de cobertura — invariantes estructurales (capa 3, hardcoded, pre-motor)

`app/services/invariantes_esftt.py` se ejecuta **antes** de `motor_reglas.evaluar()` y no pasa por el motor agnóstico — requiere códigos reales (`ANALIZAR`, `ELABORAR`, `NOTIFICAR`, `DESFAVORABLE`, `INCORRECTA`), no es sustituible por vocabulario inventado.

| Acción | Casos a cubrir |
|---|---|
| `BORRAR` | Bloqueo si el sujeto (Tarea/Trámite/Fase/Solicitud) tiene hijos (documentos vinculados / tareas / trámites / fases) |
| `FINALIZAR` (Solicitud) | Bloqueo si alguna fase carece de `documento_resultado` |
| `FINALIZAR` (Fase/Trámite) | Bloqueo si falta documento producido en tarea `ANALIZAR`/`ELABORAR`/`NOTIFICAR`; bloqueo si `Notificacion.resultado='INCORRECTA'` |
| `FINALIZAR` (Tarea) | Bloqueo según tipo: falta documento producido / falta documento usado |
| Cierre de fase (#419) | Bloqueo si hay diagnóstico `desfavorable` sin consumir y el resultado propuesto no es `DESFAVORABLE` |

Se incluye también, como hallazgo colateral no bloqueante: `app/services/requisitos.py` reimplementa su propio evaluador de condiciones en vez de reutilizar `operadores.py`, y solo soporta 6 de los 12 operadores (faltan `GT/GTE/LT/LTE/BETWEEN/NOT_BETWEEN`, que degradan en silencio a "condición cumplida"). Reportado como bug independiente — issue [#601](https://github.com/genete/bddat/issues/601).

### 8. Generación y gestión física de documentos

Encaja en el bloque M4 (escritos/motor adaptativo — #555/#556/#561) de la hoja de ruta: es pieza a certificar antes de M5, no un extra de comodidad.

**Ya manejado con cuidado hoy** (`app/services/generador_escritos.py`):

| Fallo | Cómo reacciona |
|---|---|
| Plantilla `.docx` ausente en `PLANTILLAS_BASE` | `FileNotFoundError` con mensaje explícito (`_ruta_plantilla`) |
| Context Builder no cargable | `RuntimeError` envuelto con contexto (`_cargar_context_builder`) |
| Consulta nombrada que falla | Degrada a lista vacía + `log.warning`, no rompe la generación |
| Fallo al reparar XML anidado (docxtpl/docxcompose) | Degrada, conserva el original + `log.warning` |
| `FILESYSTEM_BASE` sin configurar | `RuntimeError` explícito |

**Sin ningún manejo hoy** (mismo patrón que `Documento.resolver_url()` con ruta local ausente):

| Fallo | Qué pasa realmente |
|---|---|
| `guardar_docx()` escribe a disco sin try/except | Red caída, sin permisos, disco lleno → excepción sin capturar, sin mensaje BDDAT |
| `_fn_imagen()`: imagen de plantilla ausente en `recursos/` | Falla dentro de `docxtpl`/`InlineImage`, sin control BDDAT |
| `_cargar_fragmentos()`: fragmento `.docx` ausente | Se omite la clave del contexto (solo warning) en vez de fallar ahí — el error real aparece más tarde y más confuso en el render Jinja2 |
| `Documento.resolver_url()` con ruta local ausente | `FileNotFoundError` sin capturar |

**Sin verificar nunca, documentado como tal por el propio proyecto:**
- Prerequisito R10 (`DISEÑO_GENERACION_ESCRITOS.md`): si el código embebido + QR de trazabilidad sobreviven el pipeline `.docx → Portafirmas → PDF` — "probar manualmente", nunca automatizado.
- El botón "Generar escrito" end-to-end desde la UI de tramitación (B1, Fase 5 de #167): el orquestador y la API existen; el disparo real desde la UI de tramitación está marcado como pendiente en el propio diseño.

**Conexión con el ecosistema externo:** Portafirmas (firma) se documentó en sesión previa como opaco/no scrapeable, con repos exploratorios (`bandeja-downloader`, `ptwanda-tramitador`, `notifica-poc`) sin cerrar — misma familia de riesgo (dependencia de un sistema externo cuyo comportamiento ante fallo no está probado). No se diseña en este ADR; queda anotado para cuando corresponda ampliarlo.

### 9. Principio de cobertura: contemplar todo el mapa, placeholder donde no toque implementar aún

El diseño de la suite de tests y de la librería de seed debe tener un lugar reservado para cada dimensión de las tablas anteriores, aunque la implementación de una celda concreta sea, en una primera vuelta, un placeholder documentado (un test con `pytest.skip('razón — #issue futuro')`, o un caso que documenta el comportamiento actual aunque sea deficiente) en vez de la solución definitiva. Hacer el análisis solo de una parte del mapa y dejar el resto sin identificar se considera peor que dejar huecos explícitos y señalizados.

Criterio de parada de la cobertura: **un caso por cada valor de cada dimensión**, no el producto cartesiano completo — cada operador, cada efecto, cada unidad, cada forma de `campo_fecha`, cada variable (`True`/`False`), cada invariante, cada fallo de generación/E-S de la tabla del §8.

### 10. Consumidores

- **Tests de mecanismo (nuevos):** leen contra el seed persistente y compartido — no fabrican su propio dato aislado por test. Llaman directamente a `motor_reglas.evaluar()`/`auditar()`, `plazos.obtener_estado_plazo()`, `assembler.build()`/`evaluar_multi()`, `requisitos.evaluar_requisitos()`, `generador_escritos.generar_escrito()`. El patrón ya existe y funciona hoy: el dict `ESPERADOS` de `verificar_seed.py` (escenario → estado esperado) es la plantilla declarativa a extender, más allá de los 11 escenarios de listado, a toda la matriz de motor/plazos/variables/invariantes/generación.
- **Smoke tests:** sin tocar, conviven en paralelo tal como están hoy (patrón ADR-019, `tests/smoke/`).
- `scripts/verificar_seed.py` se pliega a `pytest` (parametrizado sobre la matriz completa) en vez de vivir como script suelto con su propio framework casero.
- Construir-y-limpiar dato por test (patrón `autouse` ya usado en `tests/smoke/test_smoke_catalogo_requerimientos.py`) se reserva para lo que verifica **mutación real** (crear/editar/borrar), que por definición no se puede validar solo leyendo el seed persistente.

---

## Alcance y límites

Este ADR cubre lo necesario para el salto a producción según el análisis realizado: consolidación del seed, fechas relativas, y matriz de cobertura de motor de reglas, plazos, Variable Registry, invariantes estructurales y generación/gestión física de documentos.

**Explícitamente fuera de alcance** (identificado previamente como diferible a post-producción, no reabierto aquí):
- Integración PostGIS de los elementos técnicos/activos de red (`bddat-instalaciones`, #592, M5).
- Compilación de expediente para recursos.
- Diseño detallado del ecosistema externo (Portafirmas, BandeJA, Notifica) más allá de la anotación del §8.

Si en el futuro surge una necesidad no contemplada, se amplía o modifica este mismo ADR en vez de abrir uno nuevo paralelo.

---

## Hallazgos colaterales durante el análisis

- Las suspensiones de plazo (art. 22 LPACAP) ya están implementadas por inferencia documental en `plazos.py`, contrario a lo que indica `DISEÑO_FECHAS_PLAZOS.md` §3.3 ("pendiente de estudio previo") — la documentación quedó desactualizada.
- `catalogo_variables.activa` no es un interruptor de vigencia normativa (ADR-026) — es compuerta de implementación. `seed_motor_variables.py` tiene variables en `activa=False` cuya función ya existe en código.
- `app/services/requisitos.py` no soporta 6 de los 12 operadores del catálogo compartido — issue [#601](https://github.com/genete/bddat/issues/601).

---

## Próximos pasos (fuera de este ADR)

Desglose en issues, relación con pendientes y milestones — deliberadamente no abordado en la misma sesión que este ADR.
