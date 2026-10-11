"""Documentos dummy para los expedientes-tipo y la semilla + catálogo de uso (#814, #929).

Tiene tres usos:

1. `pdf_dummy(tipo, variante=None)`: devuelve los bytes de un PDF dummy de un tipo de
   documento. Es lo que importan `scripts/expedientes_dummy/_comun.py` y la semilla de
   tests para subir un documento por la vía real. **Los PDF ya no se versionan**: se
   construyen en el momento a partir del nombre y el origen del tipo (ver
   `tests/fixtures/documentos_dummy/README.md` para el porqué). Con `invariant=1` de
   reportlab el resultado es idéntico byte a byte en cada ejecución, así que su hash es
   estable y el aviso «este fichero ya está en el expediente» (ADR-050) se comporta
   igual que con ficheros fijos.

   Los EXTERNO simulan aportación de terceros (BDDAT no los genera, solo los recibe). Los
   INTERNO simulan lo que en tramitación real produce el motor de escritos
   (ELABORAR/NOTIFICAR + generador_escritos): sirven para avanzar expedientes de prueba
   sin pasar por el generador real, pero NO sustituyen probarlo de verdad; el propio PDF
   lo deja dicho en su aviso.

2. Sin argumentos: regenera `tests/fixtures/documentos_dummy/catalogo_uso.csv`, lo único
   que sigue versionado de aquella carpeta. Es documentación: dónde se usa cada tipo de
   documento, cruzando dos fuentes de catálogo —tramites_tareas_documentos (tipo de
   documento como ENTRADA/SALIDA de una tarea de un trámite) y requisitos_documentales
   (requisito legal de aportación)—. Formato «long»: una fila por combinación tipo×uso; un
   tipo sin ningún uso registrado en ninguna de las dos fuentes deja una fila con
   fuente_uso vacío, visible como hueco de catálogo. **Regenerarlo desde el PC**: el orden
   de clasificación de Postgres en Linux cambia unas 200 líneas respecto al de Windows.

3. `--volcar [RUTA]`: escribe en disco un PDF por cada tipo de documento (y por cada
   variante), para cuando una persona necesita un fichero real que subir a mano en el
   navegador. Sin RUTA, a `docs_prueba/documentos_dummy/` (ya ignorada por git); la RUTA
   puede ser absoluta o relativa al directorio desde el que se ejecuta. Siempre
   sobrescribe y nunca borra nada de la carpeta: una ruta mal puesta no destruye ficheros
   ajenos.

Standalone: conecta a BD con psycopg2 directo (mismo patrón que scripts/reloj_dev.py,
#820), sin bootstrap de Flask; las dos salidas leen la lista de tipos del catálogo, nada
está escrito a mano. Importarlo no tiene efectos: reportlab y psycopg2 se importan dentro
de las funciones que los usan.

Uso:
    python scripts/generar_documentos_dummy.py                  # catalogo_uso.csv
    python scripts/generar_documentos_dummy.py --volcar         # PDF a docs_prueba/documentos_dummy/
    python scripts/generar_documentos_dummy.py --volcar /tmp/pdf_dummy
"""
import argparse
import csv
import io
import os
import sys
from collections import namedtuple

# La raíz del repositorio, no una ruta fija: el script tiene que poder correr
# también en la nube (Linux), donde no existe D:\BDDAT. En el PC es la misma.
BDDAT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Donde vive el catálogo de uso (lo único versionado) y su README.
DESTINO_DIR = os.path.join(BDDAT_DIR, "tests", "fixtures", "documentos_dummy")

# Adonde va `--volcar` sin ruta: ignorado por git, nunca versionado.
VOLCADO_POR_DEFECTO = os.path.join(BDDAT_DIR, "docs_prueba", "documentos_dummy")

# Lo único que `pdf_dummy` necesita de un tipo. En los consumidores es el `TipoDocumento`
# de la BD (tiene los tres atributos); aquí, una fila del catálogo.
TipoDummy = namedtuple('TipoDummy', 'codigo nombre origen')


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


_AVISOS_ORIGEN = {
    'EXTERNO': (
        'Documento dummy generado para el banco de fixtures de BDDAT (#814). '
        'Tipo EXTERNO — BDDAT no lo genera, solo lo recibe del interesado u '
        'organismo. Contenido ficticio con fines de prueba: reutilizable en '
        'cualquier expediente, sin fecha administrativa ni destino concreto.'
    ),
    'INTERNO': (
        'Documento dummy generado para el banco de fixtures de BDDAT (#814). '
        'Tipo INTERNO — en tramitación real este documento lo produce el '
        'motor de escritos (ELABORAR/NOTIFICAR + generador_escritos), no '
        'BDDAT en frío. Esta versión es una simulación para avanzar '
        'expedientes de prueba sin pasar por el generador real: NO sirve '
        'para probar el motor de escritos en sí.'
    ),
    'AMBOS': (
        'Documento dummy generado para el banco de fixtures de BDDAT (#814). '
        'Origen sin clasificar en el catálogo (AMBOS). Contenido ficticio '
        'con fines de prueba, sin fecha administrativa ni destino concreto.'
    ),
}


