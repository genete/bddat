"""Usos de un documento: qué cosas del sistema lo referencian (#881, ADR-053 §F).

Un **uso** es cada fila de otra tabla que apunta al documento: una tarea que lo consume o
lo produce, la solicitud que lo ancla, la notificación que acredita, un certificado… El
pool lo enseña como columna (nº de usos y, al pasar el ratón, cuáles) y el borrado lo lee
como guarda: **todo uso bloquea el borrado** (decisión de Carlos, 01/11/2026). El radar de
huérfanos lo usa para distinguir un documento sin destino de uno con destino declarado
pero sin tarea (el principal del proyecto, los reformados).

UN SOLO REGISTRO, NACIDO DE LAS FK REALES
=========================================
`REFERENCIAS` tiene una entrada por **cada FK** de la BD hacia `documentos.id` (16 hoy),
con la tabla y la columna que la declaran, el backref de `Documento` que la recorre y el
texto del uso. Se construye solo con backrefs de SQLAlchemy, a propósito, no con SQL a mano:
así el eager loading (`opciones_usos_documento`) es el mismo mecanismo que usa todo el resto
y un listado no paga una consulta por documento.

Por qué el registro y no una lista de `if` (lo que hubo hasta #881): cada vez que alguien
añadió una tabla con FK a `documentos`, la guarda de borrado no se enteró, y el mismo
agujero se cerró tres veces tarde —
- #738: sin mirar `notificacion`, un justificante que había perdido su vínculo de tarea
  parecía libre, y la fila `notificaciones` (`ON DELETE CASCADE`) se llevaba por delante la
  evidencia (canal, resultado, fecha);
- #838: las tres anclas de la solicitud (escrito, fin de instrucción, cierre), que el pool
  daba por libres y cuyo borrado moría en un `IntegrityError` con traza;
- #947: el documento de un certificado emitido y el que cierra una fase, igual.
Con #881 faltaban siete FK más (certificados de fase, diagnósticos, requisitos cubiertos,
interesados, organismos —dos— y la autorización de una dirección de notificación; esta
última es `SET NULL`: borrar el documento le habría quitado la autorización a la dirección
sin aviso). `desajustes_del_registro()` compara el registro con las FK que declara el
modelo, para que la próxima tabla con FK a `documentos` no pueda pasar desapercibida (una
entrada nueva es una FK nueva, y viceversa) y para que ninguna entrada quede cableada a otro
backref. Se ejecuta al arrancar, `app/checks/usos_documento.py`.

El certificado que **cita** un documento (`certificados.datos['documento_id']`, JSONB, no FK)
es un uso más pero no está en el registro: no tiene FK ni backref. Se resuelve por lotes con
`sellos.certificados_que_citan`.
"""
from __future__ import annotations

from collections import namedtuple

from sqlalchemy.orm import selectinload

from app.services import sellos

# codigo: etiqueta estable del tipo de uso · tabla/columna: la FK que lo declara ·
# atributo: backref de `Documento` que la recorre · texto: función objeto → frase del uso.
Referencia = namedtuple('Referencia', 'codigo tabla columna atributo texto')

CODIGO_CITADO_POR_CERTIFICADO = 'CITADO_POR_CERTIFICADO'


def _como_lista(valor) -> list:
    """Un backref es escalar (`uselist=False`) o lista, según el modelo: se normaliza."""
    if valor is None:
        return []
    if isinstance(valor, (list, tuple)):
        return list(valor)
    return [valor]


def _sol(solicitud) -> str:
    """«AAP #3»: el tipo de la solicitud y su número, sin lectura extra si falta el tipo."""
    tipo = solicitud.tipo_solicitud.siglas if solicitud.tipo_solicitud else None
    return f'{tipo} #{solicitud.id}' if tipo else f'#{solicitud.id}'


def _entidad(entidad) -> str:
    return entidad.nombre_completo if entidad is not None else 'una entidad'


def _texto_vinculo_tarea(vinculo) -> str:
    accion = 'Consumido por' if vinculo.rol == 'CONSUMIDO' else 'Producido por'
    tarea = vinculo.tarea
    tipo = tarea.tipo_tarea.nombre if tarea is not None and tarea.tipo_tarea else None
    tramite = (tarea.tramite.tipo_tramite.nombre
               if tarea is not None and tarea.tramite is not None and tarea.tramite.tipo_tramite
               else None)
    texto = f'{accion} la tarea {tipo}' if tipo else f'{accion} una tarea'
    return f'{texto} del trámite «{tramite}»' if tramite else texto


def _texto_notificacion(notificacion) -> str:
    canal = f' ({notificacion.canal})' if notificacion.canal else ''
    return f'Justificante de una notificación{canal}'


def _texto_reformado(corte) -> str:
    origen = f' ({corte.origen.lower()})' if corte.origen else ''
    return f'Abre un reformado de proyecto{origen}'


def _texto_fase_resultado(fase) -> str:
    nombre = fase.tipo_fase.nombre if fase.tipo_fase else f'#{fase.id}'
    return f'Documento de resultado de la fase «{nombre}»'


