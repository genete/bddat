"""Compara el catálogo de desarrollo con el de una base construida desde las
migraciones (#849).

    venv/Scripts/python.exe scripts/comparar_catalogo.py           # informe
    venv/Scripts/python.exe scripts/comparar_catalogo.py -v        # + lo que coincide

Sale con código 1 si encuentra alguna divergencia no declarada, para poder
encadenarlo en una comprobación automática.

**Qué comprueba y por qué así.** «Las dos bases tienen el mismo catálogo» se
dio por bueno una vez comparando trece tablas (commit `3e17014`) y no era
cierto: `condiciones_regla` y el contenido de `catalogo_plazos` quedaron fuera,
y con ellos una regla del motor y seis plazos con su cita normativa sin
corregir. Aquí se compara **contenido**, tabla por tabla y columna por columna,
nunca conteos.

**Los ids no se comparan, y no es una concesión.** No son estables entre
instalaciones —`MODELO_SOLICITUD` es 146 en desarrollo y 56 en una base
limpia—, así que cada tabla se compara por su clave natural y las columnas
`*_id` se resuelven al código de la fila apuntada cuando hace falta
(`catalogo_variables.norma_id`). Que dos bases correctas tengan ids distintos
es lo normal; que una migración dependa de ellos es el defecto.

**Lo que queda fuera está declarado abajo**, con su motivo: datos de negocio y
operacionales (no van en migración), y las diferencias que la semilla de tests
introduce a propósito.
"""
import argparse
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(RAIZ, '.env'))


# --- Qué no se compara, y por qué -------------------------------------------

# Datos de negocio y operacionales: no van en migración, y en la base de tests
# los pone la semilla (#849.B) o no existen todavía.
TABLAS_OPERACIONALES = {
    'expedientes', 'solicitudes', 'proyectos', 'fases', 'tramites', 'tareas',
    'documentos', 'documentos_tarea', 'documentos_requisito', 'entidades',
    'autorizados_titular', 'direcciones_notificacion', 'interesados_expediente',
    'historico_titulares_expediente', 'municipios_proyecto', 'notificaciones',
    'diagnosticos', 'bitacora', 'mensajes_internos', 'alegantes',
    'organismos_expediente', 'certificados', 'requerimientos_solicitud',
    'informacion_publica', 'resoluciones',
    # Usuarios: los de desarrollo son personas reales; los de la base de tests
    # son los siete de `scripts/semilla_test.py`, diseñados para escribir tests.
    'usuarios', 'usuarios_roles',
    # Contador del número AT: estado operacional, no catálogo.
    'contador_numero_at',
    # Control de Alembic.
    'alembic_version',
}

# Columnas que difieren por decisión, no por defecto.
COLUMNAS_IGNORADAS = {
    # `semilla_test._plantillas_inactivas` las desactiva a propósito: en el
    # mundo de tests los .docx no están en disco.
    'plantillas': {'activo'},
}

# Filas presentes solo en desarrollo que no deben llegar a ninguna instalación.
FILAS_IGNORADAS = {
    'plantillas': {
        'OTRO': 'alta de prueba en desarrollo',
        'QWEQWEQ': 'alta de prueba en desarrollo',
        'PRUEBA_CANONICIDAD_727': 'prueba del motor ODT (#727)',
        'RESOLUCION_ODT': 'prueba del motor ODT (#726)',
        'RESOLUCION_ODT_V2': 'prueba del motor ODT (#726)',
    },
}

# Clave natural de cada tabla, para informar «la fila X difiere en la columna
# Y» en vez de volcar dos tuplas y que las compare el lector. Una tabla sin
# entrada aquí se compara como conjunto de filas.
CLAVES = {
    'tipos_fases': 'codigo', 'tipos_tramites': 'codigo', 'tipos_tareas': 'codigo',
    'tipos_expedientes': 'tipo', 'tipos_solicitudes': 'siglas',
    'tipos_documentos': 'codigo', 'tipos_resultados_fases': 'codigo',
    'tipos_ia': 'siglas', 'normas': 'codigo', 'roles': 'nombre',
    'catalogo_variables': 'nombre', 'catalogo_plazos': 'camino',
    'efectos_plazo': 'codigo', 'plantillas': 'codigo',
    'consultas_nombradas': 'nombre', 'configuracion_sistema': 'clave',
    'unidades_organo_propio': 'provincia', 'municipios': 'codigo',
    'ambitos_inhabilidad': 'codigo', 'catalogo_requerimientos': 'texto',
    'usuarios': 'siglas',
}

