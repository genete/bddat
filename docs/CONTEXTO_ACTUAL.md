# Contexto actual — BDDAT

> Solo **Hecho** y **Próximo**, y se actualiza al cerrar cada issue con
> confirmación de Carlos (ADR-031 §7, nota; regla en `CLAUDE.md`). El detalle
> histórico está en `git log`; el mapa de qué falta y los documentos vivos, en
> [`docs/README.md`](README.md).

---

**Hecho:** **#1000** (2026-10-01, PR #1002), la prueba de la edición WebDAV en un puesto de la Junta: funciona con el LibreOffice corporativo 7.6, contra la IP de red y desde otra máquina por la VPN. El botón «Editar» no necesita instalar nada en el puesto (`vnd.libreoffice.command:`). Los requisitos nuevos están en ADR-050 §D. La puerta de la fase 1 queda abierta.

**Próximo:** **ADR-050, fase 0** (confirmado por Carlos el 01/10/2026): #1001, congelar los consumidores del modelo de rutas. Después, revalidar §M y crear los issues de las fases 1 a 7. El frontend de notificaciones (#929) solo espera ya a las fases 0-3 de ADR-050; hasta entonces la tramitación de una `NOTIFICAR` en el navegador sigue coja (#928 D12, #967 D1).
