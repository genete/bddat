"""Patrones de sparse checkout para el clon reducido de legalize-es (#949).

Lo llama `preparar_legalize.sh`. Lee `docs/referencia/normas_catalog.csv` y, por
cada `id_tecnico` que sea un BOE-A-* o un BOJA-b-*, busca ese fichero en el clon
(en `es/` o en `es-an/`, mirando el árbol de git: no hace falta haber descargado
ningún blob). Escribe por la salida estándar los patrones para
`git sparse-checkout set --no-cone --stdin`:

    /es-an/
    /es/fa/BOE-A-2000-24019.md
    ...

y por la salida de error el resumen de qué ids no están en el clon.

Layout de legalize-es (manifiesto `.legalize.yml`, spec 0.4): los ficheros no
cuelgan de la carpeta de jurisdicción, sino de una subcarpeta con los dos
primeros hex del SHA-1 del identificador: `{es|es-an}/{sha1(id)[:2]}/{id}.md`.
El script NO calcula ese prefijo: localiza cada id por nombre de fichero en el
árbol, así que sigue valiendo si el reparto cambia otra vez. Lo que sí vigila es
que el reparto no se le haya escapado: si no encuentra ningún id del catálogo
sale con error (código 1) y sin patrones, enseñando qué rutas ve, en lugar de
dejar un clon casi vacío con un mensaje de «0 de N» que pasa inadvertido.

Uso:
    python scripts/nube/legalize_patrones.py <clon>
"""
import csv
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[2]
CATALOGO = REPO / "docs" / "referencia" / "normas_catalog.csv"
PREFIJOS = ("BOE-A-", "BOJA-b-")
CARPETAS = ("es", "es-an")
# es-an/ se baja entero (patrón recursivo): sus ficheros no necesitan patrón propio.
CARPETA_COMPLETA = "es-an"


def ids_del_catalogo():
    with CATALOGO.open(encoding="utf-8", newline="") as f:
        ids = [fila["id_tecnico"].strip() for fila in csv.DictReader(f)]
    return sorted({i for i in ids if i.startswith(PREFIJOS)})


def ficheros_del_clon(clon):
    """Rutas `.md` de es/ y es-an/ en el árbol de HEAD, a cualquier profundidad."""
    salida = subprocess.run(
        ["git", "-C", str(clon), "ls-tree", "-r", "--name-only", "HEAD", *CARPETAS],
        check=True, capture_output=True, text=True,
    ).stdout
    return [r for r in salida.splitlines() if r.endswith(".md")]


def indexar(rutas):
    """{(carpeta, id): ruta}; el id es el nombre del fichero sin extensión."""
    return {
        (PurePosixPath(r).parts[0], PurePosixPath(r).stem): r
        for r in rutas
    }


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ids = ids_del_catalogo()
    rutas = ficheros_del_clon(sys.argv[1])
    if not rutas:
        sys.exit(
            f"legalize_patrones: el árbol de {sys.argv[1]} no tiene ningún .md en "
            f"{' ni '.join(CARPETAS)}/; ¿clon vacío o carpetas renombradas?"
        )
    indice = indexar(rutas)

    patrones = [f"/{CARPETA_COMPLETA}/"]
    ausentes = []
    for id_tecnico in ids:
        for carpeta in CARPETAS:
            ruta = indice.get((carpeta, id_tecnico))
            if ruta:
                if carpeta != CARPETA_COMPLETA:
                    patrones.append(f"/{ruta}")
                break
        else:
            ausentes.append(id_tecnico)

    encontrados = len(ids) - len(ausentes)
    resumen = (
        f"legalize_patrones: {encontrados} de {len(ids)} ids del catálogo "
        f"están en el clon; ausentes: {', '.join(ausentes) or 'ninguno'}"
    )
    if ids and not encontrados:
        sys.exit(
            f"{resumen}\n"
            f"  El árbol tiene {len(rutas)} ficheros .md en {'/'.join(CARPETAS)}; "
            f"ejemplos: {', '.join(rutas[:3])}\n"
            "  Ningún id del catálogo coincide con el nombre de ninguno: revisar si "
            "legalize-es cambió el nombre de los ficheros o el catálogo "
            "(docs/referencia/normas_catalog.csv)."
        )

    print("\n".join(patrones))
    print(resumen, file=sys.stderr)


if __name__ == "__main__":
    main()
