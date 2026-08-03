# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #725 cerrado (PR #747) — reparto motor/tabla/hardcode en ESFTT (ADR-037): nueva tabla `fases_tramites` (vocabulario y cardinalidad fase→trámite), `tipos_creables.py` reescrito a listado didáctico `canonicos`/`resto` sin evaluar el motor, categoría de bloqueo escapable de vocabulario (`vocabulario_esftt.py`, absorbe y cierra #719), `_CODIGOS_TRASLADO` centralizado, y frontend de la despensa/menú contextual adaptado al nuevo contrato con bloqueo reactivo tras el intento real de creación (de paso, corrige que el clic derecho montaba también el inspector de lectura). Derivados: **#745** (caché ausente en `motor_reglas.evaluar()`) y **#746** (CRUD de `fases_tramites`). Al intentar reproducir #716 en vivo se confirma que #720 ya lo había resuelto como efecto colateral (invariante `MUTAR` centralizado bloquea cualquier mutación sobre fase cerrada, no solo la primera) — cerrado sin cambio de código; deriva **#748** (funcionalidad: el vaciado de resultado/documento al reabrir fase debería depender del motivo de la reapertura, no ser incondicional).

**Próximo (2026-08-03):** Siguiente: **#742** ([BUG] editores bespoke de tarea ANALIZAR/ELABORAR/NOTIFICAR sin botón de borrar) — se adelanta a la cabeza de cola por gravedad, regresión de UX activa. Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco: #724, #712, #444/#555, #630. **#728** datos institucionales del órgano: en cola, no bloquea a nadie. Al final de la cola, no críticos: **#729** (la casilla «abrir carpeta al generar» abre la carpeta por defecto porque el fichero se muda justo después), **#730** (regenerar un escrito crea documento nuevo en vez de sustituir el anterior; hay que decidir antes si sustituir o versionar) y **#743** (idea de seguimiento, no urgente). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos). Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase sigue siendo unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia); #723 no lo tocó. Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
