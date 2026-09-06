"""Semilla de la base de tests (#849).

Lo que las migraciones no traen y la suite necesita: usuarios con sus roles,
las entidades con las que se tramita, y el árbol de ficheros donde los tests
pueden escribir sin ensuciar el de desarrollo.

**Usuarios ad-hoc, no copia de desarrollo.** Están diseñados para escribir
tests, no para parecerse a nadie: por eso hay un segundo TRAMITADOR y un
usuario desactivado. Con los usuarios de desarrollo hay comprobaciones que no
se pueden escribir —`es_expediente_ajeno()` (`app/utils/permisos.py:175`) exige
un tramitador que NO sea responsable del expediente, y no existía ninguno—.

**Datos de negocio.** Desde #849.B también los siembra, y por la vía real —
`alta_expediente()` y el expediente-tipo, nunca INSERT sueltos—: un expediente
tramitado hasta el final de ANALISIS_SOLICITUD y otro recién dado de alta sin
responsable. Con ellos la suite pasó de 368 tests saltados por falta de datos a
ninguno.
"""
import os

CONTRASENA = 'test'  # Solo vale en la base de tests; nunca sale de esta máquina.

# siglas, nombre, apellido, roles, activo
USUARIOS = [
    ('TADM', 'Ada',    'Admin',        ['ADMIN'],                                    True),
    ('TSUP', 'Sara',   'Supervisora',  ['SUPERVISOR'],                               True),
    ('TTRA', 'Tomás',  'Tramitador',   ['TRAMITADOR'],                               True),
    ('TADV', 'Adela',  'Administra',   ['ADMINISTRATIVO'],                           True),
    ('TMUL', 'Marta',  'Multirrol',    ['SUPERVISOR', 'TRAMITADOR', 'ADMINISTRATIVO'], True),
    ('TTR2', 'Teo',    'Tramitador2',  ['TRAMITADOR'],                               True),
    ('TOFF', 'Olga',   'Inactiva',     ['TRAMITADOR'],                               False),
]

# Para qué existe cada uno, que es lo que se olvida en seis meses:
#   TADM  las cuatro operaciones exclusivas de ADMIN (bajas físicas y archivado)
#   TSUP  administración de catálogos
#   TTRA  tramitación; responsable de los expedientes de semilla
#   TADV  cola administrativa y subida al pool
#   TMUL  login de dos pasos y cambio de rol activo
#   TTR2  expediente ajeno: tramitador que no es responsable
#   TOFF  usuario desactivado


def _usuarios(db):
    from app.models.usuarios import Rol, Usuario

    roles = {r.nombre: r for r in Rol.query.all()}
    faltan = {n for _, _, _, rs, _ in USUARIOS for n in rs} - set(roles)
    if faltan:
        raise RuntimeError(f'Faltan roles en la base: {sorted(faltan)}')

    creados = 0
    for siglas, nombre, apellido, nombres_rol, activo in USUARIOS:
        if Usuario.query.filter_by(siglas=siglas).first():
            continue
        u = Usuario(
            siglas=siglas,
            siglas_escritos=siglas,
            nombre=nombre,
            apellido1=apellido,
            email=f'{siglas.lower()}@test.local',
            activo=activo,
        )
        u.set_password(CONTRASENA)
        u.roles = [roles[n] for n in nombres_rol]
        db.session.add(u)
        creados += 1
    return creados


# nif, nombre, abrev, (titular, consultado, publicador), tipo_titular
ENTIDADES = [
    ('B00000001', 'Promotora de Prueba S.L.', None, (True, False, False), 'PROMOTOR'),
    ('B00000002', 'Distribuidora de Prueba S.A.', None, (True, False, False),
     'GRAN_DISTRIBUIDORA'),
    ('Q0000001A', 'Confederación Hidrográfica de Prueba', 'CHP', (False, True, False), None),
    ('P0000002B', 'Ayuntamiento de Villaprueba', 'AYTO-VP', (False, True, True),
     None),
    ('Q0000003C', 'Delegación Territorial de Prueba', 'DT-P', (False, True, False), None),
]

