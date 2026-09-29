"""Patrones de sparse checkout para el clon reducido de legalize-es (#949).

Lo llama `preparar_legalize.sh`. Lee `docs/referencia/normas_catalog.csv` y, por
cada `id_tecnico` que sea un BOE-A-* o un BOJA-b-*, comprueba si el clon tiene
ese fichero (en `es/` o en `es-an/`, mirando el árbol de git: no hace falta
haber descargado ningún blob). Escribe por la salida estándar los patrones para
`git sparse-checkout set --no-cone --stdin`:

    /es-an/
    /es/BOE-A-2013-13645.md
    ...

y por la salida de error el resumen de qué ids no están en el clon.

Uso:
    python scripts/nube/legalize_patrones.py <clon>
"""
import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CATALOGO = REPO / "docs" / "referencia" / "normas_catalog.csv"
PREFIJOS = ("BOE-A-", "BOJA-b-")
CARPETAS = ("es", "es-an")


def ids_del_catalogo():
    with CATALOGO.open(encoding="utf-8", newline="") as f:
        ids = [fila["id_tecnico"].strip() for fila in csv.DictReader(f)]
    return sorted({i for i in ids if i.startswith(PREFIJOS)})


def ficheros_del_clon(clon):
    salida = subprocess.run(
        ["git", "-C", str(clon), "ls-tree", "-r", "--name-only", "HEAD", *CARPETAS],
        check=True, capture_output=True, text=True,
    ).stdout
    return set(salida.splitlines())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ids = ids_del_catalogo()
    en_clon = ficheros_del_clon(sys.argv[1])

    patrones = ["/es-an/"]
    ausentes = []
    for id_tecnico in ids:
        for carpeta in CARPETAS:
            ruta = f"{carpeta}/{id_tecnico}.md"
            if ruta in en_clon:
                patrones.append(f"/{ruta}")
                break
        else:
            ausentes.append(id_tecnico)

    print("\n".join(patrones))
    print(
        f"legalize_patrones: {len(ids) - len(ausentes)} de {len(ids)} ids del catálogo "
        f"están en el clon; ausentes: {', '.join(ausentes) or 'ninguno'}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
