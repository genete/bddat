"""Servicio de la bandeja de peticiones al Supervisor (#28, ADR-040).

REGISTRO DE TIPOS — la razón de ser de este módulo (ADR-040 §5)
---------------------------------------------------------------
`mensajes_internos.datos` es JSONB: el schema no sabe qué hay dentro. Quien
GENERA una petición y quien la MUESTRA pasan los dos por el registro `TIPOS` de
aquí, así que el formato del payload se declara UNA vez.

Que esto sea estructural y no una convención que haya que recordar depende de un
detalle del diseño: el inspector es un fragmento Jinja servido por el backend
(ADR-023), así que productor y renderizador son ambos Python. No hace falta el
canal de copy compartido Python<->JS que #766 tuvo que resolver con dos
constantes gemelas.

Añadir un tipo nuevo (N055 cambios de plantilla, N056 avisos técnicos, N070
mejoras del manual) es una entrada en `TIPOS` y un `crear()` de una línea en su
punto de origen. No toca el schema, ni el modelo, ni el CRUD.

CONVENCIÓN DE COMMIT
--------------------
Como `bitacora.registrar`, las funciones de escritura de aquí hacen `add`/mutan
la fila pero NO hacen commit: eso es del consumidor, que normalmente tiene más
cosas que confirmar en la misma transacción.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.exc import OperationalError, ProgrammingError

from app import db
from app.models.mensajes_internos import MensajeInterno
from app.models.usuarios import Rol

log = logging.getLogger(__name__)

RESULTADOS = ('ATENDIDA', 'DENEGADA')

# Etiquetas del veredicto para la interfaz. El valor almacenado es el contable;
# esto es solo cómo se lee.
ETIQUETAS_RESULTADO = {
    'ATENDIDA': 'Atendida',
    'DENEGADA': 'Denegada',
}

ETIQUETAS_ESTADO = {
    'pendiente': 'Pendiente',
    'resuelto': 'Resuelta',
    'acusado': 'Acusada',
}

# Categorías de catalogo_requerimientos (ck_catalogo_requerimientos_categoria).
# Se replican aquí porque el mensaje PROPONE un alta que aún no existe: no hay
# fila de catálogo de la que leerlas, y el CHECK de aquella tabla no protege un
# JSONB de esta.
_CATEGORIAS_REQUERIMIENTO = ('documental', 'tecnica', 'administrativa', 'tasas')


class PayloadInvalido(ValueError):
    """El payload no cumple lo que su tipo declara. El endpoint responde 400."""


@dataclass(frozen=True)
class TipoMensaje:
    """Declaración completa de un tipo de petición.

    codigo     — valor de `mensajes_internos.tipo`
    etiqueta   — nombre visible del tipo
    codificar  — kwargs del productor -> dict listo para el JSONB (valida)
    resumen    — dict -> una línea para la fila del listado
    describir  — dict -> [(etiqueta, valor)] para el inspector
    """
    codigo: str
    etiqueta: str
    codificar: Callable[..., dict]
    resumen: Callable[[dict], str]
    describir: Callable[[dict], list]


# ---------------------------------------------------------------------------
# CAMBIO_ROL — Mi Perfil (N054)
# ---------------------------------------------------------------------------

def _codificar_cambio_rol(*, rol_solicitado, justificacion):
    rol_solicitado = (rol_solicitado or '').strip().upper()
    justificacion = (justificacion or '').strip()

    if not rol_solicitado:
        raise PayloadInvalido('Indica el rol que solicitas.')
    if not justificacion:
        raise PayloadInvalido('La justificación es obligatoria.')

    # El rol se valida contra la tabla, no contra una lista congelada aquí.
    # Si el catálogo no está disponible (#347) se acepta sin validar: perder la
    # petición del usuario sería peor que guardar un rol que el Supervisor
    # leerá de todos modos antes de concederlo.
    nombres = _nombres_de_roles()
    if nombres is not None and rol_solicitado not in nombres:
        raise PayloadInvalido(f'El rol «{rol_solicitado}» no existe.')

    return {'rol_solicitado': rol_solicitado, 'justificacion': justificacion}


def _nombres_de_roles():
    """Nombres de rol existentes, o None si el catálogo no está disponible."""
    try:
        return {rol.nombre for rol in Rol.query.all()}
    except (OperationalError, ProgrammingError):
        log.warning('Catálogo de roles no disponible — no se valida rol_solicitado')
        return None


# ---------------------------------------------------------------------------
# ALTA_CATALOGO_REQUERIMIENTO — shuttle de ANALIZAR (contrato heredado de #684)
# ---------------------------------------------------------------------------

def _codificar_alta_catalogo_requerimiento(*, texto, categoria):
    texto = (texto or '').strip()
    categoria = (categoria or '').strip().lower()

    if not texto:
        raise PayloadInvalido('El texto del requerimiento propuesto es obligatorio.')
    if categoria not in _CATEGORIAS_REQUERIMIENTO:
        raise PayloadInvalido(f'Categoría «{categoria}» no válida.')

    return {'texto': texto, 'categoria': categoria}


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

TIPOS = {
    'CAMBIO_ROL': TipoMensaje(
        codigo='CAMBIO_ROL',
        etiqueta='Solicitud de cambio de rol',
        codificar=_codificar_cambio_rol,
        resumen=lambda d: f'Solicita el rol {d.get("rol_solicitado", "?")}',
        describir=lambda d: [
            ('Rol solicitado', d.get('rol_solicitado', '')),
            ('Justificación', d.get('justificacion', '')),
        ],
    ),
    'ALTA_CATALOGO_REQUERIMIENTO': TipoMensaje(
        codigo='ALTA_CATALOGO_REQUERIMIENTO',
        etiqueta='Alta en el catálogo de requerimientos',
        codificar=_codificar_alta_catalogo_requerimiento,
        resumen=lambda d: f'Propone un requerimiento «{_recortar(d.get("texto", ""))}»',
        describir=lambda d: [
            ('Categoría', d.get('categoria', '')),
            ('Texto propuesto', d.get('texto', '')),
        ],
    ),
}


def _recortar(texto, limite=60):
    return texto[:limite] + ('…' if len(texto) > limite else '')


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def crear(tipo, remitente_usuario_id, **payload):
    """Crea una petición pendiente. No hace commit (ver cabecera del módulo).

    Lanza PayloadInvalido si el payload no cumple lo que declara su tipo, y
    KeyError si el tipo no está registrado (eso es un bug del llamante, no una
    entrada de usuario).
    """
    declaracion = TIPOS[tipo]
    mensaje = MensajeInterno(
        remitente_usuario_id=remitente_usuario_id,
        tipo=tipo,
        datos=declaracion.codificar(**payload),
    )
    db.session.add(mensaje)
    return mensaje


def resolver(mensaje, *, resultado, notas, usuario_id):
    """Cierra la petición: marca `hecho` y deja veredicto, notas y traza.

    No crea fila nueva — la respuesta vive en la misma (ADR-040 §3). Para el
    Supervisor esto *es* el acuse: no hay un "leído" aparte.
    """
    if resultado not in RESULTADOS:
        raise PayloadInvalido(f'Resultado «{resultado}» no válido.')

    mensaje.hecho = True
    mensaje.resultado = resultado
    mensaje.notas = (notas or '').strip() or None
    mensaje.hecho_por_id = usuario_id
    mensaje.hecho_at = datetime.now(timezone.utc)
    return mensaje


def acusar(mensaje):
    """Acuse explícito del remitente sobre una petición ya resuelta.

    Idempotente: acusar dos veces no mueve la fecha del primer acuse.
    """
    if not mensaje.hecho:
        raise PayloadInvalido('No se puede acusar una petición sin resolver.')
    if mensaje.acusado_at is None:
        mensaje.acusado_at = datetime.now(timezone.utc)
    return mensaje


def etiqueta_tipo(tipo):
    """Nombre visible del tipo. Degrada al código si el tipo es desconocido —
    un mensaje viejo de un tipo retirado se sigue pudiendo listar."""
    declaracion = TIPOS.get(tipo)
    return declaracion.etiqueta if declaracion else tipo


def resumen(mensaje):
    """Una línea para la fila del listado."""
    declaracion = TIPOS.get(mensaje.tipo)
    if not declaracion:
        return etiqueta_tipo(mensaje.tipo)
    try:
        return declaracion.resumen(mensaje.datos or {})
    except Exception:  # payload histórico con otra forma: no romper el listado
        log.warning('Payload no renderizable en mensaje %s (%s)', mensaje.id, mensaje.tipo)
        return declaracion.etiqueta


def describir(mensaje):
    """[(etiqueta, valor)] del payload, para que el inspector lo pinte.

    Devuelve pares, no HTML: el formato visual es del template, la semántica del
    payload es de aquí.
    """
    declaracion = TIPOS.get(mensaje.tipo)
    if not declaracion:
        return [('Contenido', str(mensaje.datos))]
    try:
        return declaracion.describir(mensaje.datos or {})
    except Exception:
        log.warning('Payload no renderizable en mensaje %s (%s)', mensaje.id, mensaje.tipo)
        return [('Contenido', str(mensaje.datos))]


def contar_badge(usuario_id, puede_gestionar):
    """Número del badge del sobre — un solo entero, bimodal (ADR-040 §7).

    Con `gestionar_mensajes_internos`: pendientes de todos + propias resueltas
    sin acusar. Sin él: solo propias resueltas sin acusar.

    El modo lo decide el llamante a partir del permiso del ROL ACTIVO, nunca un
    parámetro del front.
    """
    propias_sin_acusar = MensajeInterno.query.filter(
        MensajeInterno.remitente_usuario_id == usuario_id,
        MensajeInterno.hecho.is_(True),
        MensajeInterno.acusado_at.is_(None),
    ).count()

    if not puede_gestionar:
        return propias_sin_acusar

    pendientes = MensajeInterno.query.filter(
        MensajeInterno.hecho.is_(False)
    ).count()
    return pendientes + propias_sin_acusar
