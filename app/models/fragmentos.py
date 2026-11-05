"""Fragmentos de escritos (ADR-050 §J; #1009).

Un fragmento es un trozo de texto que comparten varias plantillas (el pie de recurso, los
fundamentos de derecho) y se cita en ellas con `{{r Nombre }}`. Su contenido vive en el
almacén: `fichero_ref` apunta a su fila de `ficheros`.

**`fichero_ref` solo lo lee y lo escribe el subsistema de almacenamiento**
(`app/services/almacenamiento/`), como el de `documentos` y el de `plantillas`: el resto de
BDDAT trabaja con el nombre del fragmento y le pide el contenido al módulo de contenido.
Lo vigila `tests/test_1007_subsistema_almacenamiento.py`.
"""
from app import db


class Fragmento(db.Model):
    """Un fragmento citable desde las plantillas.

    La clave es (`nombre`, `formato`): un fragmento `.docx` y otro `.odt` pueden llamarse
    igual, porque cada motor busca el de su formato. `formato` es el MIME de su fichero
    (`ficheros.formato`) y lo copia el módulo de contenido del fichero ya guardado; no viene
    de un formulario.

    Que `nombre` se pueda citar con `{{r Nombre }}` (`\\w+`, como lo reconocen los dos motores)
    lo comprueba el módulo de contenido al subir; la BD no lo valida porque el `\\w` de
    Postgres depende del locale.

    `activo = False` es un fragmento retirado: no se inserta al generar, y para la generación
    equivale a ausente (un fragmento ausente detiene la generación, ADR-050 §J).
    """
    __tablename__ = 'fragmentos'
    __table_args__ = (
        db.UniqueConstraint('nombre', 'formato', name='uq_fragmentos_nombre_formato'),
        {'schema': 'public'},
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
        comment='La clave de {{r Nombre }} en las plantillas. Con formato forma la clave única'
    )

    formato = db.Column(
        db.Text,
        nullable=False,
        comment='MIME del fichero, el de ficheros.formato. Lo copia el módulo de contenido del '
                'fichero guardado; un fragmento .docx y otro .odt pueden llamarse igual'
    )

    descripcion = db.Column(
        db.Text,
        nullable=True,
        comment='Para quien gestiona los fragmentos'
    )

    activo = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        server_default='true',
        comment='FALSE = fragmento retirado: no se inserta al generar (equivale a ausente)'
    )

    fichero_ref = db.Column(
        db.Text,
        db.ForeignKey('public.ficheros.ref', name='fk_fragmentos_fichero_ref'),
        nullable=False,
        comment='Contenido del fragmento en el almacén (ADR-050 §J). Solo lo usa el subsistema de almacenamiento'
    )

    def __repr__(self):
        return f'<Fragmento {self.nombre} {self.formato}>'

    def __str__(self):
        return self.nombre
