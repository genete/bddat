# Contexto actual — BDDAT

> Actualizar al cerrar cada issue. Una entrada por sección, no listas.

---

**Último cerrado:** #173 — Suspensión de plazos (art. 22 LPACAP). Inferencia real de intervalos desde el árbol documental de trámites; sin tabla propia. Mapa para REQUERIMIENTO_SUBSANACION, SOLICITUD_INFORME, CONSULTA_SEPARATA, SOLICITUD_COMPATIBILIDAD con triple fallback de cierre (ANALIZAR propio → ESPERAR_PLAZO.doc_producido → trámite hermano receptor). Constantes _TRAMITES_SUSPENSION/_TRAMITES_CIERRE y 4 helpers privados en plazos.py. 7 códigos nuevos en catalogo_requerido.py. 17 tests, 221 pasando. Cierra #328 (tracking — todos los hijos cerrados).

**Actuales:** —

**Próximo:** #339 — Carga del calendario de días inhábiles y aviso de año N+1. Deuda técnica de #172: investigar fuente oficial (CSV Junta/BOJA, API, carga manual) e implementar mecanismo de importación anual. Bloqueante para cierre de #328.
