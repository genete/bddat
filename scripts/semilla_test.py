"""Semilla de la base de tests (#849).

Lo que las migraciones no traen y la suite necesita: usuarios con sus roles, y
el árbol de ficheros donde los tests pueden escribir sin ensuciar el de
desarrollo.

**Usuarios ad-hoc, no copia de desarrollo.** Están diseñados para escribir
tests, no para parecerse a nadie: por eso hay un segundo TRAMITADOR y un
usuario desactivado. Con los usuarios de desarrollo hay comprobaciones que no
se pueden escribir —`es_expediente_ajeno()` (`app/utils/permisos.py:175`) exige
un tramitador que NO sea responsable del expediente, y no existía ninguno—.

No siembra datos de negocio: expedientes, solicitudes y documentos vienen
después, por `alta_expediente()` y los expedientes-tipo, cuando #428 cierre.
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
        n_plantillas = _plantillas_inactivas(db)
        db.session.commit()
        rutas = _arbol_ficheros(app)

    print(f'[semilla] usuarios creados: {n_usuarios} (de {len(USUARIOS)} previstos)')
    print(f'[semilla] plantillas desactivadas: {n_plantillas}')
    for r in rutas:
        print(f'[semilla] creado directorio {r}')
