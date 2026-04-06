#!/usr/bin/env python3
"""
Extrae artículos y disposiciones de sedeboja (BOJA consolidado) sin navegador.

Uso:
  python tools/sedeboja_extract.py {ID} --indice
  python tools/sedeboja_extract.py {ID} "artículo 1" "artículo 2"
  python tools/sedeboja_extract.py {ID} "disposición adicional primera"
  python tools/sedeboja_extract.py {ID} --todo

El ID es el recursoLegalAbstractoId numérico de sedeboja (columna «ID técnico» en
docs/NORMATIVA_LEGISLACION_AT.md §6).

Flujo interno (sin navegador, sin JavaScript):
  1. curl render_portlet → extrae URL del iframe embebido (~14 KB)
  2. curl iframe URL     → HTML estático con el texto consolidado
  3. Parse div id="ART{N}" / "DA..." / "DT..." / "DD..." / "DF..." para extraer secciones
"""

import sys
import re
import html as html_lib
import urllib.request
import unicodedata

PORTLET_URL = (
    "https://ws040.juntadeandalucia.es/sedeboja/c/portal/render_portlet"
    "?p_l_id=22228"
    "&p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet"
    "&p_p_lifecycle=0"
    "&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId={id}"
)

UA = "Mozilla/5.0 (compatible; sedeboja_extract/1.0)"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def get_text_html(norm_id):
    """Devuelve (iframe_url, html_texto). Lanza RuntimeError si no encuentra iframe."""
    portlet_html = fetch(PORTLET_URL.format(id=norm_id))
    m = re.search(r'iframe[^>]+src="([^"]+)"', portlet_html)
    if not m:
        raise RuntimeError(
            f"No se encontró iframe en portlet para ID={norm_id}. "
            "Verifica que el ID es correcto y la norma tiene versión consolidada."
        )
    url = m.group(1).replace("\\", "/")
    return url, fetch(url)


# ---------------------------------------------------------------------------
# Índice de secciones
# ---------------------------------------------------------------------------

# Mapeo: patrón div id → descripción legible
# Los IDs siguen el esquema: ART{N}, DA{ORDINAL|UNICA}, DT{...}, DD{...}, DF{N|ORDINAL|UNICA}
_ORDINALS = {
    "primera": 1, "segunda": 2, "tercera": 3, "cuarta": 4, "quinta": 5,
    "sexta": 6, "séptima": 7, "octava": 8, "novena": 9, "décima": 10,
    "undécima": 11, "duodécima": 12, "unica": 0, "única": 0,
}


def normalize(s):
    """Normaliza string para comparaciones: minúsculas, sin tildes, sin puntuación."""
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def build_index(text_html):
    """
    Devuelve lista de (div_id, título, posición_en_html) ordenada por posición.
    Extrae los títulos del índice (href="#I{N}") y los correlaciona con los div ids.
    """
    # Mapa anchor I{N} → título (del índice de navegación)
    anchor_to_title = {}
    for m in re.finditer(r'href="#(I\d+)"[^>]*>([^<]{1,120})', text_html):
        anchor_to_title[m.group(1)] = m.group(2).strip()

    # Posición de cada anchor I{N} en el texto
    anchor_positions = {}
    for m in re.finditer(r'id="(I\d+)"', text_html):
        anchor_positions[m.group(1)] = m.start()

    # Div ids con sus posiciones
    div_positions = {}
    for m in re.finditer(r'<div id="([A-Z][A-Z0-9]+)"', text_html):
        div_positions[m.group(1)] = m.start()

    # Para cada entrada del índice, buscar el div más cercano (justo después del anchor)
    entries = []
    for anchor, title in anchor_to_title.items():
        if anchor not in anchor_positions:
            continue
        apos = anchor_positions[anchor]
        # Buscar el div que sigue inmediatamente (dentro de 300 chars)
        best_div = None
        best_dist = 999999
        for div_id, dpos in div_positions.items():
            if 0 <= dpos - apos < 300:
                if dpos - apos < best_dist:
                    best_dist = dpos - apos
                    best_div = div_id
        if best_div:
            entries.append((best_div, title, div_positions[best_div]))

    # Eliminar duplicados (mismo div_id, quedar con el primero por posición)
    seen = set()
    unique = []
    for e in sorted(entries, key=lambda x: x[2]):
        if e[0] not in seen:
            seen.add(e[0])
            unique.append(e)

    # Añadir entradas derivadas de los div ids semánticos que no estén en el índice
    # (ej: DADICUNICA → "Disposición adicional única", que el índice puede poner
    #  como "DISPOSICIONES ADICIONALES" sin permitir match exacto)
    div_ids_in_index = {e[0] for e in unique}
    for div_id, dpos in sorted(div_positions.items(), key=lambda x: x[1]):
        if div_id in div_ids_in_index:
            continue
        canonical = _decode_div_id(div_id)
        if canonical:
            unique.append((div_id, canonical, dpos))

    return sorted(unique, key=lambda x: x[2])


