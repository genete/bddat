"""
Servicio de generación de escritos administrativos (.docx).

RESPONSABILIDAD:
    Orquesta las capas de contexto + python-docx-template para producir
    un fichero .docx relleno a partir de una plantilla registrada en
    tipos_escritos.

FLUJO:
    1. Carga la plantilla .docx desde PLANTILLAS_BASE
    2. Construye el contexto: Capa 1 (ContextoBaseExpediente) + Capa 2 opcional
    3. Ejecuta las consultas nombradas referenciadas en la plantilla
    4. Renderiza con DocxTemplate (python-docx-template / Jinja2)
    5. Devuelve bytes del .docx resultante

USO:
    from app.services.generador_escritos import generar_escrito

    docx_bytes = generar_escrito(tipo_escrito, expediente, db_session)
    # Guardar bytes en FILESYSTEM_BASE y registrar en pool del expediente

DEPENDENCIA:
    pip install python-docx-template
"""

import importlib
import os

from docxtpl import DocxTemplate

from app.services.escritos import ContextoBaseExpediente


def generar_escrito(tipo_escrito, expediente, db_session) -> bytes:
    """
    Genera el .docx relleno para el tipo_escrito y expediente dados.

    Args:
        tipo_escrito:  Instancia de TipoEscrito (plantilla + contexto registrado).
        expediente:    Instancia de Expediente con relaciones cargadas.
        db_session:    Sesión SQLAlchemy activa (para ejecutar consultas nombradas).

    Returns:
        bytes — Contenido del .docx generado, listo para guardar en disco.

    Raises:
        FileNotFoundError — Si la plantilla .docx no existe en PLANTILLAS_BASE.
        RuntimeError      — Si el Context Builder especificado no se puede cargar.
    """
    plantilla_path = _ruta_plantilla(tipo_escrito.ruta_plantilla)

    # Capa 1: contexto base del expediente
    ctx = ContextoBaseExpediente(expediente).get_contexto()

    # Capa 2: Context Builder opcional
    if tipo_escrito.contexto_clase:
        builder = _cargar_context_builder(tipo_escrito.contexto_clase)
        ctx.update(builder(expediente, db_session).get_contexto())

    # Consultas nombradas: se añaden al contexto con su nombre como clave
    ctx.update(_ejecutar_consultas(tipo_escrito, expediente, db_session))

    # Renderizado
    tpl = DocxTemplate(plantilla_path)
    tpl.render(ctx)

    # Devolver bytes sin escribir a disco (la escritura es responsabilidad del caller)
    import io
    buffer = io.BytesIO()
    tpl.save(buffer)
    return buffer.getvalue()


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
            f'Comprueba PLANTILLAS_BASE y la ruta registrada en tipos_escritos.'
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


def _ejecutar_consultas(tipo_escrito, expediente, db_session) -> dict:
    """
    Ejecuta las consultas nombradas referenciadas en la plantilla.

    Por ahora devuelve un dict vacío: las consultas nombradas se detectarán
    automáticamente al parsear la plantilla en una versión futura, o se
    registrarán explícitamente en tipos_escritos cuando sea necesario.

    TODO (Parte 2 o issue posterior):
        - Parsear la plantilla para detectar {%tr for row in X %} y ejecutar
          la consulta_nombrada con nombre X para cada bloque encontrado.
    """
    return {}
