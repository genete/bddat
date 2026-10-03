"""Contenidos guardados en el almacén (ADR-050 §B, §C; #1007).

Una fila por cada contenido distinto que BDDAT ha guardado en el almacén. No
sabe nada de expedientes, nombres ni tareas: eso es de `documentos`, que apunta
aquí con `fichero_ref`.

**Solo la lee y la escribe el subsistema de almacenamiento**
(`app/services/almacenamiento/`): el resto de BDDAT trabaja con `documentos.id`
y pide el contenido al módulo de contenido. Las comprobaciones que dan coherencia
al contenido (sellado, bitácora) viven ahí, y quien escribiera aquí por su cuenta
se las saltaría. Lo vigila un test.
"""
from app import db

# Estados de un contenido (CHECK `ck_ficheros_estado` en la migración).
OK = 'OK'
CORRUPTO = 'CORRUPTO'
AUSENTE = 'AUSENTE'
ESTADOS = (OK, CORRUPTO, AUSENTE)


class Fichero(db.Model):
    """Un contenido del almacén, con su ref y su hash.

    `ref` y `contenido_sha256` van por separado a propósito (ADR-050 §B): la
    `ref` es lo que entiende el almacén y su forma es asunto suyo; el
    `contenido_sha256` lo calcula BDDAT sea cual sea el almacén, y es lo que usan
    la deduplicación, el aviso de «ya existe» y la integridad. Que con el almacén
    de hoy coincidan es casualidad de ese almacén, no un contrato.

    Restricciones en la migración `1007_almacen_ficheros`: `contenido_sha256`
    único y en hexadecimal en minúsculas (dos grafías del mismo hash romperían
    la deduplicación), `tamano` no negativo y `estado` en `ESTADOS`.
    """
    __tablename__ = 'ficheros'
    __table_args__ = {'schema': 'public'}

    ref = db.Column(
        db.Text,
        primary_key=True,
        comment='Lo que devuelve el almacén para volver a encontrar el contenido. Opaca para el resto de BDDAT',
    )
    contenido_sha256 = db.Column(
        db.CHAR(64),
        nullable=False,
        unique=True,
        comment='SHA-256 del contenido, calculado por BDDAT. Deduplicación, aviso de duplicado e integridad',
    )
    tamano = db.Column(
        db.BigInteger,
        nullable=False,
        comment='Tamaño en bytes',
    )
    formato = db.Column(
        db.Text,
        nullable=False,
        comment='MIME detectado por el contenido, no por la extensión (ADR-050 §E)',
    )
    fecha_creacion = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        comment='Cuándo se guardó por primera vez',
    )
    fecha_verificacion = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        comment='Última comprobación de integridad (fase 7)',
    )
    estado = db.Column(
        db.String(10),
        nullable=False,
        default=OK,
        server_default=OK,
        comment='OK | CORRUPTO | AUSENTE. Un contenido que no está OK no se usa ni se vincula (ADR-050 §G)',
    )
    fecha_sin_referencias = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
        comment='Desde cuándo no lo referencia nada: el reloj de la limpieza (fase 7)',
    )

    def __repr__(self):
        return f'<Fichero {self.ref[:12]}… {self.estado}>'