# Variantes de un tipo (#903): el mismo tipo con otro contenido, para el escenario que
# necesita dos documentos distintos del mismo tipo —el reformado del proyecto técnico—.
# {(código de tipo, variante): (título, línea que sigue al código)}.
VARIANTES = {
    ('DOC_PROYECTO', 'reformado'): (
        'REFORMADO DE PROYECTO TÉCNICO',
        'Segunda versión del proyecto técnico presentada por el titular.',
    ),
}


def nombre_fichero(tipo, variante=None):
    """Nombre del fichero de un documento dummy: `<codigo>.pdf`, o
    `<codigo>_<variante>.pdf`. Es el que ve el expediente al subirlo y el que escribe
    `--volcar`."""
    sufijo = f'_{variante}' if variante else ''
    return f'{tipo.codigo.lower()}{sufijo}.pdf'


def pdf_dummy(tipo, variante=None):
    """Bytes del PDF dummy de un tipo de documento.

    `tipo` es cualquier objeto con `codigo`, `nombre` y `origen` (el `TipoDocumento` de la
    BD, o `TipoDummy`). `variante` pide el otro contenido de un tipo de `VARIANTES`; una
    variante que el tipo no tiene lanza `ValueError` en vez de devolver el PDF normal,
    porque el escenario que la pide necesita dos documentos distintos y uno repetido
    pasaría por bueno.

    Determinista: el mismo tipo da los mismos bytes en cada ejecución (`invariant=1` fija
    las fechas y el identificador que reportlab, si no, cambia en cada PDF)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    titulo, linea_variante = tipo.nombre.upper(), None
    if variante is not None:
        if (tipo.codigo, variante) not in VARIANTES:
            raise ValueError(f'El tipo {tipo.codigo} no tiene la variante «{variante}» '
                             f'(las hay: {sorted(v for (c, v) in VARIANTES if c == tipo.codigo)}).')
        titulo, linea_variante = VARIANTES[(tipo.codigo, variante)]

    estilos = getSampleStyleSheet()
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=estilos['Heading2'], fontSize=10, spaceAfter=4)
    estilo_titulo = ParagraphStyle('Titulo', parent=estilos['Heading1'], fontSize=13, spaceAfter=6)
    estilo_normal = ParagraphStyle('Normal', parent=estilos['Normal'], fontSize=9, spaceAfter=3)
    estilo_pie = ParagraphStyle('Pie', parent=estilos['Normal'], fontSize=7, textColor=colors.grey)

    contenido = [
        Paragraph('Consejería de Industria, Energía y Minas', estilo_subtitulo),
        Paragraph('Junta de Andalucía', estilo_subtitulo),
        Spacer(1, 0.5 * cm),
        Paragraph(titulo, estilo_titulo),
        Spacer(1, 0.2 * cm),
        Paragraph(f'Código de tipo: {tipo.codigo} ({tipo.origen})', estilo_normal),
    ]
    if linea_variante:
        contenido.append(Paragraph(linea_variante, estilo_normal))
    contenido += [
        Spacer(1, 1 * cm),
        Paragraph(_AVISOS_ORIGEN.get(tipo.origen, _AVISOS_ORIGEN['AMBOS']), estilo_normal),
        Spacer(1, 2 * cm),
        Paragraph(
            'Este documento no tiene validez alguna fuera del entorno de pruebas de BDDAT.',
            estilo_pie,
        ),
    ]
    buffer = io.BytesIO()
    SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        invariant=1,
    ).build(contenido)
    return buffer.getvalue()


def _volcar(tipos, destino):
    """Escribe en `destino` el PDF de cada tipo y de cada una de sus variantes.

    Siempre sobrescribe y nunca borra: es seguro repetirlo (la salida es determinista) y
    una ruta mal puesta no se lleva por delante lo que hubiera en ella."""
    os.makedirs(destino, exist_ok=True)
    escritos = 0
    for tipo in tipos:
        variantes = [None] + sorted(v for (codigo, v) in VARIANTES if codigo == tipo.codigo)
        for variante in variantes:
            with open(os.path.join(destino, nombre_fichero(tipo, variante)), 'wb') as f:
                f.write(pdf_dummy(tipo, variante))
            escritos += 1
    print(f"{escritos} PDF escritos en {destino}")


def main():
    parser = argparse.ArgumentParser(
        description='Documentos dummy y catálogo de uso (#814, #929). Sin argumentos regenera '
                    'catalogo_uso.csv.')
    parser.add_argument(
        '--volcar', nargs='?', const=VOLCADO_POR_DEFECTO, default=None, metavar='RUTA',
        help='escribe en disco un PDF por cada tipo de documento (y variante), en RUTA o, sin '
             'ella, en docs_prueba/documentos_dummy/. Sobrescribe y nunca borra; no toca el CSV')
    args = parser.parse_args()

    conn = _conectar()
    try:
        with conn.cursor() as cur:
            tipos = _obtener_tipos_documentos(cur)
            if args.volcar is None:
                usos_tt = _obtener_usos_tramite_tarea(cur)
                usos_rl = _obtener_usos_requisito_legal(cur)
    finally:
        conn.close()

    if args.volcar is not None:
        _volcar([TipoDummy(codigo, nombre, origen) for _id, codigo, nombre, origen in tipos],
                os.path.abspath(args.volcar))
        return

    _escribir_csv(tipos, usos_tt, usos_rl, os.path.join(DESTINO_DIR, 'catalogo_uso.csv'))


if __name__ == '__main__':
    main()
