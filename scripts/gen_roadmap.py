#!/usr/bin/env python3
"""
gen_roadmap.py — Genera docs/PLAN_ROADMAP.md desde GitHub API (via gh CLI).

Uso:
    python scripts/gen_roadmap.py

Requisito: gh CLI autenticado (gh auth status).

La sección "Decisiones de arquitectura abiertas" está embebida como constante
en este script — edítala aquí cuando cambie, no en el MD directamente.
"""

import json
import subprocess
import sys
from datetime import date

REPO = "genete/bddat"
OUTPUT = "docs/PLAN_ROADMAP.md"

# Números de milestone en GitHub (M1=4, M2=5, M3=6, M4=7, M5=8).
# Hardcodeados para incluirlos siempre, incluso si GitHub los marca como cerrados.
MILESTONE_NUMBERS = [4, 5, 6, 7, 8]

# ---------------------------------------------------------------------------
# Sección estática: Decisiones de arquitectura abiertas
# Nota: la columna "Milestone" puede quedar obsoleta; la fuente de verdad
# de cada decisión está en el documento de diseño correspondiente.
# ---------------------------------------------------------------------------
DECISIONES_ARQUITECTURA = """\
## Decisiones de arquitectura abiertas

> Tabla orientativa — puede estar desactualizada. Consultar el documento
> de diseño correspondiente para el estado real de cada decisión.

| Decisión | Opciones |
|----------|----------|
| Almacenamiento de documentos | Filesystem local / S3-compatible / PostgreSQL bytea |
| Motor de plantillas | python-docx (Word) / Jinja2 sobre ODT / WeasyPrint (HTML→PDF) |
| Firma electrónica | @firma JdA integrada / flujo manual en dos pasos |
| Modelo de elementos eléctricos | Genérico con JSON / Tablas específicas por tipo |
| PostGIS vs coordenadas simples | PostGIS / lat+lon numérico |
| Plazos: suspensión | Modelo de eventos de suspensión / solo fecha_limite estática |
| Permisos granulares | Por acción+expediente en tablas / roles fijos ampliados |
| Notificaciones externas | Email directo / Notific@ JdA / manual |
| Integración registro de entrada | BandeJA JdA / registro propio / ninguno |
| Legacy | Inventario pendiente: estructura, volumen, documentos |
"""


def gh_api(path: str) -> list | dict:
    """Llama a gh api y devuelve JSON. Maneja paginación automáticamente."""
    result = subprocess.run(
        ["gh", "api", "--paginate", f"repos/{REPO}/{path}"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"ERROR gh api {path}:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    raw = result.stdout.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # gh --paginate puede concatenar múltiples arrays JSON
        arrays = []
        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(raw):
            raw_slice = raw[pos:].lstrip()
            if not raw_slice:
                break
            obj, offset = decoder.raw_decode(raw_slice)
            arrays.extend(obj if isinstance(obj, list) else [obj])
            pos += len(raw) - len(raw_slice) + offset
        return arrays


def get_milestones() -> list:
    milestones = []
    for num in MILESTONE_NUMBERS:
        data = gh_api(f"milestones/{num}")
        if isinstance(data, dict) and "number" in data:
            milestones.append(data)
    return milestones


def get_open_issues(milestone_number: int) -> list:
    """Devuelve issues abiertos de un milestone (excluye PRs)."""
    all_issues = gh_api(
        f"issues?milestone={milestone_number}&state=open&per_page=100"
    )
    issues = [i for i in all_issues if "pull_request" not in i]
    return sorted(issues, key=lambda i: i["number"])


def get_orphan_issues() -> list:
    """Issues abiertos sin milestone."""
    all_issues = gh_api("issues?milestone=none&state=open&per_page=100")
    return [i for i in all_issues if "pull_request" not in i]


def milestone_estado(m: dict) -> str:
    open_c = m["open_issues"]
    closed_c = m["closed_issues"]
    if open_c == 0 and closed_c > 0:
        return f"✅ COMPLETADO ({closed_c} cerrados)"
    if closed_c == 0:
        return "PENDIENTE"
    return f"EN CURSO ({closed_c} cerrados)"


def render_milestone(m: dict) -> str:
    open_issues = get_open_issues(m["number"])
    estado = milestone_estado(m)
    lines = [f"## {m['title']}\n"]
    if m.get("description"):
        lines.append(f"**Descripción:** {m['description']}")
    lines.append(f"**Estado:** {estado}")
    lines.append("")
    if open_issues:
        lines.append("**Issues abiertos:**")
        for i in open_issues:
            labels = " ".join(f"`{lb['name']}`" for lb in i.get("labels", []))
            label_str = f" {labels}" if labels else ""
            lines.append(f"- #{i['number']} — {i['title']}{label_str}")
        lines.append("")
    else:
        lines.append("_Sin issues abiertos._")
        lines.append("")
    return "\n".join(lines)


def render_orphans(orphans: list) -> str:
    if not orphans:
        return ""
    lines = [
        "## ⚠️ Issues sin milestone\n",
        "> Estos issues no están asignados a ningún milestone.",
        "> Asígnalos y vuelve a ejecutar el script.\n",
    ]
    for i in orphans:
        labels = " ".join(f"`{lb['name']}`" for lb in i.get("labels", []))
        label_str = f" {labels}" if labels else ""
        lines.append(f"- #{i['number']} — {i['title']}{label_str}")
    lines.append("")
    return "\n".join(lines)


def main():
    today = date.today().isoformat()
    milestones = get_milestones()
    orphans = get_orphan_issues()

    parts = []

    parts.append(f"""\
# ROADMAP — BDDAT · Estado de implementación

> **Propósito:** Estado vivo del proyecto. Generado automáticamente desde GitHub.
> La verbosidad (qué falta, cómo hacerlo) vive en los issues de GitHub, no aquí.
> La visión estratégica y clasificación de bloques está en `PLAN_ESTRATEGIA.md`.
>
> **Generado:** {today} · `python scripts/gen_roadmap.py`

---

""")

    for m in milestones:
        parts.append(render_milestone(m))
        parts.append("---\n\n")

    orphan_section = render_orphans(orphans)
    if orphan_section:
        parts.append(orphan_section)
        parts.append("---\n\n")

    parts.append(DECISIONES_ARQUITECTURA)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    print(f"Generado: {OUTPUT}")
    for m in milestones:
        print(f"  {m['title']}: {m['open_issues']} abiertos, {m['closed_issues']} cerrados")
    if orphans:
        print(f"\n  ⚠️  {len(orphans)} issues sin milestone: "
              + ", ".join(f"#{i['number']}" for i in orphans))


if __name__ == "__main__":
    main()