# Para qué existe cada una, que es lo que se olvida en seis meses:
#   B00000001  titular por defecto de los expedientes de semilla
#   B00000002  segundo titular: expediente ajeno, filtros de listado
#   Q0000001A  organismo consultado con abreviatura (carpetas ESFTT, ADR-032 #665)
#   P0000002B  consultado Y publicador: tablón de ayuntamiento
#   Q0000003C  segundo consultado, para consultas con más de un destinatario


def _entidades(db):
    """Entidades ad-hoc, no copia de desarrollo — mismo criterio que los usuarios.

    Sin ellas 23 tests fallan y otros tantos se saltan: el titular es
    obligatorio para dar de alta un expediente, y las consultas a organismos
    necesitan alguien a quien consultar. Que la tabla esté vacía es un defecto
    de la semilla, no un motivo para saltarse el test (#849, criterio 6).
    """
    from app.models.entidad import Entidad

    creadas = 0
    for nif, nombre, abrev, (titular, consultado, publicador), tipo in ENTIDADES:
        if Entidad.query.filter_by(nif=nif).first():
            continue
        db.session.add(Entidad(
            nif=nif,
            nombre_completo=nombre,
            abrev=abrev,
            rol_titular=titular,
            rol_consultado=consultado,
            rol_publicador=publicador,
            tipo_titular=tipo,
            activo=True,
        ))
        creadas += 1
    return creadas


def _plantillas_inactivas(db):
    """Las plantillas sembradas por migración apuntan a .docx que aquí no están.

    Cuatro migraciones (#402, #403, #404, #776) registran plantillas con su
    `ruta_plantilla` bajo PLANTILLAS_BASE. En la base de tests los registros
    existen pero los ficheros no, así que un test de generación fallaría por el
    fichero ausente y no por la lógica. Se desactivan: el test que quiera
    ejercitar una plantilla se fabrica la suya.
    """
    from app.models.plantillas import Plantilla

    afectadas = Plantilla.query.filter_by(activo=True).all()
    for p in afectadas:
        p.activo = False
    return len(afectadas)


def _modulos_expediente_tipo():
    """Los expedientes-tipo que alimentan la base de tests.

    Añadir aquí el módulo es todo lo que hace falta para que un escenario de
    desarrollo sirva también de semilla — y para que deje de poder pudrirse en
    silencio: si un cambio de la aplicación lo rompe, `preparar_bd_test.py
    --recrear` falla en vez de esperar a que alguien lo ejecute a mano.
    """
    from scripts.expedientes_dummy import (
        analisis_doc_dos_vueltas, consultas_varios_estados,
    )
    return (analisis_doc_dos_vueltas, consultas_varios_estados)


def _expedientes(app):
    """Los datos de negocio: los expedientes-tipo completos, por el circuito real.

    Son los mismos escenarios que se construyen en desarrollo
    (`scripts/expedientes_dummy/`), invocados con la app de tests y sin sus
    efectos de máquina —`efectos_desarrollo=False` deja fuera el reloj
    simulado—. Se reutilizan en vez de escribir una semilla paralela a
    propósito: dos caminos que construyen lo mismo terminan divergiendo, que es
    justo lo que #428 tuvo que arreglar entre el wizard y el script.

    Idempotente uno a uno: el que ya esté no se vuelve a construir. Recrear la
    base (`preparar_bd_test.py --recrear`) es la vía para partir de cero.

    Devuelve [(codigo, expediente_id | None), ...] — `None` en los que ya estaban.
    """
    from app.models.solicitudes import Solicitud

    construidos = []
    for tipo in _modulos_expediente_tipo():
        with app.app_context():
            existente = Solicitud.query.filter(
                Solicitud.observaciones.like(f'{tipo.MARCA}%')).first()
        if existente is not None:
            construidos.append((tipo.CODIGO, None))
            continue
        _numero_at, expediente_id = tipo.main(app, efectos_desarrollo=False)
        construidos.append((tipo.CODIGO, expediente_id))
    return construidos


