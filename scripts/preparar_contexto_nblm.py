#!/usr/bin/env python3
"""
Genera el contexto normativo BDDAT para NotebookLM.

A diferencia de preparar_contexto.py (que vuelca todo el código),
este script compila solo los documentos de diseño relevantes para
el trabajo de extracción normativa: guías, variables, hallazgos
ya consolidados y catálogo de normas.

Uso:
    python scripts/preparar_contexto_nblm.py
    python scripts/preparar_contexto_nblm.py --out "H:/Mi unidad/bddat-notebooklm/contexto_normativo.txt"
"""

import os
import argparse
from pathlib import Path
from datetime import date

REPO_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Documentos a incluir, en orden de lectura para NotebookLM
DOCUMENTOS = [
    "docs/GUIA_NORMAS.md",
    "docs/normas_catalog.csv",
    "docs/DISEÑO_CONTEXT_ASSEMBLER.md",
    "docs/NORMATIVA_MAPA_PROCEDIMENTAL.md",
    "docs/NORMATIVA_EXCEPCIONES_AT.md",
    "docs/NORMATIVA_PLAZOS.md",
]

OUTPUT_DEFAULT = REPO_ROOT / "docs_prueba" / "temp" / "contexto_normativo_nblm.txt"


def main():
    parser = argparse.ArgumentParser(
        description="Genera contexto normativo BDDAT para NotebookLM"
    )
    parser.add_argument(
        "--out", help="Ruta de salida (por defecto docs_prueba/temp/contexto_normativo_nblm.txt)"
    )
    args = parser.parse_args()

    output_path = Path(args.out) if args.out else OUTPUT_DEFAULT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    incluidos = []
    omitidos = []

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"CONTEXTO NORMATIVO BDDAT — para NotebookLM\n")
        f.write(f"Generado: {date.today().isoformat()}\n")
        f.write("=" * 64 + "\n\n")

        for rel_path in DOCUMENTOS:
            p = REPO_ROOT / rel_path
            if not p.exists():
                omitidos.append(rel_path)
                continue
            f.write(f"\n{'=' * 64}\n")
            f.write(f"DOCUMENTO: {rel_path}\n")
            f.write(f"{'=' * 64}\n\n")
            f.write(p.read_text(encoding="utf-8"))
            f.write("\n")
            incluidos.append(rel_path)

    print(f"\nIncluidos:  {len(incluidos)}")
    if omitidos:
        print(f"Omitidos:   {omitidos}")
    print(f"Salida:     {output_path}")


if __name__ == "__main__":
    main()
