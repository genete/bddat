#!/usr/bin/env python3
"""
gen_issues.py — Genera ficheros de contexto de issues abiertos en .issues/

Salida (gitignored):
    .issues/M1_Bloqueantes.md
    .issues/M2_Necesarios.md
    ...
    .issues/sin_milestone.md  (si los hay)

Uso:
    python scripts/gen_issues.py            # todos los milestones
    python scripts/gen_issues.py 5          # solo milestone número 5

Requisito: gh CLI autenticado (gh auth status).
"""

import json
import os
import re
import subprocess
import sys
from datetime import date

REPO = "genete/bddat"
OUTPUT_DIR = ".issues"

# Números de milestone en GitHub (M1=4, M2=5, M3=6, M4=7, M5=8).
MILESTONE_NUMBERS = [4, 5, 6, 7, 8]


def gh_api(path: str) -> list | dict:
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


def get_milestones(filter_number: int | None = None) -> list:
    numbers = [filter_number] if filter_number is not None else MILESTONE_NUMBERS
    milestones = []
    for num in numbers:
        data = gh_api(f"milestones/{num}")
        if isinstance(data, dict) and "number" in data:
            milestones.append(data)
    return milestones


def get_open_issues(milestone_number: int) -> list:
    all_issues = gh_api(
        f"issues?milestone={milestone_number}&state=open&per_page=100"
    )
    issues = [i for i in all_issues if "pull_request" not in i]
    return sorted(issues, key=lambda i: i["number"])


def get_orphan_issues() -> list:
    all_issues = gh_api("issues?milestone=none&state=open&per_page=100")
    return [i for i in all_issues if "pull_request" not in i]


def safe_filename(title: str) -> str:
    """Convierte un título en nombre de fichero seguro."""
    name = re.sub(r"[^\w\s-]", "", title)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:60]


def render_issue(i: dict) -> str:
    labels = ", ".join(lb["name"] for lb in i.get("labels", []))
    body = (i.get("body") or "_Sin descripción._").strip()
    lines = [
        f"### #{i['number']} — {i['title']}",
        "",
    ]
    if labels:
        lines.append(f"**Labels:** {labels}")
    if i.get("milestone"):
        lines.append(f"**Milestone:** {i['milestone']['title']}")
    lines.append("")
    lines.append(body)
    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def write_milestone_file(m: dict, issues: list, today: str):
    slug = safe_filename(m["title"])
    filepath = os.path.join(OUTPUT_DIR, f"{slug}.md")
    closed_c = m["closed_issues"]
    estado = "✅ COMPLETADO" if m["open_issues"] == 0 else "EN CURSO" if closed_c > 0 else "PENDIENTE"

    lines = [
        f"# {m['title']}",
        "",
        f"> Generado: {today} · `python scripts/gen_issues.py`",
        f"> Estado: {estado} | Abiertos: {len(issues)} | Cerrados: {closed_c}",
        "",
    ]
    if m.get("description"):
        lines.append(f"**Descripción del milestone:** {m['description']}")
        lines.append("")
    lines.append("---")
    lines.append("")

    if issues:
        for i in issues:
            lines.append(render_issue(i))
    else:
        lines.append("_Sin issues abiertos._")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath, len(issues)


def write_orphan_file(issues: list, today: str):
    if not issues:
        return
    filepath = os.path.join(OUTPUT_DIR, "sin_milestone.md")
    lines = [
        "# ⚠️ Issues sin milestone",
        "",
        f"> Generado: {today} · `python scripts/gen_issues.py`",
        "> Estos issues deben asignarse a un milestone.",
        "",
        "---",
        "",
    ]
    for i in issues:
        lines.append(render_issue(i))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  ⚠️  {len(issues)} issues sin milestone → {filepath}")


def main():
    filter_number = int(sys.argv[1]) if len(sys.argv) > 1 else None
    today = date.today().isoformat()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    milestones = get_milestones(filter_number)
    if not milestones:
        print(f"No se encontró milestone con número {filter_number}", file=sys.stderr)
        sys.exit(1)

    for m in milestones:
        issues = get_open_issues(m["number"])
        filepath, count = write_milestone_file(m, issues, today)
        print(f"  {m['title']}: {count} issues abiertos -> {filepath}")

    if filter_number is None:
        orphans = get_orphan_issues()
        write_orphan_file(orphans, today)

    print(f"\nFicheros en {OUTPUT_DIR}/ (gitignored - no versionar)")


if __name__ == "__main__":
    main()
