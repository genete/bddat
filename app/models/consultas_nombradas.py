from app import db


class ConsultaNombrada(db.Model):
    """
    Catálogo de consultas SQL predefinidas para uso en plantillas .docx.

    PROPÓSITO:
        Permite que el supervisor inserte tablas dinámicas en plantillas sin
        necesidad de escribir SQL. Referencia la consulta por nombre en el
        marcador de plantilla: {%tr for row in municipios_afectados %}.

        BDDAT ejecuta el SQL parametrizado y pasa el resultado como contexto
        a python-docx-template.

    CAMPOS:
        nombre      — Slug estable usado en la plantilla (.docx) y en código.
                      Debe ser snake_case: municipios_afectados, organismos_consultados.
        descripcion — Texto legible mostrado al supervisor en el contextualizador.
        sql         — SQL parametrizado. Parámetro esperado: :expediente_id
        columnas    — [{campo, descripcion}] para mostrar al supervisor qué campos
                      puede usar dentro del bloque de tabla (row.nombre, row.provincia...).
        activo      — FALSE = oculta en UI pero conservada para histórico de plantillas.
    """
    __tablename__ = 'consultas_nombradas'
    __table_args__ = (
        db.UniqueConstraint('nombre', name='uq_consultas_nombradas_nombre'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    nombre = db.Column(
        db.Text,
        nullable=False,
        comment='Slug estable usado en plantillas: municipios_afectados'
    )

    descripcion = db.Column(
        db.Text,
        nullable=False,
        comment='Descripción legible para el supervisor en la UI'
    )

    sql = db.Column(
        db.Text,
        nullable=False,
        comment='SQL parametrizado. Parámetro esperado: :expediente_id'
    )

    columnas = db.Column(
        db.JSON,
        nullable=False,
        comment='[{campo, descripcion}] — columnas disponibles para el supervisor'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment='FALSE = oculta en UI pero conservada para histórico'
    )

    def __repr__(self):
        return f'<ConsultaNombrada {self.nombre}>'

    def __str__(self):
        return self.descripcion
