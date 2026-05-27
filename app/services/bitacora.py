"""Servicio de escritura en el cuaderno de bitácora (issue #1)."""
from app import db
from app.models.bitacora import Bitacora


def registrar(usuario_id, operacion, tabla, registro_id, *, columna=None, detalle=None):
    """
    Añade una entrada al cuaderno de bitácora.

    No valida dominio. No filtra. No decide si registrar — eso es responsabilidad
    del consumidor. El commit es responsabilidad del consumidor.
    """
    entrada = Bitacora(
        usuario_id=usuario_id,
        operacion=operacion,
        tabla=tabla,
        registro_id=registro_id,
        columna=columna,
        detalle=detalle,
    )
    db.session.add(entrada)
    return entrada
