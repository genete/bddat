# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1001** (2026-10-02, PR #1003), la congelación de los consumidores del modelo de rutas (ADR-050, fase 0). Un test cuenta, fichero a fichero, cuántas veces usa `app/` los símbolos del disco: falla si el número sube, y también si baja sin actualizarlo. La regla está en `REGLAS_DESARROLLO.md`, «Documentos: la ficha, no el fichero».

**Próximo:** **ADR-050, fase 0** (confirmado por Carlos el 02/10/2026): revalidar la tabla de consumidores de §M y crear los issues de las fases 1 a 7. El frontend de notificaciones (#929) solo espera ya a las fases 0-3 de ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
