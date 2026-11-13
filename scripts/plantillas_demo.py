"""Plantillas y fragmento de demostración (#1009, bloque 3).

Para qué sirven. Generar un escrito de punta a punta —un expediente dummy, su tarea ELABORAR, una
plantilla, un fragmento, el motor y el almacén— no se podía probar con nada que no fuera
sintético dentro de un test: las plantillas reales las sube el supervisor y no están en git, y las
cinco que siembran las migraciones no tienen fichero (ADR-050 §J). Aquí se registran plantillas
**sintéticas**, con código propio (`DEMO_*`), hechas a partir de las bases canónicas del
repositorio (`app/data/plantillas_base/`), con las mismas funciones de contenido que usa la subida
desde el navegador. Las usan la semilla de tests y la de la BD de desarrollo de la nube
(`semilla_test.sembrar()`), y los scripts de Playwright que emulen una tramitación.

**Una por trámite ELABORAR de los expedientes-tipo** (`scripts/expedientes_dummy/`), con el tipo de
documento y el contexto ESFTT del trámite real, para que aparezcan en el desplegable de esa tarea
y el documento generado sea del tipo que el motor de reglas espera. Si un expediente-tipo nuevo
pasa por otro ELABORAR, se añade una entrada a `PLANTILLAS`.

**Qué llevan.** Las bases son esqueletos sin marcadores. A cada una se le sustituye el párrafo de
ejemplo por uno con datos del expediente (`numero_at`, `titular_nombre`, `fecha_hoy`) y por la cita
a un fragmento, para que un escrito generado demuestre que se renderiza y que el fragmento se
inserta. Casi todas son solo Capa 1 (sin `contexto_clase`): lo que se prueba es el circuito. Las dos del
análisis de la solicitud (`REQUERIMIENTO_SUBSANACION` y `COMUNICACION_INICIO_ADMISION`) declaran además su
Context Builder y usan sus tokens (`defectos_*`, `actos`, `fecha_recepcion_solicitud`) con las etiquetas de bloque
`{%p … %}` del motor `.odt`, para que un escrito generado demuestre que la capa 2 llega al documento. El guion de
interfaz (`scripts/expedientes_dummy/interfaz/`) comprueba esos textos contra los datos del expediente.

**Solo `.odt`.** El motor `.docx` se mantiene mientras la ADA no decida (ADR-050 §J) y tiene su test
(`test_1009_motor_docx`), pero no hay bases canónicas `.docx` de las que partir.

**Prefijo.** `registrar(prefijo=...)` cambia el prefijo de los códigos y del fragmento. La semilla
usa `DEMO_`; un test que genere en un almacén temporal usa otro, para no tocar las filas de la
semilla: leer su contenido desde un almacén que no lo tiene las marcaría como ausentes (§G).

Este módulo no importa `app` al cargarse (lo hacen las funciones), para que
`scripts/comparar_catalogo.py` pueda leer `codigos()` sin una app.

**Desde la línea de comandos** (la BD es la de `DATABASE_URL` del `.env`; el almacén, el de
`ALMACEN_BASE`, que tiene que estar inicializado):

    python scripts/plantillas_demo.py                        # registra las cinco y el fragmento
    python scripts/plantillas_demo.py --claves RESOLUCION    # solo algunas
    python scripts/plantillas_demo.py --prefijo PRUEBA_      # con otro prefijo (PRUEBA_RESOLUCION…)
    python scripts/plantillas_demo.py --quitar               # las borra (con el mismo prefijo)

Es idempotente: ejecutarlo dos veces no duplica nada. Desde Python, `registrar(prefijo, claves)`.
"""
import io
import zipfile
from pathlib import Path

PREFIJO = 'DEMO_'
RAIZ = Path(__file__).resolve().parent.parent
BASES = RAIZ / 'app' / 'data' / 'plantillas_base'

# El texto de ejemplo de cada base, que se sustituye. Todas lo llevan en un párrafo `Normal`.
_EJEMPLO = {
    'carta_base.odt': 'Cuerpo de texto del documento',
    'resolucion_base.odt': 'Texto de la parte dispositiva.',
    'fragmento_base.odt': '[Contenido del fragmento]',
}

