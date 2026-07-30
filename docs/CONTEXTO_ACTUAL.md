# Contexto actual — BDDAT

> Actualizar al cerrar cada issue, con confirmación de Carlos (regla existente
> en `CLAUDE.md`). Detalle histórico: `git log`. Panorama de cobertura y qué
> falta: `docs/diseño/MATRIZ_COBERTURA_BDDAT.md`. Backlog completo: GitHub
> (milestones + labels `necesidad:N0XX`, ver ADR-031). Esqueleto sin campo
> "Actual" desde 2026-07-09 (ADR-031 §7, nota) — ver `docs/decisiones/ADR-031-matriz-cobertura-necesidades-ciclo-trabajo.md`.

---

**Hecho:** #726 cerrado (PR #731) — motor ODT, elección por extensión y el `.docx` en su propio módulo. Lo implementado está en el issue, en ADR-035 y en `DISEÑO_GENERACION_ESCRITOS.md`. Lo que no está en ellos: los tres huecos que aparecieron **no** salieron del enunciado, sino de recorrer el circuito entero en la interfaz. El bucle de párrafo `{%p %}` lo vi mirando el panel de tokens, no leyendo el issue; y dar de alta una plantilla y generar de verdad destapó **#729** y **#730**, dos defectos anteriores del flujo de ELABORAR (de #608 y #167) que ninguna prueba automática iba a encontrar porque viven en el orden entre cliente, disco y base de datos. El endpoint respondía 200 en los tres casos. De paso queda comprobado que el formato nuevo encaja con la organización documental de ADR-032 sin tocarla, que se daba por supuesto desde ADR-035 §6.

**Próximo (2026-07-30):** Siguiente: **#727** plantilla base canónica (desbloquea además los acentos descompuestos en el texto extraíble del PDF, ADR-035 §5), junto con **#732** — fijar el contrato del motor ODT contra un fichero real de LibreOffice: los 31 tests de #726 fabrican el `.odt` sintéticamente, así que si Writer cambia su salida siguen verdes y el motor roto. La plantilla base de #727 es el fixture natural, y hacerlas a la vez ahorra fabricar dos veces el mismo fichero. Luego: **#182** códigos embebidos; **#717** consumo real del diagnóstico; **#722** guardia viva del borrado del árbol; **#720** fase cerrada no sellada (absorbe #716); **#715** los tests de `invariantes_esftt` mockean `db`; **#723** revisión de invariantes; **#725** creación y orden de ESFTT entre dato y motor (condiciona #719). Foco fijo (2026-07-16): fase `ANÁLISIS_SOLICITUD` completamente tramitable. En cola, mismo foco: #724, #719 (esperar a #725 si se quiere hacer de una vez), #712, #444/#555, #630. **#728** datos institucionales del órgano: en cola, no bloquea a nadie. Al final de la cola, no críticos: **#729** (la casilla «abrir carpeta al generar» abre la carpeta por defecto porque el fichero se muda justo después) y **#730** (regenerar un escrito crea documento nuevo en vez de sustituir el anterior; hay que decidir antes si sustituir o versionar). Aplazados: #698 (poblado puro de catálogo), #572 (ortogonal, diferido por Carlos). Huecos de diseño sin issue: (a) `ESPERAR_PLAZO` no admite N documentos simultáneos (`DISEÑO_ANALISIS_SOLICITUD.md` §5); (b) el invariante de cierre de fase es unidireccional — `_check_cierre_fase` corta en seco con resultado `DESFAVORABLE`, así que nunca comprueba el caso simétrico (cerrar DESFAVORABLE teniendo un diagnóstico favorable como última evidencia). Sin issue a propósito: el guardián "el resultado de fase debe reflejar el diagnóstico" corresponde a la revisión de la fase `RESOLUCIÓN`, donde el diagnóstico único *es* el veredicto tras el certificado de finalización de fases; fijarlo antes sería diseñar en abstracto. Detalle en #711. Fuera de foco: ADR-021 y #644-648, aparcados.

---

## Documentos vivos

- `docs/diseño/MATRIZ_COBERTURA_BDDAT.md` — panorama de cobertura por
  necesidad (fuente de qué falta y dónde mirar para elegir el próximo foco).
- `docs/diseño/DETALLE_NECESIDADES_BDDAT.md` — catálogo de necesidades (qué es
  cada una, quién la necesita).
- `docs/diseño/DECISIONES_UI.md` — estado del revamping de interfaz.
- `docs/decisiones/` — ADRs. ADR-031 fija el ciclo de trabajo que gobierna
  este documento (ciclo diario + ciclo de reposición).
