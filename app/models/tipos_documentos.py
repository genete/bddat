from app import db


class TipoDocumento(db.Model):
    """
    Catálogo maestro de tipos semánticos de documentos.

    PROPÓSITO:
        Clasificación de negocio de los documentos (distinta del tipo MIME).
        Permite al motor de reglas evaluar la existencia de un documento
        por su tipo semántico (criterio EXISTE_DOCUMENTO_TIPO).

    CÓDIGO:
        Identificador textual único estable, usado en el motor de reglas
        y en el código para referenciar tipos sin depender del id numérico.
        Ejemplos: OTROS, DR_NO_DUP, INFORME_ORGANISMO, RESOLUCION, ...

    CAJÓN DE SASTRE:
        'OTROS' (id=1, server_default) agrupa documentos sin tipo definido.
        Es el tipo por defecto al crear un documento.
    """
    __tablename__ = 'tipos_documentos'
    __table_args__ = (
        db.UniqueConstraint('codigo', name='uq_tipos_documentos_codigo'),
        {'schema': 'public'}
    )

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Identificador único autogenerado'
    )

    codigo = db.Column(
        db.Text,
        nullable=False,
        comment='Código textual único estable (usado en motor de reglas y código)'
    )

    nombre = db.Column(
        db.Text,
        nullable=False,
        comment='Nombre legible para mostrar en interfaz'
    )

    descripcion = db.Column(
        db.Text,
        nullable=True,
        comment='Descripción ampliada del tipo de documento'
    )

    origen = db.Column(
        db.String(10),
        nullable=False,
        default='AMBOS',
        server_default='AMBOS',
        comment='Origen: INTERNO (generado por administración), EXTERNO (aportado por interesado), AMBOS'
    )

    def __repr__(self):
        return f'<TipoDocumento {self.codigo}>'

    def __str__(self):
        return self.nombre
