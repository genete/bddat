"""Cuaderno de bitácora agnóstico de operaciones (issue #1)."""
from __future__ import annotations

from sqlalchemy.dialects.postgresql import JSONB

from app import db


class Bitacora(db.Model):
    __tablename__ = 'bitacora'
    __table_args__ = {'schema': 'public'}

    id          = db.Column(db.Integer, primary_key=True)
    usuario_id  = db.Column(db.Integer, db.ForeignKey('public.usuarios.id'), nullable=False)
    operacion   = db.Column(db.String(10), nullable=False)
    tabla       = db.Column(db.String(60), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    columna     = db.Column(db.String(60), nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True), server_default=db.text('now()'), nullable=False)
    detalle     = db.Column(
        db.JSON().with_variant(JSONB(), 'postgresql'), nullable=True,
        comment='dict generado por código, sin valor probatorio en el orden de '
                'claves — jsonb, no json (#802). Es la tabla que más crece de '
                'todo el sistema (append-only) y la candidata número uno a '
                'consultar por dentro («¿quién tocó el campo X?») e indexar con GIN',
    )
