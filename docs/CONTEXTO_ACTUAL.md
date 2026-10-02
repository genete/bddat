# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1004** (2026-10-02, PR #1005), `pytest` a secas desde la raíz vuelve a ejecutar la suite completa, como dice `tests/README.md`. Un `pytest.ini` con `testpaths = tests` evita que recorra `docs_prueba/temp/` (los `test*.txt` como doctest) y `scripts/` (`cobertura_por_test.py`). Nodeids, marcadores y opciones no cambian; los comandos de cobertura sin ruta también funcionan ya.

**Próximo:** **ADR-050, fase 0** (confirmado por Carlos el 02/10/2026): revalidar la tabla de consumidores de §M y crear los issues de las fases 1 a 7. El frontend de notificaciones (#929) solo espera ya a las fases 0-3 de ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
