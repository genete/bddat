#!/usr/bin/env python3
"""
Busca referencias cruzadas en legalize-es y compara con normas_catalog.csv.

Busca una cadena de texto en todos los ficheros MD de legalize-es
(solo es/ y es-an/) y muestra qué normas la mencionan, indicando
cuáles ya están en el catálogo y cuáles son nuevas.

Uso:
    python scripts/legalize_xref.py "1955/2000"
    python scripts/legalize_xref.py "RD 223/2008"
    python scripts/legalize_xref.py "1955/2000" --add
"""

import sys
import os
import csv
import re
import argparse
from pathlib import Path

# Rutas base
REPO_ROOT   = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CATALOG_PATH = REPO_ROOT / "docs" / "normas_catalog.csv"
LEGALIZE_DIR = Path(os.environ.get("LEGALIZE_DIR", r"D:\legalize-es"))
SEARCH_DIRS  = ["es", "es-an"]


def leer_frontmatter(filepath):
    """Lee el bloque frontmatter YAML de un fichero MD. Devuelve dict."""
    fields = {}
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        if not lines or lines[0].strip() != "---":
            return fields
        for line in lines[1:]:
            if line.strip() == "---":
                break
            # Acepta: clave: valor  o  clave: "valor entre comillas"
            m = re.match(r'^([\w_]+):\s*"?([^"]*)"?\s*$', line)
            if m:
                fields[m.group(1)] = m.group(2).strip()
    except Exception:
        pass
    return fields


def buscar_en_legalize(query):
    """
    Busca query (case-sensitive) en es/ y es-an/.
    Devuelve lista de (Path, frontmatter_dict).
    """
    resultados = []
    for subdir in SEARCH_DIRS:
        d = LEGALIZE_DIR / subdir
        if not d.exists():
            print(f"AVISO: directorio no encontrado: {d}", file=sys.stderr)
            continue
        for md in sorted(d.glob("*.md")):
            try:
                contenido = md.read_text(encoding="utf-8")
                if query in contenido:
                    fm = leer_frontmatter(md)
                    resultados.append((md, fm))
            except Exception:
                pass
    return resultados


def cargar_catalog():
    """
    Carga normas_catalog.csv.
    Devuelve dict {id_tecnico: fila} para búsqueda rápida.
    """
    conocidos = {}
    try:
        with open(CATALOG_PATH, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                id_tec = row.get("id_tecnico", "").strip()
                if id_tec:
                    conocidos[id_tec] = row
    except FileNotFoundError:
        print(f"ERROR: no se encuentra {CATALOG_PATH}", file=sys.stderr)
        sys.exit(1)
    return conocidos


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


def main():
    parser = argparse.ArgumentParser(
        description="Busca referencias cruzadas en legalize-es frente a normas_catalog.csv"
    )
    parser.add_argument("query", help='Cadena a buscar, ej: "1955/2000"')
    parser.add_argument(
        "--add",
        action="store_true",
        help="Añade las normas nuevas al catálogo con estado IDENTIFICADA",
    )
    args = parser.parse_args()

    print(f"\nBuscando: «{args.query}»")
    print(f"Directorios: {', '.join(SEARCH_DIRS)} en {LEGALIZE_DIR}\n")

    resultados = buscar_en_legalize(args.query)
    catalog    = cargar_catalog()

    nuevas        = []
    ya_en_catalog = []

    for path, fm in resultados:
        identifier = fm.get("identifier", path.stem)
        if identifier in catalog:
            ya_en_catalog.append((identifier, fm, catalog[identifier]))
        else:
            nuevas.append((identifier, fm))

    sep = "=" * 64
    print(sep)
    print(
        f"Encontradas: {len(resultados)}"
        f"  |  Ya en catálogo: {len(ya_en_catalog)}"
        f"  |  Nuevas: {len(nuevas)}"
    )
    print(sep)

    if ya_en_catalog:
        print(f"\n-- Ya en catalogo ({len(ya_en_catalog)}) --")
        for identifier, fm, row in ya_en_catalog:
            estado = row.get("estado", "?")
            titulo = fm.get("title", fm.get("referencia", ""))
            print(f"  {identifier:30s}  [{estado:20s}]  {titulo}")

    if nuevas:
        print(f"\n-- Nuevas - no estan en el catalogo ({len(nuevas)}) --")
        for identifier, fm in nuevas:
            titulo = fm.get("title", fm.get("referencia", ""))
            rango  = fm.get("rank", inferir_rango(titulo))
            print(f"  {identifier:30s}  [{rango:20s}]  {titulo}")

        if args.add:
            print(f"\nAñadiendo {len(nuevas)} normas al catálogo…")
            with open(CATALOG_PATH, encoding="utf-8", newline="", mode="a") as f:
                writer = csv.writer(f)
                for identifier, fm in nuevas:
                    titulo  = fm.get("title", fm.get("referencia", ""))
                    source  = fm.get("source", "")
                    # nombre_corto: hasta la primera coma, máx 60 chars
                    nombre_corto = (titulo.split(",")[0] if titulo else identifier)[:60]
                    writer.writerow([
                        "",              # id_ref — rellenar manualmente
                        nombre_corto,
                        "",              # ambito
                        "",              # procedimientos
                        "IDENTIFICADA",
                        identifier,
                        source,
                        "",              # doc_extraccion
                        f"xref:{args.query}",
                    ])
            print(f"  >> Anadidas en {CATALOG_PATH}")
        else:
            print("\n  (Usa --add para añadirlas al catálogo)")
    else:
        print("\nTodos los resultados ya están en el catálogo.")


if __name__ == "__main__":
    main()