# clave → qué es la plantilla. La clave se añade al prefijo para formar el código. `fase` y
# `tramite` son códigos de `tipos_fases` y `tipos_tramites`; `documento`, de `tipos_documentos`.
#
# Claves opcionales: `contexto` es el Context Builder (capa 2) que declara la plantilla (`contexto_clase`) y
# `cuerpo` los párrafos que van entre el encabezado y la cita al fragmento, con los tokens de ese builder.
# Una etiqueta `{%p … %}` repite o quita el párrafo que la contiene; la de cierre va en el párrafo siguiente
# (que sale vacío) y es la que cierra antes de él (ver `_elevar_etiquetas_de_bloque` del motor).
# Los rótulos de los apartados («Defectos documentales:»…) los espera el guion de interfaz
# (`APARTADO_POR_ORIGEN` de su escenario): si cambian aquí, cambian allí.


def _bloque_de_defectos(titulo: str, lista: str) -> list[str]:
    """Un apartado del requerimiento: el título (solo si hay defectos de ese origen) y un párrafo por defecto."""
    return [
        '{%p if ' + lista + ' %}' + titulo,
        '{%p for defecto in ' + lista + ' %}• {{ defecto }}',
        '{%p endfor %}{%p endif %}',
    ]


PLANTILLAS = {
    'REQUERIMIENTO_SUBSANACION': {
        'etiqueta': 'Requerimiento de subsanación', 'base': 'carta_base.odt',
        'documento': 'OFICIO_REQUERIMIENTO', 'fase': 'ANALISIS_SOLICITUD',
        'tramite': 'REQUERIMIENTO_SUBSANACION',
        'contexto': 'ContextoSubsanacion',
        'cuerpo': [
            *_bloque_de_defectos('Defectos documentales:', 'defectos_documentales'),
            *_bloque_de_defectos('Defectos técnicos:', 'defectos_tecnicos'),
            *_bloque_de_defectos('Otros defectos:', 'defectos_libres'),
        ],
    },
    'COMUNICACION_INICIO_ADMISION': {
        'etiqueta': 'Comunicación de inicio y admisión a trámite', 'base': 'carta_base.odt',
        'documento': 'OFICIO_INICIO_ADMISION', 'fase': 'ANALISIS_SOLICITUD',
        'tramite': 'COMUNICACION_INICIO_ADMISION',
        'contexto': 'ContextoComunicacionInicioAdmision',
        'cuerpo': [
            'Solicitud recibida el {{ fecha_recepcion_solicitud }}. Plazo máximo para resolver y notificar:',
            '{%p for acto in actos %}• {{ acto.nombre }}: {{ acto.plazo_maximo_resolucion }} {{ acto.unidad_plazo }} '
            '({{ acto.norma_plazo }}); silencio: {{ acto.efecto_silencio }}',
            '{%p endfor %}',
        ],
    },
    'CONSULTA_SEPARATA': {
        'etiqueta': 'Separata a organismo', 'base': 'carta_base.odt',
        'documento': 'OFICIO_SEPARATA', 'fase': 'CONSULTAS', 'tramite': 'CONSULTA_SEPARATA',
    },
    'CONSULTA_TRASLADO_TITULAR': {
        'etiqueta': 'Traslado de la respuesta del organismo al titular', 'base': 'carta_base.odt',
        'documento': 'OFICIO_TRASLADO_RESPUESTA', 'fase': 'CONSULTAS',
        'tramite': 'CONSULTA_TRASLADO_TITULAR',
    },
    'RESOLUCION': {
        'etiqueta': 'Resolución de autorización administrativa', 'base': 'resolucion_base.odt',
        'documento': 'RESOLUCION', 'fase': 'RESOLUCION', 'tramite': 'ELABORACION',
    },
}

# El texto con que empieza el párrafo del fragmento: el escrito generado lo lleva, y un test lo busca.
TEXTO_DEL_FRAGMENTO = 'Pie de demostración: este párrafo procede del fragmento'


def codigos(prefijo: str = PREFIJO) -> list[str]:
    """Los códigos de plantilla que registra `registrar` con ese prefijo."""
    return [prefijo + clave for clave in PLANTILLAS]


