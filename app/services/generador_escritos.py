"""
Servicio de generación de escritos administrativos (.docx).

RESPONSABILIDAD:
    Orquesta las capas de contexto + python-docx-template para producir
    un fichero .docx relleno a partir de una Plantilla registrada.

FLUJO:
    1. Carga la plantilla .docx desde PLANTILLAS_BASE
    2. Construye el contexto: Capa 1 (ContextoBaseExpediente) + Capa 2 opcional
    3. Ejecuta las consultas nombradas referenciadas en la plantilla
    4. Renderiza con DocxTemplate (python-docx-template / Jinja2)
    5. Devuelve bytes del .docx resultante

FUNCIONES PÚBLICAS ADICIONALES (Fase 5 #167):
    componer_nombre_documento  — Nombre sistematizado para el .docx generado
    ruta_destino_documento     — Ruta en FILESYSTEM_BASE/AT-XXXX/
    guardar_docx               — Escribe bytes a disco (sobrescribe si existe)

USO:
    from app.services.generador_escritos import generar_escrito
    from app.services.generador_escritos import componer_nombre_documento, ruta_destino_documento, guardar_docx

    docx_bytes = generar_escrito(plantilla, expediente, db_session)
    nombre = componer_nombre_documento(tarea, plantilla)
    ruta = ruta_destino_documento(expediente, nombre)
    guardar_docx(docx_bytes, ruta)

DEPENDENCIA:
    pip install python-docx-template
"""

import importlib
import logging
import os
import re

from docxtpl import DocxTemplate

from app.services.escritos import ContextoBaseExpediente

logger = logging.getLogger(__name__)


def generar_escrito(plantilla, expediente, db_session) -> bytes:
    """
    Genera el .docx relleno para la plantilla y expediente dados.

    Args:
        plantilla:   Instancia de Plantilla (plantilla + contexto registrado).
        expediente:  Instancia de Expediente con relaciones cargadas.
        db_session:  Sesión SQLAlchemy activa (para ejecutar consultas nombradas).

    Returns:
        bytes — Contenido del .docx generado, listo para guardar en disco.

    Raises:
        FileNotFoundError — Si la plantilla .docx no existe en PLANTILLAS_BASE.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
    """
    plantilla_path = _ruta_plantilla(plantilla.ruta_plantilla)

    # Capa 1: contexto base del expediente
    ctx = ContextoBaseExpediente(expediente).get_contexto()

    # Capa 2: Context Builder opcional
    if plantilla.contexto_clase:
        builder = _cargar_context_builder(plantilla.contexto_clase)
        ctx.update(builder(expediente, db_session).get_contexto())

    # Consultas nombradas: se añaden al contexto con su nombre como clave
    ctx.update(_ejecutar_consultas(plantilla, expediente, db_session))

    # Renderizado
    tpl = DocxTemplate(plantilla_path)

    # Fragmentos insertables: {{r NombreFragmento}} → tpl.new_subdoc(ruta)
    ctx.update(_cargar_fragmentos(tpl, plantilla_path))

    tpl.render(ctx)

    # Devolver bytes sin escribir a disco (la escritura es responsabilidad del caller)
    import io
    buffer = io.BytesIO()
    tpl.save(buffer)
    return buffer.getvalue()


# ------------------------------------------------------------------
# Funciones públicas — nombre, ruta y guardado (Fase 5 #167)
# ------------------------------------------------------------------

# Caracteres no válidos en nombres de fichero Windows
_CARACTERES_INVALIDOS = re.compile(r'[\\/:*?"<>|]')


def componer_nombre_documento(tarea, plantilla) -> str:
    """
    Genera un nombre sistematizado para el .docx a partir de la cadena ESFTT.

    Recorre tarea → tipo_tarea → tramite → tipo_tramite → fase → tipo_fase
    → solicitud → tipo_solicitud → expediente, tomando nombre_en_plantilla
    de cada nivel. NULL al final se omite; NULL en medio se reemplaza por "ANY".

    Si plantilla.variante existe, se añade " V {variante}" al final.
    Sufijo siempre .docx. Caracteres inválidos para fichero → '_'.
    """
    tramite = tarea.tramite
    fase = tramite.fase if tramite else None
    solicitud = fase.solicitud if fase else None
    expediente = solicitud.expediente if solicitud else None

    # Recoger nombre_en_plantilla de cada nivel (de más genérico a más específico)
    partes_raw = [
        getattr(tarea.tipo_tarea, 'nombre_en_plantilla', None) if tarea.tipo_tarea else None,
        getattr(tramite.tipo_tramite, 'nombre_en_plantilla', None) if tramite and tramite.tipo_tramite else None,
        getattr(fase.tipo_fase, 'nombre_en_plantilla', None) if fase and fase.tipo_fase else None,
        getattr(solicitud.tipo_solicitud, 'nombre_en_plantilla', None) if solicitud and solicitud.tipo_solicitud else None,
        f'AT-{expediente.numero_at}' if expediente and expediente.numero_at else None,
    ]

    # Recortar NULLs del final; reemplazar NULLs internos por "ANY"
    while partes_raw and partes_raw[-1] is None:
        partes_raw.pop()

    partes = [p if p is not None else 'ANY' for p in partes_raw]

    nombre = ' '.join(partes)

    if plantilla.variante:
        nombre += f' V {plantilla.variante}'

    nombre += '.docx'

    # Sanitizar caracteres inválidos para nombre de fichero
    nombre = _CARACTERES_INVALIDOS.sub('_', nombre)

    return nombre


