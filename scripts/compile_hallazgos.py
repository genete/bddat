#!/usr/bin/env python3
"""
Genera el fichero consolidado de hallazgos normativos para NotebookLM.

Concatena todos los *_reglas.md de docs/normas/hallazgos_nblm/ en orden
jerárquico (norma general → norma especial). El fichero resultante se sube
como fuente única al cuaderno de NotebookLM, sustituyendo los ficheros
individuales de cada norma.

Uso:
    python scripts/compile_hallazgos.py
    python scripts/compile_hallazgos.py --out "H:/Mi unidad/bddat-notebooklm/hallazgos_consolidados.txt"
"""

import argparse
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
HALLAZGOS_DIR = REPO_ROOT / "docs" / "normas" / "hallazgos_nblm"

OUTPUT_DEFAULT = REPO_ROOT / "docs_prueba" / "temp" / "hallazgos_consolidados.txt"


def main():
    parser = argparse.ArgumentParser(
        description="Consolida hallazgos normativos BDDAT para NotebookLM"
    )
    parser.add_argument(
        "--out",
        help="Ruta de salida (por defecto docs_prueba/temp/hallazgos_consolidados.txt)",
    )
    args = parser.parse_args()

    output_path = Path(args.out) if args.out else OUTPUT_DEFAULT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ficheros = sorted(HALLAZGOS_DIR.glob("*_reglas.md"))

    if not ficheros:
        print("No se encontraron ficheros *_reglas.md en", HALLAZGOS_DIR)
        return

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("HALLAZGOS NORMATIVOS BDDAT — consolidado para NotebookLM\n")
        f.write(f"Generado: {date.today().isoformat()}\n")
        f.write(f"Normas incluidas: {len(ficheros)}\n")
        f.write("=" * 64 + "\n\n")

        for p in ficheros:
            f.write(f"\n{'=' * 64}\n")
            f.write(f"NORMA: {p.stem}\n")
            f.write(f"{'=' * 64}\n\n")
            f.write(p.read_text(encoding="utf-8"))
            f.write("\n")

    print(f"\nNormas incluidas ({len(ficheros)}):")
    for p in ficheros:
        print(f"  {p.name}")
    print(f"\nSalida: {output_path}")


if __name__ == "__main__":
    main()
