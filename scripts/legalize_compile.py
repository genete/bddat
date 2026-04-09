#!/usr/bin/env python3
"""
Compila normas del catálogo BDDAT en un MD unificado para NotebookLM.

Para cada norma del catálogo que tenga fichero local (legalize-es o
docs/normas/) genera un bloque con cabecera YAML normalizada seguido
del texto completo de la norma.

Fuentes:
  - id_tecnico tipo BOE-A-*  → D:/legalize-es/es/ o es-an/
  - id_tecnico numérico      → docs/normas/sedeboja_{id}.md

Uso:
    python scripts/legalize_compile.py
    python scripts/legalize_compile.py --area 6.1
    python scripts/legalize_compile.py --area 6.2 --out mi_salida.md
    python scripts/legalize_compile.py --estado MAPEO_CONTEXTO
"""

import sys
import os
import csv
import re
import argparse
from pathlib import Path
from datetime import date

# Rutas base
REPO_ROOT    = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_PATH = REPO_ROOT / "docs" / "normas_catalog.csv"
NORMAS_DIR   = REPO_ROOT / "docs" / "normas"
LEGALIZE_DIR = Path(os.environ.get("LEGALIZE_DIR", r"D:\legalize-es"))
OUTPUT_DEFAULT = REPO_ROOT / "docs_prueba" / "temp" / "normas_compiladas.md"


def leer_frontmatter_y_cuerpo(filepath):
    """
    Separa el bloque frontmatter YAML del cuerpo del fichero MD.
    Devuelve (dict_campos, texto_cuerpo).
    """
    fields = {}
    cuerpo_inicio = 0
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    cuerpo_inicio = i + 1
                    break
                m = re.match(r'^([\w_]+):\s*"?([^"]*)"?\s*$', line)
                if m:
                    fields[m.group(1)] = m.group(2).strip()
        cuerpo = "".join(lines[cuerpo_inicio:])
    except Exception as e:
        cuerpo = f"[Error leyendo fichero: {e}]\n"
    return fields, cuerpo


def inferir_rango(titulo):
    """Deduce el rango normativo a partir del inicio del título."""
    t = titulo.lower()
    if "real decreto-ley" in t or "real decreto ley" in t:
        return "real_decreto_ley"
    if "real decreto" in t:
        return "real_decreto"
    if "decreto-ley" in t or "decreto ley" in t:
        return "decreto_ley"
    if "decreto" in t:
        return "decreto"
    if "ley orgánica" in t:
        return "ley_organica"
    if "ley" in t:
        return "ley"
    if "orden" in t:
        return "orden"
    if "resolución" in t or "resolucion" in t:
        return "resolucion"
    return "norma"


def localizar_norma(id_tecnico):
    """
    Devuelve Path al fichero local de la norma, o None si no existe.
      - Numérico  → docs/normas/sedeboja_{id}.md
      - BOE-A-*   → legalize-es/es/ o es-an/
    """
    if not id_tecnico:
        return None
    if id_tecnico.isdigit():
        p = NORMAS_DIR / f"sedeboja_{id_tecnico}.md"
        return p if p.exists() else None
    if id_tecnico.startswith("BOE"):
        for subdir in ["es", "es-an"]:
            p = LEGALIZE_DIR / subdir / f"{id_tecnico}.md"
            if p.exists():
                return p
    return None


