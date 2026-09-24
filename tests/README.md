# tests/ — cómo usar la suite

Punto de entrada para quien ejecuta o escribe tests. Las normas de detalle viven
donde nacieron —aquí se resumen y se enlazan—:

| Qué | Fuente de verdad |
|---|---|
| Fixtures, aislamiento por SAVEPOINT, `fs_tmp`, `ArbolESFTT` | docstrings de [`conftest.py`](conftest.py) |
| Construcción y semilla de la BD de tests | [`scripts/preparar_bd_test.py`](../scripts/preparar_bd_test.py), [`scripts/semilla_test.py`](../scripts/semilla_test.py) |
| Variables de entorno | [`.env.example`](../.env.example) |
| Convención de smoke tests | [`REGLAS_DESARROLLO.md` §Tests](../docs/guias/REGLAS_DESARROLLO.md) · [ADR-019](../docs/decisiones/ADR-019-tests-ui-estrategia-fases.md) |
| Dataset ficticio y matriz de cobertura | [ADR-030](../docs/decisiones/ADR-030-dataset-ficticio-y-matriz-cobertura.md) |
| Revisión de la suite (qué sobra, qué fusionar) | #946 |

---

## 1. Ejecutar

La suite corre contra **su propia base de datos**, nunca la de desarrollo (#849):

```bash
# .env: TEST_DATABASE_URL, TEST_FILESYSTEM_BASE, TEST_PLANTILLAS_BASE (ver .env.example)
python scripts/preparar_bd_test.py --recrear   # migraciones + semilla; repetir tras cada migración nueva
pytest                                         # suite completa (~30 s)
pytest tests/smoke                             # solo smoke
pytest tests/test_720_sellado_fase_cerrada.py -k borrado   # un fichero / un caso
pytest -rs                                     # ver por qué se saltó algo
```

- `create_app('testing')` → `TestingConfig`. `comprobar_aislamiento()` aborta si
  `TEST_DATABASE_URL` apunta a la misma base que `DATABASE_URL`.
- La BD se construye **desde las migraciones** (`upgrade heads`), no desde los
  modelos: si una migración deriva del modelo, la suite lo dice.
- **Tope de skips = 0** (`UMBRAL_SKIPS` en `conftest.py`). Un solo `skip` pone la
  sesión en rojo aunque todo lo demás pase. El número solo baja.

### Fuera del PC de desarrollo (sesión en la nube, Linux)

Verificado el 2026-09-24 con la suite completa. Lo que hay que saber:

- **Python 3.14**: el código usa `uuid.uuid7`. Con 3.12 no arranca.
- **Rol `claude_desktop`**: 32 migraciones hacen `GRANT … TO claude_desktop`.
  Crearlo antes de migrar: `CREATE ROLE claude_desktop NOLOGIN`.
- **LibreOffice**: `test_182` y `test_732` lo buscan en `C:\Program Files\…`;
  sin él se saltan y el tope de skips pone la sesión en rojo. Es esperado.
- **`test_365::test_ruta_local_absoluta_con_unidad_rechazada`** falla en Linux:
  `C:/…` no es ruta absoluta fuera de Windows.

### Cobertura

```bash
pytest --cov=app --cov-report=term-missing                      # global (71 % el 2026-09-24)
COVERAGE_CORE=ctrace pytest --cov=app --cov-context=test --cov-report=
python scripts/cobertura_por_test.py                            # líneas exclusivas por fichero
```

Por test, **`COVERAGE_CORE=ctrace` es obligatorio**: el núcleo por defecto de
Python ≥ 3.12 registra cada línea una sola vez por proceso y los contextos salen
incompletos sin avisar. Requiere `pip install pytest-cov` (no está en
`requirements.txt`).

---

## 2. Qué protege cada tipo de test

Clasificación de la supervisión de #946 (2026-09-24). "Retoques" = commits que
modifican el fichero tras su alta: mide cuánto cuesta mantenerlo.

| Tipo | Protege | Retoques medios | Cuándo escribirlo |
|---|---|--:|---|
| **Unitario puro** (sin BD ni mocks) | Algoritmos: cómputo de plazos, suspensiones, operadores, estado de dominio, parsers | **0,7** | Siempre que la lógica se pueda aislar en una función pura. Es el más barato. |
| **Smoke UI** (`tests/smoke/`) | Que la vista renderiza (200 + `app-main`) y responde por rol | 1,4 | Obligatorio con cada vista nueva (ADR-019). |
| **Integración con BD real** | Reglas de negocio sobre el árbol real: invariantes, sellado, cierres, certificados | 2,0 | Lo normal para reglas ESFTT y motor. |
| **Ruta HTTP con efectos** | Formularios y endpoints que mutan | 1,2 | Contrato de la ruta (códigos, JSON, redirecciones). |
| **Unitario con mocks** | Constructores de contexto, evaluadores | **3,0** | Solo para lo que no se puede reproducir: BD caída, servicio externo (`test_347`). |
| **Datos / semilla** | Que las migraciones dejan ciertas filas de catálogo | **3,0** | Solo invariantes del catálogo (qué debe existir), no copias de las filas. |

Los dos tipos más caros —mocks y datos— son los que más se retocan: están atados
a la *forma* del código o a filas concretas, no al comportamiento, y se rompen en
cada refactor sin que haya fallo real.

---

## 3. Reglas al escribir un test

1. **Nunca `pytest.skip` por falta de datos.** La base la sembramos nosotros: un
   dato ausente es un defecto de la semilla → `assert x is not None, 'la semilla
   debe traer…'`. El único skip legítimo es una dependencia opcional del entorno
   (`pytest.importorskip`, LibreOffice).
2. **Fabrica los datos, no los busques.** Buscar «una tarea NOTIFICAR sin
   vínculos» en la base funciona solo mientras nadie la toque. Usar:
   - `crear_expediente_de_prueba()` / fixture `alta_propia` — alta por la vía real.
   - `arbol_aislado` → `ArbolESFTT` con `solicitud_propia()`, `tarea_propia()`,
     `fase()`, `tramite()`, `documento()`, `diagnostico()`, `notificacion()`…
   - `documento_ancla_de_prueba()` — si solo hace falta que la `Solicitud` exista.
3. **Prefiere BD real a mocks.** Con `arbol_aislado` montar un árbol cuesta
   pocas líneas; un `MagicMock` que imita un modelo acepta cualquier atributo y se
   desalinea del modelo sin avisar.
4. **Aislamiento:**
   - BD: `app_ctx` (o `arbol_esftt` / `arbol_aislado`, que lo traen) — todo se
     revierte al acabar, aunque la aplicación haga `commit()`.
   - Disco: `fs_tmp` en cuanto el código escriba ficheros (alta, escritos,
     certificados, pool). El SAVEPOINT no revierte el disco.
   - `client` y las fixtures `usuario_*` **no** pasan por `app_ctx` (#836): lo que
     muten por HTTP queda escrito; limpiar o apuntar a nodos inexistentes.
5. **Fechas con `reloj_simulado.hoy()`**, nunca `date.today()`: el validador de
   #824 rechaza fechas futuras respecto al reloj de la aplicación.
6. **`ORDER BY` explícito** en cualquier `first()` de un test o fixture (#836):
   sin él, la tupla devuelta cambia con cada `UPDATE`.
7. **Login por rol, no por siglas**: `usuario_admin`, `usuario_supervisor`,
   `usuario_tramitador`, `usuario_administrativo`. Para saber quién es:
   `id_usuario_autenticado(client)`.
8. **N+1**: `contar_consultas(f)` comparando dos variantes, no un número absoluto.

---

## 4. Organización

- `tests/smoke/test_smoke_<vista>.py` — un fichero por vista (ADR-019).
- `tests/test_<issue>_<tema>.py` — el resto, por issue de origen. Es la convención
  histórica; su coste (cada issue vuelve a probar el mismo módulo desde otro
  ángulo) está en revisión en #946. Mientras tanto: **antes de crear un fichero
  nuevo, busca si ya hay uno que pruebe ese módulo** y amplíalo.
- `tests/fixtures/` — ficheros reales (ODT de LibreOffice, documentos de prueba).