def nombre_fragmento(prefijo: str = PREFIJO) -> str:
    """El nombre del fragmento (`{{r <nombre> }}`) que citan las plantillas con ese prefijo."""
    return f'{prefijo}Pie'


def _odt_con_cuerpo(base: str, parrafos: list[str]) -> bytes:
    """La base canónica con su párrafo de ejemplo sustituido por `parrafos` (texto ya en XML).

    Determinista: conserva la fecha y la compresión de cada entrada del zip, así que registrar
    dos veces lo mismo da el mismo SHA-256 y no escribe nada nuevo en el almacén."""
    ejemplo = f'<text:p text:style-name="Normal">{_EJEMPLO[base]}</text:p>'
    nuevo = ''.join(f'<text:p text:style-name="Normal">{p}</text:p>' for p in parrafos)
    salida = io.BytesIO()
    with zipfile.ZipFile(BASES / base) as origen, \
            zipfile.ZipFile(salida, 'w', zipfile.ZIP_DEFLATED) as destino:
        for info in origen.infolist():
            datos = origen.read(info.filename)
            if info.filename == 'content.xml':
                texto = datos.decode('utf-8')
                if ejemplo not in texto:
                    raise RuntimeError(
                        f'La base {base} ya no lleva su párrafo de ejemplo «{_EJEMPLO[base]}»: '
                        f'hay que actualizar scripts/plantillas_demo.py')
                datos = texto.replace(ejemplo, nuevo, 1).encode('utf-8')
            destino.writestr(info, datos)
    return salida.getvalue()


def odt_de_plantilla(clave: str, prefijo: str = PREFIJO) -> bytes:
    """El `.odt` de la plantilla `clave`: su base, con datos del expediente y la cita al fragmento."""
    datos = PLANTILLAS[clave]
    return _odt_con_cuerpo(datos['base'], [
        f'[DEMO] {datos["etiqueta"]}. Expediente {{{{ numero_at }}}}, titular '
        f'{{{{ titular_nombre }}}}, a {{{{ fecha_hoy }}}}.',
        *datos.get('cuerpo', []),
        f'{{{{r {nombre_fragmento(prefijo)} }}}}',
    ])


def odt_del_fragmento(prefijo: str = PREFIJO) -> bytes:
    """El `.odt` del fragmento: su base con un texto reconocible (`TEXTO_DEL_FRAGMENTO`) y su
    nombre. Lleva el nombre a propósito: el almacén guarda el contenido por su hash, y dos
    prefijos con el mismo texto compartirían la fila de `ficheros`."""
    return _odt_con_cuerpo('fragmento_base.odt',
                           [f'{TEXTO_DEL_FRAGMENTO} {nombre_fragmento(prefijo)}.'])


def _id_del_catalogo(modelo, columna, valor, que: str) -> int:
    fila = modelo.query.filter(columna == valor).first()
    if fila is None:
        raise RuntimeError(f'Falta {que} «{valor}» en el catálogo: hay que actualizar '
                           f'scripts/plantillas_demo.py')
    return fila.id