def _expediente_sin_asignar(app):
    """Un segundo expediente, del otro titular y sin responsable.

    No es un escenario de tramitación: es la variedad mínima que la suite
    necesita y que un solo expediente no puede dar —«otro expediente» para los
    tests de aislamiento entre expedientes, y uno «sin asignar» para la
    asignación masiva—. Por `alta_expediente()`, como todo lo demás.
    """
    import os
    from datetime import timedelta

    from app.models.entidad import Entidad
    from app.models.municipios import Municipio
    from app.models.solicitudes import Solicitud
    from app.models.tipos_expedientes import TipoExpediente
    from app.models.tipos_solicitudes import TipoSolicitud
    from app.services.alta_expediente import (
        DatosAlta, DocumentoSolicitud, alta_expediente,
    )
    from app.services.reloj_simulado import hoy

    marca = '[SEMILLA] expediente sin responsable'
    with app.app_context():
        if Solicitud.query.filter_by(observaciones=marca).first() is not None:
            return None

        titular = (Entidad.query
                   .filter(Entidad.rol_titular.is_(True), Entidad.activo.is_(True))
                   .order_by(Entidad.id.desc()).first())
        municipio = Municipio.query.order_by(Municipio.id).first()
        tipo_exp = TipoExpediente.query.order_by(TipoExpediente.id).first()
        tipo_sol = TipoSolicitud.query.filter_by(siglas='AAP').first()
        for nombre, valor in (('entidad titular', titular), ('municipio', municipio),
                              ('tipo de expediente', tipo_exp),
                              ("tipo de solicitud 'AAP'", tipo_sol)):
            if valor is None:
                raise RuntimeError(f'Falta {nombre} para el expediente de semilla')

        ruta_pdf = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'tests', 'fixtures', 'documentos_dummy', 'modelo_solicitud.pdf')
        with open(ruta_pdf, 'rb') as f:
            contenido = f.read()

        resultado = alta_expediente(DatosAlta(
            tipo_expediente_id=tipo_exp.id,
            responsable_id=None,
            heredado=False,
            titulo='Centro de transformación Camino de la Vega',
            descripcion='Segundo expediente de semilla, sin tramitar.',
            finalidad='Distribución de energía eléctrica',
            emplazamiento='T.M. de prueba',
            fecha_proyecto=hoy() - timedelta(days=20),
            ia_id=None,
            municipios_ids=[municipio.id],
            titular_id=titular.id,
            tipo_solicitud_id=tipo_sol.id,
            solicitante_id=titular.id,
            observaciones=marca,
            documento=DocumentoSolicitud(
                contenido=contenido,
                nombre_original='modelo_solicitud.pdf',
                fecha_registro=hoy() - timedelta(days=10),
            ),
        ))
        return resultado.expediente.id


def _arbol_ficheros(app):
    """Crea la raíz de ficheros de tests si no existe."""
    creados = []
    for clave in ('FILESYSTEM_BASE', 'PLANTILLAS_BASE'):
        ruta = app.config.get(clave)
        if not ruta:
            raise RuntimeError(f'{clave} sin configurar en la config de tests')
        if not os.path.isdir(ruta):
            os.makedirs(ruta, exist_ok=True)
            creados.append(ruta)
    return creados


def sembrar(app):
    """Punto de entrada. Idempotente: se puede repetir sobre una base sembrada."""
    from app import db

    with app.app_context():
        n_usuarios = _usuarios(db)
        n_entidades = _entidades(db)
        n_plantillas = _plantillas_inactivas(db)
        db.session.commit()
        rutas = _arbol_ficheros(app)

    print(f'[semilla] usuarios creados: {n_usuarios} (de {len(USUARIOS)} previstos)')
    print(f'[semilla] entidades creadas: {n_entidades} (de {len(ENTIDADES)} previstas)')
    print(f'[semilla] plantillas desactivadas: {n_plantillas}')
    for r in rutas:
        print(f'[semilla] creado directorio {r}')

    # Fuera del app_context de arriba: cada expediente-tipo abre el suyo propio,
    # y necesitan el árbol de ficheros ya creado para subir documentos al pool.
    for codigo, expediente_id in _expedientes(app):
        if expediente_id is None:
            print(f'[semilla] expediente-tipo {codigo}: ya estaba, no se construye otro')
        else:
            print(f'[semilla] expediente-tipo {codigo} construido '
                  f'(expediente id={expediente_id})')

    segundo_id = _expediente_sin_asignar(app)
    if segundo_id is None:
        print('[semilla] expediente sin responsable: ya estaba')
    else:
        print(f'[semilla] expediente sin responsable creado (id={segundo_id})')
