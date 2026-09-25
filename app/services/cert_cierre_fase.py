"""
CERT_CIERRE_FASE — el cierre de la fase finalizadora (#956, N4b).

ADR-049 §F. Hasta aquí una fase finalizadora (la de Resolución) se cerraba desde el
editor del inspector: un resultado y **cualquier documento del pool** como
«documento de resultado», con un escape a nivel de fase si quedaba algún trámite
sin terminar, y sin comprobar que constara la notificación al titular. Desde #956
cerrarla es emitir este certificado, que:

- responde siempre con un informe «¿cómo voy?» —qué está hecho, qué falta y qué se
  salvó por un escape—, sin crear nada mientras falte algo;
- **solo se emite si no falta nada**, y entre lo que no puede faltar está el
  `CERT_CUMPLIMIENTO_FASE` de #947 (la notificación al titular);
- ocupa `Fase.documento_resultado_id`: emitirlo **es** cerrar la fase, con el
  sellado de ADR-036 que ya existe;
- guarda en `certificados.datos` una **foto fija** del informe (D4);
- se deshace **reabriendo la fase**, con justificación (`deshacer`, al que delega
  `mutaciones_arbol.reabrir_fase`).

QUÉ CUENTA COMO OBLIGATORIO (D1)
================================
Lo **creado** en la fase está completo, el resultado está fijado y el certificado
de cumplimiento está emitido. De lo que **nunca se creó** responde hoy el
tramitador; lo cubrirá #805 (vigilante de trámites obligatorios sin crear), que
entrará por `_pendientes_de_creacion`.

SIN ESCAPE A NIVEL DE FASE (D2)
===============================
Con cualquier pendiente no se emite, y no hay justificación que lo evite. Es el
modelo de `CERT_FIN_INSTRUCCION`: cada escape se registra en su propio acto y nodo
—la tarea, el trámite—, y el certificado solo los **lee y relata** como salvados.
Cerrar la finalizadora con un organismo o un interesado sin notificar es zona de
nulidad (art. 47.1.e LPACAP) o de anulabilidad por indefensión (art. 48.2), por
mucho que se justifique en bitácora: mejor la fase abierta y el escape quirúrgico
de lo que de verdad lo admita. Excepción razonada al criterio de #723 (allí la
puerta cerrada se reservó a cuando el acto ya salió fuera; aquí ya salió, porque se
exige el certificado de cumplimiento) y enmienda de la D4 de #928 para las
finalizadoras (la sede pendiente ya no se fuerza al cerrar la fase: se justifica en
su tarea, `sede_justificacion`).

FOTO FIJA (D4)
==============
Al emitir se guarda en `datos` el informe ya redactado. La vista del emitido lee de
ahí y no recalcula; el borrador se calcula y no se guarda (§F: «con sello se lee»).
El sellado de ADR-036 no protege la fecha, el tipo ni el fichero de los documentos
de la fase en el pool (#954): un certificado pintado en directo podría cambiar de
contenido en silencio.

IRREVERSIBLE CUANDO RESUELVE LA SOLICITUD (D5)
==============================================
`_check_reabrir` no cambia: con la solicitud RESUELTA y notificada ninguna fase se
reabre. Como emitir exige el certificado de cumplimiento —la notificación al
titular—, el certificado que cierra la **última** finalizadora es irreversible
dentro de BDDAT. Por eso, cuando la emisión deja la solicitud resuelta
(`cierra_solicitud`), se exige la confirmación expresa (`FRASE_CONFIRMACION`), que
la interfaz pide escribiendo la frase y que aquí se comprueba para que no se salte
llamando a la API.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from flask_login import current_user

from app import db
from app.models.certificados import Certificado
from app.models.documentos import Documento
from app.models.tipos_documentos import TipoDocumento
from app.services import bitacora as bitacora_svc
from app.services import informe_instruccion as informe_svc
from app.services import sellos
from app.services.actos_solicitud import actos_de, fase_de
from app.services.assembler import build_sujeto
from app.services.informe_instruccion import PASA, PENDIENTE, SALVADO, Bloque
from app.services.invariantes_esftt import (
    advertir_documentos_criticos_huerfanos, check_invariante,
)

log = logging.getLogger(__name__)

CODIGO_CERT = sellos.CERT_CIERRE_FASE

# La confirmación expresa del cierre irreversible (D5). La interfaz la pide
# escrita, como al borrar un repositorio en GitHub; el backend la compara sin
# distinguir mayúsculas ni espacios de los extremos.
FRASE_CONFIRMACION = 'cerrar finalizadora'

# Cómo consta en bitácora el deshacer: lo mismo que `reabrir_fase` (`escape: True`,
# `accion: REABRIR`, ADR-036 #720) más el certificado retirado. Así los listados de
# escapes siguen viendo toda reapertura igual, y `informe_instruccion.
# relato_reaperturas_fase` la cuenta en el relato del certificado siguiente.
ACCION_REABRIR = 'REABRIR'

# Versión de la forma de `datos` (foto fija). Si cambia la plantilla de la vista,
# la del emitido tiene que seguir sabiendo leer lo que se congeló con la anterior.
VERSION_DATOS = 1


# ---------------------------------------------------------------------------
# Revisión — el informe «¿cómo voy?», sin efectos
# ---------------------------------------------------------------------------

@dataclass
class Informe:
    """El informe de cierre de una fase: bloques ya redactados + lo que decide.

    `bloques` son `informe_instruccion.Bloque`: el primero es el de la fase, que
    compone este módulo; después uno por trámite, redactado por
    `informe_instruccion.bloque_tramite`, que reutiliza PENDIENTE/SALVADO/PASA y el
    relato de escapes de bitácora.
    """
    fase: object
    finalizadora: bool
    bloques: list = field(default_factory=list)
    cierra_solicitud: bool = False
    # No bloqueante (#738): justificantes del pool sin vincular a ninguna tarea.
    advertencia: Optional[dict] = None

    @property
    def limpio(self) -> bool:
        return self.finalizadora and not any(b.categoria == PENDIENTE for b in self.bloques)

    @property
    def pendientes(self) -> list:
        return [b for b in self.bloques if b.categoria == PENDIENTE]

    @property
    def salvados(self) -> list:
        return [b for b in self.bloques if b.salvado]

    @property
    def falta(self) -> Optional[str]:
        """Frase única para los errores de verdad; lo que falta va en los bloques."""
        if not self.finalizadora:
            return ('Solo las fases finalizadoras se cierran con certificado de cierre: '
                    'esta fase no resuelve ningún acto.')
        return None

    def a_dict(self) -> dict:
        return {
            'limpio': self.limpio,
            'cierra_solicitud': self.cierra_solicitud,
            'bloques': [b.a_dict() for b in self.bloques],
            'pendientes': [b.a_dict() for b in self.pendientes],
            'salvados': [b.a_dict() for b in self.salvados],
            'advertencia': self.advertencia,
        }


def revisar(fase) -> Informe:
    """El informe de cierre de `fase`, sin crear nada. Se puede repetir.

    Orden de los bloques: la fase habla de sí misma (encabezado, resultado,
    notificación al titular, reaperturas y escapes propios) y después cada trámite.
    El estado «pendiente de cerrar» de la propia fase **no** cuenta como pendiente:
    es el acto que se está haciendo (como las reglas del art. 82.1 en el de
    instrucción). Sí cuenta que falte el resultado (D3).
    """
    finalizadora = bool(fase.tipo_fase and fase.tipo_fase.es_finalizadora)
    if not finalizadora:
        return Informe(fase=fase, finalizadora=False)

    escapes = informe_svc.escapes_de_fase(fase)
    bloques = _bloques_de_fase(fase, escapes)
    for tramite in sorted(fase.tramites, key=lambda t: t.id):
        bloque = informe_svc.bloque_tramite(tramite, escapes)
        if bloque is not None:
            bloques.append(bloque)
    bloques.extend(_pendientes_de_creacion(fase))

    return Informe(
        fase=fase,
        finalizadora=True,
        bloques=bloques,
        cierra_solicitud=cierra_solicitud(fase),
        advertencia=advertir_documentos_criticos_huerfanos(fase.solicitud.expediente_id),
    )


def cierra_solicitud(fase) -> bool:
    """True si cerrar `fase` dejaría la solicitud resuelta (D5).

    `Solicitud.estado` pasa a RESUELTA_* cuando todas las fases están cerradas y
    alguna es finalizadora; como `fase` lo es, basta con que las demás lo estén. Con
    dos finalizadoras (RESOLUCION + RESOLUCION_DUP), cerrar la primera no la
    resuelve y se deshace con una reapertura normal.
    """
    return all(f.finalizada for f in fase.solicitud.fases if f is not fase)


def _bloques_de_fase(fase, escapes: dict) -> list:
    """Lo que la fase dice de sí misma, compuesto aquí y no por
    `informe_instruccion._fase`: aquella trata el «pendiente de cerrar» como
    pendiente, y aquí es precisamente el acto que se hace."""
    nombre = _nombre_fase(fase)
    bloques = []

    # 1. La fase: encabezado, resultado, reaperturas anteriores y escapes propios.
    tipo_sol = fase.solicitud.tipo_solicitud
    actos = _actos(fase)
    relato = [f'Fase «{nombre}» de la solicitud #{fase.solicitud_id} '
              f'({tipo_sol.siglas if tipo_sol else "sin tipo"})'
              + (f', que resuelve {", ".join(actos)}.' if actos else '.')]
    pendiente = []
    if fase.resultado_fase is not None:
        relato.append(f'Resultado de la fase: '
                      f'{fase.resultado_fase.nombre or fase.resultado_fase.codigo}.')
    else:
        pendiente.append('Falta decidir el resultado de la fase: fíjelo en el editor de '
                         'la fase antes de cerrarla.')
    if fase.planificada:
        pendiente.append('La fase no tiene ningún trámite: no hay nada hecho que '
                         'certificar.')
    relato.extend(informe_svc.relato_reaperturas_fase(escapes, fase, codigo_cert=CODIGO_CERT))
    # Escapes propios de la fase (p. ej. cierres forzados anteriores a #956). Las
    # reaperturas ya van en el relato: no se repiten como salvadas.
    salvado = informe_svc.relato_escapes(
        escapes, 'fases', fase.id, f'la fase «{nombre}»',
        excluir_acciones=frozenset({ACCION_REABRIR}))
    bloques.append(Bloque(
        PENDIENTE if pendiente else (SALVADO if salvado else PASA),
        f'Fase «{nombre}»',
        relato=tuple(relato), pendiente=tuple(pendiente), salvado=salvado,
        nodo=('fase', fase.id),
    ))

    # 2. La notificación al titular, por su certificado (#947). Sin escape posible.
    cumplimiento = sellos.certificado_cumplimiento(fase)
    if cumplimiento is None:
        bloques.append(Bloque(
            PENDIENTE, 'Notificación al titular',
            pendiente=('No consta certificado el cumplimiento: emita antes el '
                       'certificado de cumplimiento de la fase, que acredita la '
                       'notificación al titular.',),
            nodo=('fase', fase.id),
        ))
    else:
        citado = sellos.documento_citado(cumplimiento)
        detalle = ''
        if citado is not None:
            tipo = citado.tipo_doc.nombre if citado.tipo_doc else f'Documento {citado.id}'
            fecha = (f' de {citado.fecha_administrativa.strftime("%d/%m/%Y")}'
                     if citado.fecha_administrativa else '')
            detalle = f', acreditada por {tipo}{fecha} (nº {citado.id})'
        momento = sellos.momento_emision(cumplimiento)
        emitido = f', emitido el {momento.strftime("%d/%m/%Y")}' if momento else ''
        bloques.append(Bloque(
            PASA, 'Notificación al titular',
            relato=(f'Consta la notificación al titular{detalle}, según el certificado '
                    f'de cumplimiento nº {cumplimiento.id}{emitido}.',),
            nodo=('fase', fase.id),
        ))
    return bloques


def _pendientes_de_creacion(fase) -> list:
    """Hueco para #805 (D1): los trámites obligatorios de la fase que nunca se
    crearon, como bloques PENDIENTE.

    Hoy no hay quien lo sepa —de lo nunca creado responde el tramitador—, así que
    devuelve una lista vacía. Cuando #805 exista (vigilante de trámites obligatorios
    sin crear, efecto `RECORDAR`), este es el punto único donde entran: un bloque por
    trámite que falta, con su `nodo` apuntando a la fase donde crearlo.
    """
    return []


# ---------------------------------------------------------------------------
# Emitir — el cierre
# ---------------------------------------------------------------------------

@dataclass
class Emision:
    """Resultado del gesto: siempre hay informe; a veces, además, certificado.

    `error` y `bloqueo` son para fallos reales —fase no finalizadora, catálogo sin
    el tipo, falta la confirmación del cierre irreversible, la puerta cerrada dijo
    que no—, no para «faltan cosas»: eso es el informe con pendientes, y no se ha
    creado nada.
    """
    informe: Informe
    emitido: bool = False
    ya_emitido: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    requiere_confirmacion: bool = False
    error: Optional[str] = None
    bloqueo: object = None

    def a_dict(self) -> dict:
        datos = self.informe.a_dict()
        datos.update({
            'emitido': self.emitido,
            'ya_emitido': self.ya_emitido,
            'documento_id': self.documento_id,
            'certificado_id': self.certificado_id,
            'requiere_confirmacion': self.requiere_confirmacion,
        })
        return datos


def confirmacion_valida(confirmacion) -> bool:
    return (confirmacion or '').strip().lower() == FRASE_CONFIRMACION


def emitir(fase, *, confirmacion: Optional[str] = None) -> Emision:
    """Cierra `fase` emitiendo su `CERT_CIERRE_FASE`, si no falta nada.

    - ya emitido → el existente, sin tocar nada;
    - informe con pendientes → el informe, y nada creado;
    - deja la solicitud resuelta sin la confirmación expresa → error, nada creado (D5);
    - limpio → `Documento` (`fecha_administrativa` NULL, url
      `bddat://certificados/{id}`) + `Certificado(tipo, fase_id, datos=<foto
      fija>)` + `fase.documento_resultado_id` = ese documento + bitácora
      `CREAR documentos`. El cierre es este acto: no pasa por `editar_fase`.
    """
    existente = sellos.certificado_cierre(fase)
    if existente is not None:
        return Emision(informe=revisar(fase), emitido=True, ya_emitido=True,
                       documento_id=existente.documento_id, certificado_id=existente.id)

    informe = revisar(fase)
    if not informe.finalizadora:
        return Emision(informe=informe, error=informe.falta)
    if not informe.limpio:
        return Emision(informe=informe)

    if informe.cierra_solicitud and not confirmacion_valida(confirmacion):
        return Emision(
            informe=informe, requiere_confirmacion=True,
            error=(f'Cerrar esta fase deja la solicitud resuelta, y con la notificación '
                   f'ya hecha no podrá reabrirse: confírmelo escribiendo '
                   f'«{FRASE_CONFIRMACION}».'),
        )

    # Puerta cerrada: sus supuestos ya los cubre el informe; se comprueba igualmente
    # porque el invariante tiene la última palabra (mismo criterio que
    # `cert_fin_instruccion.consolidar` y `cert_cumplimiento_fase.emitir`).
    res_inv = check_invariante('EMITIR', 'FASE', fase.id, tipo_codigo=CODIGO_CERT)
    if res_inv is not None:
        log.warning('cert_cierre_fase: el informe de la fase %s salió limpio pero el '
                    'invariante bloquea — %s', fase.id,
                    res_inv.motivo or res_inv.norma_compilada)
        return Emision(informe=informe, bloqueo=res_inv)

    tipo_doc = TipoDocumento.query.filter_by(codigo=CODIGO_CERT).first()
    if tipo_doc is None:
        return Emision(informe=informe,
                       error=f'TipoDocumento {CODIGO_CERT!r} no encontrado en el catálogo.')

    expediente = fase.solicitud.expediente
    try:
        documento = Documento(
            expediente_id=expediente.id,
            tipo_doc_id=tipo_doc.id,
            url='bddat://certificados/0',   # provisional hasta tener cert.id
            fecha_administrativa=None,
            asunto=f'Cierre de la fase — {_nombre_fase(fase)}',
        )
        db.session.add(documento)
        db.session.flush()

        # Por las relaciones y no por los id a pelo: así `fase.certificados_cumplimiento`
        # y `documento.certificado`, si ya estaban cargados, ven el certificado nuevo.
        certificado = Certificado(
            documento=documento, tipo=CODIGO_CERT, fase=fase,
            datos=foto_fija(informe),
            generado_en=datetime.now(UTC).replace(tzinfo=None),
        )
        db.session.add(certificado)
        db.session.flush()
        documento.url = f'bddat://certificados/{certificado.id}'

        # Cerrar la fase ES esto (D6). Por la relación, para que `fase.finalizada`
        # y `solicitud.estado` lo vean en la misma sesión.
        fase.documento_resultado = documento
        db.session.flush()

        bitacora_svc.registrar(
            current_user.id, 'CREAR', 'documentos', documento.id,
            detalle={
                'tipo_documento': CODIGO_CERT,
                'fase_id': fase.id,
                'certificado_id': certificado.id,
                'cierra_solicitud': informe.cierra_solicitud,
                'actos_salvados': sum(len(b.salvado) for b in informe.salvados),
                'sujeto': build_sujeto(expediente, fase),
            },
        )
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cierre_fase: fallo emitiendo el de la fase %s: %s', fase.id, exc)
        return Emision(informe=informe, error=str(exc))

    log.info('CERT_CIERRE_FASE emitido: doc=%s cert=%s fase=%s expediente=%s '
             '(cierra solicitud: %s)', documento.id, certificado.id, fase.id,
             expediente.id, informe.cierra_solicitud)
    return Emision(informe=informe, emitido=True,
                   documento_id=documento.id, certificado_id=certificado.id)


def foto_fija(informe: Informe) -> dict:
    """El informe congelado que se guarda en `certificados.datos` (D4).

    Texto ya redactado, no ids que haya que volver a resolver: la vista del emitido
    lo pinta tal cual, aunque después cambie la fecha, el tipo o el fichero de algún
    documento de la fase en el pool (#954). La huella —número de certificado y de
    documento, emisión— no va aquí: es de la propia fila.
    """
    fase = informe.fase
    expediente = fase.solicitud.expediente
    tipo_sol = fase.solicitud.tipo_solicitud
    return {
        'version': VERSION_DATOS,
        'expediente': f'AT-{expediente.numero_at}',
        'solicitud': tipo_sol.siglas if tipo_sol else f'Solicitud #{fase.solicitud_id}',
        'fase': _nombre_fase(fase),
        'actos': _actos(fase),
        'resultado': (fase.resultado_fase.nombre or fase.resultado_fase.codigo
                      if fase.resultado_fase is not None else None),
        'cierra_solicitud': informe.cierra_solicitud,
        'bloques': [b.a_dict() for b in informe.bloques],
    }


# ---------------------------------------------------------------------------
# Deshacer — reabrir la fase finalizadora
# ---------------------------------------------------------------------------

@dataclass
class Reversion:
    """Resultado de deshacer: qué se retiró, o por qué no pudo retirarse."""
    ok: bool = False
    documento_id: Optional[int] = None
    certificado_id: Optional[int] = None
    error: Optional[str] = None
    bloqueo: object = None


def deshacer(fase, *, justificacion: str) -> Reversion:
    """Reabre la fase finalizadora retirando su certificado de cierre. Es
    `reabrir_fase` para las finalizadoras: `mutaciones_arbol.reabrir_fase` delega
    aquí.

    - `justificacion` obligatoria: no hay reapertura silenciosa.
    - `_check_reabrir` sin cambios (D5): con la solicitud resuelta y notificada es
      puerta cerrada.
    - Borra la fila de `certificados` y su `Documento`, y vacía
      `documento_resultado_id` y `resultado_fase_id` (como hoy `reabrir_fase`).
    - Bitácora `ALTERAR fases`: lo mismo que `reabrir_fase` más el documento y el
      certificado retirados. La relata el certificado siguiente.

    Una finalizadora cerrada antes de #956 —con un documento del pool, sin
    certificado— se reabre igual, vaciando los dos campos sin nada que borrar.
    """
    if not fase.finalizada:
        return Reversion(error='La fase no está cerrada.')
    if not justificacion or not justificacion.strip():
        return Reversion(error='La reapertura de una fase requiere justificación.')

    res_inv = check_invariante('REABRIR', 'FASE', fase.id)
    if res_inv is not None:
        return Reversion(bloqueo=res_inv)

    certificado = sellos.certificado_cierre(fase)
    documento = certificado.documento if certificado is not None else None
    # Nada lo consume por catálogo, pero la Despensa deja vincular cualquier
    # documento del pool: borrarlo con el vínculo vivo moriría en IntegrityError.
    if documento is not None and documento.vinculos_tarea:
        tarea = documento.vinculos_tarea[0].tarea
        return Reversion(error=(
            f'El certificado de cierre está vinculado a la tarea «{_nombre_tarea(tarea)}»: '
            f'desvincúlelo de ella antes de reabrir la fase.'
        ))

    documento_id = documento.id if documento is not None else None
    certificado_id = certificado.id if certificado is not None else None
    expediente = fase.solicitud.expediente

    try:
        fase.resultado_fase_id = None
        fase.documento_resultado = None
        db.session.flush()
        if certificado is not None:
            db.session.delete(certificado)
            db.session.flush()
            db.session.delete(documento)
            db.session.flush()

        detalle = {
            'escape': True, 'justificacion': justificacion.strip(),
            'sujeto': build_sujeto(expediente, fase), 'accion': ACCION_REABRIR,
        }
        if certificado is not None:
            detalle.update({'tipo_documento': CODIGO_CERT, 'documento_id': documento_id,
                            'certificado_id': certificado_id})
        bitacora_svc.registrar(current_user.id, 'ALTERAR', 'fases', fase.id, detalle=detalle)
        db.session.commit()
    except Exception as exc:  # noqa: BLE001 — se devuelve al llamador, no se traga
        db.session.rollback()
        log.error('cert_cierre_fase: fallo reabriendo la fase %s: %s', fase.id, exc)
        return Reversion(error=str(exc))

    log.info('CERT_CIERRE_FASE deshecho (fase reabierta): doc=%s cert=%s fase=%s',
             documento_id, certificado_id, fase.id)
    return Reversion(ok=True, documento_id=documento_id, certificado_id=certificado_id)


# ---------------------------------------------------------------------------
# Vista — lo que pinta la plantilla, emitido o calculado
# ---------------------------------------------------------------------------

@dataclass
class Vista:
    """Datos de la plantilla única. Emitido, todo sale de `datos` (foto fija) y de
    la propia fila; sin emitir, del informe calculado ahora."""
    expediente: str
    solicitud: str
    fase_id: int
    fase: str
    actos: list
    resultado: Optional[str]
    emitido: bool
    limpio: bool
    cierra_solicitud: bool
    pendientes: list          # [Bloque-dict] — solo en el borrador
    salvados: list            # [Bloque-dict]
    relato: list              # [str]
    advertencia: Optional[str] = None
    falta: Optional[str] = None
    certificado_id: Optional[int] = None
    documento_certificado_id: Optional[int] = None
    emitido_en: Optional[str] = None
    calculado_en: Optional[str] = None


def vista(fase) -> Vista:
    """La vista del certificado de cierre de `fase`: el emitido, leído de su foto
    fija; o, si no lo hay, el informe calculado al vuelo, sin guardar nada."""
    certificado = sellos.certificado_cierre(fase)
    if certificado is not None:
        datos = certificado.datos or {}
        bloques = datos.get('bloques') or []
        momento = sellos.momento_emision(certificado)
        return Vista(
            expediente=datos.get('expediente', ''),
            solicitud=datos.get('solicitud', ''),
            fase_id=fase.id,
            fase=datos.get('fase', _nombre_fase(fase)),
            actos=datos.get('actos') or [],
            resultado=datos.get('resultado'),
            emitido=True, limpio=True,
            cierra_solicitud=bool(datos.get('cierra_solicitud')),
            pendientes=[],
            salvados=[b for b in bloques if b.get('salvado')],
            relato=[linea for b in bloques for linea in (b.get('relato') or [])],
            certificado_id=certificado.id,
            documento_certificado_id=certificado.documento_id,
            emitido_en=momento.strftime('%d/%m/%Y %H:%M') if momento else None,
        )

    informe = revisar(fase)
    expediente = fase.solicitud.expediente
    tipo_sol = fase.solicitud.tipo_solicitud
    return Vista(
        expediente=f'AT-{expediente.numero_at}',
        solicitud=tipo_sol.siglas if tipo_sol else f'Solicitud #{fase.solicitud_id}',
        fase_id=fase.id,
        fase=_nombre_fase(fase),
        actos=_actos(fase),
        resultado=(fase.resultado_fase.nombre or fase.resultado_fase.codigo
                   if fase.resultado_fase is not None else None),
        emitido=False, limpio=informe.limpio,
        cierra_solicitud=informe.cierra_solicitud,
        pendientes=[b.a_dict() for b in informe.pendientes],
        salvados=[b.a_dict() for b in informe.salvados],
        relato=[linea for b in informe.bloques for linea in b.relato],
        advertencia=(informe.advertencia or {}).get('motivo'),
        falta=informe.falta,
        calculado_en=datetime.now().strftime('%d/%m/%Y %H:%M'),
    )


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def _actos(fase) -> list:
    return [acto.siglas for acto in actos_de(fase.solicitud) if fase_de(acto) is fase]


def _nombre_fase(fase) -> str:
    tf = fase.tipo_fase
    return (tf.nombre or tf.codigo) if tf else f'Fase #{fase.id}'


def _nombre_tarea(tarea) -> str:
    """«Trámite › Tarea (#id)»: lo que el técnico busca en el árbol."""
    tt = tarea.tipo_tarea
    tr = tarea.tramite.tipo_tramite
    nombre_tarea = (tt.nombre if tt else None) or 'Tarea'
    nombre_tramite = (tr.nombre if tr else None) or 'Trámite'
    return f'{nombre_tramite} › {nombre_tarea} (#{tarea.id})'