def registrar(prefijo: str = PREFIJO, claves=None) -> dict[str, int]:
    """Registra el fragmento y las plantillas de demostración (todas, o solo `claves`) y devuelve
    `{clave: plantilla.id}`. Idempotente: lo que ya está se deja como está, salvo su contenido, que
    se pone al día si ha cambiado (mismo SHA-256 = no se escribe nada).

    Necesita una app con contexto y el almacén inicializado. **No hace commit**: es de quien llama
    (la semilla hace uno; un test que pase por rutas, otro). `activo` solo se fija al crear: pausar
    una demostración y volver a sembrar no la reactiva."""
    from app import db
    from app.models.plantillas import Plantilla
    from app.models.tipos_documentos import TipoDocumento
    from app.models.tipos_fases import TipoFase
    from app.models.tipos_tramites import TipoTramite
    from app.services.almacenamiento import contenido
    from app.services.almacenamiento.formatos import MIME_ODT
    from app.services.generador_escritos import validar_plantilla

    fragmento, resultado = contenido.guardar_fragmento(
        nombre_fragmento(prefijo), io.BytesIO(odt_del_fragmento(prefijo)),
        f'{nombre_fragmento(prefijo)}.odt',
        descripcion='Pie de demostración (#1009): lo citan las plantillas de demostración.')
    if resultado == contenido.CREADO:
        db.session.add(fragmento)

    registradas = {}
    for clave in (claves or PLANTILLAS):
        datos = PLANTILLAS[clave]
        odt = odt_de_plantilla(clave, prefijo)
        error = validar_plantilla(odt, MIME_ODT)
        if error:
            raise RuntimeError(f'La plantilla de demostración {clave} no valida: {error}')

        codigo = prefijo + clave
        plantilla = Plantilla.query.filter_by(codigo=codigo).first()
        nueva = plantilla is None
        if nueva:
            plantilla = Plantilla(codigo=codigo, activo=True)
        plantilla.nombre = f'{datos["etiqueta"]} (demostración)'
        plantilla.descripcion = ('Plantilla sintética de la semilla (#1009): sirve para probar un '
                                 'expediente de punta a punta. No es una plantilla real.')
        plantilla.contexto_clase = datos.get('contexto')   # None = solo capa 1
        plantilla.tipo_documento_id = _id_del_catalogo(
            TipoDocumento, TipoDocumento.codigo, datos['documento'], 'el tipo de documento')
        plantilla.tipo_fase_id = _id_del_catalogo(
            TipoFase, TipoFase.codigo, datos['fase'], 'el tipo de fase')
        plantilla.tipo_tramite_id = _id_del_catalogo(
            TipoTramite, TipoTramite.codigo, datos['tramite'], 'el tipo de trámite')
        contenido.guardar_plantilla(plantilla, io.BytesIO(odt), f'{codigo}.odt')
        if nueva:
            db.session.add(plantilla)
        db.session.flush()
        registradas[clave] = plantilla.id
    return registradas


def quitar(prefijo: str = PREFIJO) -> tuple[int, int]:
    """Borra las plantillas y el fragmento de demostración de ese prefijo y devuelve cuántas
    filas de cada tipo. No hace commit. El contenido ya subido al almacén lo recoge la limpieza
    cuando nada lo referencie (ADR-050 §G): aquí solo se borran las filas."""
    from app.models.fragmentos import Fragmento
    from app.models.plantillas import Plantilla

    plantillas = Plantilla.query.filter(Plantilla.codigo.in_(codigos(prefijo))).delete(
        synchronize_session=False)
    fragmentos = Fragmento.query.filter_by(nombre=nombre_fragmento(prefijo)).delete()
    return plantillas, fragmentos


def _principal(argv=None) -> int:
    """Punto de entrada de la línea de comandos (ver la cabecera del módulo)."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Registra (o quita) las plantillas y el fragmento de demostración en la BD y '
                    'el almacén del .env.')
    parser.add_argument('--prefijo', default=PREFIJO,
                        help=f'prefijo de los códigos y del fragmento (por defecto {PREFIJO})')
    parser.add_argument('--claves', nargs='+', choices=sorted(PLANTILLAS), metavar='CLAVE',
                        help='solo estas plantillas (por defecto, todas): '
                             + ', '.join(sorted(PLANTILLAS)))
    parser.add_argument('--quitar', action='store_true',
                        help='borra las filas de ese prefijo en lugar de registrarlas')
    args = parser.parse_args(argv)

    sys.path.insert(0, str(RAIZ))
    from dotenv import load_dotenv
    load_dotenv(RAIZ / '.env')       # antes de importar `app`: la configuración lee el entorno al cargar

    from app import create_app, db
    app = create_app('development')
    with app.app_context():
        url = db.engine.url
        print(f'Base de datos: {url.database} en {url.host}:{url.port}')
        print(f'Almacén: {app.config.get("ALMACEN_BASE")}')
        if args.quitar:
            plantillas, fragmentos = quitar(args.prefijo)
            db.session.commit()
            print(f'Borradas: {plantillas} plantillas y {fragmentos} fragmento(s) '
                  f'con el prefijo {args.prefijo}')
            return 0
        registradas = registrar(args.prefijo, args.claves)
        db.session.commit()
        print(f'Registradas {len(registradas)} plantillas y el fragmento '
              f'{nombre_fragmento(args.prefijo)}:')
        for clave, plantilla_id in registradas.items():
            print(f'  {args.prefijo}{clave}  (id {plantilla_id})')
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(_principal())