def _texto_diagnostico(diagnostico) -> str:
    resultado = f' ({diagnostico.resultado})' if diagnostico.resultado else ''
    return f'Es el diagnóstico de un análisis{resultado}'


def _texto_requisito(vinculo) -> str:
    requisito = vinculo.requisito
    tipo = (requisito.tipo_documento.nombre
            if requisito is not None and requisito.tipo_documento else None)
    return f'Cubre el requisito documental «{tipo}»' if tipo else 'Cubre un requisito documental'


def _texto_interesado(interesado) -> str:
    nombre = interesado.nombre or (interesado.entidad.nombre_completo if interesado.entidad else None)
    if nombre:
        return f'Acredita al interesado «{nombre}»'
    return f'Acredita a un interesado ({(interesado.tipo_origen or "").lower()})'


def _texto_organismo(prefijo):
    def texto(organismo_expediente) -> str:
        return f'{prefijo} «{_entidad(organismo_expediente.organismo)}»'
    return texto


REFERENCIAS = (
    Referencia('TAREA', 'documentos_tarea', 'documento_id', 'vinculos_tarea',
               _texto_vinculo_tarea),
    Referencia('NOTIFICACION', 'notificaciones', 'documento_id', 'notificacion',
               _texto_notificacion),
    Referencia('REFORMADO', 'reformados_proyecto', 'documento_id', 'reformado_proyecto',
               _texto_reformado),
    Referencia('PROYECTO_PRINCIPAL', 'proyectos', 'documento_principal_id',
               'anclado_como_proyecto_principal',
               lambda proyecto: 'Es el proyecto de la instalación'),
    Referencia('SOLICITUD', 'solicitudes', 'documento_solicitud_id', 'anclado_en_solicitud',
               lambda s: f'Escrito de la solicitud {_sol(s)}'),
    Referencia('FIN_INSTRUCCION', 'solicitudes', 'documento_fin_instruccion_id',
               'anclado_en_fin_instruccion',
               lambda s: f'Certificado de fin de instrucción de la solicitud {_sol(s)}'),
    Referencia('CIERRE', 'solicitudes', 'documento_cierre_id', 'anclado_en_cierre',
               lambda s: f'Certificado de cierre de la solicitud {_sol(s)}'),
    Referencia('FASE_RESULTADO', 'fases', 'documento_resultado_id', 'fases_resultado',
               _texto_fase_resultado),
    Referencia('CERTIFICADO', 'certificados', 'documento_id', 'certificado',
               lambda c: f'Es un certificado emitido ({c.tipo})'),
    Referencia('CERTIFICADO_FASE', 'certificados_fase', 'documento_id', 'certificados_fase',
               lambda c: f'PDF del certificado de fase ({c.tipo_cert})'),
    Referencia('DIAGNOSTICO', 'diagnosticos', 'documento_id', 'diagnostico',
               _texto_diagnostico),
    Referencia('REQUISITO', 'documentos_requisito', 'documento_id', 'cubre_requisitos',
               _texto_requisito),
    Referencia('INTERESADO', 'interesados_expediente', 'documento_acreditativo_id',
               'acredita_interesados', _texto_interesado),
    Referencia('ORGANISMO', 'organismos_expediente', 'documento_id', 'usado_por_organismos',
               _texto_organismo('Documento del organismo')),
    Referencia('ORGANISMO_CONDICIONADOS', 'organismos_expediente', 'condicionados_doc_id',
               'condicionado_de_organismos', _texto_organismo('Condicionado del organismo')),
    Referencia('DIRECCION_AUTORIZACION', 'direcciones_notificacion',
               'documento_autorizacion_id', 'autoriza_direcciones',
               lambda d: f'Autoriza una dirección de notificación de «{_entidad(d.entidad)}»'),
)


def _usos(documento, certificado_que_cita) -> list:
    usos = []
    for referencia in REFERENCIAS:
        for objeto in _como_lista(getattr(documento, referencia.atributo)):
            usos.append({'codigo': referencia.codigo, 'texto': referencia.texto(objeto)})
    if certificado_que_cita is not None:
        fase = certificado_que_cita.fase
        nombre = fase.tipo_fase.nombre if fase is not None and fase.tipo_fase else 'una fase'
        usos.append({
            'codigo': CODIGO_CITADO_POR_CERTIFICADO,
            'texto': f'Lo cita el certificado de cumplimiento de la fase «{nombre}»',
        })
    return usos


def usos_de_documentos(documentos) -> dict:
    """`{documento_id: [uso, …]}` de varios documentos de una vez. Cada uso es
    `{codigo, texto}`; una lista vacía es un documento que nadie usa (borrable).

    Para listar, cargar los documentos con `.options(*opciones_usos_documento())`: así el
    cálculo son unas consultas por relación y no una por documento. Una sola consulta más
    resuelve qué certificado cita a cada documento (`sellos.certificados_que_citan`).
    """
    documentos = list(documentos)
    citan = sellos.certificados_que_citan(d.id for d in documentos)
    return {d.id: _usos(d, citan.get(d.id)) for d in documentos}