def construir_header(fm, row, fuente):
    """
    Construye el bloque frontmatter YAML normalizado para NotebookLM.
    Combina datos del fichero original con los del catálogo BDDAT.
    """
    titulo = fm.get("title") or fm.get("referencia") or row.get("nombre_corto", "")
    rango  = fm.get("rank") or inferir_rango(titulo)

    jurisdiction = fm.get("jurisdiction", "")
    if jurisdiction == "es":
        ambito_juridico = "estatal"
    elif jurisdiction.startswith("es-"):
        ambito_juridico = "andalucia"
    elif fuente == "sedeboja":
        ambito_juridico = "andalucia"
    else:
        ambito_juridico = "estatal"

    fecha   = (fm.get("last_updated")
               or fm.get("version_consolidada")
               or fm.get("publication_date", ""))
    id_tec  = (fm.get("identifier")
               or str(fm.get("sedeboja_id", ""))
               or row.get("id_tecnico", ""))

    lines = [
        "---",
        f'titulo: "{titulo}"',
        f'rango: "{rango}"',
        f'ambito_juridico: "{ambito_juridico}"',
        f'fecha_consolidada: "{fecha}"',
        f'id_tecnico: "{id_tec}"',
        f'procedimientos_bddat: "{row.get("procedimientos", "")}"',
        f'estado_bddat: "{row.get("estado", "")}"',
        f'fuente: "{fuente}"',
        "---",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compila normas del catálogo BDDAT para NotebookLM"
    )
    parser.add_argument("--area",   help="Filtrar por ámbito del CSV (ej: 6.1, 6.2)")
    parser.add_argument("--estado", help="Filtrar por estado del CSV (ej: MAPEO_CONTEXTO)")
    parser.add_argument("--out",    help="Ruta del fichero de salida")
    parser.add_argument("--solo-confirmadas", action="store_true",
                        help="Solo normas con ámbito asignado y estado no OBSOLETA")
    parser.add_argument("--individual", action="store_true",
                        help="Genera un fichero por norma en el directorio de salida (--out debe ser una carpeta)")
    args = parser.parse_args()

    output_path = Path(args.out) if args.out else OUTPUT_DEFAULT

    with open(CATALOG_PATH, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    # Filtros opcionales
    if args.area:
        rows = [r for r in rows if r.get("ambito", "").strip() == args.area]
    if args.estado:
        rows = [r for r in rows if r.get("estado", "").strip() == args.estado]
    if args.solo_confirmadas:
        rows = [r for r in rows if r.get("ambito", "").strip()
                and r.get("estado", "").strip() not in ("OBSOLETA",)]

    incluidas = []
    omitidas  = []

    if args.individual:
        # Modo individual: un fichero por norma en el directorio de salida
        out_dir = output_path if output_path.suffix == "" else output_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        for row in rows:
            id_tec  = row.get("id_tecnico", "").strip()
            nombre  = row.get("nombre_corto", id_tec or "sin nombre")

            path = localizar_norma(id_tec)
            if not path:
                motivo = "sin id_tecnico" if not id_tec else "fichero no encontrado localmente"
                omitidas.append((nombre, id_tec, motivo))
                continue

            fuente = "sedeboja" if id_tec.isdigit() else "legalize-es"
            fm, cuerpo = leer_frontmatter_y_cuerpo(path)
            header = construir_header(fm, row, fuente)

            # Nombre de fichero: id_tecnico sanitizado
            safe_name = id_tec.replace("/", "-").replace("\\", "-") or "norma"
            fichero = out_dir / f"{safe_name}.txt"
            fichero.write_text(header + "\n" + cuerpo.rstrip() + "\n", encoding="utf-8")
            incluidas.append(nombre)
    else:
        # Modo compilado: un único fichero
        bloques = []
        for row in rows:
            id_tec  = row.get("id_tecnico", "").strip()
            nombre  = row.get("nombre_corto", id_tec or "sin nombre")

            path = localizar_norma(id_tec)
            if not path:
                motivo = "sin id_tecnico" if not id_tec else "fichero no encontrado localmente"
                omitidas.append((nombre, id_tec, motivo))
                continue

            fuente = "sedeboja" if id_tec.isdigit() else "legalize-es"
            fm, cuerpo = leer_frontmatter_y_cuerpo(path)
            header = construir_header(fm, row, fuente)

            bloques.append(header + "\n")
            bloques.append(cuerpo.rstrip() + "\n")
            bloques.append("\n---\n\n")
            incluidas.append(nombre)

        encabezado = (
            f"# Normas BDDAT — compilación para NotebookLM\n\n"
            f"Generado: {date.today().isoformat()}  "
            f"|  Normas incluidas: {len(incluidas)}"
        )
        if args.area:
            encabezado += f"  |  Área: {args.area}"
        if args.estado:
            encabezado += f"  |  Estado: {args.estado}"
        encabezado += "\n\n---\n\n"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(encabezado + "".join(bloques), encoding="utf-8")

    # Resumen en consola
    sep = "=" * 64
    print(f"\n{sep}")
    print(f"Incluidas:  {len(incluidas)}")
    print(f"Omitidas:   {len(omitidas)}")
    print(f"Salida:     {output_path}")
    print(sep)
    if omitidas:
        print("\nOmitidas (sin fichero local — ejecutar sedeboja_extract.py --guardar):")
        for nombre, id_tec, motivo in omitidas:
            print(f"  [{id_tec or '?':>10}]  {nombre[:55]}  ({motivo})")


if __name__ == "__main__":
    main()
