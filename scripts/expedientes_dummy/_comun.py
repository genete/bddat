"""Piezas compartidas por los expedientes-tipo de esta carpeta.

Extraídas de `analisis_doc_dos_vueltas.py` (#814) al escribir el segundo
expediente-tipo (#862): son las que cualquier escenario necesita —subir un
documento por la vía real, cerrar una NOTIFICAR de verdad, derivar una fecha del
plazo que diga el catálogo— y ninguna es específica de un escenario concreto.

Nada aquí construye escenario: cada módulo de expediente-tipo sigue siendo el
dueño de su propia historia. Los comentarios explican por qué cada pieza hace lo
que hace, porque cada uno viene de un fallo real; no repetirlos en cada script.
"""
import io
import json
import os
import sys
from datetime import date, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Banco de documentos dummy (#814 parte 1). Vive bajo tests/ porque la semilla de
# la base de tests también lo usa — ver README.md de esta carpeta.
FIXTURES_DIR = os.path.join(RAIZ, 'tests', 'fixtures', 'documentos_dummy')

from app import db  # noqa: E402


# ---------------------------------------------------------------------------
# Catálogo — resuelto por clave natural, nunca PK hardcodeado
# ---------------------------------------------------------------------------

def tipo_fase(codigo):
    from app.models.tipos_fases import TipoFase
    return TipoFase.query.filter_by(codigo=codigo).first()


def tipo_tramite(codigo):
    from app.models.tipos_tramites import TipoTramite
    return TipoTramite.query.filter_by(codigo=codigo).first()


def tipo_tarea(codigo):
    from app.models.tipos_tareas import TipoTarea
    return TipoTarea.query.filter_by(codigo=codigo).first()


def tipo_documento(codigo):
    from app.models.tipos_documentos import TipoDocumento
    return TipoDocumento.query.filter_by(codigo=codigo).first()


def titular_y_tramitador():
    """Titular y responsable por rol, no por NIF/siglas concretos (#849): así el
    mismo escenario se construye en desarrollo y en la base de tests, cuyas
    entidades y usuarios son otros a propósito. Orden explícito para que dos
    ejecuciones elijan la misma fila (#836).
    """
    from app.models.entidad import Entidad
    from app.models.usuarios import Usuario, Rol

    entidad = (Entidad.query
               .filter(Entidad.rol_titular.is_(True), Entidad.activo.is_(True))
               .order_by(Entidad.id).first())
    usuario = (Usuario.query
               .join(Usuario.roles)
               .filter(Rol.nombre == 'TRAMITADOR', Usuario.activo.is_(True))
               .order_by(Usuario.id).first())
    return entidad, usuario


def abortar_si_catalogo_incompleto(cat):
    faltantes = [k for k, v in cat.items() if v is None]
    if faltantes:
        print(f"ABORTADO: catálogo incompleto, faltan: {faltantes}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Reciclaje del expediente anterior (marca, sin borrado)
# ---------------------------------------------------------------------------

def reciclar_si_existe(marca):
    """Marca `[RECICLAR]` el expediente de una ejecución anterior de este mismo
    expediente-tipo. No borra: el borrado real es `limpiar_reciclables.py`, y la
    separación ya pagó (el vestigio AT-15 permitió reconstruir qué había pasado
    en una ejecución defectuosa).
    """
    from app.models.solicitudes import Solicitud
    anterior = Solicitud.query.filter(Solicitud.observaciones.like(f'{marca}%')).first()
    if anterior is None:
        print("No hay expediente previo con esta marca — se crea desde cero.")
        return
    numero_at = anterior.expediente.numero_at
    anterior.observaciones = f'[RECICLAR] {anterior.observaciones}'
    db.session.commit()
    print(f"Expediente previo AT-{numero_at} marcado [RECICLAR] (sin borrar).")


# ---------------------------------------------------------------------------
# Cliente HTTP autenticado
# ---------------------------------------------------------------------------

def abrir_cliente(app, usuario):
    """Cliente de test con sesión iniciada y rol activo — la mitad HTTP del
    circuito real (subida multipart, checklist, diagnóstico, acciones de fase).
    """
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(usuario.id)
        sess['_fresh'] = True
        rol = usuario.roles[0] if usuario.roles else None
        if rol:
            sess['rol_activo_id'] = rol.id
            sess['rol_activo_nombre'] = rol.nombre
    return client


# ---------------------------------------------------------------------------
# Subida de documentos dummy (multipart real, ADR-032)
# ---------------------------------------------------------------------------

def subir(client, expediente_id, codigo_tipo_doc, tipo_doc_id, fecha_admin, asunto,
          fichero=None, *, es_principal=False, abre_reformado=False, origen_reformado=None):
    """Sube un documento del banco dummy por la ruta real de ingesta.

    `fichero`: nombre dentro de FIXTURES_DIR; por defecto `<codigo en minúsculas>.pdf`,
    que es como está nombrado el banco.

    `es_principal`/`abre_reformado`/`origen_reformado` (ADR-044 §C/§D, #903): mismas claves
    que lee `declarar_desde_metadatos` del dict de metadatos de un `DOC_PROYECTO` — la rama
    la decide el estado del ancla, no el caller, así que pasar `es_principal=True` cuando el
    proyecto ya tiene ancla, o `abre_reformado=True` cuando todavía no la tiene, simplemente
    no hace nada (ver `rama_de_la_ingesta`).
    """
    nombre = fichero or f'{codigo_tipo_doc.lower()}.pdf'
    with open(os.path.join(FIXTURES_DIR, nombre), 'rb') as f:
        contenido = f.read()
    metadato = {
        'tipo_doc_id': tipo_doc_id,
        'fecha_administrativa': fecha_admin.isoformat(),
        'asunto': asunto,
        'prioridad': False,
    }
    if es_principal:
        metadato['es_principal'] = True
    if abre_reformado:
        metadato['abre_reformado'] = True
        metadato['origen_reformado'] = origen_reformado or 'VOLUNTARIO'
    r = client.post(
        f'/expedientes/{expediente_id}/documentos/subir',
        data={
            'ficheros': (io.BytesIO(contenido), nombre),
            'metadatos': json.dumps([metadato]),
        },
        content_type='multipart/form-data',
    )
    body = r.get_json()
    if not body or not body.get('ok'):
        print(f"ABORTADO: fallo al subir {codigo_tipo_doc}: {body}")
        sys.exit(1)
    return body['documentos'][0]['id']


# ---------------------------------------------------------------------------
# Helpers de mutación con comprobación de bloqueo
# ---------------------------------------------------------------------------

def check(res, etiqueta):
    """Desempaqueta un `ResultadoMutacion`, abortando con el motivo del bloqueo."""
    if not res.ok:
        motivo = res.bloqueo.motivo or res.bloqueo.norma_compilada if res.bloqueo else res.error
        print(f"ABORTADO en {etiqueta}: {motivo}")
        sys.exit(1)
    return res.ids[0] if res.ids else None


def requisito_id(codigo_tipo_doc):
    """`RequisitoDocumental.id` activo para un código de tipo de documento."""
    from app.models.requisitos_documentales import RequisitoDocumental
    from app.models.tipos_documentos import TipoDocumento

    req = (
        RequisitoDocumental.query
        .join(TipoDocumento)
        .filter(TipoDocumento.codigo == codigo_tipo_doc,
                RequisitoDocumental.activo.is_(True))
        .first()
    )
    if req is None:
        print(f"ABORTADO: no hay RequisitoDocumental activo para {codigo_tipo_doc}")
        sys.exit(1)
    return req.id


def cubrir_requisito_tasa(solicitud, doc_tasa_id):
    """Vincula el justificante de pago al requisito documental de la tasa
    (art. 45.1 Ley 10/2021) — bloquea cualquier fase tras ANALISIS_SOLICITUD
    si no está cubierto (variable de motor 'tasa_impagada', calculado.py:287).
    Replica app/routes/api_expedientes.py:vincular_requisito_documental (ahí
    la ruta exige un tarea_id de contexto que aquí no aplica — es un simple
    upsert de DocumentoRequisito, sin motor de por medio)."""
    from app.models.requisitos_documentales import DocumentoRequisito

    db.session.add(DocumentoRequisito(
        requisito_id=requisito_id('JUSTIFICANTE_PAGO_TASA'),
        solicitud_id=solicitud.id, documento_id=doc_tasa_id,
    ))
    db.session.commit()
    print("Requisito de pago de tasa cubierto.")


def requisitos_aplicables(solicitud, fase):
    """Códigos de tipo de documento de los requisitos que el catálogo considera
    aplicables a esta solicitud, en orden de checklist.

    Se pregunta al evaluador real (`evaluar_requisitos`, el mismo que alimenta el
    checklist del contenedor de ANALIZAR) en vez de escribir la lista a mano: un
    expediente-tipo que dice "sin defectos" tiene que seguir sin defectos cuando
    mañana entre un requisito nuevo en el catálogo, o cuando cambien las
    condiciones de uno existente.
    """
    from app.services.assembler import build
    from app.services.requisitos import evaluar_requisitos

    _, variables = build(solicitud.expediente, objeto=fase)
    resultado = evaluar_requisitos(solicitud, variables)
    return [item['requisito'].tipo_documento.codigo for item in resultado['items']]


def casar_requisitos(client, exp_id, tarea_analizar_id, pares, etiqueta):
    """Casa documentos del pool con sus requisitos documentales por el circuito
    real (`POST .../requisitos-documentales/<id>`, #495).

    `pares`: [(codigo_tipo_doc, documento_id), ...].

    Esto es lo que alimenta el checklist del contenedor de ANALIZAR: lo que
    quede sin casar se convierte en defecto documental del diagnóstico
    (`consolidar_defectos`), y el resultado se deriva de ahí. Casar también
    deriva los vínculos CONSUMIDO de la tarea (ADR-033 §1, #677) — por eso los
    scripts NO los vinculan a mano en las tareas ANALIZAR extendidas: la
    sincronización liberaría cualquier consumido que no venga de un requisito.
    """
    for codigo, doc_id in pares:
        r = client.post(
            f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_analizar_id}'
            f'/requisitos-documentales/{requisito_id(codigo)}',
            json={'documento_id': doc_id},
        )
        body = r.get_json() or {}
        if not body.get('ok'):
            print(f"ABORTADO al casar {codigo} en {etiqueta}: {body}")
            sys.exit(1)
    print(f"  checklist {etiqueta}: casados {', '.join(c for c, _ in pares)}.")


def producir_diagnostico(client, exp_id, tarea_analizar_id, etiqueta, resultado=None):
    """Produce el diagnóstico por el circuito real (`POST .../analizar`, ADR-033).

    `resultado` solo se manda en el ANALIZAR simple (consultas y traslados), donde
    el sentido es elección del tramitador: favorable | condicionado | desfavorable.
    En el ANALIZAR extendido (ANALISIS_DOCUMENTAL, REQUERIMIENTO_SUBSANACION) se
    omite: el sentido no se elige, se deriva del borrador consolidado —favorable si
    no queda ningún defecto, desfavorable si queda alguno— y el endpoint ignora lo
    que mande el cliente. Los ítems no cubiertos del checklist quedan congelados en
    `Diagnostico.defectos` con su cita normativa y su `requisito_id` (#724).

    Devuelve el `documento_id` del diagnóstico.
    """
    cuerpo = {} if resultado is None else {'resultado': resultado}
    r = client.post(f'/api/expedientes/{exp_id}/nodo/tarea/{tarea_analizar_id}/analizar',
                    json=cuerpo)
    body = r.get_json() or {}
    if not body.get('ok'):
        print(f"ABORTADO al producir el diagnóstico de {etiqueta}: {body}")
        sys.exit(1)

    doc_id = body['documento']['id']
    from app.models.documentos import Documento
    diag = Documento.query.get(doc_id).diagnostico
    print(f"  diagnóstico {etiqueta}: {diag.resultado} "
          f"({len(diag.defectos or [])} defecto(s) congelado(s)).")
    return doc_id


def notificar(tarea_notif, doc_consumido_id, doc_justificante_id, fecha, etiqueta,
              canal='NOTIFICA'):
    """Cierra NOTIFICAR de verdad — vincula el justificante como PRODUCIDO
    y registra la Notificacion (ADR-034) con resultado CORRECTA.

    El hook automático (_hook_657_notificar_resultado, mutaciones_arbol.py)
    no basta aquí: solo actúa sobre justificantes NOTIFICA parseables de
    verdad (parsear_documento_notifica). Un PDF dummy nunca lo es, así que
    replica a mano el "Registrar puesta a disposición" + "Registrar
    notificación" manuales (api_expedientes.py POST+PATCH
    /nodo/tarea/<id>/notificar) — sin esto la tarea queda en
    PENDIENTE_NOTIFICAR (#814, hallazgo de revisión) y, desde #823, el
    ESPERAR_PLAZO siguiente ni siquiera podría crearse: el invariante de
    precedencia exige la NOTIFICAR del trámite completa (producido y
    `Notificacion.resultado = CORRECTA`).

    `canal`: NOTIFICA para el titular; SIR es el canal entre administraciones,
    el que corresponde a las comunicaciones a organismos.
    """
    from app.models.notificaciones import Notificacion
    from app.services import mutaciones_arbol as svc

    check(svc.editar_tarea(tarea_notif, documentos_consumidos_ids=[doc_consumido_id],
                           documento_producido_id=doc_justificante_id, notas=None),
          f'vincular producido NOTIFICAR {etiqueta}')
    notif = Notificacion.query.filter_by(tarea_id=tarea_notif.id).first()
    if notif is None:
        notif = Notificacion(tarea_id=tarea_notif.id)
        db.session.add(notif)
    notif.documento_id = doc_justificante_id
    notif.canal = canal
    notif.fecha_puesta_disposicion = fecha
    notif.resultado = 'CORRECTA'
    notif.fecha_resultado = fecha
    notif.numero_intento = 1
    db.session.commit()


# ---------------------------------------------------------------------------
# Calendario hábil y plazos
# ---------------------------------------------------------------------------

def inhabiles_entre(desde, hasta):
    """Días inhábiles de BD en el intervalo, para el cómputo local del script."""
    filas = db.session.execute(db.text(
        "SELECT fecha FROM dias_inhabiles WHERE fecha >= :ini AND fecha <= :fin"
    ), {'ini': desde, 'fin': hasta}).fetchall()
    return frozenset(r[0] for r in filas)


def avanzar_habiles(fecha_ini, n):
    """Replica _sumar_dias_habiles de scripts/reloj_dev.py usando db.session
    (ya en contexto Flask aquí, evita duplicar la conexión psycopg2 aparte)."""
    inhabiles = inhabiles_entre(fecha_ini, fecha_ini + timedelta(days=n * 3 + 15))

    cursor = fecha_ini
    dias = 0
    while dias < n:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in inhabiles:
            dias += 1
    return cursor


def retroceder_habiles(fecha_fin, n):
    """Inverso de `avanzar_habiles`: n días hábiles hacia atrás desde `fecha_fin`."""
    inhabiles = inhabiles_entre(fecha_fin - timedelta(days=n * 3 + 15), fecha_fin)

    cursor = fecha_fin
    dias = 0
    while dias < n:
        cursor -= timedelta(days=1)
        if cursor.weekday() < 5 and cursor not in inhabiles:
            dias += 1
    return cursor


def fecha_respuesta_en_plazo(tarea_espera, etiqueta, margen_habiles):
    """Fecha en la que se responde, derivada del plazo REAL de la tarea.

    PATRÓN para los expedientes-tipo (copiar esto, no un número de días): la
    fecha se calcula desde el vencimiento que devuelve el propio servicio de
    plazos para esta ESPERAR_PLAZO —la entrada de `catalogo_plazos` que le
    corresponde por camino y condiciones, con su valor y su unidad— retrocediendo
    `margen_habiles`. Un "+7 días hábiles" fijo diría "dentro de plazo" solo por
    casualidad: si mañana esa entrada pasa de 10 días hábiles a 5, o a meses, el
    escenario dejaría de ser el que dice ser sin que nada avise.

    El margen es lo único que elige el escenario, y elegirlo es decir cuánto
    antes del vencimiento contesta ese interviniente: márgenes amplios dejan sitio
    a los trámites que vienen después dentro de la misma ventana.

    Llamar DESPUÉS de vincular el documento CONSUMIDO que dispara el plazo; sin
    disparo el servicio devuelve SIN_PLAZO y aquí se aborta en vez de inventar
    una fecha. Para el escenario inverso (responde fuera de plazo) basta avanzar
    desde `fecha_limite` en lugar de retroceder.
    """
    from app.services.plazos import obtener_estado_plazo_tarea

    estado = obtener_estado_plazo_tarea(tarea_espera)
    if estado.fecha_limite is None:
        print(f"ABORTADO: la ESPERAR_PLAZO de {etiqueta} no tiene plazo aplicable en "
              f"catálogo (estado {estado.estado}); no se puede situar la respuesta.")
        sys.exit(1)

    fecha = retroceder_habiles(estado.fecha_limite, margen_habiles)
    if estado.fecha_disparo and fecha <= estado.fecha_disparo:
        # Plazo más corto que el margen: la respuesta va al día hábil siguiente
        # al disparo, que sigue estando dentro de plazo.
        fecha = avanzar_habiles(estado.fecha_disparo, 1)
    if fecha > date.today():
        # Seguir solo lleva a que el invariante de #824 rechace el documento
        # siguiente, a media generación y sin pista de por qué.
        print(f"ABORTADO: la respuesta de {etiqueta} caería en {fecha}, posterior a hoy. "
              f"El escenario no cabe en la ventana que se ha reservado — ampliarla.")
        sys.exit(1)
    print(f"  plazo {etiqueta}: {estado.plazo_valor} {estado.plazo_unidad} "
          f"({estado.norma_origen}) — disparo {estado.fecha_disparo}, "
          f"vence {estado.fecha_limite}, responde {fecha}.")
    return fecha