def ruta_destino_documento(expediente, nombre_fichero) -> str:
    """
    Calcula la ruta absoluta donde guardar el documento generado.

    Estructura: FILESYSTEM_BASE / AT-{numero_at} / {nombre_fichero}
    Crea el subdirectorio si no existe.

    NOTA: Ruta hardcoded provisional. Se reemplazará por rutas configurables
    en tablas maestras cuando se implemente esa decisión de arquitectura
    (Bloque 2/8 del roadmap).
    """
    from flask import current_app
    base = current_app.config.get('FILESYSTEM_BASE', '')
    if not base:
        raise RuntimeError('FILESYSTEM_BASE no está configurado')

    carpeta_exp = f'AT-{expediente.numero_at}'
    directorio = os.path.join(base, carpeta_exp)
    os.makedirs(directorio, exist_ok=True)

    return os.path.join(directorio, nombre_fichero)


def guardar_docx(docx_bytes, ruta_destino) -> str:
    """
    Escribe bytes del .docx a disco. Sobrescribe si existe (regeneración B6).

    Returns:
        str — Ruta absoluta del fichero escrito.
    """
    with open(ruta_destino, 'wb') as f:
        f.write(docx_bytes)
    return ruta_destino


# ------------------------------------------------------------------
# Helpers privados
# ------------------------------------------------------------------

def _ruta_plantilla(ruta_relativa: str) -> str:
    """Resuelve la ruta absoluta de la plantilla dentro de PLANTILLAS_BASE."""
    from flask import current_app
    base = current_app.config['PLANTILLAS_BASE']
    ruta = os.path.join(base, 'plantillas', ruta_relativa)
    if not os.path.isfile(ruta):
        raise FileNotFoundError(
            f'Plantilla no encontrada: {ruta}. '
            f'Comprueba PLANTILLAS_BASE y la ruta registrada en la plantilla.'
        )
    return ruta


def _cargar_context_builder(nombre_clase: str):
    """
    Importa y devuelve la clase Context Builder por nombre.

    Convenio de módulo: app.services.context_builders.<nombre_clase_en_snake>
    Ejemplo: 'RequerimientoSubsanacion' → app.services.context_builders.requerimiento_subsanacion
    """
    import re
    snake = re.sub(r'(?<!^)(?=[A-Z])', '_', nombre_clase).lower()
    modulo_path = f'app.services.context_builders.{snake}'
    try:
        modulo = importlib.import_module(modulo_path)
        return getattr(modulo, nombre_clase)
    except (ModuleNotFoundError, AttributeError) as e:
        raise RuntimeError(
            f'No se pudo cargar el Context Builder "{nombre_clase}" '
            f'desde {modulo_path}: {e}'
        )


def _cargar_fragmentos(tpl, plantilla_path) -> dict:
    """
    Detecta etiquetas {{r NombreFragmento}} en el XML de la plantilla y carga
    los subdocumentos correspondientes desde PLANTILLAS_BASE/fragmentos/.

    python-docx-template requiere que el contexto contenga un objeto Subdoc
    creado con tpl.new_subdoc(ruta) para cada {{r variable}}.
    """
    import zipfile

    # Leer el XML del .docx para encontrar las etiquetas {{r ...}}
    with zipfile.ZipFile(plantilla_path) as z:
        xml = z.read('word/document.xml').decode('utf-8')

    # Patrón: {{r nombre}} — captura el nombre del fragmento
    nombres = re.findall(r'\{\{r\s+(\w+)\s*\}\}', xml)
    if not nombres:
        return {}

    from flask import current_app
    base = current_app.config['PLANTILLAS_BASE']
    fragmentos_dir = os.path.join(base, 'fragmentos')

    resultado = {}
    for nombre in set(nombres):
        ruta_frag = os.path.join(fragmentos_dir, nombre + '.docx')
        if os.path.isfile(ruta_frag):
            resultado[nombre] = tpl.new_subdoc(ruta_frag)
        else:
            logger.warning(
                'Fragmento "%s.docx" referenciado en plantilla pero no encontrado en %s',
                nombre, fragmentos_dir
            )

    return resultado


def _ejecutar_consultas(plantilla, expediente, db_session) -> dict:
    """
    Ejecuta TODAS las ConsultaNombrada activas con :expediente_id y las pasa
    al contexto. Las no referenciadas en la plantilla se ignoran por Jinja2.

    Estrategia simple: ejecutar todas es más barato que parsear el .docx
    buscando etiquetas {%tr for row in X %}. Si una consulta falla, se
    registra un warning y se pasa como lista vacía (no rompe la generación).
    """
    from app.models.consultas_nombradas import ConsultaNombrada
    from sqlalchemy import text

    resultado = {}

    for cn in ConsultaNombrada.query.filter_by(activo=True).all():
        try:
            rows = db_session.execute(
                text(cn.sql),
                {'expediente_id': expediente.id}
            ).mappings().all()
            resultado[cn.nombre] = [dict(r) for r in rows]
        except Exception as e:
            logger.warning(
                'Consulta nombrada "%s" (id=%s) falló para expediente %s: %s',
                cn.nombre, cn.id, expediente.id, e
            )
            resultado[cn.nombre] = []

    return resultado
