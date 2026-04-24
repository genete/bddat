# Reglas de desarrollo — BDDAT

## Ramas

- `develop` — rama por defecto; todo cambio pasa por aquí
- `main` — solo recibe merges desde develop al cerrar milestone; lleva tags `vMAJOR.MINOR.PATCH`
- Ramas temporales nacen de develop y vuelven via PR; borrar remota inmediatamente tras merge
- No squash merge — preservar historial completo de commits

**Naming:** `feature/issue-XX-descripcion` · `bugfix/issue-XX-descripcion` · `refactor/descripcion` · `docs/descripcion`

---

## Commit directo vs rama temporal

**Commit directo en develop** — docs, typos, 1-2 ficheros sin lógica de negocio, sin necesidad de `flask run`.
Si el commit resuelve un issue, cerrarlo a mano (sin PR no hay auto-close):
`gh issue close <N> --comment "Resuelto en commit <SHA> (develop)."`

**Rama + PR** — 3+ ficheros, modelos, rutas, templates, migraciones, cualquier cambio que requiera prueba funcional.

---

## Commits

Formato: `[CATEGORÍA] #N descripción en imperativo`

| Categoría | Cuándo |
|-----------|--------|
| `[BD]` | SQL directo, cambios en schema |
| `[MODELO]` | Modelos SQLAlchemy |
| `[RUTA]` | Rutas Flask |
| `[TEMPLATE]` | Templates HTML |
| `[STYLE]` | CSS / JS |
| `[MIGA]` | Ficheros en migrations/versions/ |
| `[SERVICIO]` | app/services/ |
| `[FEATURE]` | Feature completa multi-capa |
| `[FIX]` | Corrección de bug |
| `[TEST]` | Tests |
| `[DOCS]` | Documentación |
| `[MERGE]` | Merge commits |
| `[RELEASE]` | Releases y tags |

---

## Migraciones de BD

**Nunca `flask db migrate`** — bug conocido con `include_schemas` que regenera todas las FK existentes.

```bash
flask db revision -m "descripcion"   # crear vacía
# editar manualmente: solo añadir los cambios necesarios, nunca tocar FK existentes
flask db upgrade
```

`env.py` sin `include_schemas` (estado por defecto del repo). Todas las tablas usan `schema='public'` explícito.

---

## Naming

- snake_case en todo: tablas, columnas, variables, funciones, rutas, ficheros
- CamelCase solo para clases de modelo Python (`Expediente`, `Solicitud`, `DocumentoPuro`)

---

## Releases

Al cerrar milestone: PR develop → main, tag anotado `vX.Y.Z`, GitHub Release con changelog.
No hay CHANGELOG.md — los PRs cerrados en GitHub son la fuente de verdad.

---

## Decisiones arquitectónicas

Registrar en `docs/decisiones/` como ADR numerado. Ver ADR-001 y ADR-002 como referencia de formato.
