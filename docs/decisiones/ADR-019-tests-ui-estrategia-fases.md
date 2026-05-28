# ADR-019 — Estrategia de tests UI por fases

**Estado:** Adoptada
**Fecha:** 2026-05-28
**Issue:** #503 (Fase 1 — smoke tests pytest)

---

## Contexto

El proyecto tiene una buena base de **50 tests pytest backend** con cobertura amplia (motor, plazos, ESFTT, documentos, CBs) y verificación manual con **Playwright MCP** para la UI cuando hace falta. La UI **no tiene tests automatizados** propios.

El análisis crítico fase 3 (§5.7) planteó la decisión política: introducir tests UI mínimos o no.

Variables que pesan:

- **1 dev + IA** con ratio alto de productividad — el tiempo dedicado a tests es tiempo no dedicado a features.
- **Revamping de UI en curso** — los componentes React van a iterar constantemente durante varias semanas. Tests rotos por cada iteración son tiempo perdido.
- **Coste/beneficio asimétrico** por tipo de test (smoke pytest barato vs E2E Playwright caro).
- **Test de éxito del usuario** (estudio fase 2): "no marcha atrás, métrica mala = retraso en tramitación". Tests UI nunca deben ralentizar el desarrollo del revamping.

---

## Decisión

### Estrategia por 3 fases

**Las fases no son del proyecto BDDAT, son del propio sistema de tests UI.** Cada fase introduce un nivel de cobertura adicional cuando el contexto lo permite.

### Fase 1 — Durante el revamping (estado actual)

| Tipo | Estado | Razón |
|---|---|---|
| **Smoke tests pytest** | **SÍ — añadir para cada vista nueva** | Coste mínimo (ms por test), no necesitan build React, detectan errores 500 y "vista no carga" |
| Verificación manual con Playwright MCP | SÍ — continúa | Patrón ya establecido. Por cada PR significativo |
| E2E formales con Playwright | NO | La UI no es estable; tests E2E se romperían con cada iteración |
| RTL + Vitest para componentes React | NO | Los componentes React iteran constantemente durante revamping; falso amigo |
| Tests visuales (Chromatic/Percy) | NO | Overkill; SaaS de pago |

#### Qué cubre un smoke test pytest

Ejemplo plantilla:

```python
def test_arbol_expediente_render(client, app_ctx, expediente_seed):
    resp = client.get(f'/expedientes/{expediente_seed.id}/arbol')
    assert resp.status_code == 200
    assert b'<div id="app-root"' in resp.data
    assert b'class="app-shell"' in resp.data
```

No invoca navegador, no ejecuta JS, no compila bundle. Solo verifica que el endpoint Flask responde con el HTML esperado del shell `base_app.html`. Tiempo de ejecución: ~10ms por test.

#### Cobertura objetivo Fase 1

Un smoke test por vista grande:

- Dashboard (`/`).
- Listado expedientes (`/expedientes/`).
- Detalle expediente (`/expedientes/<id>`).
- Árbol expediente (`/expedientes/<id>/arbol`).
- Pool documentos (`/expedientes/<id>/documentos`).
- Listado entidades (`/entidades/`).
- Detalle entidad (`/entidades/<id>`).
- Listado proyectos (`/proyectos/`).
- Listado usuarios (`/usuarios/`).
- Listado plantillas (`/admin/plantillas/`).
- Detalle plantilla (`/admin/plantillas/<id>`).
- Mi trabajo (`/mi_trabajo/`).
- Perfil (`/perfil/`).
- Login (`/auth/login`).
- Errores (`/404`, `/500`).

Total: **~15 smoke tests** cubriendo el sistema entero. Por permisos: variantes para ADMINISTRATIVO (ver que `/admin/plantillas/` da 200 tras ADR-013, pero `POST /editar` da 403).

### Fase 2 — Tras revamping (componentes estabilizados)

