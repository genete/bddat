#!/usr/bin/env python3
"""
Busca una norma en sedeboja y devuelve su ID técnico (recursoLegalAbstractoId).

Uso:
  python scripts/sedeboja_buscar.py "Decreto 550/2022"
  python scripts/sedeboja_buscar.py "Ley 7/2021"
  python scripts/sedeboja_buscar.py "356/2010"
"""

import sys
import re
import html as html_lib
import urllib.request
import urllib.parse

UA = "Mozilla/5.0 (compatible; sedeboja_buscar/1.0)"

SEARCH_URL = (
    "https://ws040.juntadeandalucia.es/sedeboja/web/textos-consolidados/inicio"
    "?p_p_id=buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet"
    "&p_p_lifecycle=0"
    "&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet__facesViewIdRender="
    "%2Fviews%2Frecurso-legal%2Fpublic-search-basic-founds.xhtml"
    "&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_texto={query}"
    "&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloTitulo=false"
    "&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloConsolidada=false"
    "&_buscarpublicarecursolegal_WAR_sedebojatextoconsolidadoportlet_soloVigente=false"
)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def buscar(query):
    url = SEARCH_URL.format(query=urllib.parse.quote(query))
    html = fetch(url)

    # Cada resultado tiene: >Título</label>{titulo}</div> ... value : '{id}'
    resultados = []
    for bloque in re.finditer(r'panel-resultado-titulo.*?value\s*:\s*\'(\d+)\'', html, re.DOTALL):
        texto = bloque.group(0)
        id_ = bloque.group(1)
        # Título: texto entre >Título</label> y el siguiente <
        m_titulo = re.search(r'>T[íi]tulo</label>([^<]+)', texto)
        titulo = html_lib.unescape(m_titulo.group(1).strip()) if m_titulo else "(sin título)"
        # Fecha
        m_fecha = re.search(r'>Fecha Texto</label>([^<]+)', texto)
        fecha = m_fecha.group(1).strip() if m_fecha else ""
        resultados.append((id_, fecha, titulo))

    return resultados


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Buscando: {query}\n")

    try:
        resultados = buscar(query)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not resultados:
        print("Sin resultados.")
        return

    for id_, fecha, titulo in resultados:
        print(f"ID: {id_}  ({fecha})")
        print(f"    {titulo}")
        print()


if __name__ == "__main__":
    main()
