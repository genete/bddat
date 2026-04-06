#!/usr/bin/env python3
"""
Extrae artículos y disposiciones de sedeboja (BOJA consolidado) sin navegador.

Uso:
  python scripts/sedeboja_extract.py {ID} --indice
  python scripts/sedeboja_extract.py {ID} "artículo 1" "artículo 2"
  python scripts/sedeboja_extract.py {ID} "disposición adicional única"
  python scripts/sedeboja_extract.py {ID} --todo
  python scripts/sedeboja_extract.py {ID} --guardar   (--todo + persiste en docs/normas/)

El ID es el recursoLegalAbstractoId numérico de sedeboja (columna «ID técnico» en
docs/NORMATIVA_LEGISLACION_AT.md §6).

Flujo interno (sin navegador, sin JavaScript):
  1. curl render_portlet → extrae título, URL del iframe y versión (~14 KB)
  2. curl iframe URL     → HTML estático con el texto consolidado
  3. Parse div id="ART{N}" / "DA..." / "DT..." / "DD..." / "DF..." para extraer secciones
"""

import sys
import os
import re
import html as html_lib
import urllib.request
import unicodedata
from datetime import date

PORTLET_URL = (
    "https://ws040.juntadeandalucia.es/sedeboja/c/portal/render_portlet"
    "?p_l_id=22228"
    "&p_p_id=resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet"
    "&p_p_lifecycle=0"
    "&_resumenrecursolegal_WAR_sedebojatextoconsolidadoportlet_recursoLegalAbstractoId={id}"
)

UA = "Mozilla/5.0 (compatible; sedeboja_extract/1.0)"

# Directorio de normas persistidas, relativo a la raíz del repo
NORMAS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "docs", "normas")


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace")


def get_all(norm_id):
    """
    Devuelve (portlet_html, iframe_url, text_html).
    Lanza RuntimeError si no encuentra iframe.
    """
    portlet_html = fetch(PORTLET_URL.format(id=norm_id))
    m = re.search(r'iframe[^>]+src="([^"]+)"', portlet_html)
    if not m:
        raise RuntimeError(
            f"No se encontró iframe en portlet para ID={norm_id}. "
            "Verifica que el ID es correcto y la norma tiene versión consolidada."
        )
    iframe_url = m.group(1).replace("\\", "/")
    return portlet_html, iframe_url, fetch(iframe_url)


# ---------------------------------------------------------------------------
# Metadatos desde portlet e iframe URL
# ---------------------------------------------------------------------------

def get_title(portlet_html):
    """Extrae el título completo de la norma del portlet."""
    # El span (no label) con versiotitulo en el id contiene "fecha - CONSOLIDADA - título"
    m = re.search(r'<span[^>]+versiotitulo[^>]*>([^<]+)<', portlet_html)
    if m:
        raw = html_lib.unescape(m.group(1).strip())
        parts = raw.split(" - ", 2)
        return parts[-1].strip() if len(parts) >= 3 else raw
    return None


def get_version_date(iframe_url):
    """Extrae la fecha de versión consolidada de la URL del iframe: .../con/20240217/..."""
    m = re.search(r'/con/(\d{4})(\d{2})(\d{2})/', iframe_url)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


# ---------------------------------------------------------------------------
# Índice de secciones
# ---------------------------------------------------------------------------

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
    anchor_to_title = {}
    for m in re.finditer(r'href="#(I\d+)"[^>]*>([^<]{1,120})', text_html):
        anchor_to_title[m.group(1)] = m.group(2).strip()

    anchor_positions = {}
    for m in re.finditer(r'id="(I\d+)"', text_html):
        anchor_positions[m.group(1)] = m.start()

    div_positions = {}
    for m in re.finditer(r'<div id="([A-Z][A-Z0-9]+)"', text_html):
        div_positions[m.group(1)] = m.start()

    entries = []
    for anchor, title in anchor_to_title.items():
        if anchor not in anchor_positions:
            continue
        apos = anchor_positions[anchor]
        best_div = None
        best_dist = 999999
        for div_id, dpos in div_positions.items():
            if 0 <= dpos - apos < 300:
                if dpos - apos < best_dist:
                    best_dist = dpos - apos
                    best_div = div_id
        if best_div:
            entries.append((best_div, title, div_positions[best_div]))

    seen = set()
    unique = []
    for e in sorted(entries, key=lambda x: x[2]):
        if e[0] not in seen:
            seen.add(e[0])
            unique.append(e)

    # Aliases semánticos para divs no mapeados por el índice
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
# Extracción de texto
# ---------------------------------------------------------------------------

def _clean(html_segment):
    """Convierte HTML a markdown preservando párrafos y encabezados."""
    s = html_segment
    # Eliminar anclas vacías de referencia cruzada (<li class="AN">, <a class="AN">)
    s = re.sub(r'<li\s+class="AN"[^>]*>.*?</li>', "", s, flags=re.DOTALL)
    s = re.sub(r'<li\s+class="AN"[^>]*/?>',       "", s)
    # Notas editoriales (modificaciones, vigencias) → bloque separado con prefijo >
    s = re.sub(r'<div[^>]+class="ccn[^"]*"[^>]*>(.*?)</div>',
               lambda m: f"\n\n> {re.sub(r'<[^>]+>', '', m.group(1)).strip()}\n\n",
               s, flags=re.DOTALL)
    # Encabezados → markdown
    def _h(m):
        level = int(m.group(1))
        inner = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        return f"\n\n{'#' * (level + 2)} {inner}\n\n"
    s = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>", _h, s, flags=re.DOTALL)
    # Listas: solo <li> reales (sin class="AN", ya eliminados arriba)
    s = re.sub(r"<li[^>]*>", "\n- ", s)
    s = re.sub(r"</li>", "\n", s)
    # Saltos de línea explícitos
    s = re.sub(r"<br\s*/?>", "\n", s)
    # Párrafos → doble salto
    s = re.sub(r"<p[^>]*>", "", s)
    s = re.sub(r"</p>", "\n\n", s)
    # Eliminar tags restantes
    s = re.sub(r"<[^>]+>", "", s)
    s = html_lib.unescape(s)
    # Limpiar espacios dentro de cada línea sin colapsar saltos de párrafo
    lines = [re.sub(r" +", " ", line).strip() for line in s.split("\n")]
    s = "\n".join(lines)
    # Máximo dos saltos consecutivos
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def _div_text(text_html, div_id, next_div_id=None):
    """Extrae el innerText del div id=div_id hasta el inicio de next_div_id."""
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
    return _clean(text_html[start:end])


