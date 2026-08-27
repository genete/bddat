"""Banco de documentos dummy reutilizables + catálogo de uso (#814).

Produce dos salidas en tests/fixtures/documentos_dummy/:

    <codigo_minuscula>.pdf   Uno por cada tipos_documentos.origen = 'EXTERNO'
        (BDDAT no los genera, solo los recibe; los INTERNO se generan de
        verdad al tramitar, vía ELABORAR/NOTIFICAR + generador_escritos —
        no llevan dummy).

    catalogo_uso.csv         Catálogo COMPLETO (los 78 tipos, no solo los
        EXTERNO con PDF): dónde se usa cada tipo de documento, cruzando dos
        fuentes de catálogo — tramites_tareas_documentos (tipo de documento
        como ENTRADA/SALIDA de una tarea de un trámite) y
        requisitos_documentales (requisito legal de aportación). Formato
        "long": una fila por combinación tipo×uso; un tipo sin ningún uso
        registrado en ninguna de las dos fuentes deja una fila con
        fuente_uso vacío, visible como hueco de catálogo.

Standalone: conecta a BD con psycopg2 directo (mismo patrón que
scripts/reloj_dev.py, #820), sin bootstrap de Flask. No hardcodea la lista
de tipos — si el catálogo cambia, basta con reejecutar.

Uso:
    python scripts/generar_documentos_dummy.py
"""
import csv
import os
import sys

BDDAT_DIR = r"D:\BDDAT"
DESTINO_DIR = os.path.join(BDDAT_DIR, "tests", "fixtures", "documentos_dummy")


def _conectar():
    import psycopg2
    from dotenv import load_dotenv

    load_dotenv(os.path.join(BDDAT_DIR, ".env"))
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("ERROR: DATABASE_URL no configurado (.env)", file=sys.stderr)
        raise SystemExit(1)
    return psycopg2.connect(dsn)


def _obtener_tipos_documentos(cur):
    cur.execute("SELECT id, codigo, nombre, origen FROM tipos_documentos ORDER BY codigo")
    return cur.fetchall()


def _obtener_usos_tramite_tarea(cur):
    """tipo_documento_id -> lista de usos vía tramites_tareas_documentos (catálogo)."""
    cur.execute("""
        SELECT ttd.tipo_documento_id, tt.codigo, tarea.codigo, ttd.orden_tarea, ttd.rol
        FROM tramites_tareas_documentos ttd
        JOIN tipos_tramites tt ON tt.id = ttd.tipo_tramite_id
        JOIN tramites_tareas tta
          ON tta.tipo_tramite_id = ttd.tipo_tramite_id AND tta.orden = ttd.orden_tarea
        JOIN tipos_tareas tarea ON tarea.id = tta.tipo_tarea_id
        WHERE ttd.tipo_documento_id IS NOT NULL
        ORDER BY tt.codigo, ttd.orden_tarea, ttd.rol
    """)
    usos = {}
    for tipo_doc_id, cod_tramite, cod_tarea, orden, rol in cur.fetchall():
        usos.setdefault(tipo_doc_id, []).append({
            'fuente_uso': 'TRAMITE_TAREA',
            'codigo_tramite': cod_tramite,
            'codigo_tipo_tarea': cod_tarea,
            'orden_tarea': orden,
            'rol': rol,
            'norma': '',
            'articulo': '',
            'descripcion_legal': '',
        })
    return usos


def _obtener_usos_requisito_legal(cur):
    """tipo_documento_id -> lista de usos vía requisitos_documentales activos (catálogo)."""
    cur.execute("""
        SELECT rd.tipo_documento_id, rd.descripcion_legal, rd.articulo, n.codigo
        FROM requisitos_documentales rd
        LEFT JOIN normas n ON n.id = rd.norma_id
        WHERE rd.activo = true
        ORDER BY rd.tipo_documento_id, rd.orden
    """)
    usos = {}
    for tipo_doc_id, descripcion, articulo, cod_norma in cur.fetchall():
        usos.setdefault(tipo_doc_id, []).append({
            'fuente_uso': 'REQUISITO_LEGAL',
            'codigo_tramite': '',
            'codigo_tipo_tarea': '',
            'orden_tarea': '',
            'rol': '',
            'norma': cod_norma or '',
            'articulo': articulo or '',
            'descripcion_legal': descripcion or '',
        })
    return usos


