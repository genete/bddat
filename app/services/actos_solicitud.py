"""El acto: la unidad del plazo para resolver (#930, ADR-049 §E).

Una solicitud `AAP+AAC+DUP` pide tres autorizaciones, cada una con su artículo
y su plazo (3, 3 y 6 meses). La solicitud es un contenedor; quien cumple o
incumple el plazo de resolver es cada **acto**. Aquí el acto es un valor
derivado —cada tipo atómico de `solicitud.tipos_simples`— y no una entidad:
nada que guardar ni que sincronizar, sin tabla y sin consultas propias (solo
lee `solicitud.fases` y `fase.tipo_fase`, que el árbol ya carga).

La división simple manda: `AAP+AAC` son dos actos aunque se resuelvan juntos
en una sola `RESOLUCION`, y `AE_DEFINITIVA+AAT` dos actos de 1 y 3 meses.

FUENTE ÚNICA DE «QUÉ FASE RESUELVE CADA ACTO» (D4)
==================================================

Antes vivía en `informe_instruccion`, indexado por combinación de solicitud
(`AAC+DUP`, `AAP+DUP`…): la huella del supuesto «una solicitud = un acto». Por
acto colapsa a cuatro reglas con los mismos resultados en los 22 tipos de
solicitud. `informe_instruccion.codigos_fase_finalizadora` y el guardián de
`app/checks/catalogo_requerido.py` consumen este módulo; no hay dos verdades.

Es un invariante en código (ADR-046/047 lo fijan), no regla del motor ni dato
de catálogo: si aparece una finalizadora nueva en `tipos_fases` y no aquí, lo
dicen el aviso de arranque de `catalogo_requerido` y el test de catálogo.

¿ESTÁ RESUELTO CADA ACTO? (#996, D6)
====================================

`actos_sin_resolver` es la única respuesta a «¿queda algún acto sin su fase de
resolución creada y cerrada?». La usan `Solicitud.estado` (la solicitud no está
resuelta mientras quede alguno), `cert_cierre_fase.cierra_solicitud` (¿cerrar
esta fase es lo último?) y el certificado de cierre de la solicitud. Antes de
#996 el estado contaba solo las fases que existen, y una `AAC+DUP` con la
`RESOLUCION` cerrada y sin `RESOLUCION_DUP` salía resuelta y firme. El filtro SQL
del seguimiento no puede llamarla —no tiene la solicitud cargada— y se genera
desde el mismo mapa con `fases_resolutoras_de_siglas`.

Dependencias en una sola dirección: este módulo importa
`services.notificaciones` (el cumplimiento); `notificaciones` no importa este.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.services.notificaciones import documento_cumplimiento_fase

# Actos con fase propia, se resuelvan como se resuelvan los demás.
_FASE_DE_ACTO = {
    'DUP': 'RESOLUCION_DUP',
    'INTERESADO': 'RECONOCIMIENTO_INTERESADO',
}
# El resto —AAT, AE_*, CIERRE, RAIPEE_*, RECURSO…— se resuelve por RESOLUCION.
_FASE_POR_DEFECTO = 'RESOLUCION'

# Resolución partida (ADR-047 §B, #918): AAP y AAC en fases separadas. Es una
# elección del técnico en tiempo de ejecución, así que se lee del árbol: si
# consta RESOLUCION_AAP o RESOLUCION_AAC, la solicitud se resuelve partida;
# sin elección todavía, conjunta (nadie fuerza la elección antes de tiempo).
# Solo cabe en las dos solicitudes que piden AAP y AAC a la vez.
_FASE_DE_ACTO_PARTIDA = {
    'AAP': 'RESOLUCION_AAP',
    'AAC': 'RESOLUCION_AAC',
}
_SOLICITUDES_PARTIBLES = frozenset({'AAP+AAC', 'AAP+AAC+DUP'})
# Las fases cuya mera existencia dice que la solicitud se resuelve partida.
FASES_PARTIDAS = frozenset(_FASE_DE_ACTO_PARTIDA.values())

# Todo lo que el mapa puede emitir. El guardián de catalogo_requerido lo
# compara con `TipoFase.es_finalizadora`.
FASES_RESOLUTORAS = frozenset({
    'RESOLUCION', 'RESOLUCION_AAP', 'RESOLUCION_AAC',
    'RESOLUCION_DUP', 'RECONOCIMIENTO_INTERESADO',
})


@dataclass(frozen=True)
class ActoSolicitud:
    """Un acto de la solicitud: su tipo atómico, dentro de su contenedor.

    El atributo se llama `solicitud` a propósito: `plazos._resolver_campo_fecha`
    sube a `elemento.solicitud` cuando el elemento no tiene el atributo del
    `fk` (mecanismo de ADR-048), así que el disparo del plazo del acto
    —`documento_solicitud_id`— se resuelve sin código nuevo.
    """
    solicitud: object          # Solicitud (sin import: evita el ciclo con los modelos)
    siglas: str                # tipo atómico: 'AAP', 'AAC', 'DUP'…

    @property
    def documento_cumplimiento(self) -> Optional['Documento']:  # noqa: F821
        """Documento que acredita la notificación al solicitante en la fase que
        resuelve este acto, o `None` (la fase aún no existe, o no consta).

        Delega (D1): la regla de cumplimiento existe una sola vez, en
        `notificaciones.documento_cumplimiento_fase`, y el acto solo la
        expone. Es la propiedad que nombra `{"calculado":
        "documento_cumplimiento"}` en `catalogo_plazos`. Dos actos resueltos
        por la misma fase (AAP y AAC en una RESOLUCION) reciben el mismo
        documento: una notificación cumple los dos plazos, cada uno contra el
        suyo.
        """
        fase = fase_de(self)
        return documento_cumplimiento_fase(fase) if fase is not None else None


def actos_de(solicitud) -> list[ActoSolicitud]:
    """Un acto por cada tipo atómico de la solicitud; `[]` sin tipo."""
    return [ActoSolicitud(solicitud=solicitud, siglas=s) for s in solicitud.tipos_simples]


def fase_resolutora(solicitud, siglas: str) -> str:
    """Código de la fase que resuelve el acto `siglas`, exista ya o no."""
    partida = siglas in _FASE_DE_ACTO_PARTIDA and _resuelta_partida(solicitud)
    return _fase_de_siglas(siglas, partida=partida)


def _fase_de_siglas(siglas: str, *, partida: bool) -> str:
    """El mapa acto → fase, con la elección conjunta/partida ya hecha."""
    if siglas in _FASE_DE_ACTO:
        return _FASE_DE_ACTO[siglas]
    if partida and siglas in _FASE_DE_ACTO_PARTIDA:
        return _FASE_DE_ACTO_PARTIDA[siglas]
    return _FASE_POR_DEFECTO


def fases_resolutoras_de_siglas(siglas_solicitud: str) -> tuple[frozenset, Optional[frozenset]]:
    """Las fases que resuelven los actos de un tipo de solicitud, sin mirar el
    árbol: `(conjunta, partida)`, con `partida` None si el tipo no admite
    resolución partida (#996).

    Para quien pregunta en SQL y no tiene la solicitud cargada —el filtro por
    estado del seguimiento—: la misma regla que `fase_resolutora`, desde las
    siglas del tipo. `'AAC+DUP'` → `({'RESOLUCION', 'RESOLUCION_DUP'}, None)`;
    `'AAP+AAC'` → `({'RESOLUCION'}, {'RESOLUCION_AAP', 'RESOLUCION_AAC'})`. Cuál
    de las dos vale lo decide el árbol: partida si consta alguna de `FASES_PARTIDAS`.
    """
    actos = siglas_solicitud.split('+') if siglas_solicitud else []
    conjunta = frozenset(_fase_de_siglas(s, partida=False) for s in actos)
    if siglas_solicitud not in _SOLICITUDES_PARTIBLES:
        return conjunta, None
    return conjunta, frozenset(_fase_de_siglas(s, partida=True) for s in actos)


def fase_de(acto: ActoSolicitud):
    """La `Fase` que resuelve el acto, de las que ya constan en
    `solicitud.fases`, o `None`: nace al final de la instrucción, mucho después
    de que el plazo empiece a correr."""
    codigo = fase_resolutora(acto.solicitud, acto.siglas)
    return next(
        (f for f in acto.solicitud.fases if f.tipo_fase and f.tipo_fase.codigo == codigo),
        None,
    )


def actos_sin_resolver(solicitud, *, contando_cerrada=None) -> list[ActoSolicitud]:
    """Los actos de `solicitud` cuya fase de resolución no existe o no está
    cerrada (#996, D6). Lista vacía = cada acto tiene la suya creada y cerrada.

    `contando_cerrada` es una fase que se da por cerrada aunque aún no lo esté:
    la pregunta de `cert_cierre_fase.cierra_solicitud`, «si cierro esta, ¿queda
    alguno?».

    Una solicitud con DUP que termina sin resolver el fondo (tenida por
    desistida, archivada…) tampoco está resuelta hasta que la parte de la DUP se
    cierre en su propia fase: son dos actos de órganos distintos, que no pueden
    ser el mismo ni compartir pie de recurso (ADR-045 §B; decisión de Carlos en
    #996).

    Sin consultas: lee `tipo_solicitud`, `fases` y `fase.tipo_fase`, que el árbol
    ya carga (`opciones_solicitud`), y `finalizada`, que es una columna.
    """
    pendientes = []
    for acto in actos_de(solicitud):
        fase = fase_de(acto)
        if fase is None or not (fase is contando_cerrada or fase.finalizada):
            pendientes.append(acto)
    return pendientes


def _resuelta_partida(solicitud) -> bool:
    """La solicitud pide AAP y AAC y en el árbol consta alguna de sus fases
    partidas. Con solo `RESOLUCION_AAP` creada, la AAC ya va a `RESOLUCION_AAC`
    aunque aún no exista: la elección está hecha."""
    tipo = solicitud.tipo_solicitud
    if tipo is None or tipo.siglas not in _SOLICITUDES_PARTIBLES:
        return False
    partidas = set(_FASE_DE_ACTO_PARTIDA.values())
    return any(f.tipo_fase and f.tipo_fase.codigo in partidas for f in solicitud.fases)