Cuando los componentes React del árbol y de Mi trabajo dejen de mutar significativamente (estimación: tras cerrar #500 y #501, posiblemente con 1-2 sprints de uso real):

| Tipo | Estado |
|---|---|
| **E2E Playwright mínimo** | **SÍ — añadir** |
| RTL + Vitest para componentes complejos | Considerable según necesidad |

#### Suite E2E objetivo Fase 2 — 3-5 flujos críticos

1. **Login + dashboard**: usuario entra, ve su dashboard según rol.
2. **Búsqueda y apertura de expediente**: `Ctrl+K`, escribe número, abre, ve árbol.
3. **Crear nodo desde árbol**: selecciona fase, modo edición, drag tipo desde despensa, guarda.
4. **Subir documento (admin)**: login admin, va a Mi trabajo, sube doc al pool.
5. **Generar escrito**: tarea ELABORAR, genera escrito desde plantilla, verifica .docx producido.

Infraestructura:
- BD test con fixture sembrada (`scripts/seed_demo.py` extendido si hace falta).
- `npm run build` antes de la suite.
- Flask arrancado con bundles ya generados.

### Fase 3 — Pre-producción (M4)

| Tipo | Estado |
|---|---|
| **Suite E2E ampliada** | **SÍ** — cubrir flujos del administrativo, plantillas, motor |
| **RTL completos** para componentes que sobrevivieron al revamping | **SÍ** |
| Tests visuales | A evaluar según madurez |

Foco: cobertura mínima viable para certificar despliegue. No se busca 100% de cobertura — se busca que las regresiones graves se detecten antes de producción.

---

## Por qué

- **Smoke tests pytest tienen ratio coste/valor óptimo** durante el revamping: detectan los errores más graves (500, vista no carga) sin penalizar la iteración.
- **NO añadir RTL/E2E durante revamping** evita la trampa del "tests rotos por cada cambio" que consume el ratio de productividad sin ganancia real. Patrón observado en muchos proyectos: tests escritos antes de que el componente estabilice se reescriben más veces que se ejecutan.
- **La verificación manual con Playwright MCP** es **defensa real** durante revamping, asistida por IA, sin coste de mantenimiento.
- **Diferir E2E formales a tras revamping** alinea con el principio del estudio de usuario: "no marcha atrás" — no ralentizar.

---

## Cómo implementar (Fase 1 — issue inmediato)

1. **Convención de naming**: `tests/test_smoke_<vista>.py`. Agrupar por dominio.
2. **Fixture común** en `conftest.py`: `usuario_admin`, `usuario_supervisor`, `usuario_tramitador`, `usuario_administrativo` para variantes por rol.
3. **Fixture `expediente_seed`** (extender si no existe) para tests que necesitan un expediente real.
4. **Smoke tests iniciales** — el listado de §Fase 1 (~15 tests).
5. **Convención**: cada nueva vista que entre durante revamping añade su smoke test en el mismo PR.

---

## Alternativa descartada

### A. Sin tests UI automatizados durante revamping (opción C de la discusión)

Considerada. Descartada porque los smoke tests pytest son tan baratos que el coste/beneficio favorece introducirlos desde ya. Sin ellos, un cambio de rutas o un error de import en el template puede pasar desapercibido hasta producción.

### B. E2E Playwright completos desde el inicio (opción B de la discusión)

Considerada. Descartada por el riesgo del "tests rotos por cada cambio" durante revamping. Los E2E son lentos (10-30s por test), frágiles ante cambios de CSS y timing, y costosos de mantener. Su valor crece cuando la UI estabiliza, no antes.

### C. Tests RTL desde ahora para los componentes React nuevos

Descartada por la misma razón que B, agravada porque los componentes React del revamping (árbol, despensa, inspector, command palette) son **exactamente los que más van a iterar**. Escribir RTL para `<NodoTarea>` o `<Despensa>` antes de que su API estabilice es trabajo desechado.