def usos_documento(documento) -> list:
    """Los usos de un documento (ver `usos_de_documentos`). Para un listado, el de lotes."""
    return usos_de_documentos([documento])[documento.id]


def opciones_usos_documento() -> tuple:
    """Eager loading de lo que lee `usos_de_documentos` (`.options(*opciones_usos_documento())`).

    Una carga por relación del registro, más lo que cada texto necesita de ella (el tipo de
    tarea y de trámite, el tipo de solicitud, el organismo…). Es función y no constante
    porque los backrefs solo existen cuando los mapeadores ya están configurados.
    """
    from app.models.direccion_notificacion import DireccionNotificacion
    from app.models.documentos import Documento
    from app.models.documentos_tarea import DocumentoTarea
    from app.models.fases import Fase
    from app.models.interesados_expediente import InteresadoExpediente
    from app.models.organismos_expediente import OrganismoExpediente
    from app.models.requisitos_documentales import DocumentoRequisito, RequisitoDocumental
    from app.models.solicitudes import Solicitud
    from app.models.tareas import Tarea
    from app.models.tramites import Tramite

    def carga(atributo):
        return selectinload(getattr(Documento, atributo))

    con_su_solicitud = {'anclado_en_solicitud', 'anclado_en_fin_instruccion', 'anclado_en_cierre'}
    profundas = {
        'vinculos_tarea': carga('vinculos_tarea')
        .selectinload(DocumentoTarea.tarea)
        .options(selectinload(Tarea.tipo_tarea),
                 selectinload(Tarea.tramite).selectinload(Tramite.tipo_tramite)),
        'fases_resultado': carga('fases_resultado').selectinload(Fase.tipo_fase),
        'cubre_requisitos': carga('cubre_requisitos')
        .selectinload(DocumentoRequisito.requisito)
        .selectinload(RequisitoDocumental.tipo_documento),
        'acredita_interesados': carga('acredita_interesados')
        .selectinload(InteresadoExpediente.entidad),
        'usado_por_organismos': carga('usado_por_organismos')
        .selectinload(OrganismoExpediente.organismo),
        'condicionado_de_organismos': carga('condicionado_de_organismos')
        .selectinload(OrganismoExpediente.organismo),
        'autoriza_direcciones': carga('autoriza_direcciones')
        .selectinload(DireccionNotificacion.entidad),
    }
    for atributo in con_su_solicitud:
        profundas[atributo] = carga(atributo).selectinload(Solicitud.tipo_solicitud)

    return tuple(profundas.get(r.atributo) or carga(r.atributo) for r in REFERENCIAS)


def desajustes_del_registro() -> list:
    """Lo que no cuadra entre `REFERENCIAS` y el modelo, como frases legibles: vacía si todo cuadra.

    Es la guarda de este módulo, y está dentro del código y no en un test (`tests/README.md` §3,
    tercera pregunta): una FK hacia `documentos` que se olvide aquí no da ningún error, deja el
    documento «libre» y se puede borrar —con `CASCADE` o `SET NULL`, perdiendo el dato—. Se
    comprueba al arrancar (`app/checks/usos_documento.py`, como `registro_variables`, #587). Mira
    tres cosas:

    1. Una FK del modelo hacia `documentos.id` sin su entrada: el hueco de #738, #838 y #947.
    2. Una entrada sin FK: un nombre mal escrito, o una FK que se retiró.
    3. Una entrada **mal cableada**: `Documento.<atributo>` no recorre la FK que la entrada dice
       (un backref equivocado contaría los usos contra otra tabla sin avisar de nada), o ni
       siquiera existe.
    """
    from sqlalchemy import inspect as inspeccionar

    from app import db
    from app.models.documentos import Documento

    declaradas = {
        (fk.parent.table.name, fk.parent.name)
        for tabla in db.metadata.tables.values()
        for fk in tabla.foreign_keys
        if fk.column.table.name == 'documentos'
    }
    registradas = {(r.tabla, r.columna) for r in REFERENCIAS}

    avisos = []
    for tabla, columna in sorted(declaradas - registradas):
        avisos.append(
            f'{tabla}.{columna} referencia documentos.id y no tiene su uso en REFERENCIAS: el '
            f'documento que referencia saldría «libre» y se podría borrar')
    for tabla, columna in sorted(registradas - declaradas):
        avisos.append(
            f'REFERENCIAS registra {tabla}.{columna}, que no es una FK hacia documentos.id '
            f'(¿mal escrita, o la FK se retiró?)')

    relaciones = inspeccionar(Documento).relationships
    for r in REFERENCIAS:
        if r.atributo not in relaciones:
            avisos.append(f'{r.codigo}: Documento no tiene la relación «{r.atributo}»')
            continue
        recorre = {(remota.table.name, remota.name)
                   for _local, remota in relaciones[r.atributo].local_remote_pairs}
        if (r.tabla, r.columna) not in recorre:
            avisos.append(
                f'{r.codigo}: Documento.{r.atributo} no recorre {r.tabla}.{r.columna} sino '
                f'{sorted(recorre)}: los usos se contarían contra otra FK')
    return avisos
