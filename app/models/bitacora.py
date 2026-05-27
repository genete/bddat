"""Cuaderno de bitácora agnóstico de operaciones (issue #1)."""
from __future__ import annotations

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
    detalle     = db.Column(db.JSON, nullable=True)
