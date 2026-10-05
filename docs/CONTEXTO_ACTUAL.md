# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1014** (2026-10-05): un solo sitio de `conftest.py` monta los documentos con contenido, las notificaciones y las solicitudes de los tests, y el guard de asserts exige nombrar la decisión que cambia un `assert` ajeno. En el corte de #1007 cambia el helper, no los tests.

**Próximo:** **#1007** (ADR-050, fase 1), PR 4: el corte. El frontend de notificaciones (#929) solo espera ya a ella.