def _intro_text(text_html, index):
    """
    Extrae la exposición de motivos: texto dentro de dTxT antes del primer div del índice.
    """
    dtxt_marker = '<div id="dTxT"'
    dtxt_start = text_html.find(dtxt_marker)
    if dtxt_start < 0:
        return None

    # Fin de la intro = inicio del primer div del índice
    if index:
        first_div_marker = f'<div id="{index[0][0]}"'
        intro_end = text_html.find(first_div_marker, dtxt_start)
        if intro_end < 0:
            intro_end = dtxt_start + 500  # fallback
    else:
        intro_end = dtxt_start + 500

    segment = text_html[dtxt_start:intro_end]
    text = _clean(segment)
    # Quitar el propio id del div del texto limpio
    text = re.sub(r'^dTxT\s*', '', text).strip()
    return text if len(text) > 50 else None


def extract_structured(text_html):
    """
    Extrae el texto completo con cabeceras ## por sección.
    Incluye exposición de motivos si existe.
    Devuelve string markdown.
    """
    index = build_index(text_html)
    parts = []

    intro = _intro_text(text_html, index)
    if intro:
        parts.append(f"## Exposición de motivos\n\n{intro}")

    for i, (div_id, title, _) in enumerate(index):
        next_div = index[i + 1][0] if i + 1 < len(index) else None
        text = _div_text(text_html, div_id, next_div)
        if text:
            parts.append(f"## {title}\n\n{text}")

    return "\n\n---\n\n".join(parts)


def extract_sections(text_html, queries):
    """Extrae secciones concretas por nombre."""
    index = build_index(text_html)
    norm_map = {normalize(title): (div_id, title, pos) for div_id, title, pos in index}
    for div_id, title, pos in index:
        canonical = _decode_div_id(div_id)
        if canonical:
            alias_key = normalize(canonical)
            if alias_key not in norm_map:
                norm_map[alias_key] = (div_id, canonical, pos)

    results = []
    for query in queries:
        nq = normalize(query)
        match = norm_map.get(nq)
        if not match:
            candidates = [(k, v) for k, v in norm_map.items() if nq in k or k in nq]
            if candidates:
                candidates.sort(key=lambda x: len(x[0]))
                match = candidates[0][1]
        if not match:
            results.append(f"**{query}**: No encontrado en el índice.")
            continue

        div_id, title, _ = match
        idx_pos = next((i for i, e in enumerate(index) if e[0] == div_id), None)
        next_div = index[idx_pos + 1][0] if idx_pos is not None and idx_pos + 1 < len(index) else None
        text = _div_text(text_html, div_id, next_div)
        if text:
            results.append(f"## {title}\n\n{text}")
        else:
            results.append(f"**{query}**: div id={div_id} no encontrado en el HTML.")

    return results


# ---------------------------------------------------------------------------
# Persistencia en docs/normas/
# ---------------------------------------------------------------------------

def build_frontmatter(norm_id, title, version_date, iframe_url):
    today = date.today().isoformat()
    lines = ["---"]
    if title:
        lines.append(f'referencia: "{title}"')
    lines.append(f"sedeboja_id: {norm_id}")
    if version_date:
        lines.append(f"version_consolidada: {version_date}")
    lines.append(f"extraido: {today}")
    lines.append(f'iframe_url: "{iframe_url}"')
    lines.append("---")
    return "\n".join(lines)


def save_norm(norm_id, title, version_date, iframe_url, body):
    """Guarda la norma en docs/normas/sedeboja_{ID}.md"""
    os.makedirs(NORMAS_DIR, exist_ok=True)
    path = os.path.join(NORMAS_DIR, f"sedeboja_{norm_id}.md")
    frontmatter = build_frontmatter(norm_id, title, version_date, iframe_url)
    heading = f"# {title}" if title else f"# sedeboja {norm_id}"
    content = f"{frontmatter}\n\n{heading}\n\n{body}\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def print_index(text_html, norm_id, iframe_url):
    index = build_index(text_html)
    print(f"# Índice — sedeboja ID={norm_id}")
    print(f"# Fuente: {iframe_url}\n")
    for div_id, title, _ in index:
        print(f"  {div_id:20} {title}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    norm_id = sys.argv[1]
    args = sys.argv[2:]

    try:
        portlet_html, iframe_url, text_html = get_all(norm_id)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not args or "--indice" in args:
        print_index(text_html, norm_id, iframe_url)
        return

    if "--guardar" in args or "--todo" in args:
        body = extract_structured(text_html)
        if "--guardar" in args:
            title = get_title(portlet_html)
            version_date = get_version_date(iframe_url)
            path = save_norm(norm_id, title, version_date, iframe_url, body)
            print(f"Guardado: {path}", file=sys.stderr)
        print(body)
        return

    sections = extract_sections(text_html, args)
    for s in sections:
        print(s)
        print()


if __name__ == "__main__":
    main()
