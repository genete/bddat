import uuid

from app import db


class ActivoRed(db.Model):
    """
    Tabla base de identidad de los activos de red (#591).

    Corte mínimo de integración con el modelo técnico de
    https://github.com/genete/bddat-instalaciones (ADR-000/ADR-002 de ese
    repositorio). Deliberadamente delgada: no es instanciable por sí sola,
    toda fila tiene una especialización (por ahora, únicamente Envolvente).

    PK en UUID (uuid7, generado en Python) porque es el "gancho" de
    referencia que también usará el modelo externo — un id autoincremental
    de esta BD no tendría significado fuera de BDDAT. `envolvente_id` es
    autorreferencia genérica de contención: la puede ejercer cualquier
    activo con ubicación, no solo los de tipo Envolvente (ADR-006 C8).
    """
    __tablename__ = 'activo_red'
    __table_args__ = (
        db.Index('idx_activo_red_envolvente', 'envolvente_id'),
        {'schema': 'public'},
    )

    id = db.Column(
        db.Uuid,
        primary_key=True,
        default=uuid.uuid7,
        comment='UUID (uuid7) generado en Python — gancho de referencia externo',
    )

    nombre = db.Column(
        db.Text,
        nullable=False,
        comment='Denominación del activo',
    )

    envolvente_id = db.Column(
        db.Uuid,
        db.ForeignKey('public.activo_red.id'),
        nullable=True,
        comment='Contenedor (físico o lógico). Autorreferencia',
    )

    notas = db.Column(
        db.Text,
        nullable=True,
        comment='Texto libre para datos ocasionales',
    )

    contenido = db.relationship(
        'ActivoRed',
        backref=db.backref('contenedor', remote_side=[id]),
    )

    def __repr__(self):
        return f'<ActivoRed id={self.id} nombre={self.nombre!r}>'

    def __str__(self):
        return self.nombre


# Tipos de envolvente física (recinto — RD 337/2014) y lógica (agrupación de
# líneas, sin recinto — RD 223/2008). Ver modelo-datos.md de bddat-instalaciones.
TIPOS_ENVOLVENTE_FISICA = frozenset({
    'centro_transformacion', 'subestacion', 'posicion',
    'armario_seccionamiento', 'celda_prefabricada',
    'planta_fotovoltaica', 'parque_eolico',
    'planta_almacenamiento', 'planta_hibrida',
})
TIPOS_ENVOLVENTE_LOGICA = frozenset({'linea', 'circuito'})


class Envolvente(db.Model):
    """
    Contenedor de activo_red (recinto físico o agrupación lógica), anidable.

    Única subtabla de activo_red en este corte mínimo. El `tipo` distingue
    envolventes físicas (RD 337/2014) de lógicas (RD 223/2008) — ver
    TIPOS_ENVOLVENTE_FISICA / TIPOS_ENVOLVENTE_LOGICA.
    """
    __tablename__ = 'envolvente'
    __table_args__ = (
        db.CheckConstraint(
            "tipo IN ("
            "'centro_transformacion', 'subestacion', 'posicion', "
            "'armario_seccionamiento', 'celda_prefabricada', "
            "'planta_fotovoltaica', 'parque_eolico', "
            "'planta_almacenamiento', 'planta_hibrida', "
            "'linea', 'circuito'"
            ")",
            name='ck_envolvente_tipo',
        ),
        {'schema': 'public'},
    )

    activo_id = db.Column(
        db.Uuid,
        db.ForeignKey('public.activo_red.id'),
        primary_key=True,
    )

    tipo = db.Column(
        db.String(30),
        nullable=False,
        comment='Tipo físico o lógico de envolvente — ver TIPOS_ENVOLVENTE_*',
    )

    activo = db.relationship(
        'ActivoRed',
        backref=db.backref('envolvente', uselist=False),
    )

    @property
    def es_fisica(self) -> bool:
        return self.tipo in TIPOS_ENVOLVENTE_FISICA

    @property
    def es_logica(self) -> bool:
        return self.tipo in TIPOS_ENVOLVENTE_LOGICA

    def __repr__(self):
        return f'<Envolvente activo={self.activo_id} tipo={self.tipo}>'