COLUMNAS_TECNICAS = {'id', 'created_at', 'updated_at', 'fecha_creacion',
                     'fecha_modificacion', 'creado_en', 'actualizado_en'}

# Tablas cuya clave natural no es una columna sino un camino a otra tabla: se
# comparan por una huella escrita a mano, que además se lee mejor en el informe
# que una tupla de ids resueltos.
#
# `reglas_motor` es el caso de manual: no tiene clave natural —ni `codigo` ni
# constraint único—, y su identidad de facto es (sujeto, descripción), que es
# lo que ya usa tests/test_470_cert_fin_ip_consultas.py para localizarlas.
ESPECIALES = {
    'reglas_motor + condiciones_regla': """
        SELECT r.sujeto, r.descripcion, r.accion, r.efecto, r.prioridad,
               r.activa, r.articulo, r.apartado,
               (SELECT n.codigo FROM public.normas n WHERE n.id = r.norma_id),
               coalesce(string_agg(v.nombre || ' ' || c.operador || ' ' || c.valor::text,
                                   ' | ' ORDER BY c.orden), '(sin condiciones)')
        FROM public.reglas_motor r
        LEFT JOIN public.condiciones_regla c ON c.regla_id = r.id
        LEFT JOIN public.catalogo_variables v ON v.id = c.variable_id
        GROUP BY r.id, r.sujeto, r.descripcion, r.accion, r.efecto, r.prioridad,
                 r.activa, r.articulo, r.apartado, r.norma_id
    """,
    'condiciones_requisito': """
        SELECT (SELECT td.codigo FROM public.tipos_documentos td
                WHERE td.id = r.tipo_documento_id),
               v.nombre, c.operador, c.valor::text, c.orden
        FROM public.condiciones_requisito c
        JOIN public.requisitos_documentales r ON r.id = c.requisito_id
        LEFT JOIN public.catalogo_variables v ON v.id = c.variable_id
    """,
    'tramites_tareas_documentos': """
        SELECT (SELECT tt.codigo FROM public.tipos_tramites tt
                WHERE tt.id = d.tipo_tramite_id),
               d.orden_tarea, d.rol,
               (SELECT td.codigo FROM public.tipos_documentos td
                WHERE td.id = d.tipo_documento_id),
               d.obligatorio
        FROM public.tramites_tareas_documentos d
    """,
    'excepciones_motor': """
        SELECT r.sujeto, r.descripcion,
               (SELECT n.codigo FROM public.normas n WHERE n.id = e.norma_id),
               e.articulo, e.apartado, e.activa
        FROM public.excepciones_motor e
        JOIN public.reglas_motor r ON r.id = e.regla_id
    """,
}

# Las que cubre ESPECIALES no pasan por la comparación genérica.
TABLAS_ESPECIALES = {'reglas_motor', 'condiciones_regla', 'condiciones_requisito',
                     'tramites_tareas_documentos', 'excepciones_motor'}

def _claves_ajenas(engine, tabla):
    """{columna: tabla destino} leídas del propio esquema.

    Se descubren en vez de listarlas a mano porque media docena de tablas del
    catálogo son *solo* claves ajenas —`fases_tramites`, `tramites_tareas`,
    `tramites_tareas_documentos`— y saltárselas por «no comparo columnas `_id`»
    dejaría fuera precisamente el esqueleto del procedimiento.
    """
    filas = _consulta(engine, """
        SELECT kcu.column_name, ccu.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON kcu.constraint_name = tc.constraint_name
         AND kcu.table_schema = tc.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON ccu.constraint_name = tc.constraint_name
         AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = 'public' AND tc.table_name = :t
    """, {'t': tabla})
    return {col: destino for col, destino in filas}