def _escribir_csv(tipos, usos_tt, usos_rl, ruta_csv):
    columnas = [
        'codigo_tipo_documento', 'nombre_tipo_documento', 'origen',
        'fuente_uso', 'codigo_tramite', 'codigo_tipo_tarea', 'orden_tarea', 'rol',
        'norma', 'articulo', 'descripcion_legal',
    ]
    fila_vacia = {
        'fuente_uso': '', 'codigo_tramite': '', 'codigo_tipo_tarea': '',
        'orden_tarea': '', 'rol': '', 'norma': '', 'articulo': '', 'descripcion_legal': '',
    }
    total_filas = 0
    with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columnas)
        writer.writeheader()
        for tipo_id, codigo, nombre, origen in tipos:
            filas_tipo = usos_tt.get(tipo_id, []) + usos_rl.get(tipo_id, [])
            if not filas_tipo:
                filas_tipo = [fila_vacia]
            for fila in filas_tipo:
                writer.writerow({
                    'codigo_tipo_documento': codigo,
                    'nombre_tipo_documento': nombre,
                    'origen': origen,
                    **fila,
                })
                total_filas += 1
    print(f"CSV generado: {ruta_csv} ({total_filas} filas, {len(tipos)} tipos)")


def _generar_pdfs(tipos_externos, destino_dir):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    estilos = getSampleStyleSheet()
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=estilos['Heading2'], fontSize=10, spaceAfter=4)
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=13, spaceAfter=6)
    estilo_normal = ParagraphStyle('Normal', parent=estilos['Normal'], fontSize=9, spaceAfter=3)
    estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=7, textColor=colors.grey)

    os.makedirs(destino_dir, exist_ok=True)
    for _tipo_id, codigo, nombre, _origen in tipos_externos:
        ruta = os.path.join(destino_dir, f'{codigo.lower()}.pdf')
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        )
        contenido = [
            Paragraph('Consejería de Industria, Energía y Minas', estilo_subtitulo),
            Paragraph('Junta de Andalucía', estilo_subtitulo),
            Spacer(1, 0.5 * cm),
            Paragraph(nombre.upper(), estilo_titulo),
            Spacer(1, 0.2 * cm),
            Paragraph(f'Código de tipo: {codigo}', estilo_normal),
            Spacer(1, 1 * cm),
            Paragraph(
                'Documento dummy generado para el banco de fixtures de BDDAT (#814). '
                'Contenido ficticio con fines de prueba: reutilizable en cualquier '
                'expediente, sin fecha administrativa ni destino concreto.',
                estilo_normal,
            ),
            Spacer(1, 2 * cm),
            Paragraph(
                'Este documento no tiene validez alguna fuera del entorno de pruebas de BDDAT.',
                estilo_pie,
            ),
        ]
        doc.build(contenido)
    print(f"{len(tipos_externos)} PDFs generados en {destino_dir}")


def main():
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            tipos = _obtener_tipos_documentos(cur)
            usos_tt = _obtener_usos_tramite_tarea(cur)
            usos_rl = _obtener_usos_requisito_legal(cur)
    finally:
        conn.close()

    tipos_externos = [t for t in tipos if t[3] == 'EXTERNO']
    _generar_pdfs(tipos_externos, DESTINO_DIR)

    ruta_csv = os.path.join(DESTINO_DIR, 'catalogo_uso.csv')
    _escribir_csv(tipos, usos_tt, usos_rl, ruta_csv)


if __name__ == '__main__':
    main()