def _decode_div_id(div_id):
    """Decodifica IDs semánticos como DADICUNICA → 'Disposición adicional única'."""
    _ord_map = {
        "UNICA": "única", "PRIMERA": "primera", "SEGUNDA": "segunda",
        "TERCERA": "tercera", "CUARTA": "cuarta", "QUINTA": "quinta",
        "SEXTA": "sexta", "SEPTIMA": "séptima", "OCTAVA": "octava",
    }
    if div_id.startswith("ART") and div_id[3:].isdigit():
        return f"Artículo {div_id[3:]}"
    if div_id.startswith("DADIC"):
        suf = div_id[5:]
        return f"Disposición adicional {_ord_map.get(suf, suf.lower())}"
    if div_id.startswith("DTRANS"):
        suf = div_id[6:]
        return f"Disposición transitoria {_ord_map.get(suf, suf.lower())}"
    if div_id.startswith("DDER"):
        suf = div_id[4:]
        return f"Disposición derogatoria {_ord_map.get(suf, suf.lower())}"
    if div_id.startswith("DFIN") and div_id[4:].isdigit():
        nums = {"1": "primera", "2": "segunda", "3": "tercera", "4": "cuarta", "5": "quinta"}
        return f"Disposición final {nums.get(div_id[4:], div_id[4:])}"
    return None


# ---------------------------------------------------------------------------
# Extracción de secciones
# ---------------------------------------------------------------------------

def _div_text(text_html, div_id, next_div_id=None):
    """Extrae el innerText del div id=div_id hasta el inicio de next_div_id."""
    # str.find evita problemas de re en Windows cp1252 con Python 3.14
    marker = f'<div id="{div_id}"'
    start = text_html.find(marker)
    if start < 0:
        return None

    if next_div_id:
        end_marker = f'<div id="{next_div_id}"'
        end = text_html.find(end_marker, start + len(marker))
        if end < 0:
            end = len(text_html)
    else:
        end = len(text_html)

    segment = text_html[start:end]
    # Limpiar HTML
    clean = re.sub(r"<[^>]+>", " ", segment)
    clean = html_lib.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def extract_sections(text_html, queries):
    """
    Extrae secciones por nombre. queries es lista de strings como
    ["artículo 1", "disposición adicional única", "disposición final primera"].
    Devuelve lista de strings markdown.
    """
    index = build_index(text_html)
    # Construir mapa normalizado → (div_id, título, posición)
    norm_map = {normalize(title): (div_id, title, pos) for div_id, title, pos in index}
    # Añadir aliases semánticos derivados del div_id (ej: DADICUNICA → "disposicion adicional unica")
    for div_id, title, pos in index:
        canonical = _decode_div_id(div_id)
        if canonical:
            alias_key = normalize(canonical)
            if alias_key not in norm_map:
                norm_map[alias_key] = (div_id, canonical, pos)

    results = []
    for query in queries:
        nq = normalize(query)
        # Búsqueda exacta
        match = norm_map.get(nq)
        # Búsqueda parcial si no hay exacta
        if not match:
            candidates = [(k, v) for k, v in norm_map.items() if nq in k or k in nq]
            if candidates:
                # Preferir el más corto (más específico)
                candidates.sort(key=lambda x: len(x[0]))
                match = candidates[0][1]
        if not match:
            results.append(f"**{query}**: No encontrado en el índice.")
            continue

        div_id, title, pos = match
        # Siguiente sección en el índice
        idx_pos = next((i for i, e in enumerate(index) if e[0] == div_id), None)
        next_div = index[idx_pos + 1][0] if idx_pos is not None and idx_pos + 1 < len(index) else None

        text = _div_text(text_html, div_id, next_div)
        if text:
            results.append(f"## {title}\n\n{text}")
        else:
            results.append(f"**{query}**: div id={div_id} no encontrado en el HTML del texto.")

    return results


def print_index(text_html, norm_id, iframe_url):
    index = build_index(text_html)
    print(f"# Índice — sedeboja ID={norm_id}")
    print(f"# Fuente: {iframe_url}\n")
    for div_id, title, _ in index:
        print(f"  {div_id:20} {title}")


def extract_all(text_html):
    """Extrae el texto completo del div dTxT."""
    m = re.search(r'<div id="dTxT"', text_html)
    if not m:
        return None
    start = m.start()
    clean = re.sub(r"<[^>]+>", " ", text_html[start:])
    clean = html_lib.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    norm_id = sys.argv[1]
    args = sys.argv[2:]

    try:
        iframe_url, text_html = get_text_html(norm_id)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not args or "--indice" in args:
        print_index(text_html, norm_id, iframe_url)
        return

    if "--todo" in args:
        result = extract_all(text_html)
        if result:
            print(result)
        else:
            print("No se encontró div dTxT.", file=sys.stderr)
        return

    sections = extract_sections(text_html, args)
    for s in sections:
        print(s)
        print()


if __name__ == "__main__":
    main()