def _consulta(engine, sql, params=None):
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(sql), params or {})]


def _tablas(engine):
    return [r[0] for r in _consulta(engine, """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)]


def _columnas(engine, tabla):
    return [r[0] for r in _consulta(engine, """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = :t
        ORDER BY ordinal_position
    """, {'t': tabla})]


def _expresion(columna, fks):
    """SQL para leer una columna: las FK salen como clave natural del destino."""
    destino = fks.get(columna)
    if destino:
        clave = CLAVES[destino]
        return (f'(SELECT d."{clave}" FROM public."{destino}" d '
                f'WHERE d.id = t."{columna}")')
    return f't."{columna}"::text'


def _filas(engine, tabla, columnas, fks):
    sel = ', '.join(_expresion(c, fks) for c in columnas)
    return _consulta(engine, f'SELECT {sel} FROM public."{tabla}" t')


class Informe:
    def __init__(self):
        self.divergencias = 0
        self.iguales = []
        self.vacias = []
        self.no_comparado = []

    def diferencia(self, tabla, texto):
        self.divergencias += 1
        print(f'  {tabla}: {texto}')


def _comparar_tabla(dev, vir, tabla, informe):
    cols_dev, cols_vir = _columnas(dev, tabla), _columnas(vir, tabla)
    if set(cols_dev) != set(cols_vir):
        informe.diferencia(tabla, 'ESTRUCTURA distinta — '
                           f'solo dev: {sorted(set(cols_dev) - set(cols_vir))}, '
                           f'solo migrada: {sorted(set(cols_vir) - set(cols_dev))}')

    ignoradas = COLUMNAS_IGNORADAS.get(tabla, set())
    fks = _claves_ajenas(dev, tabla)
    # Una FK a una tabla sin clave natural declarada no se puede comparar sin
    # caer en los ids: se avisa en vez de dejarla fuera en silencio.
    sin_clave = {c: d for c, d in fks.items() if d not in CLAVES}
    fks = {c: d for c, d in fks.items() if d in CLAVES}
    comunes = [c for c in cols_dev
               if c in cols_vir and c not in COLUMNAS_TECNICAS and c not in ignoradas
               and c not in sin_clave
               and (not c.endswith('_id') or c in fks)]
    if not comunes:
        return
    if sin_clave:
        informe.no_comparado.append((tabla, sin_clave))

    clave = CLAVES.get(tabla)
    filas_dev = _filas(dev, tabla, comunes, fks)
    filas_vir = _filas(vir, tabla, comunes, fks)

    if not filas_vir:
        informe.vacias.append((tabla, len(filas_dev)))
        return

    saltadas = FILAS_IGNORADAS.get(tabla, {})

    if clave and clave in comunes:
        i = comunes.index(clave)
        dic_dev = {f[i]: f for f in filas_dev if f[i] not in saltadas}
        dic_vir = {f[i]: f for f in filas_vir if f[i] not in saltadas}
        hubo = False
        for k in sorted(set(dic_dev) - set(dic_vir), key=str):
            informe.diferencia(tabla, f'{clave}={k!r} solo en desarrollo')
            hubo = True
        for k in sorted(set(dic_vir) - set(dic_dev), key=str):
            informe.diferencia(tabla, f'{clave}={k!r} solo en la base migrada')
            hubo = True
        for k in sorted(set(dic_dev) & set(dic_vir), key=str):
            for col, a, b in zip(comunes, dic_dev[k], dic_vir[k]):
                if a != b:
                    informe.diferencia(
                        tabla, f'{clave}={k!r} columna {col}:\n'
                               f'      desarrollo = {a!r}\n'
                               f'      migrada    = {b!r}')
                    hubo = True
        if not hubo:
            informe.iguales.append((tabla, len(dic_dev)))
        return

    conj_dev, conj_vir = set(filas_dev), set(filas_vir)
    solo_dev, solo_vir = conj_dev - conj_vir, conj_vir - conj_dev
    if not solo_dev and not solo_vir:
        informe.iguales.append((tabla, len(conj_dev)))
        return
    for f in sorted(solo_dev, key=str)[:10]:
        informe.diferencia(tabla, f'fila solo en desarrollo: {f}')
    for f in sorted(solo_vir, key=str)[:10]:
        informe.diferencia(tabla, f'fila solo en la base migrada: {f}')


def _comparar_especial(dev, vir, nombre, sql, informe):
    """Compara por huella escrita a mano. Las dos primeras columnas de cada
    consulta identifican la fila; el resto es contenido."""
    conj_dev = set(_consulta(dev, sql))
    conj_vir = set(_consulta(vir, sql))
    solo_dev, solo_vir = conj_dev - conj_vir, conj_vir - conj_dev
    if not solo_dev and not solo_vir:
        informe.iguales.append((nombre, len(conj_dev)))
        return
    for fila in sorted(solo_dev, key=str):
        informe.diferencia(nombre, f'solo en desarrollo:      {fila[0]} · {fila[1]}\n'
                                   f'      resto: {fila[2:]}')
    for fila in sorted(solo_vir, key=str):
        informe.diferencia(nombre, f'solo en la base migrada: {fila[0]} · {fila[1]}\n'
                                   f'      resto: {fila[2:]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-v', '--verboso', action='store_true',
                        help='lista también las tablas que coinciden')
    args = parser.parse_args()

    url_dev = os.environ.get('DATABASE_URL')
    url_vir = os.environ.get('TEST_DATABASE_URL')
    if not url_dev or not url_vir:
        sys.exit('Faltan DATABASE_URL o TEST_DATABASE_URL en .env')

    dev, vir = create_engine(url_dev), create_engine(url_vir)
    print(f'desarrollo : {url_dev.rsplit("/", 1)[-1]}')
    print(f'migrada    : {url_vir.rsplit("/", 1)[-1]}\n')

    t_dev, t_vir = set(_tablas(dev)), set(_tablas(vir))

    # CLAVES se escribe a mano: si una columna declarada no existe, la
    # comparación se caería a media ejecución con un error de SQL.
    mal = [f'{t}.{c}' for t, c in CLAVES.items()
           if t in t_dev and c not in _columnas(dev, t)]
    if mal:
        sys.exit(f'CLAVES declara columnas que no existen: {", ".join(mal)}')
    informe = Informe()

    if t_dev - t_vir:
        informe.diferencia('(esquema)', f'tablas solo en desarrollo: {sorted(t_dev - t_vir)}')
    if t_vir - t_dev:
        informe.diferencia('(esquema)', f'tablas solo en la migrada: {sorted(t_vir - t_dev)}')

    print('Divergencias:')
    inicio = informe.divergencias
    for tabla in sorted(t_dev & t_vir):
        if tabla in TABLAS_OPERACIONALES or tabla in TABLAS_ESPECIALES:
            continue
        _comparar_tabla(dev, vir, tabla, informe)
    for nombre, sql in ESPECIALES.items():
        _comparar_especial(dev, vir, nombre, sql, informe)
    if informe.divergencias == inicio:
        print('  ninguna')

    if args.verboso and informe.iguales:
        print('\nCoinciden:')
        for tabla, n in informe.iguales:
            print(f'  {tabla} ({n} filas)')
    if informe.vacias:
        print('\nCon filas en desarrollo y vacías en la base migrada '
              '(esperado si son datos que no van en migración):')
        for tabla, n in informe.vacias:
            print(f'  {tabla} ({n} filas en desarrollo)')
    if informe.no_comparado:
        print('\nColumnas NO comparadas — apuntan a una tabla sin clave natural '
              'en CLAVES, y por id no se puede comparar:')
        for tabla, cols in informe.no_comparado:
            for col, destino in cols.items():
                print(f'  {tabla}.{col} -> {destino}')

    print(f'\n{len(informe.iguales)} tablas coinciden · '
          f'{informe.divergencias} divergencias')
    return 1 if informe.divergencias else 0


if __name__ == '__main__':
    sys.exit(main())
