#!/usr/bin/env python3
"""
Extrae el índice o bloques (artículos, disposiciones...) de la legislación
consolidada del BOE por la API de datos abiertos, sin navegador. Análogo a
sedeboja_extract.py, pero para normas estatales.

Uso:
  python scripts/boe_extract.py {BOE-ID} --indice
  python scripts/boe_extract.py {BOE-ID} a115
  python scripts/boe_extract.py {BOE-ID} a115 a116 daprimera

El BOE-ID (BOE-A-AAAA-NNNNN) es la columna «id_tecnico» de
docs/referencia/normas_catalog.csv. Los id_bloque son los del índice (a52,
a59bis, daprimera, ti...); ver .claude/skills/boe/SKILL.md.

De cada bloque imprime solo la versión más reciente, en texto plano. La API exige
la cabecera Accept: application/xml.
"""

import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

API = "https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{id}/texto/{ruta}"
UA = "Mozilla/5.0 (compatible; boe_extract/1.0)"


def obtener_xml(boe_id, ruta):
    req = urllib.request.Request(
        API.format(id=boe_id, ruta=ruta),
        headers={"Accept": "application/xml", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return ET.fromstring(r.read())


def indice(boe_id):
    root = obtener_xml(boe_id, "indice")
    for b in root.findall(".//bloque"):
        print(f"{(b.findtext('id') or ''):20} {b.findtext('titulo') or ''}")


def bloque(boe_id, id_bloque):
    root = obtener_xml(boe_id, f"bloque/{id_bloque}")
    b = root.find(".//bloque")
    if b is None or not b.findall("version"):
        raise RuntimeError(f"la respuesta no trae ningún bloque «{id_bloque}»")
    ultima = b.findall("version")[-1]
    vigencia = ultima.get("fecha_vigencia") or ultima.get("fecha_publicacion")
    lineas = [f"# {b.get('titulo', '')}", f"*Vigente desde: {vigencia}*", ""]
    for elem in ultima:
        if elem.tag == "blockquote":  # notas al pie
            continue
        texto = "".join(elem.itertext()).strip()
        if not texto:
            continue
        clase = elem.get("class", "")
        if clase == "articulo":
            lineas.append(f"## {texto}")
        elif clase == "parrafo_2":
            lineas.append(f"  {texto}")
        else:
            lineas.append(texto)
        lineas.append("")
    print("\n".join(lineas))


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.exit(__doc__)
    boe_id, pedidos = args[0], args[1:]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if pedidos == ["--indice"]:
            indice(boe_id)
        else:
            for id_bloque in pedidos:
                bloque(boe_id, id_bloque)
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR: HTTP {e.code} de la API del BOE (¿BOE-ID o id_bloque incorrectos?)")
    except (urllib.error.URLError, ET.ParseError, RuntimeError) as e:
        sys.exit(f"ERROR: {e}")


if __name__ == "__main__":
    main()
